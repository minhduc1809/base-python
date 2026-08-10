from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])



@router.post("/login", response_model=TokenResponse)
async def login(dto: LoginRequest, req: Request, db: AsyncSession = Depends(get_db_session)):
    service = AuthService(db)
    ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")
    origin = req.headers.get("origin")
    return await service.login(dto, ip=ip, user_agent=user_agent, origin=origin)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(dto: RefreshTokenRequest, db: AsyncSession = Depends(get_db_session)):
    service = AuthService(db)
    await service.logout(dto.get_token())
    return {"message": "Đăng xuất thành công"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(dto: RefreshTokenRequest, db: AsyncSession = Depends(get_db_session)):
    service = AuthService(db)
    return await service.refresh_tokens(dto.get_token())


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        roles=[r.name for r in current_user.roles],
        data_partition_code=current_user.data_partition_code,
        created_at=current_user.created_at,
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    dto: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    await service.change_password(current_user.id, dto)
    return {"message": "Đổi mật khẩu thành công"}
