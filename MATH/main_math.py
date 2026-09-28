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


DB_TIMEOUT = httpx.Timeout(30.0)

async def get_coff(name: str) -> dict:
    if name in _coef_cache:
        return _coef_cache[name]
    async with _cache_lock:
        if name in _coef_cache:
            return _coef_cache[name]
        async with httpx.AsyncClient(timeout=DB_TIMEOUT) as session:
            lookup = name if name.lower() != "k_load" else "k_load"
            user = await session.get(get_db_URL("coef"), params={"name": lookup})
            if user.status_code == 404 and lookup != name:
                user = await session.get(get_db_URL("coef"), params={"name": name})
            try:
                data = user.json()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")
            if user.status_code != 200:
                raise HTTPException(status_code=user.status_code, detail=data.get("detail", "Коэффициент не найден"))
            data["opt"] = data.get("max", data.get("base", 1))
            data["pess"] = data.get("min", data.get("base", 1))
            _coef_cache[name] = data
            return data

async def get_id(id : int, category: str):
    param = {"dataset": "case_id", "robot": "robot_id", "case": "case_id"}.get(category, "id")
    async with httpx.AsyncClient(timeout=DB_TIMEOUT) as session:
        response = await session.get(get_db_URL(category), params={param: id})
        try:
            data = response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=data.get("detail", "Не найдено"))
        return data

async def get_dataset(dataset_id : int) -> SDatasetRead:
    return SDatasetRead.model_validate(await get_id(dataset_id, "dataset"))
async def get_robot(robot_id : int) -> SRobot:
    return SRobot.model_validate(await get_id(robot_id, "robot"))

async def get_case(case_id: int) -> SCaseRead:
    return SCaseRead.model_validate(await get_id(case_id, "case"))

def field_num(data: dict, *names, default=0.0) -> float:
    for name in names:
        item = data.get(name)
        if item is None:
            continue
        raw = item.get("base", item.get("scenario")) if isinstance(item, dict) else item
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return float(default)


def operations_per_day(data: dict) -> float:
    direct = field_num(data, "OperationsInDay", "Объём отбора (штук/сутки, всего)", "Количество операций")
    if direct:
        return direct
    return (
        field_num(data, "Входящие операции")
        + field_num(data, "Внутрискладские операции")
        + field_num(data, "Исходящие операции")
        + field_num(data, "Перевозок в сутки")
    )


def work_hours(data: dict) -> float:
    explicit = field_num(data, "WorkTimeInDay")
    if explicit:
        return explicit
    days = field_num(data, "Рабочих дней в году")
    shifts = field_num(data, "Количество рабочих смен в сутки")
    shift = field_num(data, "Продолжительность смены")
    if days and shifts and shift:
        return days * shifts * shift
    hours = field_num(data, "Режим работы", default=8)
    weeks = field_num(data, "Рабочих дней", default=5)
    return hours * weeks * 52


async def coef_value(name: str, scenario: str) -> float:
    coef = await get_coff(name)
    if scenario in coef:
        return float(coef[scenario])
    return float(coef.get("base", 1))


@app.post("/math/cache")
async def clear_cache():
    _coef_cache.clear()
    return {"ok": True}


