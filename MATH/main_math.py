import asyncio
import os
import httpx

from dotenv import load_dotenv

from fastapi import FastAPI, WebSocketDisconnect, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware

import tokenFabric
from MATH.formulas import *
from schemas import SIndex

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

_coef_cache: dict[str, dict] = {}
_cache_lock = asyncio.Lock()
active_simulations: dict[int, dict] = {}


dataset ={
    "OperationsInDay" : 1000,
    "OperationsValue" : 100,
    "WorkTimeInDay" : 22.0
}

TTC = {
    "PassportPerformance" : 100,
    "WorkTime" : 6.0,
    "ChargeTime" : 0.3,
    "Cost" : 200000,
    "power_kW" : 20000
}

async def get_dataset(robotID : int):
    return dataset

async def get_TTC(robotID : int):
    return TTC

async def get_robot(robotID : int):
    return {
        "robot_name" : "bobot",
        "robot_cost" : 10000
    }

def get_db_URL(route : str = "") -> str :
    load_dotenv()
    URL = os.getenv("URL", "http://127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", 8000)
    return f"{URL}:{DB_PORT}/" + route


async def get_coff(name: str) -> dict:
    if name in _coef_cache:
        return _coef_cache[name]
    async with _cache_lock:
        if name in _coef_cache:
            return _coef_cache[name]
        async with httpx.AsyncClient() as session:
            user = await session.get(get_db_URL("coef"), params={"name": name})
            try:
                data = user.json()
                _coef_cache[name] = data
                return data

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")


@app.post("math/cache")
async def clear_cache():
    _coef_cache.clear()


@app.get("math/robots")
async def get_robot_count(robotID : int, scenario : str):
    try:
        return robot_count(
            k_res=(await get_coff("k_res"))[scenario],
            k_PeLo = (await get_coff("k_PeLo"))[scenario],
            k_load = (await get_coff("K_load"))[scenario],

            dataset = await get_dataset(robotID),
            TTC = await get_TTC(robotID)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")


@app.get("math/CAPEX")
async def get_CAPEX(robotID : int, scenario : str):
    try:
        k_solCost = 1.0
        if(scenario == "opt"):
            k_solCost = 1.2
        elif(scenario == "pess"):
            k_solCost = 0.8

        return CAPEX(
            k_solCost = k_solCost,
            k_res=(await get_coff("k_res"))[scenario],
            k_PO = (await  get_coff("k_PO"))[scenario],
            k_integ = (await  get_coff("k_integ"))[scenario],
            k_PNR = (await  get_coff("k_PNR"))[scenario],
            k_learn = (await  get_coff("k_learn"))[scenario],
            robot_count = (await get_robot_count(robotID, scenario))["robot_count"],
            TTC=get_TTC(robotID))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")

@app.get("math/OPEX/robot")
async def get_OPEX_robot(robotID : int, count: int, scenario : str):

    capex_data = (await get_CAPEX(robotID, scenario))
    TTC = await get_TTC(robotID)

    return OPEX(
        k_service = (await get_coff("k_service"))[scenario],
        k_lic = (await get_coff("k_lic"))[scenario],
        k_conn =(await get_coff("k_conn"))[scenario],
        k_cons = (await get_coff("k_cons"))[scenario],
        k_rep = (await get_coff("k_rep"))[scenario],
        k_FOT = (await get_coff("k_FOT"))[scenario],
        salary = 0,
        capex = capex_data["CAPEX"],
        equip = capex_data["equip"],
        count = count,
        power_kW = TTC["power_kW"],
        work_hours = 0,
        tariff = 0
    )

@app.websocket("/ws/dynKPI/{user_id}")
async def websocket_dynamic_KPI(websocket: WebSocket, user_id: int):
    await websocket.accept()

    headers = websocket.headers
    token = headers.get("user_access_token")

    if not tokenFabric.decode(token):  # Ваша функция проверки токена
        await websocket.close(code=1008, reason="Unauthorized")
        return

    active_simulations[user_id]["WebSocket"] = websocket
    active_simulations[user_id]["Task"] = asyncio.create_task(simulation(user_id))

    try:
        while True:
            data = await websocket.receive_text()
            if data is not None:
                active_simulations[user_id]["SIndex"] = SIndex.model_validate_json(data)

    except WebSocketDisconnect:
        active_simulations[user_id]["Task"].cancel()
        await active_simulations[user_id]["Task"]
        active_simulations.pop(user_id, None)

async def simulation(user_id):
    while True:
        k_FOT = (await get_coff("k_FOT"))["base"]
