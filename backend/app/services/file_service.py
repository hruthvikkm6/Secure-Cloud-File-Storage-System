import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Tuple, Optional
from app.db import models
import mimetypes
import tempfile
from pathlib import Path
from typing import cast

SAFE_PREVIEW_MIMES = {
    "image/png",
    "image/jpeg",
    "application/pdf",
}

SAFE_PREVIEW_EXTS = {".png", ".jpg", ".jpeg", ".pdf"}


def _decrypt_bytes(encrypted: bytes, salt_hex: str, iv_hex: str, password: str) -> bytes:
    key = derive_key(password, bytes.fromhex(salt_hex))
    cipher = Cipher(algorithms.AES(key), modes.CBC(bytes.fromhex(iv_hex)))
    decryptor = cipher.decryptor()
    padded = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded) + unpadder.finalize()
    return data


def _ensure_owned_file(db: Session, file_id: int, user_id: int) -> models.File:
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if db_file.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
    return db_file


def _write_tempfile(content: bytes, filename: str) -> str:
    suffix = ''.join(Path(filename).suffixes) or ''
    fd, tmp_path = tempfile.mkstemp(prefix="mgd_", suffix=suffix)
    with os.fdopen(fd, 'wb') as f:
        f.write(content)
    return tmp_path


def download_file(db: Session, file_id: int, user: models.User, password: str, bg: BackgroundTasks) -> FileResponse:
    db_file = _ensure_owned_file(db, file_id, user.id)
    try:
        data = _decrypt_bytes(db_file.encrypted_content, db_file.encryption_salt, db_file.encryption_iv, password)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password or corrupted file")
    tmp_path = _write_tempfile(data, db_file.filename)
    # clean up after response is sent
    bg.add_task(lambda p: os.path.exists(p) and os.remove(p), tmp_path)
    return FileResponse(path=tmp_path, filename=db_file.filename, media_type="application/octet-stream")


def preview_file(db: Session, file_id: int, user: models.User, password: str, bg: BackgroundTasks) -> FileResponse:
    db_file = _ensure_owned_file(db, file_id, user.id)
    ext = Path(db_file.filename).suffix.lower()
    guessed, _ = mimetypes.guess_type(db_file.filename)
    media_type = guessed or "application/octet-stream"
    if media_type not in SAFE_PREVIEW_MIMES and ext not in SAFE_PREVIEW_EXTS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Preview not supported for this file type")
    try:
        data = _decrypt_bytes(db_file.encrypted_content, db_file.encryption_salt, db_file.encryption_iv, password)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password or corrupted file")
    tmp_path = _write_tempfile(data, db_file.filename)
    bg.add_task(lambda p: os.path.exists(p) and os.remove(p), tmp_path)
    # inline preview (no forced download)
    # Return inline (no Content-Disposition attachment) by omitting filename
    return FileResponse(path=tmp_path, media_type=media_type)


def delete_file(db: Session, file_id: int, user: models.User) -> dict:
    db_file = _ensure_owned_file(db, file_id, user.id)
    # Data is stored in DB (encrypted_content); there is no separate disk path, so deleting the row removes the content
    db.delete(db_file)
    db.commit()
    return {"status": "success", "message": "File deleted"}

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
    return kdf.derive(password.encode('utf-8'))

def encrypt_file(file_content: bytes, password: str) -> dict:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    iv = os.urandom(16)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(file_content) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return {"encrypted_content": encrypted_data, "salt": salt.hex(), "iv": iv.hex()}

def get_files_for_user(db: Session, user_id: int) -> List[models.File]:
    return db.query(models.File).filter(models.File.owner_id == user_id).all()

async def save_file(db: Session, upload_file: UploadFile, user: models.User, password: str) -> models.File:
    file_content = await upload_file.read()
    encryption_data = encrypt_file(file_content, password)
    db_file = models.File(
        filename=upload_file.filename,
        encrypted_content=encryption_data["encrypted_content"],
        encryption_salt=encryption_data["salt"],
        encryption_iv=encryption_data["iv"],
        owner_id=user.id,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file