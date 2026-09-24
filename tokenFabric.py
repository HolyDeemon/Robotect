import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "key")

ALGORITHM = "HS256"
TOKEN_EXPIRE = timedelta(days=1)

def create(userID: int, role:str = "user"):
    now = datetime.now(timezone.utc)
    payload = {
        "sub" : str(userID),
        "role" : role,
        "iat" : now,
        "exp" : now + TOKEN_EXPIRE
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Невалидный токен")

def checkRole(token: str, role : str) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["role"] == role
    except:
        raise HTTPException(status_code=401, detail="Невалидный токен")

