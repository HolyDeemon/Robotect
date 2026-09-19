from fastapi import *
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
from DATABASE.db_dao import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)


@app.get("/{id}")
async def getUser( id : int):
    return UsersDAO.find_one_or_none_by_id(id)


@app.post("/post")
async def registerUser(user_data: SUserRegister):
    return await UsersDAO.add(
        name=SUserRegister.name,
        email=SUserRegister.email,
        password=SUserRegister.password
    )

