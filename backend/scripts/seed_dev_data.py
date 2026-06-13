"""开发测试数据生成脚本

生成内容:
  - 3 个测试用户(管理员 1 个 + 普通 2 个,带推广关系)
  - 1 个已支付的月卡订单(给 user_a)
  - 3 个未使用兑换码(50/100/500 积分各 1 个)
  - 1 个测试简历文件记录

用法:
  cd 代码/backend && python scripts/seed_dev_data.py
  cd 代码 && make seed-dev
"""
import os
import sys
import secrets
import hashlib
from datetime import datetime, timedelta

# 让脚本能 import app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash  # 实际未用,占位
from app.models import user, sms_code, point, order, redeem, resume  # noqa
from app.models.user import User
from app.models.point import PointAccount, PointTransaction
from app.models.order import Order
from app.models.redeem import RedeemCode
from app.models.resume import ResumeFile


# ---------- 配置 ----------
DEV_USERS = [
    # (phone, is_admin, invite_code, invite_user_phone)
    ("13800000000", True, "ADMIN01", None),         # 管理员
    ("13800000001", False, "USERA01", None),        # 普通用户 A(无推广人)
    ("13800000002", False, "USERB02", "13800000001"),  # 普通用户 B(A 推广来的)
    ("13800000003", False, "USERC03", "13800000001"),  # 普通用户 C(A 推广来的)
]


def gen_invite_code() -> str:
    """生成 8 位推广码"""
    return secrets.token_hex(4).upper()


def gen_redeem_code() -> str:
    """生成 XXXX-XXXX-XXXX 格式兑换码"""
    return "-".join(secrets.token_hex(2).upper() for _ in range(3))


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def mask_code(code: str) -> str:
    """脱敏:XXXX-****-XXXX"""
    parts = code.split("-")
    if len(parts) == 3:
        return f"{parts[0]}-****-{parts[2]}"
    return code[:4] + "****" + code[-4:]