@app.get("/math/robots")
async def get_robot_count(case_id:int, robot_id: int, scenario : str):
    try:
        dataset = await get_dataset(case_id)
        robot = await get_robot(robot_id)
        data = dataset.data
        ops = operations_per_day(data) or 1
        hours = work_hours(data) or 1
        return robot_count(
            k_res=await coef_value("k_res", scenario),
            k_PeLo=field_num(data, "Пиковый коэффициент нагрузки", default=1) or 1,
            k_load=await coef_value("k_load", scenario),
            dataset={"OperationsInDay": ops, "WorkTimeInDay": hours},
            efficiency=robot.efficiency,
            work_time=robot.work_time,
            charge_time=robot.charge_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")


def salary_rub(data: dict) -> float:
    named = field_num(data, "Стоимость персонала")
    if named:
        return named
    picker = field_num(data, "Средняя з/п отборщика (gross)")
    driver = field_num(data, "Средняя з/п оператора погрузчика (gross)")
    if picker or driver:
        return (picker + driver) / 2
    return 0.0


def fot_coef(data: dict, fallback: float) -> float:
    value = field_num(data, "Коэффициент начислений на ФОТ (страховые взносы)")
    return value or fallback


@app.get("/math/CAPEX")
async def get_CAPEX(case_id: int, robot_id : int, scenario : str):
    try:
        robot = await get_robot(robot_id)
        robots = await get_robot_count(case_id, robot_id, scenario)
        k_solCost = 1.2 if scenario == "opt" else 0.8 if scenario == "pess" else 1.0
        return CAPEX(
            k_solCost=k_solCost,
            k_res=await coef_value("k_res", scenario),
            k_PO=await coef_value("k_PO", scenario),
            k_integ=await coef_value("k_integ", scenario),
            k_PNR=await coef_value("k_PNR", scenario),
            k_learn=await coef_value("k_learn", scenario),
            robot_count=robots["robot_count"],
            cost=robot.cost,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")

@app.get("/math/OPEX")
async def get_OPEX(case_id : int, robot_id : int, scenario : str):
    try:
        case = await get_case(case_id)
        dataset = await get_dataset(case_id)
        capex = await get_CAPEX(case_id, robot_id, scenario)
        data = dataset.data
        return OPEX(
            k_service=await coef_value("k_service", scenario),
            k_lic=await coef_value("k_lic", scenario),
            k_conn=await coef_value("k_conn", scenario),
            k_cons=await coef_value("k_cons", scenario),
            k_rep=await coef_value("k_rep", scenario),
            k_FOT=fot_coef(data, await coef_value("k_FOT", scenario)),
            salary=0,
            count=case.robot_count,
            capex=capex["CAPEX"],
            equip=capex["equip"],
            power_kW=field_num(data, "Мощность электроснабжения (доступная)", default=1) or 1,
            work_hours=work_hours(data) or 1,
            tariff=case.tariff,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")

@app.get("/math/YearEffect")
async def get_year_econ_effect(case_id : int, robot_id : int, add_inc:int,
                prev_los:int, scenario : str):
    try:
        case = await get_case(case_id)
        dataset = await get_dataset(case_id)
        opex = await get_OPEX(case_id, robot_id, scenario)
        data = dataset.data
        return year_econ_effect(
            opex=opex["OPEX"],
            k_FOT=fot_coef(data, await coef_value("k_FOT", scenario)),
            salary=salary_rub(data),
            shortened_count=case.shortened,
            add_inc=add_inc,
            prev_los=prev_los,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")

@app.get("/math/PBPeriod")
async def get_payback_period(case_id : int, robot_id : int, add_inc:int,
                prev_los:int, scenario : str):
    try:
        capex = await get_CAPEX(case_id, robot_id, scenario)
        effect = await get_year_econ_effect(case_id, robot_id, add_inc, prev_los, scenario)
        if not effect["year_effect"]:
            return {"ok": False, "payback_period": None, "detail": "Годовой эффект равен нулю, срок окупаемости не считается"}
        return payback_period(capex["CAPEX"], effect["year_effect"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")


@app.get("/math/ROI")
async def get_ROI(case_id: int, robot_id: int, add_inc: int,
                 prev_los: int, scenario: str):
    try:
        capex = await get_CAPEX(case_id, robot_id, scenario)
        effect = await get_year_econ_effect(case_id, robot_id, add_inc, prev_los, scenario)
        dataset = await get_dataset(case_id)
        horizon = field_num(dataset.data, "Горизонт расчёта окупаемости") or await coef_value("horizon", scenario)
        return ROI(capex["CAPEX"], effect["year_effect"], horizon or 1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")

@app.get("/math/TCO")
async def get_TCO(case_id: int, robot_id: int, scenario: str):
    try:
        capex = await get_CAPEX(case_id, robot_id, scenario)
        opex = await get_OPEX(case_id, robot_id, scenario)
        dataset = await get_dataset(case_id)
        robot = await get_robot(robot_id)
        horizon = int(field_num(dataset.data, "Горизонт расчёта окупаемости") or await coef_value("horizon", scenario) or 5)
        life = robot.accum_life or 1
        return TCO(
            capex=capex["CAPEX"],
            opex=opex["OPEX"],
            horizon=horizon,
            equip=capex["equip"],
            accum_life=life,
            inflation=await coef_value("inflation", scenario),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {e}")


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
            "robots": sim.robots_payload(),
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
        session.owner = id(ws)
        session.simflag = True

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

    except WebSocketDisconnect:
        return
    except Exception as e:
        print(f"[WS] init error: {e}")
        try:
            await ws.send_json({"type": "error", "message": "Симуляция не запустилась: сервис базы не успел ответить."})
        except Exception:
            pass
        try:
            await ws.close(code=1008, reason="У кейса нет датасета или нераспознаны данные")
        except Exception:
            pass
        return
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
                await ws.send_json({"type": "started"})

            # ================= STOP =================
            elif action == "stop":
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
        current = SESSIONS.get(user_id)
        if current is not None and getattr(current, "owner", None) == id(ws):
            current.simflag = False
            if current.task and not current.task.done():
                current.task.cancel()
            SESSIONS.pop(user_id, None)
        print(f"[WS] disconnected: {user_id}")

    except Exception as e:
        print(f"[WS] error: {e}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

async def run_simulation(ws: WebSocket, session: Session):
    sim = session.sim
    limit = int(session.meta.get("n_steps") or 300)
    try:
        while session.simflag and sim.tick < limit:
            sim.step()
            await ws.send_json({
                "type": "state",
                "tick": sim.tick,
                "robots": sim.robots_payload(),
                "kpi": sim.kpi(),
            })
            await asyncio.sleep(0.05)
        if session.simflag:
            session.simflag = False
            await ws.send_json({"type": "done", "tick": sim.tick, "kpi": sim.kpi()})

    except asyncio.CancelledError:
        await ws.send_json({"type": "stopped"})
        raise

