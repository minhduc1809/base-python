from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import AppException
from app.core.database import get_db_session
from app.core.security import hash_password
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.auth.models import User
from app.modules.auth.schemas import ChangePasswordRequest, UserResponse

router = APIRouter(prefix="/user", tags=["user"])


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    system_role: str = "USER"
    data_partition_code: Optional[str] = None


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    full_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    system_role: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    data_partition_code: Optional[str] = None


class PaginatedUserResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    limit: int


def _map_user_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        username=u.username,
        email=u.email,
        full_name=u.full_name or f"{u.lastname or ''} {u.firstname or ''}".strip(),
        avatar_url=u.avatar_url,
        is_active=u.is_active,
        is_superuser=u.is_superuser,
        roles=[r.name for r in u.roles],
        data_partition_code=u.data_partition_code,
        created_at=u.created_at,
    )


@router.get("", response_model=PaginatedUserResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Tìm theo username, email, fullname"),
    partition_code: Optional[str] = Query(None, description="Lọc theo data partition"),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(["ADMIN", "SUPERADMIN"])),
):
    stmt = select(User)
    if partition_code:
        stmt = stmt.where(User.data_partition_code == partition_code)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            (User.username.ilike(pattern))
            | (User.email.ilike(pattern))
            | (User.full_name.ilike(pattern))
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Paginate
    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    res = await db.execute(stmt)
    users = res.scalars().all()

    return PaginatedUserResponse(
        items=[_map_user_response(u) for u in users],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return _map_user_response(current_user)


@router.put("/me/password", response_model=UserResponse)
async def change_password_me(
    dto: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Đổi mật khẩu người dùng hiện tại."""
    from app.core.security import verify_password
    if not verify_password(dto.old_password, current_user.hashed_password):
        raise AppException(status_code=400, message="Mật khẩu cũ không chính xác", error="Bad Request")

    current_user.hashed_password = hash_password(dto.new_password)
    await db.flush()
    return _map_user_response(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(["ADMIN", "SUPERADMIN"])),
):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise AppException(status_code=404, message="Không tìm thấy người dùng", error="Not Found")
    return _map_user_response(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    dto: CreateUserRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(["ADMIN", "SUPERADMIN"])),
):
    # Check duplicate
    stmt = select(User).where(User.username == dto.username)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise AppException(status_code=400, message=f"Tài khoản '{dto.username}' đã tồn tại", error="Conflict")

    user = User(
        username=dto.username,
        hashed_password=hash_password(dto.password),
        email=dto.email,
        firstname=dto.firstname,
        lastname=dto.lastname,
        full_name=dto.full_name or f"{dto.lastname or ''} {dto.firstname or ''}".strip() or dto.username,
        gender=dto.gender,
        dob=dto.dob,
        system_role=dto.system_role,
        data_partition_code=dto.data_partition_code,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return _map_user_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    dto: UpdateUserRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(["ADMIN", "SUPERADMIN"])),
):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise AppException(status_code=404, message="Không tìm thấy người dùng", error="Not Found")

    for field, val in dto.model_dump(exclude_unset=True).items():
        if hasattr(user, field):
            setattr(user, field, val)

    await db.flush()
    return _map_user_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(["ADMIN", "SUPERADMIN"])),
):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise AppException(status_code=404, message="Không tìm thấy người dùng", error="Not Found")

    await db.delete(user)
    await db.flush()
