from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .dependencies import get_db
from .models.doctor import doctors

router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = "CHANGE_ME_USE_ENV_VAR"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

_BCRYPT_MAX_BYTES = 72


def _prepare_password(password: str) -> bytes:
    data = password.encode("utf-8")
    if len(data) > _BCRYPT_MAX_BYTES:
        # bcrypt ignores everything past 72 bytes; we truncate explicitly to avoid ValueErrors
        data = data[:_BCRYPT_MAX_BYTES]
    return data


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare_password(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare_password(plain_password), password_hash.encode("utf-8"))
    except ValueError:
        # incompatible hash format
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: Optional[str] = None

def authenticate_doctor(db: Session, email: str, password: str) -> Optional[doctors]:
    user = db.query(doctors).filter(doctors.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

async def get_current_doctor(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> doctors:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(sub=sub)
    except JWTError:
        raise credentials_exception

    user = db.get(doctors, int(token_data.sub))
    if user is None:
        raise credentials_exception
    return user

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a doctor using email + password.
    In Swagger, click "Authorize" → username = email, password = password.
    """
    user = authenticate_doctor(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)

@router.get("/me")
def me(current: doctors = Depends(get_current_doctor)):
    """Return the currently logged-in doctor's basic info."""
    return {
        "id": current.id,
        "first_name": current.first_name,
        "last_name": current.last_name,
        "email": current.email,
        "status": current.status.value if hasattr(current.status, "value") else current.status,
    }
