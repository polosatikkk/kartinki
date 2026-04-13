import os
import uuid
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])

UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=schemas.PostOut)
async def create_post(
        description: str = Form(None),
        file: UploadFile = File(...),  # Картинка обязательна
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    file_ext = file.filename.split(".")[-1]
    if file_ext.lower() not in ["jpg", "jpeg", "png", "gif", "webp"]:
        raise HTTPException(400, "Неподдерживаемый формат файла")

    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    db_post = models.Post(
        description=description,
        image_path=filename,
        user_id=current_user.id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return db_post


@router.get("/", response_model=List[schemas.PostOut])
def get_feed(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    # Простая лента: последние посты
    posts = db.query(models.Post).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts