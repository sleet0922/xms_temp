"""认证与个人中心：登录 / 注册 / 资料维护 / 修改密码"""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import (
    create_access_token, get_current_user, get_password_hash, verify_password,
)
from database import get_db
from models import User
from schemas import (
    ChangePasswordRequest, LoginRequest, TokenResponse, UserCreate, UserResponse, UserUpdate,
)
from services.audit import get_rules, record_audit
from config import settings

router = APIRouter(prefix="/api/auth", tags=["认证与个人中心"])


@router.post("/login", response_model=TokenResponse, summary="登录获取令牌")
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status == "frozen":
        raise HTTPException(status_code=403, detail="账户已被冻结，请联系服务台处理")

    token = create_access_token(data={"sub": user.username, "role": user.role})
    record_audit(db, user, "LOGIN", "USER", str(user.id), f"用户 {user.username} 成功登录系统", request)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="读者自助注册")
def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="电子邮箱已被注册")

    card_number = user_data.card_number
    if not card_number:
        sequence = db.query(User).count() + 101
        while True:
            candidate = f"CARD-{datetime.now().strftime('%Y%m')}{sequence:03d}"
            if not db.query(User).filter(User.card_number == candidate).first():
                card_number = candidate
                break
            sequence += 1
    elif db.query(User).filter(User.card_number == card_number).first():
        raise HTTPException(status_code=400, detail="借书卡号已被占用")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        role="reader",
        card_number=card_number,
        # 取系统设置中的「普通读者最大借阅本数」，管理员改设置后新注册读者立即生效
        max_borrow_limit=get_rules(db)["max_borrow_books"],
        balance=Decimal("0.00"),
        status="active",
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="用户名、邮箱或借书卡号已被占用")
    db.refresh(new_user)
    record_audit(db, new_user, "REGISTER", "USER", str(new_user.id), f"读者注册: {new_user.username}", request)
    return new_user


@router.get("/me", response_model=UserResponse, summary="获取当前登录用户")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse, summary="更新个人资料")
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.email and user_update.email != current_user.email:
        if db.query(User).filter(User.email == user_update.email, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail="该邮箱已被其他读者使用")
        current_user.email = user_update.email

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/change-password", summary="修改密码")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    current_user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    record_audit(db, current_user, "CHANGE_PASSWORD", "USER", str(current_user.id), "用户自主修改密码")
    return {"message": "密码修改成功，请妥善保管"}
