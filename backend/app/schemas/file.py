from pydantic import BaseModel
from datetime import datetime

class FileBase(BaseModel):
    filename: str

class FileCreate(FileBase):
    pass

class File(FileBase):
    id: int
    created_at: datetime
    owner_id: int
    class Config:
        from_attributes = True