# dataset.py
# -*- coding: utf-8 -*-
"""
Работа с датасетами симуляции.

Поддерживает:
  • CSV (UTF-8, UTF-8-BOM, cp1251), разделители ; , \t
  • Excel (.xlsx/.xls) с листами «Склад» / «Аэропорт» / «Медучреждение»
  • bytes (для приёма по WebSocket)
  • автоопределение кодировки и разделителя
  • поиск строки-заголовка («Параметр … Базовое значение …»)
"""

from __future__ import annotations

import csv as csv_module
from io import StringIO
from pathlib import Path
from typing import Dict, Optional, Union

try:
    import chardet
except ImportError:
    chardet = None

import pandas as pd


# ---------------------------------------------------------------------------
# Типы
# ---------------------------------------------------------------------------
Param = Dict[str, dict]                 # {имя_параметра: {unit, base, min, max, note}}


# ---------------------------------------------------------------------------
# Публичные функции
# ---------------------------------------------------------------------------

def load_dataset(source: Union[str, Path, bytes, bytearray],
                 sheet: Optional[str] = None) -> Param:
    """
    Универсальная загрузка датасета.

    source : путь к .csv / .xlsx / .xls ИЛИ сырые байты CSV
    sheet  : имя листа Excel (обязательно для .xlsx с несколькими листами)

    Возвращает dict[str, dict] — {имя_параметра: {unit, base, min, max, note}}
    """
    # --- Excel ---
    if isinstance(source, (str, Path)) and str(source).lower().endswith((".xlsx", ".xls")):
        if not sheet:
            raise ValueError(
                "Для Excel нужно указать sheet='Склад'/'Аэропорт'/'Медучреждение'"
            )
        return _load_from_excel(source, sheet)

    # --- CSV из файла или bytes ---
    text = _read_text_smart(source).lstrip("\ufeff")
    return _parse_csv_text(text)


def get_num(data: Param, key: str, default: float = 0.0) -> float:
    """Числовое значение параметра (base) с fallback."""
    try:
        v = data[key]["base"]
        if isinstance(v, str):
            v = v.replace(",", ".").strip()
        return float(v)
    except Exception:
        return default


def get_str(data: Param, key: str, default: str = "") -> str:
    """Строковое значение параметра (base) с fallback."""
    try:
        return str(data[key]["base"]).strip()
    except Exception:
        return default


def get_range(data: Param, key: str) -> tuple[float, float]:
    """Диапазон (min, max) параметра."""
    try:
        lo = float(str(data[key]["min"]).replace(",", "."))
    except Exception:
        lo = float("nan")
    try:
        hi = float(str(data[key]["max"]).replace(",", "."))
    except Exception:
        hi = float("nan")
    return lo, hi


def to_csv_bytes(data: Param, include_ranges: bool = True) -> bytes:
    """Обратная операция: сериализовать датасет в CSV-байты."""
    buf = StringIO()
    w = csv_module.writer(buf, delimiter=";")
    cols = ["Параметр", "Ед. изм.", "Базовое значение"]
    if include_ranges:
        cols += ["Диапазон (min)", "Диапазон (max)"]
    cols.append("Примечание")
    w.writerow(cols)
    for name, p in data.items():
        row = [name, p.get("unit", ""), p.get("base", "")]
        if include_ranges:
            row += [p.get("min", ""), p.get("max", "")]
        row.append(p.get("note", ""))
        w.writerow(row)
    return buf.getvalue().encode("utf-8-sig")


# --- работа с загруженными файлами ---

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_EXTS = {".csv", ".txt", ".tsv", ".xlsx", ".xls"}


def save_upload(raw: bytes, dst_dir: Union[str, Path],
                client_id: str, filename: str,
                max_bytes: int = MAX_UPLOAD_BYTES) -> Path:
    """
    Безопасно сохраняет загруженный файл датасета.
    Возвращает путь к сохранённому файлу.
    """
    if len(raw) > max_bytes:
        raise ValueError(f"Файл слишком большой: {len(raw)} > {max_bytes} байт")

    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name or "dataset.csv"
    ext = Path(safe_name).suffix.lower()
    if ext and ext not in ALLOWED_EXTS:
        raise ValueError(f"Формат {ext} не поддерживается")

    dst = dst_dir / f"{client_id}_{safe_name}"
    dst.write_bytes(raw)
    return dst