def upsert_user(db: Session, phone: str, is_admin: bool, invite_code: str, invite_user_id: int = None) -> User:
    u = db.query(User).filter(User.phone == phone).first()
    if u:
        print(f"  ↻ 用户 {phone} 已存在(id={u.id}),跳过")
        return u

    u = User(
        phone=phone,
        nickname=f"测试{('管理员' if is_admin else '用户')}{phone[-2:]}",
        is_admin=is_admin,
        invite_code=invite_code,
        invite_user_id=invite_user_id,
        status="active",
        created_at=datetime.utcnow(),
        last_active_at=datetime.utcnow(),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    print(f"  ✓ 创建用户 {phone} (id={u.id}, admin={is_admin}, invite={invite_code})")
    return u


def grant_points(db: Session, user_id: int, points: int, point_type: str, source: str,
                 expire_at=None, related_id=None, remark=""):
    """给用户加积分(走 PointAccount + PointTransaction)"""
    # 1) 账户批次
    pa = PointAccount(
        user_id=user_id,
        point_type=point_type,
        balance=points,
        total_earned=points,
        total_used=0,
        expire_at=expire_at,
        source=source,
        related_id=related_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(pa)
    db.flush()

    # 2) 流水
    pt = PointTransaction(
        user_id=user_id,
        point_type=point_type,
        change=points,
        balance_before=0,
        balance_after=points,
        source=source,
        related_id=related_id,
        feature="grant",
        remark=remark,
        created_at=datetime.utcnow(),
    )
    db.add(pt)
    db.commit()
    print(f"    ✓ {user_id} 获得 {points} 积分 ({point_type}, source={source})")


def create_order(db: Session, user_id: int, product_code: str, amount: float, status: str = "paid") -> Order:
    o = Order(
        order_no=f"TEST{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}",
        user_id=user_id,
        product_code=product_code,
        amount=amount,
        pay_amount=amount,
        pay_channel="hupijiao",
        pay_trade_no=f"TEST_TRADE_{secrets.token_hex(6)}",
        status=status,
        paid_at=datetime.utcnow() if status == "paid" else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    print(f"  ✓ 创建订单 {o.order_no} ({product_code}, ¥{amount}, status={status})")
    return o


def create_redeem_code(db: Session, points: int, note: str, created_by: int) -> tuple:
    code = gen_redeem_code()
    rc = RedeemCode(
        code_hash=hash_code(code),
        code_mask=mask_code(code),
        points=points,
        status="unused",
        note=note,
        created_by=created_by,
        created_at=datetime.utcnow(),
    )
    db.add(rc)
    db.commit()
    print(f"  ✓ 兑换码 {code} → {points} 积分 (note={note})")
    return code, rc


def create_resume(db: Session, user_id: int) -> ResumeFile:
    content = """张三
男 | 25岁 | 广州 | 13800000001

【工作经历】
2023.06 - 至今  XX 科技公司  后端开发工程师
- 负责订单系统微服务开发,使用 Spring Boot + MyBatis + Redis
- 主导日均 100 万订单的订单系统优化,接口 P99 从 800ms 降至 200ms
- 引入分布式链路追踪,故障定位时间从 30 分钟缩短到 5 分钟

2021.07 - 2023.05  YY 信息技术  Java 开发
- 参与电商后端开发,使用 Spring Cloud + MySQL + RabbitMQ
- 负责商品中心和库存中心,支撑双 11 大促

【教育背景】
2017.09 - 2021.06  XX 大学  计算机科学与技术  本科

【技能】
- 后端:Java、Spring Boot、Spring Cloud、MyBatis
- 数据库:MySQL、PostgreSQL、Redis、MongoDB
- 中间件:RabbitMQ、Kafka、Docker、Kubernetes
- 其他:分布式系统设计、高并发优化、Linux
"""
    rf = ResumeFile(
        user_id=user_id,
        type="uploaded",
        file_name="张三_简历.docx",
        file_format="docx",
        file_url=f"https://dev.oss.example.com/resume/{user_id}/sample.docx",
        file_size=len(content.encode("utf-8")),
        content_text=content,
        title="张三_简历",
        is_deleted=False,
        created_at=datetime.utcnow(),
    )
    db.add(rf)
    db.commit()
    db.refresh(rf)
    print(f"  ✓ 创建测试简历(id={rf.id}, {rf.file_name})")
    return rf


def main():
    print("=" * 60)
    print("  小Z简历 - 开发测试数据生成")
    print("=" * 60)
    print(f"  DB: {settings.DATABASE_URL}")
    print()

    # 1) 自动建表(开发模式)
    print("➜ 步骤 1: 自动建表(开发模式)")
    Base.metadata.create_all(bind=engine)
    print("  ✓ 表结构 OK\n")

    db = SessionLocal()
    try:
        # 2) 创建用户
        print("➜ 步骤 2: 创建测试用户(4 个)")
        users = {}
        for phone, is_admin, invite_code, invite_phone in DEV_USERS:
            invite_user_id = None
            if invite_phone:
                invite_user_id = users[invite_phone].id
            u = upsert_user(db, phone, is_admin, invite_code, invite_user_id)
            users[phone] = u
        print()

        # 3) 给 user_a 一些积分(用于演示)
        print("➜ 步骤 3: 给用户 A 灌积分(用于演示)")
        grant_points(db, users["13800000001"].id, 200, "purchase", source="order",
                     remark="测试 - 增购 1000 积分订单的一部分")
        grant_points(db, users["13800000001"].id, 50, "trial", source="trial",
                     expire_at=datetime.utcnow() + timedelta(days=90),
                     remark="测试 - 注册赠送试用")
        print()

        # 4) 创建月卡订单(已支付)
        print("➜ 步骤 4: 创建月卡订单(已支付)")
        o = create_order(db, users["13800000001"].id, "monthly", 29.0, status="paid")
        grant_points(db, users["13800000001"].id, 3000, "subscription", source="order",
                     expire_at=datetime.utcnow() + timedelta(days=30),
                     related_id=o.id,
                     remark=f"测试 - 月卡订单 {o.order_no} 支付成功")
        print()

        # 5) 生成兑换码
        print("➜ 步骤 5: 生成 3 个兑换码(50/100/500)")
        admin = users["13800000000"]
        code50, _ = create_redeem_code(db, 50, "测试-50 积分", admin.id)
        code100, _ = create_redeem_code(db, 100, "测试-100 积分", admin.id)
        code500, _ = create_redeem_code(db, 500, "测试-500 积分", admin.id)
        print()

        # 6) 创建测试简历
        print("➜ 步骤 6: 创建测试简历")
        rf = create_resume(db, users["13800000001"].id)
        print()

        # 输出汇总
        print("=" * 60)
        print("  ✓ 测试数据生成完成")
        print("=" * 60)
        print()
        print("【测试账号】")
        print(f"  管理员:13800000000 验证码:123456  invite=ADMIN01")
        print(f"  用户 A:13800000001 验证码:123456  invite=USERA01  (有积分有简历)")
        print(f"  用户 B:13800000002 验证码:123456  invite=USERB02  (A 推广)")
        print(f"  用户 C:13800000003 验证码:123456  invite=USERC03  (A 推广)")
        print()
        print("【可用兑换码】(登录后调 /api/redeem 兑换)")
        print(f"  {code50}   (50 积分)")
        print(f"  {code100}  (100 积分)")
        print(f"  {code500}  (500 积分)")
        print()
        print("【快速冒烟测试】")
        print("  cd 代码/backend && bash tests/smoke_test.sh")
        print()
        print("【⚠️  注意】")
        print("  - 这些数据只用于本地开发,生产环境请删除 admin 之外的所有用户")
        print("  - 兑换码明文只在这里输出一次,DB 里只存 hash,丢了找不回")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
