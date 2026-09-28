from fastapi import FastAPI, Request, HTTPException, Depends, Cookie, Body
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
async def get_coef(name: str):
    coef = await CoefDAO.find_one_or_none(name=name)
    if coef is None and name != name.lower():
        coef = await CoefDAO.find_one_or_none(name=name.lower())
    if coef is None:
        raise HTTPException(status_code=404, detail="Коэффицент не найден")
    return {
        "id": coef.id,
        "name": coef.name,
        "min": coef.min,
        "base": coef.base,
        "max": coef.max,
        "from_dataset": coef.from_dataset,
        "opt": coef.max,
        "pess": coef.min,
    }

@app.post("/coef")
async def add_coef(coef_data: SCoefCreate):
    try:
        return await CoefDAO.add(**coef_data.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")



@app.get("/robot")
async def get_robot(robot_id : int):
    robot = await RobotDAO.find_one_or_none_by_id(robot_id)
    if robot is None:
        raise HTTPException(status_code=404, detail="Робот не найден")
    return {
        "id": robot.id,
        "model": robot.model,
        "cost": robot.cost,
        "accum_life": robot.accum_life,
        "capacity": robot.capacity,
        "mass": robot.mass,
        "length": robot.size_x,
        "width": robot.size_y,
        "height": robot.size_z,
        "size_x": robot.size_x,
        "size_y": robot.size_y,
        "size_z": robot.size_z,
        "max_speed": robot.max_speed,
        "navigation_type": robot.navigation_type,
        "charge_time": robot.charge_time,
        "work_time": robot.work_time,
        "efficiency": robot.efficiency,
        "accuracy": robot.accuracy,
        "operationg_conditions": robot.from_dataset or "",
        "from_dataset": robot.from_dataset,
    }

@app.post("/robot")
async def get_dataset(data: SRobot):
    try:
        return await RobotDAO.add(**data.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")


@app.get("/dataset")
async def get_dataset(case_id: int):
    dataset = await DatasetDAO.get_by_case(case_id=case_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Датасет не найден")
    return {
        "id": dataset.id,
        "case_id": dataset.case_id,
        "object_type": dataset.object_type,
        "source_file": dataset.source_file,
        "data": dataset.data,
        "created_at": dataset.created_at,
    }

@app.post("/dataset")
async def add_dataset(data: SDatasetCreate):
    try:
        saved = await DatasetDAO.upsert_for_case(
            case_id=data.case_id,
            object_type=data.object_type,
            data=data.data,
            source_file=data.source_file,
        )
        return {"ok": True, "id": saved.id, "case_id": saved.case_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")


@app.get("/case")
async def get_case(case_id: int):
    case = await CaseDAO.find_one_or_none_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Кейс не найден")
    return {
        "id": case.id,
        "name": case.name,
        "object_type": case.object_type,
        "description": case.description,
        "robot_count": case.robot_count,
        "shortened": case.shortened,
        "tariff": case.tariff,
    }

@app.put("/case")
async def update_case(id: int, case: SCaseUpdate):
    try:
        updated = await CaseDAO.update_case(id=id, **case.model_dump(exclude_unset=True))
        return {
            "ok": True,
            "id": updated.id,
            "description": updated.description,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")