def delete_upload(path: Optional[Path]) -> bool:
    """Удаляет файл, если он существует. Возвращает True при успехе."""
    if path is None:
        return False
    p = Path(path)
    if p.exists() and p.is_file():
        try:
            p.unlink()
            return True
        except OSError:
            return False
    return False


# ---------------------------------------------------------------------------
# Внутренние помощники
# ---------------------------------------------------------------------------

def _read_text_smart(source: Union[str, Path, bytes, bytearray]) -> str:
    """Читает файл/bytes и угадывает кодировку."""
    if isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
    else:
        raw = Path(source).read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass

    if chardet is not None:
        enc = chardet.detect(raw).get("encoding") or "cp1251"
    else:
        enc = "cp1251"
    return raw.decode(enc, errors="replace")


def _detect_delimiter(sample: str) -> str:
    """Определяет разделитель CSV: ; , или tab."""
    try:
        dialect = csv_module.Sniffer().sniff(sample[:4096], delimiters=";,\t")
        return dialect.delimiter
    except csv_module.Error:
        head = sample[:4096]
        counts = {";": head.count(";"),
                  ",": head.count(","),
                  "\t": head.count("\t")}
        return max(counts, key=counts.get)


def _normalize_header(name: str) -> str:
    """Приводит заголовки к каноническим: param/unit/base/vmin/vmax/note."""
    n = name.strip().lower()
    if "параметр" in n:
        return "param"
    if "ед" in n and "изм" in n:
        return "unit"
    if "базов" in n:
        return "base"
    if "min" in n:
        return "vmin"
    if "max" in n:
        return "vmax"
    if "примеч" in n or "источник" in n:
        return "note"
    return n


def _find_header_index(rows: list, limit: int = 20) -> int:
    """Ищет строку с 'Параметр' и 'Базовое' в первых `limit` строках."""
    for i, row in enumerate(rows[:limit]):
        joined = " ".join(c.strip().lower() for c in row)
        if "параметр" in joined and ("базов" in joined or "значен" in joined):
            return i
    return 0


def _parse_csv_text(text: str) -> Param:
    """Парсит CSV-текст в словарь параметров."""
    delim = _detect_delimiter(text)
    reader = csv_module.reader(StringIO(text), delimiter=delim)
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return {}

    header_idx = _find_header_index(rows)
    header = [_normalize_header(c) for c in rows[header_idx]]

    data: Param = {}
    for raw in rows[header_idx + 1:]:
        raw = raw + [""] * (len(header) - len(raw))
        rec = dict(zip(header, [c.strip() for c in raw]))

        param = rec.get("param", "").strip()
        if not param:
            continue
        if param.startswith("▌") or param.startswith("#"):
            continue

        data[param] = {
            "unit": rec.get("unit", ""),
            "base": rec.get("base", ""),
            "min":  rec.get("vmin", ""),
            "max":  rec.get("vmax", ""),
            "note": rec.get("note", ""),
        }
    return data


def _load_from_excel(path: Union[str, Path], sheet: str) -> Param:
    """Парсит лист Excel в тот же формат Param."""
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    df.columns = df.iloc[1]
    df = df.iloc[2:].reset_index(drop=True)
    df.columns = ["param", "unit", "base", "vmin", "vmax", "note"]

    data: Param = {}
    for _, row in df.iterrows():
        p = str(row["param"]).strip()
        if not p or p.lower() == "nan" or p.startswith("▌"):
            continue
        data[p] = {
            "unit": row["unit"],
            "base": row["base"],
            "min":  row["vmin"],
            "max":  row["vmax"],
            "note": row["note"],
        }
    return data