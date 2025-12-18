import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import List
from app.db import models

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