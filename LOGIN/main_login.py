import os

from dotenv import load_dotenv
from fastapi import *
from fastapi.middleware.cors import CORSMiddleware
from schemas import SUserAuth
import httpx
import token
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

async def get_http_client() -> httpx.AsyncClient:
    return

@app.get("/{id}")
async def getUser(id : int):
    return

@app.get("/login")
async def getUser(user : SUserAuth, response: Response, tkn:str="") -> Response:



    load_dotenv()

    URL = os.getenv("URL", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", 6000)

    async with httpx.AsyncClient() as session:
        user = await session.get(f"{URL}:{DB_PORT}", params = {
            'email': SUserAuth.email,
            'password': SUserAuth.password
        })
        if user != None:
            response.set_cookie(token.create(user.content["id"]))
