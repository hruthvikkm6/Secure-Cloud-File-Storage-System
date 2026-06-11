from typing import List

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File as FastAPIFile,
    Form,
    HTTPException,
    status,
    BackgroundTasks,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import schemas
from app.db import models
from app.db.database import get_db
from app.services import file_service
from app.core.rate_limit import rate_limit_tickets
from app.schemas.file import FileDecryptRequest
from .auth import get_current_active_user

router = APIRouter()


@router.post(
    "/files/upload",
    response_model=schemas.file.File,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    return await file_service.save_file(
        db=db,
        upload_file=file,
        user=current_user,
        password=password,
    )


@router.get("/files", response_model=List[schemas.file.File])
def list_user_files(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return file_service.get_files_for_user(
        db=db,
        user_id=current_user.id,
    )


@router.post(
    "/files/{file_id}/ticket",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit_tickets)]
)
def create_decryption_ticket(
    file_id: int,
    request_data: FileDecryptRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    POST route to securely request a temporary, single-use file decryption ticket.
    Guards the decryption key inside in-memory cache mapped to a UUID.
    Protected from brute-force dictionary attacks.
    """
    ticket_id = file_service.create_decryption_ticket(
        db=db,
        file_id=file_id,
        user=current_user,
        password=request_data.password
    )
    return {"ticket_id": ticket_id}


@router.get("/files/{file_id}/download", response_class=FileResponse)
def download_file(
    file_id: int,
    background_tasks: BackgroundTasks,
    ticket_id: str = Query(..., description="Secure, short-lived single-use decryption ticket"),
    db: Session = Depends(get_db),
):
    """
    GET route to download a decrypted file using a single-use token.
    Excludes any plaintext user passwords from headers or GET requests.
    """
    return file_service.download_file(
        db=db,
        file_id=file_id,
        ticket_id=ticket_id,
        bg=background_tasks,
    )


@router.get("/files/{file_id}/preview", response_class=FileResponse)
def preview_file(
    file_id: int,
    background_tasks: BackgroundTasks,
    ticket_id: str = Query(..., description="Secure, short-lived single-use decryption ticket"),
    db: Session = Depends(get_db),
):
    """
    GET route to preview a decrypted file in-browser using a single-use token.
    Safe-types only: image/png, image/jpeg, application/pdf.
    """
    return file_service.preview_file(
        db=db,
        file_id=file_id,
        ticket_id=ticket_id,
        bg=background_tasks,
    )


@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return file_service.delete_file(
        db=db,
        file_id=file_id,
        user=current_user,
    )
