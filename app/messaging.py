
from datetime import datetime
from typing import Dict, Set
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (
    Conversation,
    ConversationParticipant,
    Message,
    User,
    get_async_session,
    async_session,
)
from app.users import current_active_user, UserManager, get_jwt_strategy
from fastapi_users.db import SQLAlchemyUserDatabase


router = APIRouter(prefix="/messaging", tags=["messaging"])


class ConversationCreate(BaseModel):
    user_id: uuid.UUID


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class MessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(conversation_id, set()).add(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket):
        sockets = self.connections.get(conversation_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self.connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: str, payload: dict):
        dead = []
        for websocket in self.connections.get(conversation_id, set()):
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)

        for websocket in dead:
            self.disconnect(conversation_id, websocket)


manager = ConnectionManager()


async def get_conversation_for_user(
    conversation_id: str,
    user_id,
    session: AsyncSession,
):
    result = await session.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.participants)
            .selectinload(ConversationParticipant.user)
        )
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(404, "Conversation not found.")

    if not any(str(p.user_id) == str(user_id) for p in conversation.participants):
        raise HTTPException(403, "You are not a participant in this conversation.")

    return conversation


def message_dict(message: Message, sender_email=None):
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_id": str(message.sender_id),
        "sender_email": (
            sender_email
            if sender_email is not None
            else getattr(message.sender, "email", None)
        ),
        "content": message.content,
        "message_type": message.message_type,
        "created_at": message.created_at.isoformat(),
        "edited_at": message.edited_at.isoformat() if message.edited_at else None,
        "deleted_at": message.deleted_at.isoformat() if message.deleted_at else None,
    }


