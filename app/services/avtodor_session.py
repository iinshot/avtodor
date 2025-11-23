import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LOGIN_URL = os.getenv("LOGIN_URL")

class AvtodorSession:
    def __init__(self):
        self.driver = None
        self.is_authenticated = False
        self.username = None
        self.password = None

    def __del__(self):
        """Деструктор - закрывает браузер при удалении объекта"""
        self.close()

    def init_driver(self):
        """Инициализация драйвера браузера"""
        if self.driver is not None:
            return

        options = Options()
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def login(self, username: str, password: str) -> bool:
        """Выполняет авторизацию один раз"""
        try:
            self.init_driver()
            self.username = username
            self.password = password

            wait = WebDriverWait(self.driver, 20)

            if self.is_authenticated:
                if self._check_session_active():
                    return True

            self.driver.get(LOGIN_URL)
            wait.until(EC.presence_of_element_located((By.ID, "username")))
            self.driver.find_element(By.ID, "username").send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys(password)
            login_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'], button[type='submit']"))
            )
            login_button.click()
            wait.until(EC.url_contains("lk.avtodor-tr.ru"))
            time.sleep(2)

            if self._check_auth_success():
                self.is_authenticated = True
                return True
            else:
                return False

        except Exception:
            self.is_authenticated = False
            return False

    def get_trips(self) -> list:
        """Получает данные о поездках используя существующую сессию"""
        if not self.is_authenticated or self.driver is None:
            raise Exception("Сессия не активна. Сначала выполните авторизацию.")

        try:
            wait = WebDriverWait(self.driver, 20)
            self.driver.get("https://lk.avtodor-tr.ru/account/movement")
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".el-table__row, .table, table, [class*='table'], [class*='row']"))
            )
            time.sleep(3)
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".el-table__row, tr[class*='row'], tbody tr")

            if not rows:
                return []

            trips = []

            for row in rows:
                cols = row.find_elements(By.CSS_SELECTOR, "td, .cell")

                if len(cols) < 7:
                    continue

                trip = {
                    "road": cols[2].text.strip() if len(cols) > 1 else "N/A",
                    "transponder": cols[4].text.strip() if len(cols) > 2 else "N/A",
                    "date": cols[6].text.strip() if len(cols) > 3 else "N/A",
                    "amount": cols[8].text.strip() if len(cols) > 4 else "N/A",
                    "discount": cols[10].text.strip() if len(cols) > 5 else "N/A",
                    "paid": cols[12].text.strip() if len(cols) > 6 else "N/A",
                }

                if any(trip.values()):
                    trips.append(trip)
            return trips

        except Exception:
            self.is_authenticated = False
            raise

    def close(self):
        """Закрывает браузер"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.is_authenticated = False

    def _check_session_active(self) -> bool:
        """Проверяет, активна ли текущая сессия"""
        try:
            self.driver.get("https://lk.avtodor-tr.ru/account/movement")
            return "lk.avtodor-tr.ru" in self.driver.current_url and "auth" not in self.driver.current_url
        except Exception:
            return False

    def _check_auth_success(self) -> bool:
        """Проверяет успешность авторизации"""
        try:
            self.driver.get("https://lk.avtodor-tr.ru/account/movement")
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__row, tr[class*='row'], tbody tr")))
            return True
        except Exception:
            return False

avtodor_session = AvtodorSession()