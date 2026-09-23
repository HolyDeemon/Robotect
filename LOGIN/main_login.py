import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import SUserAuth, SUserRegister
import httpx
import tokenFabric
from LOGIN.auth import verify_password, get_password_hash

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

def get_db_URL(route : str = "") -> str :
    load_dotenv()
    URL = os.getenv("URL", "http://127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", 8000)
    return f"{URL}:{DB_PORT}/" + route


@app.post("/users/register")
async def registerUser(user_data: SUserRegister ):
    async with httpx.AsyncClient() as session:
        data = user_data.model_dump()
        data["hashed_password"] = get_password_hash(data.pop("password"))
        try:
            user = await session.post(get_db_URL("user"), json=data)

            if user.status_code != 200:
                raise HTTPException(status_code=user.status_code, detail=user.text)

            return {"ok": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")


@app.post("/users/login")
async def loginUser(user_data : SUserAuth, response: Response) -> dict[str, bool | Any]:
    async with httpx.AsyncClient() as session:
        user = await session.get(get_db_URL("user"), params={"email" : user_data.email})
        data = user.json()
        try:
            print(data)
            if user.status_code != 200:
                raise HTTPException(status_code=401, detail="Неверный email или пароль")

            if not verify_password(user_data.password, data["hashed_password"]):
                raise HTTPException(status_code=401, detail="Неверный email или пароль")

            response.set_cookie("user_access_token", tokenFabric.create(data["id"]))
            return {"ok": True, "user_id": data["id"]}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")
