from typing import List
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, Form, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas
from app.db import models
from app.db.database import get_db
from app.services import file_service
from .auth import get_current_active_user

router = APIRouter()

@router.post("/files/upload", response_model=schemas.file.File, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = FastAPIFile(...), password: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    return await file_service.save_file(db=db, upload_file=file, user=current_user, password=password)

@router.get("/files", response_model=List[schemas.file.File])
def list_user_files(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return file_service.get_files_for_user(db=db, user_id=current_user.id)