import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Response, HTTPException, Depends
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

coef = {}

dataset ={
    "OperationsInDay" : 1000,
    "WorkTimeInDay" : 22.0
}

TTC = {
    "PassportPerformance" : 100,
    "WorkTime" : 6.0,
    "ChargeTime" : 0.3
}

def get_dataset(robotID : int):
    return dataset
def get_TTC(robotID : int):
    return TTC

def get_db_URL(route : str = "") -> str :
    load_dotenv()
    URL = os.getenv("URL", "http://127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", 8000)
    return f"{URL}:{DB_PORT}/" + route


async def get_coff(name: str) -> dict:
    async with httpx.AsyncClient() as session:
        user = await session.get(get_db_URL("coef"), params={"name": name})
        try:
            data = user.json()
            coef[id] = data
            return data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")

@app.get("math/robots")
async def get_robot_count(robotID : int, scenario : str):
    try:
        k_res = (await get_coff("k_res"))[scenario]
        k_PeLo = (await get_coff("k_PeLo"))[scenario]
        k_load = (await  get_coff("K_load"))[scenario]

        dataset = get_dataset(robotID)
        TTC = get_TTC(robotID)

        peak_req = dataset["OperationsInDay"] / dataset["WorkTimeInDay"] * k_PeLo
        k_avail = TTC["WorkTime"] / (TTC["WorkTime"] + TTC["ChargeTime"])
        Ef_perf = TTC["PassportPerformance"] * k_avail * k_load
        robot_count = (peak_req / Ef_perf)  * k_res

        return {
            "ok" : True, "robot_count": robot_count, "k_res":k_res, "k_PeLo": k_PeLo, "k_load": k_load,
            "peak_req":peak_req, "k_avail": k_avail, "Ef_perf": Ef_perf
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")


@app.get("math/CAPEX")
async def get_CAPEX(robotID : int, scenario : str):
    return