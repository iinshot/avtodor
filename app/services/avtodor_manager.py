import asyncio
import logging
from typing import Dict
from datetime import datetime
from ..services.web_scraper.avtodor_session import avtodor_session
from .avtodor_data import AvtodorData
from .avtodor_db import AvtodorDB
from ..config import settings
from ..services.progress_tracker import progress_tracker
from ..services.web_scraper.browser_manager import browser_manager

logger = logging.getLogger(__name__)

class AvtodorManager:
    def __init__(self):
        self.username = settings.AVTODOR_USERNAME
        self.password = settings.AVTODOR_PASSWORD
        self._is_initialized = False
        self._ensure_credentials()
        self._lock = asyncio.Lock()

    def _ensure_credentials(self):
        if not self.username or not self.password:
            raise Exception("Учетные данные Avtodor не настроены. Проверьте .env файл.")

    async def sync_transactions(self, date_from: datetime, date_to: datetime) -> Dict:
        await progress_tracker.set(0)
        try:
            browser_manager.init()
            await progress_tracker.set(10)
            await progress_tracker.set(20)
            await progress_tracker.set(30)
            await progress_tracker.set(40)
            df_str = date_from.strftime("%d.%m.%Y")
            dt_str = date_to.strftime("%d.%m.%Y")
            scraped_trips = await self._get_trips_data(df_str, dt_str)
            await progress_tracker.set(50)

            start_dt = datetime.combine(date_from.date(), datetime.min.time())
            end_dt = datetime.combine(date_to.date(), datetime.max.time())
            await AvtodorDB.delete_in_range(start_dt, end_dt)
            await progress_tracker.set(60)
            await progress_tracker.set(70)
            await progress_tracker.set(80)
            await progress_tracker.set(90)

            parsed = [AvtodorData.parse_trip_data(t) for t in scraped_trips]
            total = len(parsed)
            saved_count = 0
            batch_size = 20
            for i in range(0, total, batch_size):
                batch = parsed[i:i + batch_size]
                saved = await AvtodorDB.bulk_create_transactions(batch)
                saved_count += saved
                percent = 60 + int((saved_count / total) * 40)
                await progress_tracker.set(percent)

            await progress_tracker.set(100)
            await progress_tracker.set_items(len(scraped_trips))

            return {
                "success": True,
                "scraped_count": len(scraped_trips),
                "saved_count": saved_count,
                "message": f"Обновлено поездок: {saved_count}"
            }

        except Exception as e:
            await progress_tracker.set(0)
            try:
                await asyncio.get_event_loop().run_in_executor(None, avtodor_session.close)
            except Exception:
                pass
            self._is_initialized = False
            logger.exception("Ошибка в sync_transactions")
            raise

    async def _get_trips_data(self, date_from, date_to):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, avtodor_session.get_trips, date_from, date_to)

    async def check_status(self) -> Dict:
        """Проверяет статус менеджера"""
        return {
            "initialized": self._is_initialized,
            "authenticated": avtodor_session.is_authenticated,
            "driver_initialized": avtodor_session.driver is not None,
            "username_configured": bool(self.username),
            "password_configured": bool(self.password)
        }

    async def close(self):
        """Закрывает сессию"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, avtodor_session.close)
        self._is_initialized = False
        logger.info("🔒 Avtodor сессия закрыта")


# Глобальный экземпляр менеджера
avtodor_manager = AvtodorManager()