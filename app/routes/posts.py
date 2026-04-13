import os
import uuid
from typing import List, Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, schemas
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])

UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=schemas.PostOut)
async def create_post(
        description: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    image_filename = None

    if file:
        if file.filename:
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
    db.commit()
    db.refresh(db_post)

    return db_post


@router.get("/feed/latest", response_model=List[schemas.PostOut])
def get_latest_posts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.Post).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/feed/popular", response_model=List[schemas.PostOut])
def get_popular_posts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.Post).order_by(func.random()).offset(skip).limit(limit).all()


@router.get("/feed/following", response_model=List[schemas.PostOut])
def get_following_feed(
    current_user: models.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return db.query(models.Post).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/user/{username}", response_model=List[schemas.PostOut])
def get_user_posts(
        username: str,
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(404, "Пользователь не найден")

    posts = db.query(models.Post).filter(
        models.Post.user_id == user.id
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

    return posts


@router.get("/{post_id}", response_model=schemas.PostOut)
def get_single_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Пост не найден")
    return post


@router.delete("/{post_id}")
def delete_post(
        post_id: int,
        current_user: models.User = Depends(get_current_user),
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