@router.get("/users")
async def search_users(
    q: str = Query("", max_length=100),
    limit: int = Query(30, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    query = select(User).where(User.id != user.id)

    if q.strip():
        query = query.where(User.email.ilike(f"%{q.strip()}%"))

    result = await session.execute(
        query.order_by(User.email.asc()).limit(limit)
    )

    return [
        {
            "id": str(item.id),
            "email": item.email,
        }
        for item in result.scalars().all()
    ]


@router.post("/conversations")
async def create_conversation(
    payload: ConversationCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    if str(payload.user_id) == str(user.id):
        raise HTTPException(400, "You cannot message yourself.")

    other_result = await session.execute(
        select(User).where(User.id == payload.user_id)
    )
    other = other_result.scalar_one_or_none()

    if not other:
        raise HTTPException(404, "User not found.")

    existing = await session.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.user_id.in_([user.id, other.id]))
        .group_by(Conversation.id)
        .having(func.count(ConversationParticipant.user_id) == 2)
    )
    conversation = existing.scalar_one_or_none()

    if conversation:
        return {
            "id": conversation.id,
            "created": False,
        }

    conversation = Conversation()
    session.add(conversation)
    await session.flush()

    session.add_all(
        [
            ConversationParticipant(
                conversation_id=conversation.id,
                user_id=user.id,
            ),
            ConversationParticipant(
                conversation_id=conversation.id,
                user_id=other.id,
            ),
        ]
    )

    await session.commit()

    return {
        "id": conversation.id,
        "created": True,
    }


@router.get("/conversations")
async def list_conversations(
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    result = await session.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.user_id == user.id)
        .options(
            selectinload(Conversation.participants)
            .selectinload(ConversationParticipant.user)
        )
        .order_by(Conversation.updated_at.desc())
    )

    conversations = result.scalars().unique().all()
    response = []

    for conversation in conversations:
        other = next(
            (
                participant.user
                for participant in conversation.participants
                if str(participant.user_id) != str(user.id)
            ),
            None,
        )

        if other is None:
            continue

        participant = next(
            p for p in conversation.participants
            if str(p.user_id) == str(user.id)
        )

        last_result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_message = last_result.scalar_one_or_none()

        unread_query = select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id,
            Message.sender_id != user.id,
            Message.deleted_at.is_(None),
        )

        if participant.last_read_at:
            unread_query = unread_query.where(
                Message.created_at > participant.last_read_at
            )

        unread_result = await session.execute(unread_query)

        response.append(
            {
                "id": conversation.id,
                "other_user": {
                    "id": str(other.id),
                    "email": other.email,
                },
                "last_message": message_dict(last_message) if last_message else None,
                "unread_count": unread_result.scalar_one(),
                "updated_at": conversation.updated_at.isoformat(),
            }
        )

    return response


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: str | None = Query(None),
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    await get_conversation_for_user(conversation_id, user.id, session)

    query = (
        select(Message)
        .options(selectinload(Message.sender))
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    if before:
        before_result = await session.execute(
            select(Message.created_at).where(Message.id == before)
        )
        before_date = before_result.scalar_one_or_none()
        if before_date:
            query = query.where(Message.created_at < before_date)

    result = await session.execute(query)
    messages = list(reversed(result.scalars().all()))

    return [message_dict(message) for message in messages]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    payload: MessageCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    conversation = await get_conversation_for_user(
        conversation_id,
        user.id,
        session,
    )

    content = payload.content.strip()
    if not content:
        raise HTTPException(422, "Message cannot be empty.")

    message = Message(
        conversation_id=conversation.id,
        sender_id=user.id,
        content=content,
        message_type="text",
    )

    conversation.updated_at = datetime.utcnow()
    session.add(message)
    await session.commit()
    await session.refresh(message)

    payload_data = message_dict(message, user.email)
    await manager.broadcast(
        conversation.id,
        {
            "type": "message.created",
            "message": payload_data,
        },
    )

    return payload_data


@router.patch("/messages/{message_id}")
async def edit_message(
    message_id: str,
    payload: MessageUpdate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    result = await session.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(404, "Message not found.")

    if str(message.sender_id) != str(user.id):
        raise HTTPException(403, "You can only edit your own messages.")

    if message.deleted_at:
        raise HTTPException(400, "Deleted messages cannot be edited.")

    content = payload.content.strip()
    if not content:
        raise HTTPException(422, "Message cannot be empty.")

    message.content = content
    message.edited_at = datetime.utcnow()
    await session.commit()
    await session.refresh(message)

    payload_data = message_dict(message, user.email)
    await manager.broadcast(
        message.conversation_id,
        {
            "type": "message.updated",
            "message": payload_data,
        },
    )

    return payload_data


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    result = await session.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(404, "Message not found.")

    if str(message.sender_id) != str(user.id):
        raise HTTPException(403, "You can only delete your own messages.")

    message.content = "Message deleted"
    message.deleted_at = datetime.utcnow()
    await session.commit()

    payload_data = message_dict(message)
    await manager.broadcast(
        message.conversation_id,
        {
            "type": "message.deleted",
            "message": payload_data,
        },
    )

    return {"message": "Message deleted."}


@router.post("/conversations/{conversation_id}/read")
async def mark_read(
    conversation_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    conversation = await get_conversation_for_user(
        conversation_id,
        user.id,
        session,
    )

    participant = next(
        p for p in conversation.participants
        if str(p.user_id) == str(user.id)
    )

    participant.last_read_at = datetime.utcnow()
    await session.commit()

    return {"read_at": participant.last_read_at.isoformat()}


async def get_ws_user(token: str, session: AsyncSession):
    if not token:
        return None

    user_db = SQLAlchemyUserDatabase(session, User)
    manager_user = UserManager(user_db)

    try:
        return await get_jwt_strategy().read_token(token, manager_user)
    except Exception:
        return None


@router.websocket("/ws/{conversation_id}")
async def conversation_websocket(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(""),
):
    async with async_session() as session:
        user = await get_ws_user(token, session)

        if user is None:
            await websocket.close(code=1008)
            return

        try:
            await get_conversation_for_user(
                conversation_id,
                user.id,
                session,
            )
        except HTTPException:
            await websocket.close(code=1008)
            return

        await manager.connect(conversation_id, websocket)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(conversation_id, websocket)


