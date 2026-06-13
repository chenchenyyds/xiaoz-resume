"""订单 + 支付测试(不调真实虎皮椒,只测试本地逻辑)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

from app.core.database import Base
from app.models.user import User
from app.models.order import Order
from app.models.point import PointAccount
from app.models.config import SystemConfig
from app.services import order_service
from app.services.config_service import _cache


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    _cache.clear()
    db.add(SystemConfig(config_key="product.single.price", config_value="9.9"))
    db.add(SystemConfig(config_key="product.single.points", config_value="500"))
    db.add(SystemConfig(config_key="product.single.valid_days", config_value="30"))
    db.add(SystemConfig(config_key="product.monthly.price", config_value="29"))
    db.add(SystemConfig(config_key="product.monthly.points", config_value="3000"))
    db.add(SystemConfig(config_key="product.monthly.valid_days", config_value="30"))
    db.add(SystemConfig(config_key="product.points_1000.price", config_value="10"))
    db.add(SystemConfig(config_key="product.points_1000.points", config_value="1000"))
    db.add(SystemConfig(config_key="commission.single", config_value="0.20"))
    db.add(SystemConfig(config_key="commission.monthly", config_value="0.25"))
    db.add(SystemConfig(config_key="commission.purchase", config_value="0.05"))
    db.commit()
    yield db
    db.close()


@pytest.fixture
def user(db):
    u = User(phone="13800000001", invite_code="USER01")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def inviter(db):
    u = User(phone="13800000002", invite_code="INVI01")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_product_list(db):
    """商品列表应返回 3 个"""
    items = order_service.get_product_list(db)
    assert len(items) == 3
    codes = {i["code"] for i in items}
    assert codes == {"single", "monthly", "points_1000"}


def test_create_order(db, user):
    """创建订单应生成 order_no 和 pending 状态"""
    with patch("app.services.order_service.hupijiao_create") as mock_pay:
        mock_pay.return_value = {"pay_url": "https://test-pay-url"}
        result = order_service.create_order(db, user.id, "single")
        assert result["order_no"].startswith("XZ")
        assert result["amount"] == Decimal("9.9")
        assert result["pay_url"] == "https://test-pay-url"

    order = db.query(Order).filter(Order.order_no == result["order_no"]).first()
    assert order.status == "pending"
    assert order.user_id == user.id


def test_handle_notify_grants_points(db, user):
    """支付回调成功后应加分"""
    # 先创建订单
    with patch("app.services.order_service.hupijiao_create") as mock_pay:
        mock_pay.return_value = {"pay_url": "https://test"}
        result = order_service.create_order(db, user.id, "single")
        order_no = result["order_no"]

    # 模拟回调
    with patch("app.services.order_service.verify_notify") as mock_verify:
        mock_verify.return_value = True
        params = {
            "order_no": order_no, "status": "paid",
            "pay_trade_no": "test_trade_123", "amount": "9.90",
        }
        ret = order_service.handle_hupijiao_notify(db, params)
        assert ret == "success"

    # 验证订单状态
    order = db.query(Order).filter(Order.order_no == order_no).first()
    assert order.status == "paid"

    # 验证积分
    accs = db.query(PointAccount).filter(PointAccount.user_id == user.id).all()
    assert len(accs) == 1
    assert accs[0].balance == 500
    assert accs[0].point_type == "subscription"


def test_handle_notify_grants_commission(db, user, inviter):
    """带推广人的订单应给推广人返佣"""
    # 用推广码下单
    with patch("app.services.order_service.hupijiao_create") as mock_pay:
        mock_pay.return_value = {"pay_url": "https://test"}
        result = order_service.create_order(db, user.id, "monthly", invite_code=inviter.invite_code)
        order_no = result["order_no"]

    # 模拟回调
    with patch("app.services.order_service.verify_notify") as mock_verify:
        mock_verify.return_value = True
        params = {
            "order_no": order_no, "status": "paid",
            "pay_trade_no": "test_001", "amount": "29.00",
        }
        order_service.handle_hupijiao_notify(db, params)

    # 验证推广人收到返佣(29 * 0.25 = 7.25 元 = 725 积分)
    inviter_accs = db.query(PointAccount).filter(
        PointAccount.user_id == inviter.id, PointAccount.source == "commission"
    ).all()
    assert len(inviter_accs) == 1
    assert inviter_accs[0].balance == 725


def test_refund_order(db, user):
    """退款应能成功并退积分"""
    with patch("app.services.order_service.hupijiao_create") as mock_pay:
        mock_pay.return_value = {"pay_url": "https://test"}
        result = order_service.create_order(db, user.id, "single")
        order_no = result["order_no"]

    with patch("app.services.order_service.verify_notify") as mock_verify:
        mock_verify.return_value = True
        order_service.handle_hupijiao_notify(db, params={"order_no": order_no, "status": "paid", "pay_trade_no": "t1", "amount": "9.9"})

    # 退款
    order_service.refund_order(db, order_no, reason="用户申请")
    order = db.query(Order).filter(Order.order_no == order_no).first()
    assert order.status == "refunded"

    # 退积分后,账户应该有 500+500=1000
    total = sum(a.balance for a in db.query(PointAccount).filter(PointAccount.user_id == user.id).all())
    assert total == 1000
