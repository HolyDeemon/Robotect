# Simulation.py
# -*- coding: utf-8 -*-
"""
Тайловая карта + симуляция роботов со сменами, очередью задач и KPI.
"""

from __future__ import annotations

import math
import random
import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from dataset import get_num


def first_num(data, *keys, default=0.0):
    """Берёт первое число из набора подписей: поля формы и поля методики называются по-разному."""
    source = data or {}
    for key in keys:
        if key not in source:
            continue
        value = get_num(source, key, default=float("nan"))
        if value == value:
            return value
    return default


def schematic_size(area, aspect=1.6, max_side=64.0):
    """Ужимает объект до схемы, которую видно в окне. Метры остаются метрами шага робота."""
    area = max(float(area or 1), 1.0)
    width = math.sqrt(area * aspect)
    height = area / width
    longest = max(width, height)
    if longest > max_side:
        scale = max_side / longest
        width *= scale
        height *= scale
    return max(width, 16.0), max(height, 12.0)
from schemas import SRobot


# ===========================================================================
# 1. ТТХ РОБОТА
# ===========================================================================

def spec_from_dict(d: Optional[dict]) -> SRobot:
    """Собирает SRobot из словаря запроса; игнорирует мусор."""
    if not d:
        return SRobot()

    known = set(SRobot.__dataclass_fields__.keys())
    clean = {k: v for k, v in d.items() if k in known and v is not None}

    for key in list(clean.keys()):
        if key in ("model", "navigation"):
            continue
        try:
            clean[key] = float(clean[key])
        except (TypeError, ValueError):
            clean.pop(key)

    return SRobot(**clean)


def spec_to_dict(spec: SRobot) -> dict:
    """SRobot → dict (для отдачи на фронт), с производными."""
    d = spec.model_dump()
    d["footprint_m"] = list(spec.footprint_m)
    d["battery_drain_per_m"] = round(spec.battery_drain_per_m, 6)
    d["charge_rate_pct_per_s"] = round(spec.charge_rate_pct_per_s, 4)
    d["working_speed_mps"] = round(spec.dead_reckoning_speed_mps, 3)
    return d


# ===========================================================================
# 2. ТАЙЛОВАЯ КАРТА
# ===========================================================================

TILE_FREE, TILE_SHELF, TILE_AISLE, TILE_HIGHWAY = 0, 1, 2, 3
TILE_CHARGE, TILE_PICK, TILE_DROPOFF, TILE_WALL = 4, 5, 6, 7

TILE_NAMES = {
    0: "Свободно", 1: "Стеллаж", 2: "Проход", 3: "Магистраль",
    4: "Зарядка", 5: "Отбор", 6: "Доставка", 7: "Стена",
}


