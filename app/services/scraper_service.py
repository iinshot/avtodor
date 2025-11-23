from .avtodor_manager import avtodor_manager

class ScraperService:
    def __init__(self):
        self.manager = avtodor_manager

    async def scrape_and_save_trips(self) -> dict:
        """Получает данные используя глобальный менеджер"""
        try:
            result = await self.manager.sync_transactions()
            return result
        except Exception as e:
            await self.manager.close()
            await self.manager.initialize()
            raise Exception(f"Ошибка при получении данных из Avtodor: {str(e)}")

    async def check_credentials(self) -> bool:
        """Проверяет статус менеджера"""
        try:
            status = await self.manager.check_status()
            is_ready = status["initialized"] and status["authenticated"]
            if not is_ready:
                is_ready = await self.manager.initialize()
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
        await self.manager.close()
        await self.manager.initialize()

scraper_service = ScraperService()