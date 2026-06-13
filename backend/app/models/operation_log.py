"""管理员操作日志表"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class OperationLog(Base):
    """管理员操作审计日志(append-only)

    记录:谁(管理员)在什么时间对什么目标做了什么操作
    """
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=False, index=True)
    admin_phone = Column(String(20), nullable=False)  # 冗余存储,避免联表

    action = Column(String(50), nullable=False, index=True)
    # 操作类型枚举:
    # - refund               订单退款
    # - disable_user         禁用用户
    # - enable_user          启用用户
    # - adjust_points        调整用户积分
    # - generate_codes       生成兑换码
    # - revoke_code          作废兑换码
    # - update_config        更新系统配置
    # - login                后台登录(可选记录)

    target_type = Column(String(50))  # 目标类型:order/user/code/config
    target_id = Column(Integer)   # 目标 ID

    before_value = Column(JSON)       # 操作前值(JSON)
    after_value = Column(JSON)        # 操作后值(JSON)
    remark = Column(Text)             # 备注/原因

    ip = Column(String(64))           # 操作者 IP
    user_agent = Column(String(512))  # 浏览器 UA

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
