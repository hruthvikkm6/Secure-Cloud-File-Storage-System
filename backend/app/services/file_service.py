import os
import uuid
import time
import mimetypes
import tempfile
from pathlib import Path
from threading import Lock
from typing import List, Tuple, Optional, cast
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from app.db import models
from app.core.security import verify_password

SAFE_PREVIEW_MIMES = {
    "image/png",
    "image/jpeg",
    "application/pdf",
}

SAFE_PREVIEW_EXTS = {".png", ".jpg", ".jpeg", ".pdf"}

# Thread-safe in-memory cache for single-use decryption tickets (STAT)
ACTIVE_TICKETS = {}
tickets_lock = Lock()


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


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 32-byte key from a user password using PBKDF2-HMAC-SHA256.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_file(file_content: bytes, password: str) -> dict:
    """
    Encrypt a file using modern AES-256-GCM.
    Yields high confidentiality and data integrity, resisting padding oracles.
    """
    salt = os.urandom(16)
    key = derive_key(password, salt)
    nonce = os.urandom(12)  # Standard 12-byte IV for GCM mode

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    
    # GCM is a stream-based mode; no PKCS7 padding is required!
    ciphertext = encryptor.update(file_content) + encryptor.finalize()
    tag = encryptor.tag  # 16-byte authentication tag

    # Prepend the authentication tag to the ciphertext for convenient single-field storage
    encrypted_data = tag + ciphertext

    return {
        "encrypted_content": encrypted_data,
        "salt": salt.hex(),
        "iv": nonce.hex()
    }


def _decrypt_bytes_with_key(encrypted: bytes, iv_hex: str, key: bytes) -> bytes:
    """
    Decrypts encrypted content using a pre-derived cryptographic key.
    Detects whether the file was encrypted using legacy AES-CBC (16-byte IV)
    or upgraded AES-GCM (12-byte IV/nonce) to ensure backward compatibility.
    """
    iv_bytes = bytes.fromhex(iv_hex)

    if len(iv_bytes) == 12:  # Modern AES-256-GCM mode
        # Extract the 16-byte authentication tag prepended during encryption
        tag = encrypted[:16]
        ciphertext = encrypted[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv_bytes, tag))
        decryptor = cipher.decryptor()
        
        # This will automatically raise an InvalidTag exception if ciphertext or tag was tampered with
        data = decryptor.update(ciphertext) + decryptor.finalize()
        return data

    else:  # Legacy AES-256-CBC mode fallback
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv_bytes))
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        
        # Remove PKCS7 padding
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data


def _decrypt_bytes(encrypted: bytes, salt_hex: str, iv_hex: str, password: str) -> bytes:
    """
    Derives key from password on-the-fly and decrypts data.
    """
    key = derive_key(password, bytes.fromhex(salt_hex))
    return _decrypt_bytes_with_key(encrypted, iv_hex, key)


def create_decryption_ticket(db: Session, file_id: int, user: models.User, password: str) -> str:
    """
    Validates user credentials, derives the file key, and registers a single-use
    decryption ticket in memory with a 60-second lifetime.
    Passes zero sensitive passwords in future GET URLs.
    """
    # 1. Verify file ownership and existence first
    db_file = _ensure_owned_file(db, file_id, user.id)

    # 2. Derive the file decryption key in memory
    derived_key = derive_key(password, bytes.fromhex(db_file.encryption_salt))

    # 3. Cryptographically verify the passcode by performing an in-memory test decryption.
    # If the passcode is incorrect, GCM tag verification or CBC padding check will raise an exception.
    try:
        _decrypt_bytes_with_key(db_file.encrypted_content, db_file.encryption_iv, derived_key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect encryption password.")

    current_time = time.time()
    
    # Thread-safe write to ticket register
    with tickets_lock:
        # Housekeeping: prune any expired tickets to prevent leaks
        expired_keys = [k for k, v in ACTIVE_TICKETS.items() if current_time > v["expires_at"]]
        for ek in expired_keys:
            ACTIVE_TICKETS.pop(ek, None)

        # 4. Generate a unique, highly random ticket UUID
        ticket_id = str(uuid.uuid4())
        ACTIVE_TICKETS[ticket_id] = {
            "file_id": file_id,
            "key": derived_key,
            "expires_at": current_time + 60.0  # 60 seconds lifespan
        }

    return ticket_id


def download_file(db: Session, file_id: int, ticket_id: str, bg: BackgroundTasks) -> FileResponse:
    """
    Redeems a secure single-use ticket to decrypt and download a file.
    Does not log sensitive passwords in system HTTP GET headers or proxy logs.
    """
    current_time = time.time()
    
    # Retrieve and destroy the ticket immediately (single-use constraint)
    with tickets_lock:
        ticket = ACTIVE_TICKETS.pop(ticket_id, None)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used decryption ticket."
        )

    if ticket["file_id"] != file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Violation: Ticket mismatch for requested file."
        )

    if current_time > ticket["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Alert: Decryption ticket has expired."
        )

    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Decrypt using pre-derived key
        data = _decrypt_bytes_with_key(db_file.encrypted_content, db_file.encryption_iv, ticket["key"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decryption failed. The file may be corrupted or has been altered."
        )

    tmp_path = _write_tempfile(data, db_file.filename)
    bg.add_task(lambda p: os.path.exists(p) and os.remove(p), tmp_path)
    return FileResponse(path=tmp_path, filename=db_file.filename, media_type="application/octet-stream")


def preview_file(db: Session, file_id: int, ticket_id: str, bg: BackgroundTasks) -> FileResponse:
    """
    Redeems a secure single-use ticket to decrypt and preview a file inline.
    Guarantees strict safety boundaries on previews.
    """
    current_time = time.time()
    
    # Retrieve and destroy the ticket immediately (single-use constraint)
    with tickets_lock:
        ticket = ACTIVE_TICKETS.pop(ticket_id, None)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used decryption ticket."
        )

    if ticket["file_id"] != file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Violation: Ticket mismatch for requested file."
        )

    if current_time > ticket["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Alert: Decryption ticket has expired."
        )

    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    ext = Path(db_file.filename).suffix.lower()
    
    # Explicit mapping for safe preview types to ensure consistency across operating systems
    MIME_FALLBACK = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf"
    }
    
    guessed, _ = mimetypes.guess_type(db_file.filename)
    media_type = guessed or MIME_FALLBACK.get(ext) or "application/octet-stream"
    
    # Force the correct media type if extension is standard but system mime-types are unregistered
    if ext in MIME_FALLBACK:
        media_type = MIME_FALLBACK[ext]
        
    if media_type not in SAFE_PREVIEW_MIMES and ext not in SAFE_PREVIEW_EXTS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Safe preview is not supported for this format. Please download the file instead."
        )

    try:
        # Decrypt using pre-derived key
        data = _decrypt_bytes_with_key(db_file.encrypted_content, db_file.encryption_iv, ticket["key"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decryption failed. The file may be corrupted or has been altered."
        )

    tmp_path = _write_tempfile(data, db_file.filename)
    bg.add_task(lambda p: os.path.exists(p) and os.remove(p), tmp_path)
    return FileResponse(path=tmp_path, media_type=media_type)


def delete_file(db: Session, file_id: int, user: models.User) -> dict:
    db_file = _ensure_owned_file(db, file_id, user.id)
    db.delete(db_file)
    db.commit()
    return {"status": "success", "message": "File and encrypted blocks deleted successfully."}


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