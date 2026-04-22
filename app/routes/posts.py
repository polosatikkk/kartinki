import os
import uuid
from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models, schemas
from app.routes.auth import get_current_user, get_current_user_optional
from app.routes.tags import parse_tags_from_text

router = APIRouter(prefix="/api/posts", tags=["posts"])

UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _enrich_post(post: models.Post, current_user_id: Optional[int], db: Session):
    likes_count = db.query(func.count(models.Like.user_id)).filter(
        models.Like.post_id == post.id
    ).scalar() or 0
    comments_count = db.query(func.count(models.Comment.id)).filter(
        models.Comment.post_id == post.id
    ).scalar() or 0
    bookmarks_count = db.query(func.count(models.Bookmark.user_id)).filter(
        models.Bookmark.post_id == post.id
    ).scalar() or 0
    is_liked = False
    is_bookmarked = False
    if current_user_id:
        is_liked = db.query(models.Like).filter(
            models.Like.user_id == current_user_id,
            models.Like.post_id == post.id
        ).first() is not None

        is_bookmarked = db.query(models.Bookmark).filter(
            models.Bookmark.user_id == current_user_id,
            models.Bookmark.post_id == post.id
        ).first() is not None
    tags = []
    for tag in post.tags:
        posts_count = db.query(func.count(models.post_tags.c.post_id)).filter(
            models.post_tags.c.tag_id == tag.id
        ).scalar() or 0
        tags.append({
            "id": tag.id,
            "name": tag.name,
            "posts_count": posts_count
        })
    return {
        "id": post.id,
        "description": post.description,
        "image_path": post.image_path,
        "created_at": post.created_at,
        "user_id": post.user_id,
        "author_username": post.author.username,
        "author_nickname": post.author.nickname,
        "author_avatar_url": f"/uploads/avatars/{post.author.avatar_path}" if post.author.avatar_path else None,
        "likes_count": likes_count,
        "comments_count": comments_count,
        "bookmarks_count": bookmarks_count,
        "is_liked": is_liked,
        "is_bookmarked": is_bookmarked,
        "is_owner": current_user_id == post.user_id,
        "tags": tags
    }

