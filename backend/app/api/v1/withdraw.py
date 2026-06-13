"""提现 API - 1 个(只查余额,V1 暂不真打款)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import points_service

router = APIRouter(prefix="/withdraw", tags=["提现(V1 仅查询)"])


@router.get("/balance", summary="我的可提现余额")
async def my_withdraw_balance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """V1:把可提现理解为「通过返佣获得的、还在钱包里待提现的积分」
    V1 暂不真打款,这里只展示数据
    """
    from app.models.point import PointTransaction
    from sqlalchemy import func

    # 查询该用户作为推广人获得的返佣总额(累计)
    commission_earned = (
        db.query(func.coalesce(func.sum(PointTransaction.change), 0))
        .filter(
            PointTransaction.user_id == user.id,
            PointTransaction.source == "commission",
        )
        .scalar()
        or 0
    )

    # 已提现(V1=0)
    withdrawn = 0

    return {
        "commission_earned": abs(int(commission_earned)),  # change 是正数表示获得
        "withdrawn": int(withdrawn),
        "available": abs(int(commission_earned)) - int(withdrawn),
        "note": "V1 阶段返佣以积分形式发放,不打款,可在下次消费时直接用",
    }
