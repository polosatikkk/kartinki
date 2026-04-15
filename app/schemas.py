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
    bio: str | None = None
    avatar_path: str | None = None
    is_private: bool = False
    created_at: datetime

    @property
    def avatar_url(self) -> Optional[str]:
        if self.avatar_path:
            return f"/uploads/avatars/{self.avatar_path}"
        return None
class UserProfileOut(UserOut):
    posts_count: int
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False
    is_owner: bool = False
class UserUpdate(BaseModel):
    nickname: str | None = Field(None, max_length=40)
    bio: str | None = Field(None, max_length=40)
    is_private: bool | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=4)
    new_password2: str

    @field_validator('new_password2')
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Новые пароли не совпадают')
        return v

class PostBase(BaseModel):
    description: str | None = None


class PostCreate(PostBase):
    pass


class PostOut(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: Optional[str] = None
    created_at: datetime
    user_id: int

    @property
    def image_url(self) -> Optional[str]:
        if self.image_path:
            return f"/uploads/{self.image_path}"
        return None


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    nickname: str | None
    avatar_path: str | None
    is_following: bool = False

    @property
    def avatar_url(self) -> Optional[str]:
        if self.avatar_path:
            return f"/uploads/avatars/{self.avatar_path}"
        return None