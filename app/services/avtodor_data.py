import re
from typing import Dict, Optional, Tuple
from datetime import datetime

class AvtodorData:
    """Класс для парсинга и нормализации данных Avtodor"""

    @staticmethod
    def parse_trip_data(raw_trip: Dict) -> Dict:
        """Парсит и нормализует данные поездки"""
        try:
            occurred_at = AvtodorData._parse_date(raw_trip.get('date', ''))
            road = raw_trip.get('road', '')
            pvp_code, vehicle_class = AvtodorData._extract_pvp_and_vehicle_class(road)
            transponder = AvtodorData._normalize_transponder(raw_trip.get('transponder', ''))
            base_tariff = AvtodorData._parse_amount(raw_trip.get('amount', ''))
            discount = AvtodorData._parse_discount(raw_trip.get('discount', ''))
            paid = AvtodorData._parse_amount(raw_trip.get('paid', ''))
            return {
                'occurred_at': occurred_at,
                'PVP_code': pvp_code,
                'vehicle_class': vehicle_class,
                'transponder': transponder,
                'base_tariff': base_tariff,
                'discount': discount,
                'paid': paid,
                'road': road.strip(),
                'raw_row': raw_trip
            }

        except Exception:
            raise

    @staticmethod
    def _normalize_transponder(transponder: str) -> str:
        """Нормализует номер транспондера"""
        if not transponder:
            return ""

        normalized = transponder.replace('\n', ' ').replace('\r', ' ')
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    @staticmethod
    def _extract_pvp_and_vehicle_class(road: str) -> Tuple[str, Optional[int]]:
        """Извлекает код ПВП и класс транспортного средства из поля road"""
        pvp_code = "unknown"
        vehicle_class = None

        if not road:
            return pvp_code, vehicle_class

        try:
            parts = [part.strip() for part in road.split('\n') if part.strip()]

            if parts:
                pvp_code = parts[0]

            for part in parts[1:]:
                if re.match(r'^\d+$', part):
                    try:
                        vehicle_class = int(part)
                        break
                    except ValueError:
                        continue

            return pvp_code, vehicle_class

        except Exception:
            return "unknown", None

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Парсит дату из строки с русскими месяцами и подставляет год, если его нет."""
        try:
            if not date_str or date_str == 'N/A':
                return None

            original_date_str = date_str.strip()
            month_mapping = {
                'января': 'January', 'февраля': 'February', 'марта': 'March',
                'апреля': 'April', 'мая': 'May', 'июня': 'June',
                'июля': 'July', 'августа': 'August', 'сентября': 'September',
                'октября': 'October', 'ноября': 'November', 'декабря': 'December'
            }
            tmp = original_date_str.lower()

            for ru_month, en_month in month_mapping.items():
                if ru_month in tmp:
                    date_str = tmp.replace(ru_month, en_month)
                    break
            else:
                date_str = original_date_str

            formats_with_year = [
                "%d %B %Y %H:%M",
                "%d.%m.%Y %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%d.%m.%Y",
            ]
            formats_without_year = [
                "%d %B %H:%M",
                "%d %B",
            ]

            for fmt in formats_with_year:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    pass

            for fmt in formats_without_year:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    parsed = parsed.replace(year=datetime.now().year)
                    return parsed
                except ValueError:
                    pass

            return None

        except Exception:
            return None

    @staticmethod
    def _parse_amount(amount_str: str) -> Optional[float]:
        """Парсит денежную сумму"""
        try:
            if not amount_str or amount_str == 'N/A':
                return None
            cleaned = amount_str.replace(' ', '').replace('руб', '').replace(',', '.').replace('₽', '')
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_discount(discount_str: str) -> Optional[int]:
        """Парсит процент скидки"""
        try:
            if not discount_str or discount_str == 'N/A':
                return None
            cleaned = discount_str.replace('%', '').replace(' ', '')
            return int(cleaned)
        except (ValueError, TypeError):
            return None