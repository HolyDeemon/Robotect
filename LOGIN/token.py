import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

SECRET_KEY = os.dotenv("SECRET_KEY", "key")

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
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])