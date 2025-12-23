from ...config import settings
from ...services.web_scraper.browser_manager import BrowserManager
from ...services.web_scraper.avtodor_auth import AvtodorAuth
from ...services.web_scraper.avtodor_scraper import AvtodorScraper

class AvtodorSession:
    """
    Фасад для работы с Avtodor: управляет браузером, авторизацией и скрапингом.
    """

    def __init__(self):
        self.browser = BrowserManager()
        self.auth = AvtodorAuth(self.browser)
        self.scraper = AvtodorScraper(self.browser, self.auth)

    def initialize(self, headless: bool = True) -> bool:
        """
        Инициализирует браузер и пытается выполнить авторизацию по настройкам.
        Возвращает True при успешной авторизации.
        """
        try:
            self.browser.init(headless=headless)
            return self.auth.login(settings.AVTODOR_USERNAME, settings.AVTODOR_PASSWORD)
        except Exception:
            return False

    def login(self, username: str, password: str) -> bool:
        """
        Выполняет авторизацию с переданными учетными данными.
        """
        return self.auth.login(username, password)

    def is_authenticated(self) -> bool:
        """
        Возвращает True, если сессия авторизована.
        """
        return bool(self.auth.is_authenticated)

    def get_balance(self) -> str:
        """
        Возвращает баланс пользователя.
        """
        return self.scraper.get_balance()

    def has_balance(self) -> bool:
        """
        Проверяет, можно ли получить баланс пользователя.
        Возвращает True, если баланс успешно получен, иначе False.
        """
        try:
            balance = self.get_balance()
            return bool(balance and balance != "N/A")
        except Exception:
            return False

    def get_trips(self, date_from: str, date_to: str) -> list:
        """
        Возвращает список поездок за указанный диапазон дат.
        """
        return self.scraper.get_trips(date_from, date_to)

    def close(self):
        """
        Закрывает браузер и завершает сессию.
        """
        try:
            self.auth.logout()
        except Exception:
            try:
                self.browser.close()
            except Exception:
                pass


avtodor_session = AvtodorSession()
