from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext
import random
from models import User

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_reset_token(email: str):
    expiration = datetime.utcnow() + timedelta(hours=1)
    return jwt.encode({"sub": email, "exp": expiration}, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def get_user_from_token(token: str, db):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.username == username).first()
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def generate_incident_id():
    return f"INC{random.randint(1000, 9999)}"
