from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
from DATABASE.db_dao import *
from DATABASE.models import *
from tokenFabric import decode

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=False, ###TRUE
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)


async def get_current_user(user_access_token: str = Cookie(None)) -> dict:
    if not user_access_token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user_id = decode(user_access_token).get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    return await UsersDAO.find_one_or_none_by_id(int(user_id))

@app.get("/current_user")
async def get_user(user :  User = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.get("/user")
async def get_user_by_email(email : EmailStr):
    user = await UsersDAO.find_one_or_none(email = email)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.post("/user")
async def add_user(user_data : SUserRegisterHashed):
    try:
        return await UsersDAO.add(**user_data.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")


@app.get("/coef")
async def get_coef(name: int):
    coef = await CoefDAO.find_one_or_none(name=name)
    if coef is None:
        raise HTTPException(status_code=404, detail="Коэффицент не найден")
    return coef

@app.post("/coef")
async def get_coef(coef_data: SCoefCreate):
    try:
        return await CoefDAO.add(**coef_data.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")
