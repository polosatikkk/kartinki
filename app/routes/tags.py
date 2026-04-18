# app/routes/tags.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, schemas
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/tags", tags=["tags"])


def parse_tags_from_text(text: str) -> List[str]:
    if not text:
        return []
    tags = []
    for word in text.split():
        if word.startswith("#") and len(word) > 1:
            tag = word[1:].lower().strip('#')
            if tag and len(tag) <= 50:
                tags.append(tag)

    return list(set(tags))


@router.get("/search/", response_model=List[schemas.TagOut])
def search_tags(
        q: str,
        limit: int = 10,
        db: Session = Depends(get_db)
):
    tags = db.query(models.Tag).filter(
        models.Tag.name.ilike(f"%{q}%")
    ).limit(limit).all()

    result = []
    for tag in tags:
        posts_count = db.query(func.count(models.post_tags.c.post_id)).filter(
            models.post_tags.c.tag_id == tag.id
        ).scalar() or 0

        result.append({
            "id": tag.id,
            "name": tag.name,
            "posts_count": posts_count
        })

    return result


@router.get("/{tag_name}/posts", response_model=List[schemas.PostOut])
def get_posts_by_tag(
        tag_name: str,
        skip: int = 0,
        limit: int = 20,
        current_user: Optional[models.User] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    tag = db.query(models.Tag).filter(models.Tag.name == tag_name.lower()).first()
    if not tag:
        return []

    posts = db.query(models.Post).join(
        models.post_tags, models.post_tags.c.post_id == models.Post.id
    ).filter(
        models.post_tags.c.tag_id == tag.id
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    from app.routes.posts import _enrich_post
    current_user_id = current_user.id if current_user else None
    return [_enrich_post(p, current_user_id, db) for p in posts]


@router.get("/popular/", response_model=List[schemas.TagOut])
def get_popular_tags(
        limit: int = 20,
        db: Session = Depends(get_db)
):
    tags = db.query(
        models.Tag,
        func.count(models.post_tags.c.post_id).label('posts_count')
    ).join(
        models.post_tags, models.post_tags.c.tag_id == models.Tag.id
    ).group_by(
        models.Tag.id
    ).order_by(
        func.count(models.post_tags.c.post_id).desc()
    ).limit(limit).all()

    return [
        {
            "id": tag.id,
            "name": tag.name,
            "posts_count": posts_count
        }
        for tag, posts_count in tags
    ]