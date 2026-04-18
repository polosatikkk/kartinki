from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, schemas
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/comments", tags=["comments"])


def _enrich_comment(comment: models.Comment, current_user_id: Optional[int], db: Session):
    replies_count = db.query(func.count(models.Comment.id)).filter(
        models.Comment.parent_id == comment.id
    ).scalar() or 0
    likes_count = 0
    is_liked = False
    return {
        "id": comment.id,
        "text": comment.text,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "user_id": comment.user_id,
        "post_id": comment.post_id,
        "parent_id": comment.parent_id,
        "username": comment.user.username,
        "user_nickname": comment.user.nickname,
        "user_avatar_url": f"/uploads/avatars/{comment.user.avatar_path}" if comment.user.avatar_path else None,
        "replies_count": replies_count,
        "likes_count": likes_count,
        "is_liked": is_liked,
        "is_owner": current_user_id == comment.user_id
    }


@router.post("/", response_model=schemas.CommentOut)
def create_comment(
        comment_data: schemas.CommentCreate,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    post = db.query(models.Post).filter(models.Post.id == comment_data.post_id).first()
    if not post:
        raise HTTPException(404, "Пост не найден")
    parent_id = comment_data.parent_id if comment_data.parent_id and comment_data.parent_id > 0 else None
    if parent_id:
        parent = db.query(models.Comment).filter(models.Comment.id == parent_id).first()
        if not parent:
            raise HTTPException(404)
        if parent.post_id != comment_data.post_id:
            raise HTTPException(400)
    comment = models.Comment(
        text=comment_data.text,
        user_id=current_user.id,
        post_id=comment_data.post_id,
        parent_id=parent_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return _enrich_comment(comment, current_user.id, db)


@router.get("/post/{post_id}", response_model=List[schemas.CommentOut])
def get_post_comments(
        post_id: int,
        skip: int = 0,
        limit: int = 50,
        current_user: Optional[models.User] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Пост не найден")
    comments = db.query(models.Comment).filter(
        models.Comment.post_id == post_id,
        models.Comment.parent_id == None
    ).order_by(models.Comment.created_at.desc()).offset(skip).limit(limit).all()
    current_user_id = current_user.id if current_user else None
    return [_enrich_comment(c, current_user_id, db) for c in comments]


@router.get("/{comment_id}/replies", response_model=List[schemas.CommentOut])
def get_comment_replies(
        comment_id: int,
        skip: int = 0,
        limit: int = 20,
        current_user: Optional[models.User] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Комментарий не найден")
    replies = db.query(models.Comment).filter(
        models.Comment.parent_id == comment_id
    ).order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    current_user_id = current_user.id if current_user else None
    return [_enrich_comment(r, current_user_id, db) for r in replies]


@router.patch("/{comment_id}", response_model=schemas.CommentOut)
def update_comment(
        comment_id: int,
        comment_data: schemas.CommentUpdate,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    comment = db.query(models.Comment).filter(
        models.Comment.id == comment_id,
        models.Comment.user_id == current_user.id
    ).first()
    if not comment:
        raise HTTPException(404, "Комментарий не найден или вы не можете его редактировать")
    comment.text = comment_data.text
    db.commit()
    db.refresh(comment)
    return _enrich_comment(comment, current_user.id, db)


@router.delete("/{comment_id}")
def delete_comment(
        comment_id: int,
        current_user: Annotated[models.User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    comment = db.query(models.Comment).filter(
        models.Comment.id == comment_id,
        models.Comment.user_id == current_user.id
    ).first()

    if not comment:
        raise HTTPException(404, "Комментарий не найден или вы не можете его удалить")

    db.delete(comment)
    db.commit()
    return {"message": "Комментарий удален"}