"""创建管理员脚本 - 首次部署时执行

用法:
    cd backend
    python -m scripts.create_admin 13800000000
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.services import user_service, points_service


def create_admin(phone: str):
    init_db()
    db = SessionLocal()
    try:
        user = user_service.get_by_phone(db, phone)
        if not user:
            user, _ = user_service.register_or_login(db, phone, None)
            print(f"✓ 用户 {phone} 已创建")
        if not user.is_admin:
            user.is_admin = True
            db.commit()
            print(f"✓ 用户 {phone} 已设为管理员")
        else:
            print(f"✓ 用户 {phone} 已是管理员")
        print(f"  user_id: {user.id}")
        print(f"  invite_code: {user.invite_code}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python -m scripts.create_admin <手机号>")
        print("示例: python -m scripts.create_admin 13800000000")
        sys.exit(1)
    create_admin(sys.argv[1])
