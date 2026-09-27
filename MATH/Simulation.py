# -*- coding: utf-8 -*-
"""
Тайловая карта местности + симуляция передвижения роботов
на основе датасетов: Склад / Аэропорт / Медучреждение.
"""

import math
import random
import heapq
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap

# ----------------------------------------------------------------------------
# 1. ЧТЕНИЕ ДАТАСЕТА
# ----------------------------------------------------------------------------

def load_dataset(path: str, sheet: str) -> Dict[str, dict]:
    """Читает лист Excel и возвращает словарь {параметр: {value, min, max, unit}}."""
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    # Заголовок на 2-й строке (индекс 1)
    df.columns = df.iloc[1]
    df = df.iloc[2:].reset_index(drop=True)
    df.columns = ["param", "unit", "base", "vmin", "vmax", "note"]

    data = {}
    for _, row in df.iterrows():
        p = str(row["param"]).strip()
        if not p or p.lower() == "nan":
            continue
        data[p] = {
            "unit": row["unit"],
            "base": row["base"],
            "min": row["vmin"],
            "max": row["vmax"],
            "note": row["note"],
        }
    return data


def get_num(data: Dict[str, dict], key: str, default: float = 0.0) -> float:
    """Достаёт числовое значение из датасета (base), с fallback."""
    try:
        v = data[key]["base"]
        if isinstance(v, str):
            v = v.replace(",", ".").strip()
        return float(v)
    except Exception:
        return default


# ----------------------------------------------------------------------------
# 2. МОДЕЛЬ ТАЙЛОВОЙ КАРТЫ
# ----------------------------------------------------------------------------

# Типы тайлов
TILE_FREE      = 0   # свободный проход
TILE_SHELF     = 1   # стеллаж / препятствие
TILE_AISLE     = 2   # рабочий проход (узкий)
TILE_HIGHWAY   = 3   # главный проезд
TILE_CHARGE    = 4   # зарядная станция
TILE_PICK      = 5   # точка отбора / выдачи
TILE_DROPOFF   = 6   # точка доставки
TILE_WALL      = 7   # стена / граница

TILE_NAMES = {
    TILE_FREE: "Свободно",
    TILE_SHELF: "Стеллаж",
    TILE_AISLE: "Проход",
    TILE_HIGHWAY: "Магистраль",
    TILE_CHARGE: "Зарядка",
    TILE_PICK: "Отбор",
    TILE_DROPOFF: "Доставка",
    TILE_WALL: "Стена",
}


