from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.domain import Role, User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()

def hash_password(value: str) -> str: return pwd.hash(value)
def verify_password(plain: str, hashed: str) -> bool: return pwd.verify(plain, hashed)

def create_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": user.id, "exp": expires}, settings.jwt_secret, algorithm="HS256")

def create_refresh_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode({"sub": user.id,"type":"refresh","exp":expires},settings.jwt_refresh_secret,algorithm="HS256")

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        user_id = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if not user or not user.is_active: raise HTTPException(status_code=401, detail="Inactive user")
    return user

def roles(*allowed: Role):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in allowed: raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
