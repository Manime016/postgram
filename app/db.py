from collections.abc import AsyncGenerator

from datetime import datetime
import uuid

from fastapi import Depends

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.engine import URL

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
)

from fastapi_users.db import (
    SQLAlchemyUserDatabase,
    SQLAlchemyBaseUserTableUUID,
)


# =========================
# Database details
# =========================

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "Mani"
DB_PASSWORD = "Mani@123"
DB_NAME = "postgram"


# =========================
# Database URL
# =========================

DATABASE_URL = URL.create(
    drivername="mysql+aiomysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)


# =========================
# Database engine
# =========================

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)


# =========================
# Async session
# =========================

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# =========================
# Base class
# =========================

class Base(DeclarativeBase):
    pass


# =========================
# User model
# =========================

class User(
    SQLAlchemyBaseUserTableUUID,
    Base,
):

    posts = relationship(
        "Post",
        back_populates="user",
    )


# =========================
# Post model
# =========================

class Post(Base):
    __tablename__ = "posts"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = Column(
        CHAR(36),
        ForeignKey("user.id"),
        nullable=False,
    )

    caption = Column(
        String(255),
    )

    url = Column(
        Text,
        nullable=False,
    )

    file_type = Column(
        String(50),
        nullable=False,
    )

    file_name = Column(
        String(255),
        nullable=False,
    )

    imagekit_file_id = Column(
        String(255),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="posts",
    )


# =========================
# Create database tables
# =========================

async def create_db_and_tables():

    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )


# =========================
# Database dependency
# =========================

async def get_async_session() -> AsyncGenerator[
    AsyncSession,
    None,
]:

    async with async_session() as session:

        yield session


# =========================
# FastAPI Users database
# =========================

async def get_user_db(
    session: AsyncSession = Depends(
        get_async_session
    ),
):

    yield SQLAlchemyUserDatabase(
        session,
        User,
    )