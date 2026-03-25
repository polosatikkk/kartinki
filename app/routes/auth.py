from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
        user_data: schemas.UserReg,
        db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter(
        models.User.username == user_data.username
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    nickname = user_data.nickname if user_data.nickname else user_data.username
    db_user = models.User(
        username=user_data.username,
        nickname=nickname,
        hashed_password=hash_password(user_data.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "Registration successful", "user": db_user}


@router.post("/login")
def login(
        login_data: schemas.UserLog,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.username == login_data.username
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    return {
        "message": "Login successful",
        "user_id": user.id,
        "username": user.username,
        "nickname": user.nickname
    }