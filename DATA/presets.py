from pathlib import Path
import csv
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel, Field, ValidationError, field_validator
class SRobotCSV(BaseModel):
    """Схема одной строки CSV."""
    model: str = Field(..., min_length=1, max_length=255)
    capacity: int = Field(..., gt=0)
    cost: int = Field(..., ge=0)
    accum_life: int = Field(..., gt=0)
    mass: int = Field(..., gt=0)
    size_x: int = Field(..., gt=0)
    size_y: int = Field(..., gt=0)
    size_z: int = Field(..., gt=0)
    max_speed: float = Field(..., gt=0)
    navigation_type: str = Field(..., min_length=1)
    charge_time: float = Field(..., gt=0)
    work_time: float = Field(..., gt=0)
    efficiency: float = Field(..., gt=0)
    accuracy: float = Field(..., ge=0)
    from_dataset: str = Field(..., min_length=1)

    @field_validator("max_speed", "charge_time", "work_time",
                     "efficiency", "accuracy", mode="before")
    @classmethod
    def _to_float(cls, v):
        """Приводим строку '1,5' или '1.5' к float."""
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v).replace(",", ".").strip())

    @field_validator("capacity", "cost", "accum_life", "mass",
                     "size_x", "size_y", "size_z", mode="before")
    @classmethod
    def _to_int(cls, v):
        if isinstance(v, int):
            return v
        return int(str(v).strip())


def read_robots_csv(path: Path,
                    delimiter: str = ";",
                    encoding: str = "utf-8-sig") -> Iterator[SRobotCSV]:
    """
    Читает CSV и возвращает валидированные строки.
    utf-8-sig — чтобы BOM от Excel не попал в первый ключ.
    """
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for i, row in enumerate(reader, start=2):    # 2 = первая строка данных
            # убираем пробелы в ключах и значениях
            row = {k.strip(): (v.strip() if isinstance(v, str) else v)
                   for k, v in row.items()}

            try:
                yield SRobotCSV(**row)
            except ValidationError as e:
                raise ValueError(f"Ошибка в строке {i}: {e}") from e

COEFFICIENTS = [
    # --- из датасета ---
    {"name": "k_PeLo",          "min": 1.2,  "base": 1.5,  "max": 2.5},
    {"name": "K_load",          "min": 0.70, "base": 0.75, "max": 0.85},
    {"name": "k_res",           "min": 1.15, "base": 1.15, "max": 1.20},
    {"name": "k_FOT",           "min": 1.302, "base": 1.302, "max": 1.302},

    # --- CAPEX-коэффициенты ---
    {"name": "k_res_capex",     "min": None, "base": 0.10, "max": None},
    {"name": "battery_life",    "min": 3,    "base": 4,    "max": 5},        # срок службы АКБ, лет
    {"name": "k_PO",            "min": 0.05, "base": 0.07, "max": 0.10},
    {"name": "k_integ",         "min": 0.50, "base": 0.75, "max": 1.00},
    {"name": "k_PNR",           "min": 0.05, "base": 0.07, "max": 0.10},
    {"name": "k_learn",         "min": 0.02, "base": 0.03, "max": 0.05},

    # --- OPEX-коэффициенты ---
    {"name": "k_service",       "min": 0.08, "base": 0.10, "max": 0.12},
    {"name": "k_lic",           "min": 0.02, "base": 0.03, "max": 0.05},
    {"name": "k_conn",          "min": 0.01, "base": 0.01, "max": 0.02},
    {"name": "k_cons",          "min": 0.01, "base": 0.02, "max": 0.03},
    {"name": "k_rep",           "min": 0.02, "base": 0.03, "max": 0.05},

    # --- TCO / общие ---
    {"name": "inflation",       "min": 0.05, "base": 0.06, "max": 0.07},
    {"name": "what_if",         "min": 0.8,  "base": 1.0,  "max": 1.2},
]


ROBOTS = list( read_robots_csv((Path(__file__).parent / "robots.csv")))



