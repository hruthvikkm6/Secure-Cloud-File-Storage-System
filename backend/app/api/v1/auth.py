from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt
from app import schemas
from app.db import models
from app.db.database import get_db
from app.services import auth_service
from app.core.config import settings
from app.core.security import create_access_token
from app.core.rate_limit import rate_limit_login

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

@router.post(
    "/register",
    response_model=schemas.user.User,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_login)]
)
def register_user(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    return auth_service.create_user(db=db, user=user)

@router.post(
    "/login",
    response_model=schemas.user.Token,
    dependencies=[Depends(rate_limit_login)]
)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.user.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = auth_service.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
