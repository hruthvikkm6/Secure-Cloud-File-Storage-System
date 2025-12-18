from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.schemas.file import File

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: int
    is_active: bool
    hashed_password: str
    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    is_active: bool
    files: List[File] = []
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None