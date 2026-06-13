"""积分服务：核心 FIFO 消耗、加分、退款

设计要点：
1. 账户按 (user_id, point_type) 维度可拆多条 point_accounts 记录
   - 每条记录代表一个批次
   - 消耗时按 expire_at 升序 + created_at 升序的 FIFO 顺序扣
2. 每笔变动写 point_transactions(append-only)
3. 三个类型优先级:subscription(订阅)先扣、然后 trial(试用)、最后 purchase(增购)
   - 但同类型内仍按 FIFO

为什么这样设计：
- 订阅先扣,符合"先消耗会过期的"
- 增购后扣,因为增购是永久的,留着更灵活
- 试用最后扣,反正可能随时被新订阅覆盖
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from loguru import logger

from app.models.point import PointAccount, PointTransaction
from app.core.exceptions import BizException, BizCode


# 消耗顺序(V1 方案定义)
POINT_TYPE_ORDER = ["subscription", "trial", "purchase"]


def grant_points(
    db: Session,
    user_id: int,
    point_type: str,
    amount: int,
    source: str,
    feature: Optional[str] = None,
    related_id: Optional[int] = None,
    remark: Optional[str] = None,
    expire_at: Optional[datetime] = None,
) -> PointAccount:
    """加分(订阅/试用/增购/推广奖励)"""
    if amount <= 0:
        raise BizException(BizCode.PARAM_ERROR, "加分数量必须为正")

    acc = PointAccount(
        user_id=user_id,
        point_type=point_type,
        balance=amount,
        total_earned=amount,
        expire_at=expire_at,
        source=source,
        related_id=related_id,
    )
    db.add(acc)
    db.flush()

    db.add(PointTransaction(
        user_id=user_id,
        point_type=point_type,
        change=amount,
        balance_after=amount,
        source=source,
        related_id=related_id,
        feature=feature,
        remark=remark,
    ))
    logger.info(f"加分 user_id={user_id} type={point_type} amount={amount} source={source}")
    return acc


def get_balance(db: Session, user_id: int) -> dict:
    """查询三种类型的余额(返回 dict,总量为 sum)"""
    rows = db.execute(
        select(PointAccount.point_type, PointAccount.balance)
        .where(PointAccount.user_id == user_id)
    ).all()
    summary = {"trial_balance": 0, "subscription_balance": 0, "purchase_balance": 0}
    type_map = {
        "trial": "trial_balance",
        "subscription": "subscription_balance",
        "purchase": "purchase_balance",
    }
    for pt, bal in rows:
        key = type_map.get(pt)
        if key:
            summary[key] += bal
    summary["total_balance"] = sum(summary.values())
    return summary


def consume_points(
    db: Session,
    user_id: int,
    amount: int,
    feature: str,
    source: str = "consume",
    related_id: Optional[int] = None,
    remark: Optional[str] = None,
) -> Tuple[int, List[PointTransaction]]:
    """消耗积分 - FIFO

    返回 (总扣的积分, [PointTransaction 列表])
    余额不足抛 INSUFFICIENT_POINTS
    """
    if amount <= 0:
        raise BizException(BizCode.PARAM_ERROR, "消耗数量必须为正")

    # 取所有非空账户,按优先级+expire_at+created_at 排序
    accounts = (
        db.query(PointAccount)
        .filter(PointAccount.user_id == user_id, PointAccount.balance > 0)
        .order_by(PointAccount.created_at.asc())
        .all()
    )
    # 按 POINT_TYPE_ORDER 重排
    accounts.sort(key=lambda a: (
        POINT_TYPE_ORDER.index(a.point_type) if a.point_type in POINT_TYPE_ORDER else 999,
        a.expire_at or datetime(2099, 1, 1, tzinfo=timezone.utc),
        a.created_at,
    ))

    total_available = sum(a.balance for a in accounts)
    if total_available < amount:
        raise BizException(
            BizCode.INSUFFICIENT_POINTS,
            f"积分不足,需要 {amount} 积分,当前余额 {total_available}",
        )

    remaining = amount
    txns: List[PointTransaction] = []
    total_deducted = 0

    for acc in accounts:
        if remaining <= 0:
            break
        if acc.balance <= 0:
            continue
        # 已过期的账户余额视为 0(防止边界问题)
        if acc.expire_at and acc.expire_at < datetime.now(timezone.utc):
            acc.balance = 0
            continue
        deduct = min(remaining, acc.balance)
        balance_before = acc.balance
        acc.balance -= deduct
        acc.total_used += deduct
        remaining -= deduct
        total_deducted += deduct

        txn = PointTransaction(
            user_id=user_id,
            point_type=acc.point_type,
            change=-deduct,
            balance_before=balance_before,
            balance_after=acc.balance,
            source=source,
            related_id=related_id,
            feature=feature,
            remark=remark,
        )
        db.add(txn)
        txns.append(txn)

    if remaining > 0:
        # 理论上不会到这里
        raise BizException(BizCode.INSUFFICIENT_POINTS, "积分不足")

    logger.info(f"扣分 user_id={user_id} amount={amount} feature={feature} deducted_from={len(txns)}")
    return total_deducted, txns


def refund_points(
    db: Session,
    user_id: int,
    point_type: str,
    amount: int,
    source: str,
    feature: Optional[str] = None,
    related_id: Optional[int] = None,
    remark: Optional[str] = None,
    expire_at: Optional[datetime] = None,
) -> PointAccount:
    """退积分（通常是退款或奖励）"""
    return grant_points(
        db, user_id=user_id, point_type=point_type, amount=amount,
        source=source, feature=feature, related_id=related_id,
        remark=remark, expire_at=expire_at,
    )