@dataclass
class TileMap:
    """Тайловая карта местности."""
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

    # --- координаты ---
    def to_cell(self, x_m: float, y_m: float) -> Tuple[int, int]:
        c = int(np.clip(x_m / self.tile_size_m, 0, self.ncols - 1))
        r = int(np.clip(y_m / self.tile_size_m, 0, self.nrows - 1))
        return r, c

    def to_world(self, r: int, c: int) -> Tuple[float, float]:
        return (c + 0.5) * self.tile_size_m, (r + 0.5) * self.tile_size_m

    # --- модификация ---
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

    # --- поиск пути A* ---
    def astar(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        if start == goal:
            return [start]
        if not self.passable(*goal) or not self.passable(*start):
            return []

        def h(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = [(h(start, goal), 0, start)]
        came_from = {}
        g_score = {start: 0}
        visited = set()

        while open_set:
            _, g, cur = heapq.heappop(open_set)
            if cur in visited:
                continue
            visited.add(cur)
            if cur == goal:
                # восстановление пути
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


# ----------------------------------------------------------------------------
# 3. ГЕНЕРАТОРЫ КАРТ ДЛЯ РАЗНЫХ ОБЪЕКТОВ
# ----------------------------------------------------------------------------

def build_warehouse_map(data: Dict[str, dict]) -> TileMap:
    """Склад: стеллажи + проходы + магистрали."""
    area = get_num(data, "Площадь активной (роботизируемой) зоны", 10000)
    # Делаем прямоугольник ~ соотношение 1.6:1
    w = math.sqrt(area * 1.6)
    h = area / w

    tmap = TileMap(width_m=w, height_m=h, tile_size_m=1.0)
    tmap.draw_border(2)

    aisle_w = get_num(data, "Ширина рабочих проходов между стеллажами", 2.8)
    highway_w = get_num(data, "Ширина главных проездов", 3.5)

    # Горизонтальные магистрали каждые ~40 м
    y = highway_w
    while y < h - highway_w:
        tmap.fill_rect(0, y, w, y + highway_w, TILE_HIGHWAY)
        y += 40

    # Блоки стеллажей + проходы
    shelf_h = 6.0          # глубина блока стеллажей
    y = highway_w + 3
    while y + shelf_h + aisle_w < h:
        y0 = y
        # сам блок стеллажей
        tmap.fill_rect(2, y0, w - 2, y0 + shelf_h, TILE_SHELF)
        # рабочий проход под блоком
        tmap.fill_rect(2, y0 + shelf_h, w - 2, y0 + shelf_h + aisle_w, TILE_AISLE)
        y = y0 + shelf_h + aisle_w + 4  # +широкий проезд

    # Вертикальные магистрали
    x = 25
    while x < w - 5:
        tmap.fill_rect(x, 0, x + 2, h, TILE_HIGHWAY)
        x += 45

    # Зарядные станции в углах
    for (x0, y0) in [(3, 3), (w - 8, 3), (3, h - 8), (w - 8, h - 8)]:
        tmap.fill_rect(x0, y0, x0 + 5, y0 + 5, TILE_CHARGE)

    return tmap


def build_airport_map(data: Dict[str, dict]) -> TileMap:
    """Аэропорт: терминал + перрон + рулёжные дорожки."""
    term_area = get_num(data, "Суммарная площадь терминала (ов)", 85000)
    ramp_area = get_num(data, "Площадь перрона и технических зон", 100000)

    w = math.sqrt((term_area + ramp_area) * 1.4)
    h = (term_area + ramp_area) / w

    tmap = TileMap(width_m=w, height_m=h, tile_size_m=2.0)
    tmap.draw_border(3)

    # Терминал — левая половина
    term_w = w * 0.4
    tmap.fill_rect(0, 0, term_w, h, TILE_FREE)

    # Внутренние стены терминала (упрощённо)
    n_gates = int(get_num(data, "Количество выходов на посадку (гейтов)", 20))
    gate_step = h / max(n_gates, 1)
    for i in range(n_gates):
        y = i * gate_step + gate_step * 0.3
        tmap.fill_rect(term_w - 4, y, term_w, y + 2, TILE_PICK)

    # Перрон — правая половина
    tmap.fill_rect(term_w + 2, 0, w, h, TILE_HIGHWAY)

    # Рулёжные дорожки — сетка
    for i in range(1, 6):
        y = h * i / 6
        tmap.fill_rect(term_w + 2, y, w - 2, y + 3, TILE_AISLE)
    for j in range(1, 4):
        x = term_w + 2 + (w - term_w) * j / 4
        tmap.fill_rect(x, 0, x + 2, h, TILE_AISLE)

    # Зарядные станции у терминала
    for i in range(4):
        y = h * (i + 0.5) / 4
        tmap.fill_rect(term_w - 12, y, term_w - 4, y + 6, TILE_CHARGE)

    return tmap


def build_hospital_map(data: Dict[str, dict]) -> TileMap:
    """Медучреждение: этаж с коридорами, палатами, аптекой, лабораторией."""
    area = get_num(data, "Общая площадь здания(й)", 45000)
    floors = max(1, int(get_num(data, "Количество этажей (основной корпус)", 9)))
    floor_area = area / floors

    w = math.sqrt(floor_area * 1.5)
    h = floor_area / w

    tmap = TileMap(width_m=w, height_m=h, tile_size_m=1.0)
    tmap.draw_border(2)

    corridor_w = get_num(data, "Ширина коридоров (основных)", 2.4)

    # Горизонтальный центральный коридор
    cy = h / 2
    tmap.fill_rect(0, cy - corridor_w / 2, w, cy + corridor_w / 2, TILE_HIGHWAY)

    # Параллельные коридоры
    for k in (0.25, 0.75):
        y = h * k
        tmap.fill_rect(0, y, w, y + corridor_w, TILE_AISLE)

    # Вертикальные коридоры-связки
    for k in (0.2, 0.5, 0.8):
        x = w * k
        tmap.fill_rect(x, 0, x + corridor_w, h, TILE_AISLE)

    # Кабинеты/палаты (блоки-препятствия)
    n_depts = int(get_num(data, "Количество точек раздачи питания (отделений)", 18))
    for i in range(n_depts):
        x = 4 + (i % 6) * (w / 6.5)
        y = 4 + (i // 6) * (h / 3.5)
        tmap.fill_rect(x, y, x + w / 8, y + h / 6, TILE_SHELF)

    # Аптека (pick), лаборатория (dropoff), зарядки
    tmap.fill_rect(4, cy + 4, 12, cy + 12, TILE_PICK)
    tmap.fill_rect(w - 14, cy - 12, w - 4, cy - 4, TILE_DROPOFF)
    tmap.fill_rect(4, 4, 10, 10, TILE_CHARGE)
    tmap.fill_rect(w - 10, h - 10, w - 4, h - 4, TILE_CHARGE)

    return tmap


# ----------------------------------------------------------------------------
# 4. РОБОТ И СИМУЛЯЦИЯ
# ----------------------------------------------------------------------------

@dataclass
class Robot:
    rid: int
    pos: Tuple[float, float]
    speed_mps: float = 1.2          # ~4.3 км/ч
    battery_pct: float = 100.0
    battery_drain_per_m: float = 0.05
    path: List[Tuple[int, int]] = field(default_factory=list)
    target: Optional[Tuple[int, int]] = None
    color: str = "tab:blue"
    distance_traveled: float = 0.0
    tasks_done: int = 0
    waiting: int = 0
    status: str = "idle"


class Simulation:
    def __init__(self, tmap: TileMap, n_robots: int, seed: int = 42):
        self.tmap = tmap
        self.rng = random.Random(seed)
        self.robots: List[Robot] = []
        self.tick = 0
        self.history: List[dict] = []

        palette = ["tab:blue", "tab:orange", "tab:green", "tab:red",
                   "tab:purple", "tab:brown", "tab:pink", "tab:gray",
                   "tab:olive", "tab:cyan"]

        # Находим все зарядные станции и стартуем с них
        charge_cells = list(zip(*np.where(tmap.grid == TILE_CHARGE)))
        free_cells = list(zip(*np.where(tmap.grid == TILE_FREE)))

        for i in range(n_robots):
            if charge_cells:
                r, c = charge_cells[i % len(charge_cells)]
            else:
                r, c = self.rng.choice(free_cells)
            x, y = tmap.to_world(r, c)
            self.robots.append(Robot(
                rid=i, pos=(x, y), color=palette[i % len(palette)]
            ))

        self.charge_cells = charge_cells
        self.pick_cells = list(zip(*np.where(tmap.grid == TILE_PICK)))
        self.dropoff_cells = list(zip(*np.where(tmap.grid == TILE_DROPOFF)))

    # -------- назначение задач --------
    def assign_task(self, robot: Robot):
        """Назначает роботу новую задачу: pick -> dropoff или патруль."""
        if not self.pick_cells or not self.dropoff_cells:
            # патрулирование: случайная свободная точка
            free = list(zip(*np.where(self.tmap.grid == TILE_FREE)))
            if not free:
                return
            target = self.rng.choice(free)
            robot.path = self.tmap.astar(self.tmap.to_cell(*robot.pos), target)
            robot.target = target
            robot.status = "patrol"
            return

        start = self.tmap.to_cell(*robot.pos)
        pick = self.rng.choice(self.pick_cells)
        drop = self.rng.choice(self.dropoff_cells)

        p1 = self.tmap.astar(start, pick)
        if not p1:
            return
        p2 = self.tmap.astar(pick, drop)
        robot.path = p1 + p2[1:]
        robot.target = drop
        robot.status = "delivery"

    # -------- один шаг симуляции --------
    def step(self):
        self.tick += 1
        dt = 1.0  # секунда на шаг

        occupied = {}
        for r in self.robots:
            cell = self.tmap.to_cell(*r.pos)
            occupied.setdefault(cell, []).append(r.rid)

        for robot in self.robots:
            # разряд батареи
            robot.battery_pct = max(0.0, robot.battery_pct - 0.002)

            # нужна зарядка?
            if robot.battery_pct < 15 and self.charge_cells:
                cur = self.tmap.to_cell(*robot.pos)
                nearest = min(
                    self.charge_cells,
                    key=lambda cc: abs(cc[0] - cur[0]) + abs(cc[1] - cur[1]),
                )
                robot.path = self.tmap.astar(cur, nearest)
                robot.target = nearest
                robot.status = "charging"

            # нет пути — назначим задачу
            if not robot.path:
                if robot.status == "charging" and robot.target:
                    # «заряжаемся» несколько тиков
                    robot.battery_pct = min(100.0, robot.battery_pct + 1.0)
                    if robot.battery_pct >= 95:
                        robot.status = "idle"
                        self.assign_task(robot)
                    continue
                if robot.battery_pct >= 15:
                    self.assign_task(robot)
                continue

            # движение к следующей клетке
            nxt = robot.path[0]
            wx, wy = self.tmap.to_world(*nxt)

            # проверка занятости клетки (простое избегание столкновений)
            if occupied.get(nxt) and len(occupied[nxt]) > 1:
                robot.waiting += 1
                continue

            dx = wx - robot.pos[0]
            dy = wy - robot.pos[1]
            dist = math.hypot(dx, dy)
            step_len = robot.speed_mps * dt

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
                    robot.status = "idle"
            else:
                robot.pos = (
                    robot.pos[0] + dx / dist * step_len,
                    robot.pos[1] + dy / dist * step_len,
                )
                robot.distance_traveled += step_len
                robot.battery_pct = max(
                    0.0,
                    robot.battery_pct - step_len * robot.battery_drain_per_m,
                )

        # метрики
        total_dist = sum(r.distance_traveled for r in self.robots)
        avg_bat = np.mean([r.battery_pct for r in self.robots])
        busy = sum(1 for r in self.robots if r.status != "idle")
        self.history.append({
            "tick": self.tick,
            "total_distance_m": total_dist,
            "avg_battery": avg_bat,
            "busy_robots": busy,
            "total_tasks": sum(r.tasks_done for r in self.robots),
        })

    def run(self, n_steps: int):
        for _ in range(n_steps):
            self.step()


# ----------------------------------------------------------------------------
# 5. ВИЗУАЛИЗАЦИЯ
# ----------------------------------------------------------------------------

def make_cmap():
    colors = [
        "#f7f7f7",  # FREE
        "#7f7f7f",  # SHELF
        "#d9ead3",  # AISLE
        "#fff2cc",  # HIGHWAY
        "#9fc5e8",  # CHARGE
        "#f4cccc",  # PICK
        "#d9d2e9",  # DROPOFF
        "#333333",  # WALL
    ]
    return ListedColormap(colors)


def visualize(tmap: TileMap, sim: Simulation, n_steps: int = 120, save_path: Optional[str] = None):
    fig, (ax_map, ax_stats) = plt.subplots(
        1, 2, figsize=(16, 8), gridspec_kw={"width_ratios": [3, 1]}
    )
    cmap = make_cmap()

    ax_map.imshow(tmap.grid, cmap=cmap, vmin=0, vmax=7, origin="lower")
    ax_map.set_title("Тайловая карта местности (склад/аэропорт/медцентр)")
    ax_map.set_xlabel("X, тайлы")
    ax_map.set_ylabel("Y, тайлы")

    # легенда
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=cmap(i))
        for i in range(8)
    ]
    ax_map.legend(handles, [TILE_NAMES[i] for i in range(8)],
                  loc="upper right", fontsize=7, framealpha=0.9)

    robot_scatter = ax_map.scatter([], [], s=60, c=[], edgecolors="k", zorder=5)
    robot_paths = [ax_map.plot([], [], "-", lw=1, alpha=0.5,
                               color=r.color)[0] for r in sim.robots]
    robot_labels = [
        ax_map.text(0, 0, "", fontsize=7, color="black",
                    ha="center", va="center", zorder=6)
        for _ in sim.robots
    ]

    # правая панель — статистика
    ax_stats.axis("off")
    stat_text = ax_stats.text(
        0.02, 0.98, "", va="top", ha="left", family="monospace", fontsize=10
    )

    dist_line, = ax_stats.plot([], [], "b-", label="Пройдено, м")
    bat_line, = ax_stats.plot([], [], "g-", label="Ср. заряд, %")
    task_line, = ax_stats.plot([], [], "r-", label="Задач выполнено")
    ax_stats.set_xlim(0, n_steps)
    ax_stats.set_ylim(0, 100)
    ax_stats.legend(loc="lower right", fontsize=8)

    def init():
        robot_scatter.set_offsets(np.empty((0, 2)))
        robot_scatter.set_array(np.array([]))
        for line in robot_paths:
            line.set_data([], [])
        return [robot_scatter, stat_text, dist_line, bat_line, task_line] + robot_paths + robot_labels

    def update(frame):
        sim.step()

        xs, ys, cs = [], [], []
        for i, r in enumerate(sim.robots):
            xs.append(r.pos[0] / tmap.tile_size_m)
            ys.append(r.pos[1] / tmap.tile_size_m)
            cs.append(r.color)
            robot_labels[i].set_position(
                (r.pos[0] / tmap.tile_size_m, r.pos[1] / tmap.tile_size_m + 0.8)
            )
            robot_labels[i].set_text(f"R{r.rid}")

            if r.path:
                px = [(c + 0.5) for (_, c) in r.path]
                py = [(rr + 0.5) for (rr, _) in r.path]
                robot_paths[i].set_data(px, py)
            else:
                robot_paths[i].set_data([], [])

        robot_scatter.set_offsets(np.c_[xs, ys])
        robot_scatter.set_color(cs)

        h = sim.history
        ticks = [d["tick"] for d in h]
        dists = [d["total_distance_m"] for d in h]
        bats = [d["avg_battery"] for d in h]
        tasks = [d["total_tasks"] * 10 for d in h]

        dist_line.set_data(ticks, dists)
        bat_line.set_data(ticks, bats)
        task_line.set_data(ticks, tasks)
        ax_stats.set_xlim(0, max(n_steps, len(ticks)))

        stat_text.set_text(
            f"Тик: {sim.tick}\n"
            f"Роботов: {len(sim.robots)}\n"
            f"Ср. заряд: {np.mean([r.battery_pct for r in sim.robots]):5.1f}%\n"
            f"Пройдено: {sum(r.distance_traveled for r in sim.robots):8.1f} м\n"
            f"Задач: {sum(r.tasks_done for r in sim.robots)}\n"
            f"Ожиданий: {sum(r.waiting for r in sim.robots)}\n"
            f"Занято: {sum(1 for r in sim.robots if r.status != 'idle')}"
        )
        return [robot_scatter, stat_text, dist_line, bat_line, task_line] + robot_paths + robot_labels

    ani = animation.FuncAnimation(
        fig, update, frames=n_steps, init_func=init,
        interval=50, blit=False, repeat=False,
    )

    if save_path:
        ani.save(save_path, writer="pillow", fps=20)
        print(f"Анимация сохранена: {save_path}")

    plt.tight_layout()
    plt.show()
    return ani


# ----------------------------------------------------------------------------
# 6. ТОЧКА ВХОДА
# ----------------------------------------------------------------------------

def main(
    excel_path: str = "Датасеты_хакатон.xlsx",
    object_type: str = "Склад",     # "Склад" | "Аэропорт" | "Медучреждение"
    n_robots: int = 8,
    n_steps: int = 200,
    save_gif: Optional[str] = "simulation.gif",
):
    print(f"Загрузка листа «{object_type}»...")
    data = load_dataset(excel_path, object_type)

    if object_type == "Склад":
        tmap = build_warehouse_map(data)
    elif object_type == "Аэропорт":
        tmap = build_airport_map(data)
    elif object_type == "Медучреждение":
        tmap = build_hospital_map(data)
    else:
        raise ValueError(f"Неизвестный тип объекта: {object_type}")

    print(f"Карта: {tmap.ncols}×{tmap.nrows} тайлов "
          f"({tmap.width_m:.0f}×{tmap.height_m:.0f} м)")

    sim = Simulation(tmap, n_robots=n_robots, seed=7)

    # предварительный разогрев — назначим первые задачи
    for r in sim.robots:
        sim.assign_task(r)

    visualize(tmap, sim, n_steps=n_steps, save_path=save_gif)

    # Итоговые метрики
    total_d = sum(r.distance_traveled for r in sim.robots)
    total_tasks = sum(r.tasks_done for r in sim.robots)
    print("\n=== ИТОГИ СИМУЛЯЦИИ ===")
    print(f"Роботов:                {len(sim.robots)}")
    print(f"Суммарный путь:         {total_d:.1f} м")
    print(f"Средний путь на робота: {total_d / len(sim.robots):.1f} м")
    print(f"Выполнено задач:        {total_tasks}")
    print(f"Средний заряд:          "
          f"{np.mean([r.battery_pct for r in sim.robots]):.1f}%")


if __name__ == "__main__":
    # Пример: склад, 8 роботов, 200 шагов симуляции
    main(
        excel_path="Датасеты_хакатон.xlsx",
        object_type="Склад",
        n_robots=8,
        n_steps=200,
        save_gif="simulation_warehouse.gif",
    )