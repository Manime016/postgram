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
    UniqueConstraint,
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


DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "Mani"
DB_PASSWORD = "Mani@123"
DB_NAME = "postgram"

DATABASE_URL = URL.create(
    drivername="mysql+aiomysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


class User(
    SQLAlchemyBaseUserTableUUID,
    Base,
):
    posts = relationship(
        "Post",
        back_populates="user",
    )
    likes = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    conversation_participants = relationship(
        "ConversationParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sent_messages = relationship(
        "Message",
        back_populates="sender",
        cascade="all, delete-orphan",
    )


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

    caption = Column(String(255))

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

    likes = relationship(
        "Like",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    comments = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
    )


class Like(Base):
    __tablename__ = "likes"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = Column(
        CHAR(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    post_id = Column(
        CHAR(36),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="likes",
    )

    post = relationship(
        "Post",
        back_populates="likes",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "post_id",
            name="uq_like_user_post",
        ),
    )



class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    participants = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        CHAR(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        CHAR(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_read_at = Column(DateTime, nullable=True)

    conversation = relationship(
        "Conversation",
        back_populates="participants",
    )
    user = relationship(
        "User",
        back_populates="conversation_participants",
    )

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_conversation_user",
        ),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        CHAR(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(
        CHAR(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    message_type = Column(String(30), nullable=False, default="text")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    edited_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )
    sender = relationship(
        "User",
        back_populates="sent_messages",
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = Column(
        CHAR(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    post_id = Column(
        CHAR(36),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    content = Column(
        String(500),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="comments",
    )

    post = relationship(
        "Post",
        back_populates="comments",
    )


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )


async def get_async_session() -> AsyncGenerator[
    AsyncSession,
    None,
]:
    async with async_session() as session:
        yield session


async def get_user_db(
    session: AsyncSession = Depends(
        get_async_session
    ),
):
    yield SQLAlchemyUserDatabase(
        session,
        User,
    )
