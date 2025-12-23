import re
from datetime import datetime
import math
import pandas as pd


def normalize_transponder(transponder: str) -> str:
    """Нормализует номер транспондера к формату сайта: '3086595 0000 0650 5272'"""
    if not transponder:
        return ""

    transponder = str(transponder)
    digits_only = re.sub(r'\D', '', transponder)

    if len(digits_only) != 19:
        if not digits_only or len(digits_only) < 10:
            return ""
        return ' '.join([digits_only[i:i + 4] for i in range(0, len(digits_only), 4)])

    return f"{digits_only[:7]} {digits_only[7:11]} {digits_only[11:15]} {digits_only[15:19]}"


def normalize_pvp(road: str) -> str:
    """Извлекает код ПВП из строки"""
    if not road:
        return "unknown"

    try:
        # Разбиваем по всем возможным разделителям
        parts = [p.strip() for p in re.split(r'[\n\r\\/|]+', str(road)) if p.strip()]

        # Ищем ПВП в разных форматах
        for part in parts:
            # Убираем лишние пробелы
            part = re.sub(r'\s+', ' ', part).strip()

            # Если это номер ПВП (например: ПВП-416M, М4-620-Рос)
            if re.match(r'^(ПВП|М\d+|РВП)[-\s]', part, re.IGNORECASE):
                return part

            # Если содержит код типа ПВП-xxx или Мx-xxx
            if re.search(r'ПВП[-\s]\d+', part, re.IGNORECASE) or re.match(r'М\d+-\d+', part):
                return part

            # Если просто код ПВП (например: 416M)
            if re.match(r'^\d+[A-Za-z]?$', part):
                return f"ПВП-{part}"

        # Если не нашли ПВП в ожидаемых форматах, берем первую непустую часть
        return parts[0] if parts else "unknown"

    except Exception as e:
        print(f"Error normalizing PVP: {e}, road: {road}")
        return "unknown"

def normalize_date(date_str: str) -> datetime | None:
    if not date_str:
        return None

    parts = date_str.strip().split()
    if len(parts) >= 2:
        if re.match(r'\d{2}:\d{2}(:\d{2})?', parts[1]):
            date_time_str = f"{parts[0]} {parts[1]}"
        else:
            date_time_str = parts[0]
    else:
        date_time_str = date_str.strip()

    if re.match(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$', date_time_str):
        date_time_str += ":00"

    formats = [
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_time_str, fmt)
        except ValueError:
            continue

    return None

def normalize_amount(s):
    if s is None or s == "":
        return None
    if isinstance(s, (int, float)):
        return float(s)
    try:
        cleaned = str(s).replace(" ", "").replace("руб", "").replace(",", ".").replace("₽", "")
        return float(cleaned)
    except:
        return None

def normalize_discount(value):
    """Парсит значение скидки из любых типов данных."""
    if value is None:
        return "-"

    # Если значение NaN (из Excel)
    if isinstance(value, float) and math.isnan(value):
        return "-"

    # Если значение уже число
    if isinstance(value, (int, float)):
        return int(value)

    # Если строка
    try:
        cleaned = str(value).replace("%", "").replace(",", ".").strip()
        return int(float(cleaned))
    except:
        return "-"

def normalize_row(row: dict) -> dict:
    return {
        "occurred_at": normalize_date(
            row.get("Дата") or row.get("date") or row.get("Дата и время")
        ),

        "PVP_code": normalize_pvp(
            row.get("ПВП\\РВП выезда") or row.get("ПВП") or row.get("road") or ""
        ),

        "transponder": normalize_transponder(
            str(row.get("Электронное средство") or row.get("transponder") or row.get("ТС") or "")
        ),

        "base_tariff": normalize_amount(
            row.get("Сумма тарифа, ₽") or row.get("amount") or row.get("Цена") or ""
        ),

        "discount": normalize_discount(
            row.get("Скидка, %") or row.get("discount") or ""
        ),

        "paid": normalize_amount(
            row.get("Оплачено, ₽") or row.get("paid") or row.get("Итого") or ""
        )
    }

def normalize_dataframe(df: pd.DataFrame):
    df = df.fillna("")
    normalized = []
    for _, row in df.iterrows():
        normalized.append(normalize_row(row.to_dict()))
    return normalized