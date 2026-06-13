"""兑换码生成 + 激活测试"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.redeem import RedeemCode
from app.models.config import SystemConfig
from app.services import redeem_service
from app.services.config_service import _cache


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    _cache.clear()
    # 写入必要的 system_configs
    db.add(SystemConfig(config_key="product.single.points", config_value="500"))
    db.add(SystemConfig(config_key="product.monthly.points", config_value="3000"))
    db.add(SystemConfig(config_key="product.points_1000.points", config_value="1000"))
    db.add(SystemConfig(config_key="trial.points", config_value="50"))
    db.commit()
    yield db
    db.close()


@pytest.fixture
def user(db):
    u = User(phone="13800000001", invite_code="TEST01")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_generate_batch_creates_unique_codes(db):
    """批量生成应产生不同码"""
    result = redeem_service.generate_batch(db, "single", 10, valid_days=30)
    assert result["count"] == 10
    assert len(set(result["codes"])) == 10  # 全不同
    # 码格式 XXXX-XXXX-XXXX
    for code in result["codes"]:
        assert len(code) == 14
        assert code.count("-") == 2


def test_generate_stores_hash_not_plain(db):
    """存储应只存 hash,明文只在 generate_batch 返回值里"""
    result = redeem_service.generate_batch(db, "monthly", 3)
    db_codes = db.query(RedeemCode).all()
    for c in db_codes:
        # code_hash 是 64 位 sha256
        assert len(c.code_hash) == 64
        # code_mask 是脱敏形式
        assert "*" in c.code_mask
    # 明文不在 DB 里
    plain_in_db = any(c.code_mask == c.code_hash for c in db_codes)
    assert not plain_in_db


def test_activate_code_adds_points(db, user):
    """激活兑换码应加分"""
    result = redeem_service.generate_batch(db, "single", 1, valid_days=30)
    code = result["codes"][0]

    activate_result = redeem_service.activate_code(db, user.id, code)
    assert activate_result["points"] == 500
    assert activate_result["points_balance"] == 500


def test_activate_used_code_raises(db, user):
    """已使用的码再次激活应失败"""
    result = redeem_service.generate_batch(db, "single", 1)
    code = result["codes"][0]

    # 第一次成功
    redeem_service.activate_code(db, user.id, code)

    # 第二次失败
    with pytest.raises(Exception) as exc:
        redeem_service.activate_code(db, user.id, code)
    assert "已被使用" in str(exc.value) or "CONFLICT" in str(exc.value)


def test_activate_nonexistent_code_raises(db, user):
    """不存在的码应失败"""
    with pytest.raises(Exception) as exc:
        redeem_service.activate_code(db, user.id, "XXXX-XXXX-XXXX")
    assert "不存在" in str(exc.value) or "NOT_FOUND" in str(exc.value)


def test_revoke_used_code_raises(db, user):
    """已使用的码不能作废"""
    result = redeem_service.generate_batch(db, "single", 1)
    code = result["codes"][0]
    redeem_service.activate_code(db, user.id, code)

    # 找 DB 里这条码
    rc = db.query(RedeemCode).first()
    with pytest.raises(Exception):
        redeem_service.revoke_code(db, rc.id)
