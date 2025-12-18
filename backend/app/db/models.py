from sqlalchemy import (Boolean, Column, ForeignKey, Integer, String, DateTime, LargeBinary, func)
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    encrypted_content = Column(LargeBinary, nullable=False)
    encryption_iv = Column(String, nullable=False)
    encryption_salt = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="files")