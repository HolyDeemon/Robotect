import asyncio
import base64
import json
import os
from pathlib import Path

import httpx
from typing import Optional

from dotenv import load_dotenv

from fastapi import FastAPI, WebSocketDisconnect, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import tokenFabric
from MATH.Simulation import build_map, Simulation, TileMap, spec_to_dict
from MATH.formulas import *
from dataset import save_upload, delete_upload, load_dataset
from schemas import SRobot, SDatasetRead, SCaseRead

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class Session:
    def __init__(self):
        self.sim: Optional[Simulation] = None
        self.tmap: Optional[TileMap] = None
        self.task: Optional[asyncio.Task] = None
        self.meta: dict = {}
        self.simflag = True


load_dotenv()

_coef_cache: dict[str, dict] = {}
_cache_lock = asyncio.Lock()
SESSIONS: dict[str, Session] = {}
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/static")




def get_db_URL(route : str = "") -> str :
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

async def get_id(id : int, category: str):
    async with httpx.AsyncClient() as session:
        data = await session.get(get_db_URL(category), params={"id": id})
        try:
            return data.json()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")

async def get_dataset(dataset_id : int) -> SDatasetRead:
    return SDatasetRead.model_validate(await get_id(dataset_id, "dataset"))
async def get_robot(robot_id : int) -> SRobot:
    return SRobot.model_validate(await get_id(robot_id, "robot"))

async def get_case(case_id: int) -> SCaseRead:
    return SCaseRead.model_validate(await get_id(case_id, "case"))

@app.post("math/cache")
async def clear_cache():
    _coef_cache.clear()