@router.post("/", response_model=schemas.PostOut)
async def create_post(
        description: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    image_filename = None
    if file and file.filename and file.size > 0:
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
            raise HTTPException(400, "Неподдерживаемый формат файла")
        filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        image_filename = filename

    db_post = models.Post(
        description=description,
        image_path=image_filename,
        user_id=current_user.id
    )
    db.add(db_post)
    db.flush()
    if description:
        tag_names = parse_tags_from_text(description)
        for tag_name in tag_names:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
                db.flush()

            db_post.tags.append(tag)

    db.commit()
    db.refresh(db_post)
    return _enrich_post(db_post, current_user.id, db)

@router.get("/feed/latest", response_model=List[schemas.PostOut])
def get_latest_posts(
        skip: int = 0,
        limit: int = 20,
        current_user: Optional[models.User] = Depends(get_current_user_optional),
        db: Session = Depends(get_db)
):
    if current_user:
        following_ids = [u.id for u in current_user.following]
        posts = db.query(models.Post).join(models.User).filter(
            (models.User.is_private == False) |
            (models.User.id.in_(following_ids)) |
            (models.User.id == current_user.id)
        ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    else:
        posts = db.query(models.Post).join(models.User).filter(
            models.User.is_private == False
        ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

    current_user_id = current_user.id if current_user else None
    return [_enrich_post(p, current_user_id, db) for p in posts]


@router.get("/feed/popular", response_model=List[schemas.PostOut])
def get_popular_posts(
        skip: int = 0,
        limit: int = 20,
        current_user: Optional[models.User] = Depends(get_current_user_optional),
        db: Session = Depends(get_db)
):
    if current_user:
        following_ids = [u.id for u in current_user.following]
        posts = db.query(models.Post).join(models.User).filter(
            (models.User.is_private == False) |
            (models.User.id.in_(following_ids)) |
            (models.User.id == current_user.id)
        ).order_by(func.random()).offset(skip).limit(limit).all()
    else:
        posts = db.query(models.Post).join(models.User).filter(
            models.User.is_private == False
        ).order_by(func.random()).offset(skip).limit(limit).all()

    current_user_id = current_user.id if current_user else None
    return [_enrich_post(p, current_user_id, db) for p in posts]


@router.get("/feed/following", response_model=List[schemas.PostOut])
def get_following_feed(
        skip: int = 0,
        limit: int = 20,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    following_ids = [u.id for u in current_user.following]
    posts = db.query(models.Post).filter(
        models.Post.user_id.in_(following_ids)
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

    return [_enrich_post(p, current_user.id, db) for p in posts]



@router.get("/user/{username}", response_model=List[schemas.PostOut])
def get_user_posts(
        username: str,
        skip: int = 0,
        limit: int = 20,
        current_user: Optional[models.User] = Depends(get_current_user_optional),
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(404, "Пользователь не найден")

    is_owner = current_user and current_user.id == user.id
    is_following = current_user and (user in current_user.following) # !,
    if user.is_private and not is_owner and not is_following:
        return []
    posts = db.query(models.Post).filter(
        models.Post.user_id == user.id
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

    return posts


@router.get("/{post_id}", response_model=schemas.PostOut)
def get_single_post(
        post_id: int,
        current_user: Optional[models.User] = Depends(get_current_user_optional),
        db: Session = Depends(get_db)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Пост не найден")

    author = post.author
    if author.is_private:
        is_owner = current_user and current_user.id == author.id
        is_following = current_user and (author in current_user.following)

        if not is_owner and not is_following:
            raise HTTPException(403, "Это приватный пост. Подпишитесь чтобы его увидеть.")

    current_user_id = current_user.id if current_user else None
    return _enrich_post(post, current_user_id, db)

@router.delete("/{post_id}")
def delete_post(
        post_id: int,
        current_user: models.User | None = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    post = db.query(models.Post).filter(
        models.Post.id == post_id,
        models.Post.user_id == current_user.id
    ).first()
    if not post:
        raise HTTPException(404, "Пост не найден или вы не можете его удалить")
    if post.image_path:
        file_path = os.path.join(UPLOAD_DIR, post.image_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(post)
    db.commit()

    return {"message": "Пост удален"}


@router.post("/{post_id}/like")
def like_post(
        post_id: int,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):

    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Пост не найден")

    existing_like = db.query(models.Like).filter(
        models.Like.user_id == current_user.id,
        models.Like.post_id == post_id
    ).first()

    if existing_like:
        raise HTTPException(400, "Пост уже лайкнут")

    like = models.Like(user_id=current_user.id, post_id=post_id)
    db.add(like)
    db.commit()

    likes_count = db.query(models.Like).filter(models.Like.post_id == post_id).count()
    return {"message": "Лайк поставлен", "likes_count": likes_count}


@router.delete("/{post_id}/like")
def unlike_post(
        post_id: int,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):

    like = db.query(models.Like).filter(
        models.Like.user_id == current_user.id,
        models.Like.post_id == post_id
    ).first()

    if not like:
        raise HTTPException(404)
    db.delete(like)
    db.commit()
    likes_count = db.query(models.Like).filter(models.Like.post_id == post_id).count()
    return {"likes_count": likes_count}



@router.post("/{post_id}/bookmark")
def bookmark_post(
        post_id: int,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):

    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Пост не найден")
    existing = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == current_user.id,
        models.Bookmark.post_id == post_id
    ).first()
    if existing:
        raise HTTPException(400, "Пост уже в избранном")

    bookmark = models.Bookmark(user_id=current_user.id, post_id=post_id)
    db.add(bookmark)
    db.commit()

    return {"message": "Пост добавлен в избранное"}


@router.delete("/{post_id}/bookmark")
def unbookmark_post(
        post_id: int,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == current_user.id,
        models.Bookmark.post_id == post_id
    ).first()

    if not bookmark:
        raise HTTPException(404)
    db.delete(bookmark)
    db.commit()
    return {"message": "Пост удален из избранного"}


@router.get("/bookmarks/", response_model=List[schemas.PostOut])
def get_bookmarked_posts(
        skip: int = 0,
        limit: int = 20,
        current_user: Annotated[models.User, Depends(get_current_user)] = None,
        db: Session = Depends(get_db)
):
    bookmarked_posts = db.query(models.Post).join(
        models.Bookmark, models.Bookmark.post_id == models.Post.id
    ).filter(
        models.Bookmark.user_id == current_user.id
    ).order_by(models.Bookmark.created_at.desc()).offset(skip).limit(limit).all()

    return [_enrich_post(p, current_user.id, db) for p in bookmarked_posts]

