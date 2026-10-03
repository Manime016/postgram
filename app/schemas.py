from pydantic import BaseModel, Field
from fastapi_users import schemas
import uuid


class PostCreate(BaseModel):
    title: str
    content: str


class PostResponse(PostCreate):
    id: int


class PostUpdate(BaseModel):
    caption: str = Field(
        default="",
        max_length=255,
    )


class CommentCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=500,
    )


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass
