from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from jose import jwt, JWTError
from starlette.responses import RedirectResponse

from database import SessionLocal
from models import User

router = APIRouter(
    prefix='/auth',
    tags=["Authentication"]
)

SECRET_KEY = "g9oxz83e5ha8r7ubii3ejpxb9k76mo8a57atre8i77l5ytuvcblewtzbj1g3kj04"
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    payload = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        user_id = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or ID is invalid")
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
        db: db_dependency,
        username: str = Form(...),
        email: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        password: str = Form(...),
        phone_number: str = Form(...)
):
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        hashed_password=bcrypt_context.hash(password)
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.post("/token", response_model=Token)
async def login_for_access_token(
        db: db_dependency,
        username: str = Form(...),
        password: str = Form(...)
):
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı"
        )

    token = create_access_token(user.username, user.id, timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}
