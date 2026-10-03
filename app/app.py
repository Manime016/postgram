from contextlib import asynccontextmanager
import asyncio
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
    HTTPException,
    Query,
    status,
)

from sqlalchemy import func
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


# ============================================================
# Configuration
# ============================================================

MAX_UPLOAD_MB = int(
    os.getenv("MAX_UPLOAD_MB", "50")
)

MAX_UPLOAD_BYTES = (
    MAX_UPLOAD_MB * 1024 * 1024
)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "video/x-matroska",
}

ALLOWED_FILE_TYPES = (
    ALLOWED_IMAGE_TYPES
    | ALLOWED_VIDEO_TYPES
)


# ============================================================
# Application lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Postgram API",
    description="Backend API for the Postgram social media application.",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# Basic health endpoint
# ============================================================

@app.get(
    "/health",
    tags=["system"],
)
async def health_check():
    return {
        "status": "ok",
        "service": "postgram-api",
    }


# ============================================================
# Authentication routes
# ============================================================

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


# ============================================================
# Current user
# ============================================================

@app.get(
    "/me",
    tags=["users"],
)
async def get_me(
    user=Depends(current_active_user),
):
    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_superuser": user.is_superuser,
    }


# ============================================================
# Upload post
# ============================================================

@app.post(
    "/upload",
    tags=["posts"],
)
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file is required.",
        )

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Unsupported file type. "
                "Use JPG, PNG, WEBP, GIF, MP4, MOV, WEBM, or MKV."
            ),
        )

    caption = caption.strip()

    if len(caption) > 255:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Caption cannot exceed 255 characters.",
        )

    temp_file_path = None
    total_size = 0

    try:
        extension = os.path.splitext(
            file.filename
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            temp_file_path = temp_file.name

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            f"File is too large. "
                            f"Maximum size is {MAX_UPLOAD_MB} MB."
                        ),
                    )

                temp_file.write(chunk)

        upload_kwargs = {
            "file_name": file.filename,
        }

        with open(
            temp_file_path,
            "rb",
        ) as upload_file:

            upload_result = await asyncio.to_thread(
                imagekit.files.upload,
                file=upload_file,
                **upload_kwargs,
            )

        post = Post(
            user_id=user.id,
            caption=caption or None,
            url=upload_result.url,
            file_type=file.content_type,
            file_name=file.filename,
            imagekit_file_id=upload_result.file_id,
        )

        session.add(post)

        await session.commit()
        await session.refresh(post)

        return {
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
        }

    except HTTPException:
        await session.rollback()
        raise

    except Exception:
        await session.rollback()
        raise

    finally:
        if (
            temp_file_path
            and os.path.exists(temp_file_path)
        ):
            os.unlink(temp_file_path)

        await file.close()


# ============================================================
# Feed
# ============================================================

@app.get(
    "/feed",
    tags=["posts"],
)
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
    limit: int = Query(
        20,
        ge=1,
        le=50,
        description="Number of posts to return.",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of posts to skip.",
    ),
):
    total_result = await session.execute(
        select(func.count(Post.id))
    )

    total = total_result.scalar_one()

    result = await session.execute(
        select(Post)
        .options(selectinload(Post.user))
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
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
                "email": (
                    post.user.email
                    if post.user
                    else None
                ),
            }
        )

    return {
        "posts": posts_data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(posts_data) < total,
    }


# ============================================================
# Delete post
# ============================================================

@app.delete(
    "/delete/{post_id}",
    tags=["posts"],
)
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    result = await session.execute(
        select(Post).where(
            Post.id == post_id
        )
    )

    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    if post.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this post.",
        )

    try:
        await asyncio.to_thread(
            imagekit.files.delete,
            file_id=post.imagekit_file_id,
        )

        await session.delete(post)
        await session.commit()

        return {
            "message": "Post deleted successfully.",
        }

    except Exception:
        await session.rollback()
        raise
