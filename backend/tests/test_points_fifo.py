"""积分 FIFO 消耗测试 - V1 核心业务逻辑

执行:
    cd backend
    pytest tests/test_points_fifo.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.core.database import Base
from app.models.user import User
from app.models.point import PointAccount, PointTransaction
from app.services import points_service
from app.services.config_service import _cache


# 用 SQLite 内存数据库跑测试
@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    _cache.clear()  # 清空配置缓存
    yield db
    db.close()


@pytest.fixture
def user(db):
    u = User(phone="13800000001", invite_code="TEST01")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_grant_points_creates_account_and_transaction(db, user):
    """加分应同时建账户批次 + 流水"""
    acc = points_service.grant_points(
        db,
        user_id=user.id,
        point_type="trial",
        amount=50,
        source="trial",
        feature="register",
    )
    db.commit()

    accounts = db.query(PointAccount).filter(PointAccount.user_id == user.id).all()
    assert len(accounts) == 1
    assert accounts[0].balance == 50
    assert accounts[0].total_earned == 50

    txns = db.query(PointTransaction).filter(PointTransaction.user_id == user.id).all()
    assert len(txns) == 1
    assert txns[0].change == 50
    assert txns[0].balance_after == 50


def test_fifo_consume_order(db, user):
    """FIFO 消耗：subscription 先于 trial 先于 purchase"""
    # 加 3 种积分
    points_service.grant_points(
        db, user.id, "purchase", 100, "purchase", expire_at=None
    )
    db.commit()
    # 让 subscription 早于 trial 入账(让 subscription 先消耗)
    points_service.grant_points(
        db,
        user.id,
        "subscription",
        200,
        "sub",
        expire_at=datetime.now(timezone.utc) + timedelta(days=10),
    )
    db.commit()
    points_service.grant_points(
        db,
        user.id,
        "trial",
        300,
        "trial",
        expire_at=datetime.now(timezone.utc) + timedelta(days=90),
    )
    db.commit()

    # 消耗 250 分
    total, txns = points_service.consume_points(
        db, user.id, amount=250, feature="full_rewrite"
    )
    db.commit()

    assert total == 250
    # 应该有 2 笔流水(200 subscription + 50 trial)
    assert len(txns) == 2
    # 第一笔扣的应该是 subscription
    assert txns[0].point_type == "subscription"
    assert txns[0].change == -200
    assert txns[1].point_type == "trial"
    assert txns[1].change == -50


def test_insufficient_points_raises(db, user):
    """余额不足应抛 INSUFFICIENT_POINTS"""
    points_service.grant_points(db, user.id, "trial", 30, "trial")
    db.commit()

    with pytest.raises(Exception) as exc:
        points_service.consume_points(db, user.id, amount=100, feature="test")
    assert (
        "积分不足" in str(exc.value)
        or "INSUFFICIENT" in str(exc.value)
        or "41001" in str(exc.value)
    )


def test_expired_accounts_ignored(db, user):
    """已过期的账户余额视为 0"""
    # 加 50 试用积分,但已过期
    points_service.grant_points(
        db,
        user.id,
        "trial",
        50,
        "trial",
        expire_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.commit()

    with pytest.raises(Exception):
        points_service.consume_points(db, user.id, amount=10, feature="test")


def test_balance_summary(db, user):
    """balance 汇总应按类型分组"""
    points_service.grant_points(db, user.id, "trial", 50, "trial")
    points_service.grant_points(db, user.id, "subscription", 500, "sub")
    points_service.grant_points(db, user.id, "purchase", 1000, "purchase")
    db.commit()

    bal = points_service.get_balance(db, user.id)
    assert bal["trial_balance"] == 50
    assert bal["subscription_balance"] == 500
    assert bal["purchase_balance"] == 1000
    assert bal["total_balance"] == 1550


def test_refund_adds_points(db, user):
    """退款应加分(走 grant_points)"""
    points_service.grant_points(db, user.id, "subscription", 500, "sub")
    db.commit()

    points_service.refund_points(
        db,
        user_id=user.id,
        point_type="subscription",
        amount=500,
        source="refund",
        feature="order_refund",
    )
    db.commit()

    bal = points_service.get_balance(db, user.id)
    assert bal["subscription_balance"] == 1000  # 500+500
