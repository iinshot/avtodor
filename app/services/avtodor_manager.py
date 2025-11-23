import asyncio
import logging
from typing import List, Dict
from .avtodor_session import avtodor_session
from .avtodor_data import AvtodorData
from .avtodor_db import AvtodorDB
from ..config import settings

logger = logging.getLogger(__name__)

class AvtodorManager:
    """Менеджер для работы с Avtodor API"""

    def __init__(self):
        self.username = settings.AVTODOR_USERNAME
        self.password = settings.AVTODOR_PASSWORD
        self._is_initialized = False
        self._ensure_credentials()

    def _ensure_credentials(self):
        """Проверяет наличие учетных данных"""
        if not self.username or not self.password:
            raise Exception("Учетные данные Avtodor не настроены. Проверьте .env файл.")

    async def initialize(self) -> bool:
        """Инициализация менеджера"""
        if self._is_initialized:
            return True

        try:
            logger.info("Инициализация Avtodor менеджера...")

            # Инициализируем драйвер
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, avtodor_session.init_driver)

            # Выполняем авторизацию
            login_success = await loop.run_in_executor(
                None, avtodor_session.login, self.username, self.password
            )

            if login_success:
                self._is_initialized = True
                logger.info("✅ Avtodor менеджер успешно инициализирован")
                return True
            else:
                logger.error("❌ Не удалось выполнить авторизацию при инициализации")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Avtodor менеджера: {e}")
            return False

    async def sync_transactions(self) -> Dict:
        """Синхронизирует транзакции с Avtodor"""
        try:
            # Проверяем инициализацию
            if not await self._ensure_initialized():
                raise Exception("Не удалось инициализировать Avtodor менеджер")

            # Получаем данные
            scraped_trips = await self._get_trips_data()

            if not scraped_trips:
                logger.warning("Не получено данных о поездках")
                return {
                    "success": True,
                    "scraped_count": 0,
                    "saved_count": 0,
                    "message": "Нет новых данных для синхронизации"
                }

            # Парсим и сохраняем данные
            parsed_transactions = [
                AvtodorData.parse_trip_data(trip)
                for trip in scraped_trips
            ]

            saved_count = await AvtodorDB.bulk_create_transactions(parsed_transactions)

            return {
                "success": True,
                "scraped_count": len(scraped_trips),
                "saved_count": saved_count,
                "message": f"Синхронизировано {len(scraped_trips)} поездок, сохранено {saved_count} новых"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка при синхронизации транзакций: {e}")
            self._is_initialized = False
            raise

    async def _ensure_initialized(self) -> bool:
        """Проверяет и восстанавливает инициализацию при необходимости"""
        if self._is_initialized and avtodor_session.is_authenticated:
            return True

        if not self._is_initialized:
            return await self.initialize()

        # Сессия неактивна, пытаемся восстановить
        logger.info("Сессия неактивна, пытаемся восстановить...")
        loop = asyncio.get_event_loop()
        login_success = await loop.run_in_executor(
            None, avtodor_session.login, self.username, self.password
        )

        return login_success

    async def _get_trips_data(self) -> List[Dict]:
        """Получает данные о поездках"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, avtodor_session.get_trips)

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