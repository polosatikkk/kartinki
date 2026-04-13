from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class UserReg(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    nickname: Optional[str] = Field(None, max_length=40)
    password: str = Field(min_length=4)
    password2: str = Field(min_length=4)

    @field_validator('username')
    def username_correct(cls, value):
        if not value.replace('_', '').isalnum():
            raise ValueError('Только буквы, цифры и _')
        return value

    @field_validator('password2')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v

class UserLog(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    nickname: str | None
    created_at: datetime
class UserProfileOut(UserOut):
    posts_count: int
    is_following: bool = False
class UserUpdate(BaseModel):
    nickname: str | None = Field(None, max_length=40)


class PostBase(BaseModel):
    description: str | None = None


class PostCreate(PostBase):
    pass


class PostOut(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    created_at: datetime
    user_id: int


    @property
    def image_url(self) -> str:
        return f"/uploads/{self.image_path}"