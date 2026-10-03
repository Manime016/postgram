from contextlib import asynccontextmanager
import os
import shutil
import tempfile

from app.schemas import UserCreate, UserRead

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Depends,
    Form,
)

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (
    Post,
    create_db_and_tables,
    get_async_session,
)

from app.images import imagekit

from app.users import (
    fastapi_users,
    auth_backend,
    current_active_user,
)


# =========================
# Application Lifespan
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


# =========================
# Authentication Routes
# =========================

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(
        UserRead,
        UserCreate,
    ),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(
        UserRead,
        UserCreate,
    ),
    prefix="/users",
    tags=["users"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)


# =========================
# Upload File
# =========================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    temp_file_path = None

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename)[1],
        ) as temp_file:

            temp_file_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file,
            )

        # Upload file to ImageKit
        with open(temp_file_path, "rb") as upload_file:

            upload_result = imagekit.files.upload(
                file=upload_file,
                file_name=file.filename,
            )

        # ImageKit URL
        url = upload_result.url

        # Create database record
        post = Post(
            user_id=user.id,
            caption=caption,
            url=url,
            file_type=file.content_type,
            file_name=file.filename,
            imagekit_file_id=upload_result.file_id,
        )

        # Add post to database
        session.add(post)

        # Save to database
        await session.commit()

        # Refresh object
        await session.refresh(post)

        return post

    except Exception as e:

        await session.rollback()

        raise e

    finally:

        # Delete temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        # Close uploaded file
        file.file.close()


# =========================
# Get Feed
# =========================

@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):

    result = await session.execute(
        select(Post)
        .options(selectinload(Post.user))
        .order_by(Post.created_at.desc())
    )

    posts = result.scalars().all()

    posts_data = []

    for post in posts:

        posts_data.append(
            {
                "id": post.id,
                "caption": post.caption,
                "url": post.url,
                "file_type": (
                    "video"
                    if post.file_type.startswith("video/")
                    else "image"
                ),
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
                "is_owner": post.user_id == user.id,
                "email": post.user.email if post.user else None,
            }
        )

    return {
        "posts": posts_data
    }


# =========================
# Delete Post
# =========================

@app.delete("/delete/{post_id}")
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):

    try:

        # Find post
        result = await session.execute(
            select(Post).where(
                Post.id == post_id
            )
        )

        post = result.scalar_one_or_none()

        # Post doesn't exist
        if not post:
            return {
                "message": "Post not found"
            }

        # Check post ownership
        if post.user_id != user.id:
            return {
                "message": "You are not allowed to delete this post"
            }

        # Delete file from ImageKit
        imagekit.files.delete(
            file_id=post.imagekit_file_id
        )

        # Delete record from MySQL
        await session.delete(post)

        # Save deletion
        await session.commit()

        return {
            "message": "Post deleted successfully"
        }

    except Exception as e:

        await session.rollback()

        raise e