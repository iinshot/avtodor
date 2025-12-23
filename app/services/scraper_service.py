from ..services.web_scraper.browser_manager import browser_manager
from ..services.avtodor_manager import avtodor_manager
from datetime import datetime

class ScraperService:
    def __init__(self):
        self.manager = avtodor_manager
        self.browser = browser_manager

    async def scrape_range(self, date_from: datetime, date_to: datetime) -> dict:
        try:
            result = await self.manager.sync_transactions(date_from, date_to)
            return result
        except Exception as e:
            raise Exception(f"Ошибка при обновлении данных за диапазон: {e}")

    async def check_credentials(self) -> bool:
        """Проверяет статус менеджера"""
        try:
            status = await self.manager.check_status()
            is_ready = status["initialized"] and status["authenticated"]
            if not is_ready:
                is_ready = await self.browser.init
            return is_ready
        except Exception:
            return False

    async def get_session_status(self) -> dict:
        """Возвращает статус сессии"""
        try:
            return await self.manager.check_status()
        except Exception:
            return {
                "initialized": False,
                "authenticated": False,
                "driver_initialized": False,
                "username_configured": False,
                "password_configured": False
            }

    async def reset_session(self):
        """Сбрасывает сессию"""
        await self.browser.close
        await self.browser.init

scraper_service = ScraperService()