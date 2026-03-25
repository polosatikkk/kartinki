from pydantic import BaseModel, Field, field_validator
from typing import Optional

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