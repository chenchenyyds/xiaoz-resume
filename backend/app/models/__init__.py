"""SQLAlchemy 模型聚合(供 Alembic autogenerate 发现)"""
from app.models.user import User
from app.models.sms_code import SmsCode
from app.models.point import PointAccount, PointTransaction
from app.models.order import Order
from app.models.redeem import RedeemCode
from app.models.resume import ResumeFile
from app.models.rewrite import RewriteRecord
from app.models.config import SystemConfig
from app.models.operation_log import OperationLog

__all__ = [
    "User", "SmsCode", "PointAccount", "PointTransaction",
    "Order", "RedeemCode", "ResumeFile", "RewriteRecord",
    "SystemConfig", "OperationLog",
]
