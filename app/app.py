from contextlib import asynccontextmanager
import asyncio
import os
import tempfile

from app.schemas import (
    UserCreate,
    UserRead,
    PostUpdate,
    CommentCreate,
)

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
    Like,
    Comment,
    User,
    create_db_and_tables,
    get_async_session,
)

from app.images import imagekit

from app.users import (
    fastapi_users,
    auth_backend,
    current_active_user,
)

from app.messaging import router as messaging_router


MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

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

ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(
    title="Postgram API",
    description="Social photo and video sharing API.",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "service": "postgram-api",
        "version": "2.0.0",
    }


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

app.include_router(messaging_router)


@app.get("/me", tags=["users"])
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


@app.post("/upload", tags=["posts"])
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A file is required.",
        )

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type.",
        )

    caption = caption.strip()

    if len(caption) > 255:
        raise HTTPException(
            status_code=422,
            detail="Caption cannot exceed 255 characters.",
        )

    temp_file_path = None
    total_size = 0

    try:
        extension = os.path.splitext(file.filename)[1]

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
                        status_code=413,
                        detail=(
                            f"File is too large. "
                            f"Maximum size is {MAX_UPLOAD_MB} MB."
                        ),
                    )

                temp_file.write(chunk)

        with open(temp_file_path, "rb") as upload_file:
            upload_result = await asyncio.to_thread(
                imagekit.files.upload,
                file=upload_file,
                file_name=file.filename,
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
            "likes_count": 0,
            "comments_count": 0,
        }

    except HTTPException:
        await session.rollback()
        raise

    except Exception:
        await session.rollback()
        raise

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        await file.close()


@app.get("/feed", tags=["posts"])
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
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
    post_ids = [post.id for post in posts]

    like_counts = {}
    comment_counts = {}
    liked_posts = set()

    if post_ids:
        like_result = await session.execute(
            select(
                Like.post_id,
                func.count(Like.id),
            )
            .where(Like.post_id.in_(post_ids))
            .group_by(Like.post_id)
        )

        like_counts = {
            post_id: count
            for post_id, count in like_result.all()
        }

        comment_result = await session.execute(
            select(
                Comment.post_id,
                func.count(Comment.id),
            )
            .where(Comment.post_id.in_(post_ids))
            .group_by(Comment.post_id)
        )

        comment_counts = {
            post_id: count
            for post_id, count in comment_result.all()
        }

        liked_result = await session.execute(
            select(Like.post_id)
            .where(
                Like.post_id.in_(post_ids),
                Like.user_id == user.id,
            )
        )

        liked_posts = {
            post_id
            for post_id in liked_result.scalars().all()
        }

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
                "is_owner": str(post.user_id) == str(user.id),
                "email": post.user.email if post.user else None,
                "likes_count": like_counts.get(post.id, 0),
                "comments_count": comment_counts.get(post.id, 0),
                "liked_by_me": post.id in liked_posts,
            }
        )

    return {
        "posts": posts_data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(posts_data) < total,
    }


@app.post("/posts/{post_id}/like", tags=["social"])
async def toggle_like(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    post_result = await session.execute(
        select(Post.id).where(Post.id == post_id)
    )

    if post_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Post not found.",
        )

    like_result = await session.execute(
        select(Like).where(
            Like.post_id == post_id,
            Like.user_id == user.id,
        )
    )

    like = like_result.scalar_one_or_none()

    if like:
        await session.delete(like)
        liked = False
    else:
        session.add(
            Like(
                user_id=user.id,
                post_id=post_id,
            )
        )
        liked = True

    await session.commit()

    count_result = await session.execute(
        select(func.count(Like.id)).where(
            Like.post_id == post_id
        )
    )

    return {
        "liked": liked,
        "likes_count": count_result.scalar_one(),
    }


@app.get("/posts/{post_id}/comments", tags=["social"])
async def get_comments(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
    limit: int = Query(50, ge=1, le=100),
):
    result = await session.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .limit(limit)
    )

    comments = result.scalars().all()

    return [
        {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "email": comment.user.email if comment.user else "User",
            "is_owner": str(comment.user_id) == str(user.id),
        }
        for comment in comments
    ]


@app.post("/posts/{post_id}/comments", tags=["social"])
async def add_comment(
    post_id: str,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    post_result = await session.execute(
        select(Post.id).where(Post.id == post_id)
    )

    if post_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Post not found.",
        )

    content = payload.content.strip()

    if not content:
        raise HTTPException(
            status_code=422,
            detail="Comment cannot be empty.",
        )

    comment = Comment(
        user_id=user.id,
        post_id=post_id,
        content=content,
    )

    session.add(comment)
    await session.commit()
    await session.refresh(comment)

    return {
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.isoformat(),
        "email": user.email,
    }


@app.delete("/comments/{comment_id}", tags=["social"])
async def delete_comment(
    comment_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    result = await session.execute(
        select(Comment).where(Comment.id == comment_id)
    )

    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found.",
        )

    if str(comment.user_id) != str(user.id):
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own comments.",
        )

    await session.delete(comment)
    await session.commit()

    return {"message": "Comment deleted."}


@app.patch("/posts/{post_id}", tags=["posts"])
async def update_post(
    post_id: str,
    payload: PostUpdate,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    result = await session.execute(
        select(Post).where(Post.id == post_id)
    )

    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found.",
        )

    if str(post.user_id) != str(user.id):
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own posts.",
        )

    post.caption = payload.caption.strip() or None
    await session.commit()

    return {
        "message": "Post updated.",
        "caption": post.caption,
    }


@app.get("/profile/me", tags=["profile"])
async def my_profile(
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    posts_result = await session.execute(
        select(Post)
        .where(Post.user_id == user.id)
        .order_by(Post.created_at.desc())
    )

    posts = posts_result.scalars().all()
    post_ids = [post.id for post in posts]

    total_likes = 0

    if post_ids:
        likes_result = await session.execute(
            select(func.count(Like.id))
            .where(Like.post_id.in_(post_ids))
        )
        total_likes = likes_result.scalar_one()

    return {
        "id": str(user.id),
        "email": user.email,
        "post_count": len(posts),
        "likes_received": total_likes,
        "posts": [
            {
                "id": post.id,
                "url": post.url,
                "file_type": (
                    "video"
                    if post.file_type.startswith("video/")
                    else "image"
                ),
                "caption": post.caption,
                "created_at": post.created_at.isoformat(),
            }
            for post in posts
        ],
    }


@app.delete("/delete/{post_id}", tags=["posts"])
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    result = await session.execute(
        select(Post).where(Post.id == post_id)
    )

    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found.",
        )

    if str(post.user_id) != str(user.id):
        raise HTTPException(
            status_code=403,
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
