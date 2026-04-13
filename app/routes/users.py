from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{username}", response_model=schemas.UserProfileOut)
def get_user_profile(
        username: str,
        db: Session = Depends(get_db),
        current_user: models.User | None = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    posts_count = db.query(models.Post).filter(models.Post.user_id == user.id).count()

    is_following = False
    if current_user:
        pass

    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "created_at": user.created_at,
        "posts_count": posts_count,
        "is_following": is_following,
    }


@router.patch("/me", response_model=schemas.UserOut)
def update_my_profile(
        profile_data: schemas.UserUpdate,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    if profile_data.nickname is not None:
        current_user.nickname = profile_data.nickname

    db.commit()
    db.refresh(current_user)
    return current_user