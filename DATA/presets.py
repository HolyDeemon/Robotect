import json
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
    length: int = Field(..., gt=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    max_speed: float = Field(..., gt=0)
    navigation_type: str = Field(..., min_length=1)
    charge_time: float = Field(..., gt=0)
    work_time: float = Field(..., gt=0)
    efficiency: float = Field(..., gt=0)
    accuracy: float = Field(..., ge=0)
    operationg_conditions: str = Field(default="")

    @field_validator("max_speed", "charge_time", "work_time",
                     "efficiency", "accuracy", mode="before")
    @classmethod
    def _to_float(cls, v):
        """Приводим строку '1,5' или '1.5' к float."""
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v).replace(",", ".").strip())

    @field_validator("capacity", "cost", "accum_life", "mass",
                     "length", "width", "height", mode="before")
    @classmethod
    def _to_int(cls, v):
        if isinstance(v, int):
            return v
        return int(str(v).strip())


def read_robots_csv(path: Path,
                    delimiter: str = ";",
                    encoding: str = "cp1251") -> Iterator[SRobotCSV]:
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
    # ============================================================
    # из датасета
    # ============================================================
    {"name": "k_PeLo",       "opt": 1.2,   "base": 1.5,   "pess": 2.5,   "source": "dataset"},
    {"name": "K_load",       "opt": 0.85,  "base": 0.75,  "pess": 0.70,  "source": "dataset"},
    {"name": "k_res",        "opt": 1.15,  "base": 1.15,  "pess": 1.20,  "source": "dataset"},
    {"name": "k_FOT",        "opt": 1.302, "base": 1.302, "pess": 1.302, "source": "dataset"},

    # ============================================================
    # CAPEX-коэффициенты
    # ============================================================
    {"name": "k_solCost",    "opt": 0.80,  "base": 1.00,  "pess": 1.20,  "source": "catalog"},
    {"name": "k_res_capex",  "opt": 0.05,  "base": 0.10,  "pess": 0.15,  "source": "dataset"},
    {"name": "battery_life", "opt": 5,     "base": 4,     "pess": 3,     "source": "dataset"},
    {"name": "k_PO",         "opt": 0.05,  "base": 0.07,  "pess": 0.10,  "source": "assumption"},
    {"name": "k_integ",      "opt": 0.50,  "base": 0.75,  "pess": 1.00,  "source": "assumption"},
    {"name": "k_PNR",        "opt": 0.05,  "base": 0.07,  "pess": 0.10,  "source": "assumption"},
    {"name": "k_learn",      "opt": 0.02,  "base": 0.03,  "pess": 0.05,  "source": "assumption"},

    # ============================================================
    # OPEX-коэффициенты
    # ============================================================
    {"name": "k_service",    "opt": 0.08,  "base": 0.10,  "pess": 0.12,  "source": "assumption"},
    {"name": "k_lic",        "opt": 0.02,  "base": 0.03,  "pess": 0.05,  "source": "assumption"},
    {"name": "k_conn",       "opt": 0.01,  "base": 0.01,  "pess": 0.02,  "source": "assumption"},
    {"name": "k_cons",       "opt": 0.01,  "base": 0.02,  "pess": 0.03,  "source": "assumption"},
    {"name": "k_rep",        "opt": 0.02,  "base": 0.03,  "pess": 0.05,  "source": "assumption"},

    # ============================================================
    # TCO / общие
    # ============================================================
    {"name": "inflation",    "opt": 0.05,  "base": 0.06,  "pess": 0.07,  "source": "assumption"},
    {"name": "what_if",      "opt": 0.8,   "base": 1.0,   "pess": 1.2,   "source": "methodology"},
]


ROBOTS = list( read_robots_csv((Path(__file__).parent / "robot.csv")))