@app.get("math/robots")
async def get_robot_count(case_id:int, robot_id: int, scenario : str):
    try:
        dataset = await get_dataset(case_id)
        robot = await get_robot(robot_id)
        return robot_count(
            k_res=(await get_coff("k_res"))[scenario],
            k_PeLo = dataset.data["Пиковый коэффициент нагрузки"],
            k_load = (await get_coff("K_load"))[scenario],

            dataset = dataset,
            efficiency= robot.efficiency,
            work_time = robot.work_time,
            charge_time = robot.charge_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")


@app.get("math/CAPEX")
async def get_CAPEX(case_id: int, robot_id : int, scenario : str):
    try:
        robot = await get_robot(robot_id)
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
            robot_count = (await get_robot_count(robot_id, scenario))["robot_count"],
            cost = robot.cost
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")

@app.get("math/OPEX")
async def get_OPEX(case_id : int, robot_id : int, scenario : str):

    case = await get_case(case_id)
    dataset = await get_dataset(case_id)
    capex = (await get_CAPEX(robot_id, scenario))

    return OPEX(
        k_service = (await get_coff("k_service"))[scenario],
        k_lic = (await get_coff("k_lic"))[scenario],
        k_conn =(await get_coff("k_conn"))[scenario],
        k_cons = (await get_coff("k_cons"))[scenario],
        k_rep = (await get_coff("k_rep"))[scenario],
        k_FOT = dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"]["scenario"],
        salary = 0,
        count= case.robot_count,
        capex = capex["CAPEX"],
        equip = capex["equip"],
        power_kW = dataset.data["Мощность электроснабжения (доступная)"]["scenario"],
        work_hours = dataset.data["Рабочих дней в году"]["scenario"] *
                     dataset.data["Количество рабочих смен в сутки"]["scenario"] *
                     dataset.data["Продолжительность смены"]["scenario"],
        tariff = case.tariff
    )

@app.get("math/YearEffect")
async def get_year_econ_effect(case_id : int, robot_id : int, add_inc:int,
                prev_los:int, scenario : str):
    case = await  get_case(case_id)
    dataset = await get_dataset(case_id)
    capex = (await get_CAPEX(robot_id, scenario))
    opex = (await get_OPEX(case_id=case_id,robot_id =robot_id,
        k_service = (await get_coff("k_service"))[scenario],
        k_lic = (await get_coff("k_lic"))[scenario],
        k_conn =(await get_coff("k_conn"))[scenario],
        k_cons = (await get_coff("k_cons"))[scenario],
        k_rep = (await get_coff("k_rep"))[scenario],
        k_FOT = dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"][scenario],
        salary = 0,
        count= case.count,
        capex = capex["CAPEX"],
        equip = capex["equip"],
        power_kW = dataset.data["Мощность электроснабжения (доступная)"][scenario],
        work_hours = dataset.data["Рабочих дней в году"]["scenario"] *
                     dataset.data["Количество рабочих смен в сутки"][scenario] *
                     dataset.data["Продолжительность смены"][scenario],
        tariff = case.tariff
    ))

    return year_econ_effect(
        opex= opex["OPEX"],
        k_FOT= dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"][scenario],
        salary= (dataset.data["Средняя з/п отборщика (gross)"][scenario] + dataset.data["Средняя з/п оператора погрузчика (gross)"][scenario])/2,
        shortened_count= case.shortened,
        add_inc= add_inc,
        prev_los= prev_los,
    )

@app.get("math/PBPeriod")
async def get_payback_period(case_id : int, robot_id : int, add_inc:int,
                prev_los:int, scenario : str):
    case = await get_case(case_id)
    dataset = await get_dataset(case_id)
    capex = (await get_CAPEX(robot_id, scenario))
    opex = (await get_OPEX(
        k_service=(await get_coff("k_service"))[scenario],
        k_lic=(await get_coff("k_lic"))[scenario],
        k_conn=(await get_coff("k_conn"))[scenario],
        k_cons=(await get_coff("k_cons"))[scenario],
        k_rep=(await get_coff("k_rep"))[scenario],
        k_FOT=dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"]["scenario"],
        salary=0,
        count=case.count,
        capex=capex["CAPEX"],
        equip=capex["equip"],
        power_kW=dataset.data["Мощность электроснабжения (доступная)"]["scenario"],
        work_hours=dataset.data["Рабочих дней в году"]["scenario"] *
                   dataset.data["Количество рабочих смен в сутки"]["scenario"] *
                   dataset.data["Продолжительность смены"]["scenario"],
        tariff=case.tariff
    ))

    year_econ_effect = (await get_year_econ_effect(
        opex=opex["OPEX"],
        k_FOT=dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"]["scenario"],
        salary=(dataset.data["Средняя з/п отборщика (gross)"]["scenario"] + dataset.data[
            "Средняя з/п оператора погрузчика (gross)"]["scenario"]) / 2,
        shortened_count=case.shortened,
        add_inc=add_inc,
        prev_los=prev_los,
    ))

    return payback_period(capex["CAPEX"], year_econ_effect["year_effect"])


@app.get("math/ROI")
async def get_ROI(case_id: int, robot_id: int, add_inc: int,
                 prev_los: int, scenario: str):
    case = await get_case(case_id)
    capex = (await get_CAPEX(robot_id, scenario))
    dataset = await get_dataset(case_id)
    opex = (await get_OPEX(
        k_service=(await get_coff("k_service"))[scenario],
        k_lic=(await get_coff("k_lic"))[scenario],
        k_conn=(await get_coff("k_conn"))[scenario],
        k_cons=(await get_coff("k_cons"))[scenario],
        k_rep=(await get_coff("k_rep"))[scenario],
        k_FOT=dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"]["scenario"],
        salary=0,
        count=case.count,
        capex=capex["CAPEX"],
        equip=capex["equip"],
        power_kW=dataset.data["Мощность электроснабжения (доступная)"]["scenario"],
        work_hours=dataset.data["Рабочих дней в году"]["scenario"] *
                   dataset.data["Количество рабочих смен в сутки"]["scenario"] *
                   dataset.data["Продолжительность смены"]["scenario"],
        tariff=case.tariff
    ))

    year_econ_effect = (await get_year_econ_effect(
        opex=opex["OPEX"],
        k_FOT=dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"]["scenario"],
        salary=(dataset.data["Средняя з/п отборщика (gross)"]["scenario"] + dataset.data[
            "Средняя з/п оператора погрузчика (gross)"]["scenario"]) / 2,
        shortened_count=case.shortened,
        add_inc=add_inc,
        prev_los=prev_los,
    ))

    return ROI(capex["CAPEX"], year_econ_effect["year_effect"], (await get_coff("horizon"))["scenario"])

@app.get("math/TCO")
async def get_TCO(case_id: int, robot_id: int, scenario: str):
    case = await  get_case(case_id)
    capex = (await get_CAPEX(robot_id, scenario))
    dataset = await get_dataset(case_id)
    robot = await get_robot(robot_id)
    opex = (await get_OPEX(
        k_service=(await get_coff("k_service"))[scenario],
        k_lic=(await get_coff("k_lic"))[scenario],
        k_conn=(await get_coff("k_conn"))[scenario],
        k_cons=(await get_coff("k_cons"))[scenario],
        k_rep=(await get_coff("k_rep"))[scenario],
        k_FOT=dataset.data["Коэффициент начислений на ФОТ (страховые взносы)"]["scenario"],
        salary=0,
        count=case.count,
        capex=capex["CAPEX"],
        equip=capex["equip"],
        power_kW=dataset.data["Мощность электроснабжения (доступная)"]["scenario"],
        work_hours=dataset.data["Рабочих дней в году"]["scenario"] *
                   dataset.data["Количество рабочих смен в сутки"]["scenario"] *
                   dataset.data["Продолжительность смены"]["scenario"],
        tariff=case.tariff
    ))
    return TCO(
        capex=capex["CAPEX"],
        opex=opex["OPEX"],
        horizon=dataset.data["Горизонт расчёта окупаемости"]["scenario"],
        equip=capex["equip"],
        accum_life=robot.accum_life,
        inflation=(await get_coff("inflation"))["scenario"])


def build_report(sim: Simulation, tmap: TileMap, meta: dict) -> dict:
    """
    Собирает результаты симуляции в обычный dict.
    Никакого CSV — только данные. Клиент сам решит, что с ними делать.
    """
    # --- итоги по роботам ---
    robots = []
    for r in sim.robots:
        util = 100.0 * r.work_ticks / max(r.alive_ticks, 1)
        idle = 100.0 * (r.idle_ticks + r.charge_ticks) / max(r.alive_ticks, 1)
        robots.append({
            "id": r.rid,
            "distance_m": round(r.distance_traveled, 2),
            "operations": r.tasks_done,
            "battery_pct": round(r.battery_pct, 2),
            "work_ticks": r.work_ticks,
            "idle_ticks": r.idle_ticks,
            "charge_ticks": r.charge_ticks,
            "alive_ticks": r.alive_ticks,
            "utilization_pct": round(util, 2),
            "idle_pct": round(idle, 2),
            "status": r.status,
        })

    # --- KPI по тикам ---
    kpi_series = [
        {
            "tick": row["tick"],
            "sim_hours": row["sim_hours"],
            "operations_done": row["operations_done"],
            "shift_progress_pct": row["shift_progress_pct"],
            "utilization_pct": row["utilization_pct"],
            "idle_pct": row["idle_pct"],
            "task_queue_len": row["task_queue_len"],
            "savings_rub": row["savings_rub"],
            "total_distance_m": row["total_distance_m"],
            "avg_battery_pct": row["avg_battery_pct"],
            "is_working_hour": bool(row["is_working_hour"]),
        }
        for row in sim.history
    ]

    # --- итоговая сводка ---
    summary = sim.kpi()          # последний kpi() — это финальные значения

    return {
        "meta": {
            **meta,
            "shift_hours": sim.shift_hours,
            "shifts_per_day": sim.n_shifts,
            "work_hours_per_day": sim.work_hours_per_day,
            "peak_factor": sim.peak_factor,
            "saving_per_operation_rub": sim.saving_per_operation,
            "tile_size_m": tmap.tile_size_m,
            "map_cols": tmap.ncols,
            "map_rows": tmap.nrows,
        },
        "summary": summary,
        "robots": robots,
        "kpi_series": kpi_series,
    }

@app.websocket("/ws/{user_id}")
async def ws_endpoint(ws: WebSocket, user_id: str,  case_id:int, robot_id: int):
    await ws.accept()
    try:
        raw = await ws.receive_text()
        msg = json.loads(raw)

        k_FOT = (await get_coff("k_FOT"))["base"]
        k_avail = (await get_coff("k_load"))["base"]
        k_res = (await get_coff("k_res"))["base"]
        robot_spec = await get_robot(robot_id)
        ds = await get_dataset(case_id)
        data = ds.data

        if not (ds and data):
            await ws.send_json({"type": "error",
                                "message": f"dataset not available"})
            raise Exception

        object_type = msg.get("object_type", "Склад")

        tmap = build_map(object_type, data)

        sim = Simulation(
            tmap,
            n_robots=int(msg.get("n_robots", 8)),
            data=data,
            seed=int(msg.get("seed", 42)),
            time_scale=float(msg.get("time_scale", 60.0)),
            saving_per_operation=float(msg.get("saving_per_operation", 0)),
            robot_spec=robot_spec,
        )

        await ws.send_json({
            "type": "map",
            "ncols": tmap.ncols,
            "nrows": tmap.nrows,
            "tile_size_m": tmap.tile_size_m,
            "grid": tmap.grid.tolist(),
        })
        await ws.send_json({
            "type": "robot_spec",
            "payload": spec_to_dict(robot_spec),
        })
        await ws.send_json({
            "type": "dataset_info",
            "source": "",
            "params_loaded": len(data),
        })

        session = SESSIONS.setdefault(user_id, Session())

        session.sim = sim
        session.tmap = tmap
        session.meta = {
            "object_type": object_type,
            "n_robots": int(msg.get("n_robots", 8)),
            "n_steps": int(msg.get("n_steps", 300)),
            "dataset_source": "",
            "params_loaded": len(data),
            "robot_model": robot_spec.model,
        }

        if session.task and not session.task.done():
            session.task.cancel()
        session.task = asyncio.create_task(
            run_simulation(ws, session)
        )

    except Exception as e:
        await ws.close(code=1008, reason="У кейса нет датасета или нераспознаны данные")
        raise HTTPException(status_code=500, detail=f"Ошибка инициализации: {e}")
    except json.JSONDecodeError:
        await ws.send_json({"type": "error", "message": "invalid json"})
        raise HTTPException(status_code=500, detail="Ошибка декодирования сообщения")
    try:
        while True:

            raw = await ws.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            # ================= START =================
            if action == "start":

                print(f"[WS] {user_id} robot: {robot_spec.model}, "
                      f"speed={robot_spec.max_speed} м/с, "
                      f"payload={robot_spec.capacity} кг")




            # ================= STOP =================
            if action == "stop":
                if session.task and not session.task.done():
                    session.task.cancel()
                await ws.send_json({"type": "stopped"})

            # ================= GET REPORT =================
            elif action == "get_report":
                if not session.sim or not session.tmap:
                    await ws.send_json({"type": "error",
                                        "message": "Симуляция не запущена"})
                    continue
                report = build_report(session.sim, session.tmap, session.meta)
                await ws.send_json({
                    "type": "report",
                    "payload": report,
                })

            # ================= GET DATASET =================
            elif action == "get_dataset":
                dataset = await get_dataset(case_id)
                if dataset:
                    await ws.send_json({
                        "type": "dataset",
                        "data": dataset.data,
                    })
                else:
                    await ws.send_json({"type": "error",
                                        "message": "Датасет не загружен"})

            elif action == "ping":
                await ws.send_json({"type": "pong", "t": msg.get("t")})

            elif action == "KPI":
                k_avail = sim_k_avail(sim)
                ef_perf = sim_Ef_perf(sim, k_avail, robot_spec.efficiency)
                work_time = data["Рабочих дней в году"]["base"] * data["Количество рабочих смен в сутки"]["base"] * data["Продолжительность смены"]["base"]
                avg_load = data["Объём отбора (штук/сутки, всего)"]["base"] / work_time
                N_robots = sim_N_robots(ef_perf, data["Пиковый коэффициент нагрузки"]["base"] * avg_load, k_res)
                electricity = 1
                opex = 1 ##OPEX()
                battary_change = 1
                year_effect = 1
                await ws.send_json({"type": "KPI",
                                    "ef_perf" : ef_perf,
                                    "k_avail" : k_avail,
                                    "N_robots" : N_robots,
                                    "year_effect" : year_effect,
                                    "electricity" : electricity,

                })

            else:
                await ws.send_json({"type": "error",
                                    "message": f"unknown action: {action}"})

    except WebSocketDisconnect:
        SESSIONS[user_id].simflag = False
        SESSIONS[user_id].task.cancel()
        SESSIONS.pop(user_id)
        print(f"[WS] disconnected: {user_id}")

    except Exception as e:
        print(f"[WS] error: {e}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

async def run_simulation(ws: WebSocket, session: Session):
    sim = session.sim
    try:
        while session.simflag:
            if not session.simflag:
                await ws.send_json({"type": "done", "tick": sim.tick, "kpi": sim.kpi()})
                return

            await  ws.send_json({
                    "type": "state",
                    "tick": sim.tick,
                    "robots": sim.robots_payload(),
                    "kpi": sim.kpi(),
                })
            await asyncio.sleep(0.03)

    except asyncio.CancelledError:
        await ws.send_json({"type": "stopped"})
        raise

