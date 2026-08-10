from typing import AsyncGenerator
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.logging import logger


# SQLAlchemy Base Model
class Base(DeclarativeBase):
    pass


# PostgreSQL Engine & Session Factory
engine: AsyncEngine = create_async_engine(
    settings.postgres_async_url,
    echo=settings.SERVER_ENV == "development",
    pool_size=settings.SQL_MAX_POOL,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a transactional SQLAlchemy async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# MongoDB Motor Client & Database (Motor thuần cho Hybrid Model)
_mongo_uri = settings.mongo_async_url

mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(_mongo_uri, serverSelectionTimeoutMS=5000)
mongo_db: AsyncIOMotorDatabase = mongo_client[settings.MONGODB_NAME]



def get_mongo_db() -> AsyncIOMotorDatabase:
    """Dependency providing raw Motor Async MongoDB Database (dùng cho form-dong, khao-sat JSON động)."""
    return mongo_db


# Redis Client
redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> Redis:
    """Dependency providing Redis Async client."""
    return redis_client


async def seed_initial_admin():
    """Tự động khởi tạo bảng DB và tài khoản Admin mặc định nếu chưa tồn tại."""
    try:
        from sqlalchemy import select
        from app.core.security import hash_password
        from app.modules.auth.models import Role, User

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.username == settings.SERVER_DEFAULT_ADMIN_USERNAME)
            res = await session.execute(stmt)
            admin = res.scalar_one_or_none()

            if not admin:
                # Check or create SUPERADMIN role
                role_stmt = select(Role).where(Role.name == "SUPERADMIN")
                role_res = await session.execute(role_stmt)
                super_role = role_res.scalar_one_or_none()
                if not super_role:
                    super_role = Role(name="SUPERADMIN", description="Super Admin Role")
                    session.add(super_role)
                    await session.flush()

                admin_user = User(
                    username=settings.SERVER_DEFAULT_ADMIN_USERNAME,
                    hashed_password=hash_password(settings.SERVER_DEFAULT_ADMIN_PASSWORD),
                    email="admin@administrator.com",
                    full_name="Administrator",
                    system_role="ADMIN",
                    is_active=True,
                    is_superuser=True,
                    roles=[super_role],
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Default Admin User created successfully.", username=settings.SERVER_DEFAULT_ADMIN_USERNAME)
    except Exception as exc:
        logger.warn("Could not seed initial admin user (DB might not be reachable yet)", error=str(exc))


async def init_databases(document_models: list = None) -> None:
    """Khởi tạo kết nối cơ sở dữ liệu khi startup ứng dụng."""
    logger.info("Initializing PostgreSQL Engine...", url=settings.SQL_HOST)
    await seed_initial_admin()

    # Initialize Beanie ODM for fixed-schema MongoDB models if provided
    if document_models:
        logger.info("Initializing Beanie ODM with fixed-schema models...", models_count=len(document_models))
        await init_beanie(database=mongo_db, document_models=document_models)
    else:
        logger.info("MongoDB Motor Client connected (Raw Motor mode ready).")


async def close_databases() -> None:
    """Đóng tất cả kết nối DB khi shutdown ứng dụng."""
    logger.info("Closing database connections...")
    await engine.dispose()
    mongo_client.close()
    await redis_client.close()