@dataclass
class TileMap:
    width_m: float
    height_m: float
    tile_size_m: float = 1.0
    grid: np.ndarray = field(init=False)
    ncols: int = field(init=False)
    nrows: int = field(init=False)

    def __post_init__(self):
        self.ncols = max(2, int(self.width_m / self.tile_size_m))
        self.nrows = max(2, int(self.height_m / self.tile_size_m))
        self.grid = np.full((self.nrows, self.ncols), TILE_FREE, dtype=np.int8)

    def to_cell(self, x_m: float, y_m: float) -> Tuple[int, int]:
        return (int(np.clip(y_m / self.tile_size_m, 0, self.nrows - 1)),
                int(np.clip(x_m / self.tile_size_m, 0, self.ncols - 1)))

    def to_world(self, r: int, c: int) -> Tuple[float, float]:
        return (c + 0.5) * self.tile_size_m, (r + 0.5) * self.tile_size_m

    def fill_rect(self, x0, y0, x1, y1, tile: int):
        r0, c0 = self.to_cell(x0, y0)
        r1, c1 = self.to_cell(x1, y1)
        r0, r1 = sorted((r0, r1))
        c0, c1 = sorted((c0, c1))
        self.grid[r0:r1 + 1, c0:c1 + 1] = tile

    def draw_border(self, thickness: int = 2):
        self.grid[:thickness, :] = TILE_WALL
        self.grid[-thickness:, :] = TILE_WALL
        self.grid[:, :thickness] = TILE_WALL
        self.grid[:, -thickness:] = TILE_WALL

    def passable(self, r: int, c: int) -> bool:
        if r < 0 or c < 0 or r >= self.nrows or c >= self.ncols:
            return False
        return self.grid[r, c] not in (TILE_SHELF, TILE_WALL)

    def astar(self, start: Tuple[int, int],
              goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        if start == goal:
            return [start]
        if not self.passable(*goal) or not self.passable(*start):
            return []

        def h(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = [(h(start, goal), 0, start)]
        came_from, g_score, visited = {}, {start: 0}, set()

        while open_set:
            _, g, cur = heapq.heappop(open_set)
            if cur in visited:
                continue
            visited.add(cur)
            if cur == goal:
                path = [cur]
                while cur in came_from:
                    cur = came_from[cur]
                    path.append(cur)
                return path[::-1]

            r, c = cur
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if not self.passable(*nb):
                    continue
                ng = g + 1
                if ng < g_score.get(nb, 1e18):
                    g_score[nb] = ng
                    came_from[nb] = cur
                    heapq.heappush(open_set, (ng + h(nb, goal), ng, nb))
        return []


# ===========================================================================
# 3. ГЕНЕРАТОРЫ КАРТ
# ===========================================================================

def build_warehouse_map(data: Dict[str, dict]) -> TileMap:
    area = first_num(
        data,
        "Площадь активной (роботизируемой) зоны",
        "Площадь рабочих зон",
        "Площадь",
        default=10000,
    )
    w, h = schematic_size(area, 1.6)
    tmap = TileMap(w, h, 1.0)
    tmap.draw_border(2)

    aisle_w = get_num(data, "Ширина рабочих проходов между стеллажами", 2.8)
    highway_w = get_num(data, "Ширина главных проездов", 3.5)

    y = highway_w
    while y < h - highway_w:
        tmap.fill_rect(0, y, w, y + highway_w, TILE_HIGHWAY)
        y += 40

    shelf_h = 6.0
    y = highway_w + 3
    while y + shelf_h + aisle_w < h:
        tmap.fill_rect(2, y, w - 2, y + shelf_h, TILE_SHELF)
        tmap.fill_rect(2, y + shelf_h, w - 2, y + shelf_h + aisle_w, TILE_AISLE)
        y += shelf_h + aisle_w + 4

    x = 25
    while x < w - 5:
        tmap.fill_rect(x, 0, x + 2, h, TILE_HIGHWAY)
        x += 45

    for (x0, y0) in [(3, 3), (w - 8, 3), (3, h - 8), (w - 8, h - 8)]:
        tmap.fill_rect(x0, y0, x0 + 5, y0 + 5, TILE_CHARGE)

    tmap.fill_rect(w * 0.3, h * 0.25, w * 0.3 + 6, h * 0.25 + 6, TILE_PICK)
    tmap.fill_rect(w * 0.7, h * 0.75, w * 0.7 + 6, h * 0.75 + 6, TILE_DROPOFF)
    return tmap


def build_airport_map(data: Dict[str, dict]) -> TileMap:
    term_area = first_num(data, "Суммарная площадь терминала (ов)", default=0)
    ramp_area = first_num(data, "Площадь перрона и технических зон", default=0)
    area = term_area + ramp_area
    if area <= 0:
        area = first_num(data, "Протяжённость маршрутов", default=600) * 40
    w, h = schematic_size(area, 1.4, 72)
    tmap = TileMap(w, h, 2.0)
    tmap.draw_border(3)

    term_w = w * 0.4
    tmap.fill_rect(0, 0, term_w, h, TILE_FREE)

    n_gates = int(get_num(data, "Количество выходов на посадку (гейтов)", 20))
    gate_step = h / max(n_gates, 1)
    for i in range(n_gates):
        y = i * gate_step + gate_step * 0.3
        tmap.fill_rect(term_w - 4, y, term_w, y + 2, TILE_PICK)

    tmap.fill_rect(term_w + 2, 0, w, h, TILE_HIGHWAY)
    for i in range(1, 6):
        y = h * i / 6
        tmap.fill_rect(term_w + 2, y, w - 2, y + 3, TILE_AISLE)
    for j in range(1, 4):
        x = term_w + 2 + (w - term_w) * j / 4
        tmap.fill_rect(x, 0, x + 2, h, TILE_AISLE)

    for i in range(4):
        y = h * (i + 0.5) / 4
        tmap.fill_rect(term_w - 12, y, term_w - 4, y + 6, TILE_CHARGE)

    tmap.fill_rect(w * 0.7, h * 0.4, w * 0.7 + 10, h * 0.4 + 10, TILE_DROPOFF)
    return tmap


def build_hospital_map(data: Dict[str, dict]) -> TileMap:
    area = first_num(data, "Общая площадь здания(й)", "Площадь", default=45000)
    floors = max(1, int(first_num(data, "Количество этажей (основной корпус)", "Этажность", default=9)))
    floor_area = area / floors
    w, h = schematic_size(floor_area, 1.5)
    tmap = TileMap(w, h, 1.0)
    tmap.draw_border(2)

    corridor_w = get_num(data, "Ширина коридоров (основных)", 2.4)
    cy = h / 2
    tmap.fill_rect(0, cy - corridor_w / 2, w, cy + corridor_w / 2, TILE_HIGHWAY)

    for k in (0.25, 0.75):
        y = h * k
        tmap.fill_rect(0, y, w, y + corridor_w, TILE_AISLE)
    for k in (0.2, 0.5, 0.8):
        x = w * k
        tmap.fill_rect(x, 0, x + corridor_w, h, TILE_AISLE)

    n_depts = int(get_num(data, "Количество точек раздачи питания (отделений)", 18))
    for i in range(n_depts):
        x = 4 + (i % 6) * (w / 6.5)
        y = 4 + (i // 6) * (h / 3.5)
        tmap.fill_rect(x, y, x + w / 8, y + h / 6, TILE_SHELF)

    tmap.fill_rect(4, cy + 4, 12, cy + 12, TILE_PICK)
    tmap.fill_rect(w - 14, cy - 12, w - 4, cy - 4, TILE_DROPOFF)
    tmap.fill_rect(4, 4, 10, 10, TILE_CHARGE)
    tmap.fill_rect(w - 10, h - 10, w - 4, h - 4, TILE_CHARGE)
    return tmap


def build_map(object_type: str, data: Dict[str, dict]) -> TileMap:
    if object_type == "Склад":
        return build_warehouse_map(data)
    if object_type == "Аэропорт":
        return build_airport_map(data)
    if object_type == "Медучреждение":
        return build_hospital_map(data)
    raise ValueError(f"Неизвестный тип объекта: {object_type}")


# ===========================================================================
# 4. РОБОТ
# ===========================================================================

@dataclass
class Robot:
    rid: int
    pos: Tuple[float, float]
    spec: SRobot = field(default_factory=SRobot)
    color: str = "tab:blue"

    battery_pct: float = 100.0
    path: List[Tuple[int, int]] = field(default_factory=list)
    target: Optional[Tuple[int, int]] = None

    distance_traveled: float = 0.0
    tasks_done: int = 0
    waiting: int = 0
    status: str = "idle"

    work_ticks: int = 0
    idle_ticks: int = 0
    charge_ticks: int = 0
    alive_ticks: int = 0

    @property
    def speed_mps(self) -> float:
        return self.spec.dead_reckoning_speed_mps

    @property
    def battery_drain_per_m(self) -> float:
        return self.spec.battery_drain_per_m

    @property
    def charge_rate_pct_per_s(self) -> float:
        return self.spec.charge_rate_pct_per_s


# ===========================================================================
# 5. СИМУЛЯЦИЯ
# ===========================================================================

@dataclass
class SimClock:
    dt_real_s: float = 1.0
    time_scale: float = 60.0
    tick: int = 0

    @property
    def sim_seconds(self) -> float:
        return self.tick * self.dt_real_s * self.time_scale

    @property
    def sim_hours(self) -> float:
        return self.sim_seconds / 3600.0

    @property
    def sim_days(self) -> float:
        return self.sim_seconds / 86400.0


class Task:
    _next_id = 0

    def __init__(self, pick_cell, dropoff_cell, priority: float = 1.0,
                 created_tick: int = 0, weight_kg: float = 0.0):
        Task._next_id += 1
        self.tid = Task._next_id
        self.pick = pick_cell
        self.dropoff = dropoff_cell
        self.priority = priority
        self.created_tick = created_tick
        self.weight_kg = weight_kg
        self.assigned_to: Optional[int] = None


class Simulation:
    def __init__(
        self,
        tmap: TileMap,
        n_robots: int,
        data: Optional[Dict[str, dict]] = None,
        seed: int = 42,
        time_scale: float = 60.0,
        saving_per_operation: float = 0.0,
        robot_spec: Optional[SRobot] = None,
    ):
        self.tmap = tmap
        self.rng = random.Random(seed)
        self.data = data or {}
        self.clock = SimClock(1.0, time_scale)
        self.tick = 0
        self.robot_spec = robot_spec or SRobot()

        # смены
        self.shift_hours = first_num(self.data, "Продолжительность смены", "Режим работы", default=11.0)
        self.n_shifts = first_num(self.data, "Количество рабочих смен в сутки", default=1)
        self.shift_start_hour = 0.0
        self.cargo_kg = first_num(
            self.data,
            "Средняя масса грузовой единицы",
            "Средняя масса груза",
            "Масса перемещаемого объекта",
            default=20,
        )
        self.work_hours_per_day = self.shift_hours * self.n_shifts

        # пиковая нагрузка
        self.peak_factor = get_num(self.data, "Пиковый коэффициент нагрузки", 1.5)
        self.utilization_target = 0.80

        # экономия
        if saving_per_operation > 0:
            self.saving_per_operation = saving_per_operation
        else:
            self.saving_per_operation = self._estimate_saving_per_operation()

        # --- создание роботов ---
        palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                   "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
                   "#bcbd22", "#17becf"]
        self.robots: List[Robot] = []

        charge_cells = list(zip(*np.where(tmap.grid == TILE_CHARGE)))
        free_cells = list(zip(*np.where(tmap.grid == TILE_FREE)))
        if not charge_cells:
            charge_cells = free_cells[:1]

        for i in range(n_robots):
            r, c = charge_cells[i % len(charge_cells)]
            x, y = tmap.to_world(r, c)
            self.robots.append(Robot(
                rid=i,
                pos=(x, y),
                spec=self.robot_spec,
                color=palette[i % len(palette)],
            ))

        self.charge_cells = charge_cells
        self.pick_cells = list(zip(*np.where(tmap.grid == TILE_PICK)))
        self.dropoff_cells = list(zip(*np.where(tmap.grid == TILE_DROPOFF)))

        if not self.pick_cells:
            self.pick_cells = free_cells[:max(1, len(free_cells) // 10)]
        if not self.dropoff_cells:
            self.dropoff_cells = free_cells[-max(1, len(free_cells) // 10):]

        # очередь задач
        self.task_queue: deque = deque()
        self._pending_task_accumulator = 0.0

        # метрики
        self.history: List[dict] = []
        self.completed_operations = 0

    # ------------------------------------------------------------------
    def _estimate_saving_per_operation(self) -> float:
        salary = get_num(self.data, "Средняя з/п отборщика (gross)", 100000)
        charges = get_num(self.data, "Коэффициент начислений на ФОТ", 1.302)
        monthly_fot = salary * charges

        rate = get_num(self.data, "Средняя выработка отборщика (строк/ч)", 150)
        ops_per_month = rate * self.shift_hours * self.n_shifts * 22
        if ops_per_month <= 0:
            return 30.0
        return round(monthly_fot / ops_per_month, 2)

    # ------------------------------------------------------------------
    def _is_working_hour(self, sim_hours: float) -> bool:
        h = sim_hours % 24.0
        start = self.shift_start_hour
        end = start + self.work_hours_per_day
        return start <= h < end

    def _shift_progress_pct(self) -> float:
        if self.shift_hours <= 0:
            return 0.0
        h = self.clock.sim_hours % 24.0
        start = self.shift_start_hour
        if h < start:
            h += 24.0
        elapsed = h - start
        if elapsed < self.work_hours_per_day:
            in_shift = elapsed % self.shift_hours
            return min(100.0, in_shift / self.shift_hours * 100.0)
        return 100.0

    def _workload_multiplier(self, sim_hours: float) -> float:
        h = sim_hours % 24.0
        if 7 <= h < 10 or 15 <= h < 18:
            return self.peak_factor
        if 2 <= h < 7 or 18 <= h < 23:
            return 1.0
        return 0.2

    # ------------------------------------------------------------------
    def _spawn_tasks(self, dt_sim_seconds: float):
        h = self.clock.sim_hours
        mult = self._workload_multiplier(h)
        rate_per_sim_sec = 0.5 * mult
        self._pending_task_accumulator += rate_per_sim_sec * dt_sim_seconds

        while self._pending_task_accumulator >= 1.0:
            self._pending_task_accumulator -= 1.0
            pick = self.rng.choice(self.pick_cells)
            drop = self.rng.choice(self.dropoff_cells)
            cap = self.robot_spec.capacity or 200
            weight = min(self.cargo_kg or 20, cap * 0.8) or 10
            self.task_queue.append(Task(
                pick_cell=pick, dropoff_cell=drop,
                priority=1.0, created_tick=self.tick,
                weight_kg=weight,
            ))

    def _assign_next_task(self, robot: Robot) -> bool:
        if not self.task_queue:
            return False

        for idx, task in enumerate(self.task_queue):
            if task.weight_kg > robot.spec.capacity:
                continue

            del self.task_queue[idx]

            cur = self.tmap.to_cell(*robot.pos)
            p1 = self.tmap.astar(cur, task.pick)
            if not p1:
                self.task_queue.appendleft(task)
                return False
            p2 = self.tmap.astar(task.pick, task.dropoff)
            if not p2:
                self.task_queue.appendleft(task)
                return False

            robot.path = p1 + p2[1:]
            robot.target = task.dropoff
            robot.status = "delivery"
            task.assigned_to = robot.rid
            return True

        return False

    # ------------------------------------------------------------------
    def step(self):
        self.tick += 1
        self.clock.tick += 1
        dt_real = self.clock.dt_real_s
        dt_sim = dt_real * self.clock.time_scale

        working = self._is_working_hour(self.clock.sim_hours)

        if working:
            self._spawn_tasks(dt_sim)

        occupied: Dict[Tuple[int, int], List[int]] = {}
        for r in self.robots:
            occupied.setdefault(self.tmap.to_cell(*r.pos), []).append(r.rid)

        for robot in self.robots:
            robot.alive_ticks += 1
            spec = robot.spec

            # --- вне смены ---
            if not working:
                robot.battery_pct = min(
                    100.0,
                    robot.battery_pct + spec.charge_rate_pct_per_s * dt_real,
                )
                robot.charge_ticks += 1
                robot.status = "off_shift"
                continue

            # --- idle-разряд ---
            idle_drain = 5.0 / (spec.work_time * 3600.0)
            robot.battery_pct = max(0.0, robot.battery_pct - idle_drain * dt_real)

            # --- порог зарядки 15% ---
            if robot.battery_pct < 15 and self.charge_cells:
                cur = self.tmap.to_cell(*robot.pos)
                nearest = min(self.charge_cells,
                              key=lambda cc: abs(cc[0] - cur[0]) + abs(cc[1] - cur[1]))
                if cur != nearest:
                    robot.path = self.tmap.astar(cur, nearest)
                    robot.target = nearest
                    robot.status = "moving_to_charge"
                else:
                    robot.status = "charging"

            # --- зарядка ---
            if robot.status == "charging":
                robot.battery_pct = min(
                    100.0,
                    robot.battery_pct + spec.charge_rate_pct_per_s * dt_real,
                )
                robot.charge_ticks += 1
                if robot.battery_pct >= 95:
                    robot.status = "idle"
                continue

            # --- нет пути → берём задачу ---
            if not robot.path:
                if robot.battery_pct < 15:
                    continue
                if self._assign_next_task(robot):
                    pass
                else:
                    robot.status = "idle"
                    robot.idle_ticks += 1
                    continue

            # --- движение ---
            nxt = robot.path[0]
            wx, wy = self.tmap.to_world(*nxt)

            if occupied.get(nxt) and len(occupied[nxt]) > 1:
                robot.waiting += 1
                robot.idle_ticks += 1
                robot.status = "waiting"
                continue

            dx, dy = wx - robot.pos[0], wy - robot.pos[1]
            dist = math.hypot(dx, dy)
            step_len = robot.speed_mps * dt_real

            robot.work_ticks += 1
            if dist <= step_len or dist < 1e-6:
                robot.pos = (wx, wy)
                robot.distance_traveled += dist
                robot.battery_pct = max(
                    0.0,
                    robot.battery_pct - dist * robot.battery_drain_per_m,
                )
                robot.path.pop(0)
                if not robot.path:
                    robot.tasks_done += 1
                    self.completed_operations += 1
                    robot.status = "idle"
            else:
                robot.pos = (robot.pos[0] + dx / dist * step_len,
                             robot.pos[1] + dy / dist * step_len)
                robot.distance_traveled += step_len
                robot.battery_pct = max(
                    0.0,
                    robot.battery_pct - step_len * robot.battery_drain_per_m,
                )

        self.history.append(self.kpi())

    # ------------------------------------------------------------------
    def kpi(self) -> dict:
        n = len(self.robots)
        total_alive = sum(r.alive_ticks for r in self.robots) or 1
        total_work = sum(r.work_ticks for r in self.robots)
        total_idle = sum(r.idle_ticks for r in self.robots)
        total_charge = sum(r.charge_ticks for r in self.robots)

        utilization_pct = 100.0 * total_work / total_alive
        idle_pct = 100.0 * (total_idle + total_charge) / total_alive

        total_distance = sum(r.distance_traveled for r in self.robots)
        avg_battery = float(np.mean([r.battery_pct for r in self.robots])) if n else 0.0

        shift_pct = self._shift_progress_pct()
        savings_rub = self.completed_operations * self.saving_per_operation

        return {
            "tick": self.tick,
            "sim_seconds": round(self.clock.sim_seconds, 1),
            "sim_hours": round(self.clock.sim_hours, 3),
            "operations_done": self.completed_operations,
            "shift_progress_pct": round(shift_pct, 2),
            "utilization_pct": round(utilization_pct, 2),
            "idle_pct": round(idle_pct, 2),
            "task_queue_len": len(self.task_queue),
            "savings_rub": round(savings_rub, 2),
            "total_distance_m": round(total_distance, 2),
            "avg_battery_pct": round(avg_battery, 2),
            "is_working_hour": self._is_working_hour(self.clock.sim_hours),
            "robots_working": sum(1 for r in self.robots
                                  if r.status in ("delivery", "moving_to_charge")),
            "robots_idle": sum(1 for r in self.robots if r.status == "idle"),
            "robots_charging": sum(1 for r in self.robots
                                   if r.status in ("charging", "off_shift")),
            "saving_per_operation_rub": self.saving_per_operation,
        }

    def run(self, n_steps: int):
        for _ in range(n_steps):
            self.step()

    def robots_payload(self) -> List[dict]:
        return [
            {
                "id": r.rid,
                "x": round(r.pos[0] / self.tmap.tile_size_m, 2),
                "y": round(r.pos[1] / self.tmap.tile_size_m, 2),
                "battery": round(r.battery_pct, 1),
                "status": r.status,
                "tasks": r.tasks_done,
                "color": r.color,
                "path": [[int(rr), int(cc)] for rr, cc in r.path[:80]],
            }
            for r in self.robots
        ]


# ===========================================================================
# 6. CLI
# ===========================================================================

def main(excel_path: str = "Склад.csv", object_type: str = "Склад",
         n_robots: int = 8, n_steps: int = 200):
    from dataset import load_dataset

    if excel_path.endswith((".xlsx", ".xls")):
        data = load_dataset(excel_path, sheet=object_type)
    else:
        data = load_dataset(excel_path)

    tmap = build_map(object_type, data)
    spec = SRobot()  # демо-робот
    sim = Simulation(tmap, n_robots=n_robots, data=data, seed=7,
                     time_scale=60.0, robot_spec=spec)
    sim.run(n_steps)

    print("Финальные KPI:")
    for k, v in sim.kpi().items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()