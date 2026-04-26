import os
import uuid
from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models, schemas
from app.routes.auth import get_current_user, get_current_user_optional, verify_password, hash_password

router = APIRouter(prefix="/api/users", tags=["users"])
AVATAR_DIR = "app/uploads/avatars"
HEADER_DIR = "app/uploads/headers"
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(HEADER_DIR, exist_ok=True)

@router.get("/search/", response_model=List[schemas.UserListItem])
def search_users(
        q: str,
        current_user: Optional[models.User] = Depends(get_current_user_optional),
        db: Session = Depends(get_db)
):
    users = db.query(models.User).filter(
        (models.User.username.ilike(f"%{q}%")) |
        (models.User.nickname.ilike(f"%{q}%"))
    ).limit(20).all()
    result = []
    for user in users:
        is_following = False
        if current_user:
            is_following = user in current_user.following
        result.append({
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_path": user.avatar_path,
            "is_following": is_following
        })
    return result




@router.patch("/me", response_model=schemas.UserOut)
def update_my_profile(
        profile_data: schemas.UserUpdate,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    if profile_data.nickname is not None:
        current_user.nickname = profile_data.nickname
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
    if profile_data.is_private is not None:
        current_user.is_private = profile_data.is_private
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        current_user: Annotated[models.User, Depends(get_current_user)] = None,
        db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(400, "Файл не выбран")
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        raise HTTPException(400, "Неподдерживаемый формат")
    if current_user.avatar_path:
        old_path = os.path.join(AVATAR_DIR, current_user.avatar_path)
        if os.path.exists(old_path):
            os.remove(old_path)
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(AVATAR_DIR, filename)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    current_user.avatar_path = filename
    db.commit()

    return {"avatar_url": f"/uploads/avatars/{filename}"}


@router.post("/me/header")
async def upload_header(
        file: UploadFile = File(...),
        current_user: Annotated[models.User, Depends(get_current_user)] = None,
        db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(400, "Файл не выбран")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        raise HTTPException(400, "Неподдерживаемый формат")
    if current_user.header_path:
        old_path = os.path.join(HEADER_DIR, current_user.header_path)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(HEADER_DIR, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    current_user.header_path = filename
    db.commit()

    return {"header_url": f"/uploads/headers/{filename}"}


@router.delete("/me/header")
def delete_header(
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    if current_user.header_path:
        old_path = os.path.join(HEADER_DIR, current_user.header_path)
        if os.path.exists(old_path):
            os.remove(old_path)
        current_user.header_path = None
        db.commit()

    return {"message": "Шапка удалена"}

@router.post("/me/change-password")
def change_password(
        password_data: schemas.PasswordChange,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(400, "Неверный текущий пароль")
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    return {"message": "Пароль успешно изменен"}


@router.delete("/me")
def delete_my_profile(
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):

    if current_user.avatar_path:
        avatar_path = os.path.join(AVATAR_DIR, current_user.avatar_path)
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
    if current_user.header_path:
        header_path = os.path.join(HEADER_DIR, current_user.header_path)
        if os.path.exists(header_path):
            os.remove(header_path)
    posts = db.query(models.Post).filter(models.Post.user_id == current_user.id).all()
    for post in posts:
        if post.image_path:
            file_path = os.path.join("app/uploads", post.image_path)
            if os.path.exists(file_path):
                os.remove(file_path)
    db.delete(current_user)
    db.commit()

    return {"message": "Профиль удален"}


@router.post("/{username}/follow")
def follow_user(
        username: str,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    if current_user.username == username:
        raise HTTPException(400)
    user_to_follow = db.query(models.User).filter(models.User.username == username).first()
    if not user_to_follow:
        raise HTTPException(404, "Пользователь не найден")
    if user_to_follow in current_user.following:
        raise HTTPException(400, "Вы уже подписаны")

    current_user.following.append(user_to_follow)
    db.commit()
    return {"message": f"Вы подписались на {username}"}


@router.delete("/{username}/follow")
def unfollow_user(
        username: str,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    user_to_unfollow = db.query(models.User).filter(models.User.username == username).first()
    if not user_to_unfollow:
        raise HTTPException(404, "Пользователь не найден")
    if user_to_unfollow not in current_user.following:
        raise HTTPException(400, "Вы не подписаны на этого пользователя")
    current_user.following.remove(user_to_unfollow)
    db.commit()

    return {"message": f"Вы отписались от {username}"}


@router.delete("/followers/{username}")
def remove_follower(
        username: str,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    follower = db.query(models.User).filter(models.User.username == username).first()
    if not follower:
        raise HTTPException(404, "Пользователь не найден")
    if follower not in current_user.followers:
        raise HTTPException(400)
    current_user.followers.remove(follower)
    db.commit()
    return {"message": f"Подписчик удален"}

@router.get("/{username}/followers", response_model=List[schemas.UserListItem])
def get_followers(
        username: str,
        current_user: Annotated[models.User | None, Depends(get_current_user_optional)] = None,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    if user.is_private:
        if not current_user:
            raise HTTPException(403, "Профиль скрыт")
        if current_user.id != user.id and current_user not in user.followers:
            raise HTTPException(403, "Профиль скрыт")
    followers_list = []
    for follower in user.followers:
        is_following = False
        if current_user:
            is_following = follower in current_user.following
        followers_list.append({
            "id": follower.id,
            "username": follower.username,
            "nickname": follower.nickname,
            "avatar_path": follower.avatar_path,
            "is_following": is_following
        })
    return followers_list


@router.get("/{username}/following", response_model=List[schemas.UserListItem])
def get_following(
        username: str,
        current_user: Annotated[models.User | None, Depends(get_current_user_optional)] = None,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    if user.is_private:
        if not current_user:
            raise HTTPException(403, "Профиль скрыт")
        if current_user.id != user.id and current_user not in user.followers:
            raise HTTPException(403, "Профиль скрыт")
    following_list = []
    for followed in user.following:
        is_following = False
        if current_user:
            is_following = followed in current_user.following
        following_list.append({
            "id": followed.id,
            "username": followed.username,
            "nickname": followed.nickname,
            "avatar_path": followed.avatar_path,
            "is_following": is_following
        })

    return following_list


@router.get("/{username}", response_model=schemas.UserProfileOut)
def get_user_profile(
        username: str,
        current_user: Annotated[models.User | None, Depends(get_current_user_optional)] = None,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(404, "Пользователь не найден")

    is_owner = current_user and current_user.id == user.id
    is_following = current_user and (user in current_user.following)

    if user.is_private and not is_owner and not is_following:
        return schemas.UserProfileOut(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            bio=None,
            avatar_path=user.avatar_path,
            header_path=user.header_path,
            is_private=True,
            created_at=user.created_at,
            posts_count=0,
            followers_count=0,
            following_count=0,
            is_following=False,
            is_owner=False
        )

    posts_count = db.query(models.Post).filter(models.Post.user_id == user.id).count()
    followers_count = len(user.followers)
    following_count = len(user.following)

    return schemas.UserProfileOut(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        bio=user.bio,
        avatar_path=user.avatar_path,
        header_path=user.header_path,
        is_private=user.is_private,
        created_at=user.created_at,
        posts_count=posts_count,
        followers_count=followers_count,
        following_count=following_count,
        is_following=is_following,
        is_owner=is_owner
    )