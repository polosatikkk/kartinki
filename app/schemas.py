from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserReg(BaseModel):
    username: str = Field(min_length=5, max_length=40, description="")
    nickname: Optional[str] = Field(None, max_length=40)
    password: str = Field(min_length=6)
    password2: str = Field(min_length=6)

    @field_validator('username')
    def username_correct(cls, value):
        if not value.isalnum():
            raise ValueError('Имя пользователя должно содержать только буквы и цифры')
        return value

    @field_validator('password2')
    def passwords_match(cls, value, info):
        if 'password' in info.data and value != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return value


#class UserRegOut(BaseModel):
 #   username: str
  #  nickname: Optional[str] = None
   # class Config:
    #    from_attributes = True
        # для профиля потом хз

class UserLog(BaseModel):
    username: str
    password: str

