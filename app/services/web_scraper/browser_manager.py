import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class BrowserManager:
    """
    Менеджер браузерного драйвера Selenium.
    Отвечает за инициализацию, закрытие и базовые утилиты для работы с драйвером.
    """

    def __init__(self):
        self._driver = None
        self._lock = threading.RLock()

    @property
    def driver(self):
        """
        Возвращает экземпляр webdriver или None, если он не инициализирован.
        """
        return self._driver

    def init(self, headless: bool = False, window_size: str = "1366,768"):
        """
        Инициализирует Chrome WebDriver (если ещё не инициализирован).
        """
        with self._lock:
            if self._driver is not None:
                return
            options = Options()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument(f"--window-size={window_size}")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=options)
            self._driver.implicitly_wait(2)

    def close(self):
        """
        Закрывает браузер и освобождает ресурсы.
        """
        with self._lock:
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
                self._driver = None

    def get(self, url: str):
        """
        Открывает URL в браузере.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        self._driver.get(url)

    def wait(self, selector: tuple, timeout: int = 20):
        """
        Ожидает присутствие элемента, возвращает WebElement.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        wait = WebDriverWait(self._driver, timeout)
        return wait.until(EC.presence_of_element_located(selector))

    def wait_clickable(self, selector: tuple, timeout: int = 20):
        """
        Ожидает, что элемент станет кликабельным, возвращает WebElement.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        wait = WebDriverWait(self._driver, timeout)
        return wait.until(EC.element_to_be_clickable(selector))

    def find(self, by, value):
        """
        Находит первый элемент по селектору.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        return self._driver.find_element(by, value)

    def finds(self, by, value):
        """
        Находит все элементы по селектору.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        return self._driver.find_elements(by, value)

    def scroll_to_bottom(self):
        """
        Скроллит страницу вниз.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def js_click(self, element):
        """
        Выполняет клик по элементу через JavaScript.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        self._driver.execute_script("arguments[0].click();", element)

    def execute_script(self, script: str, *args):
        """
        Выполняет произвольный JS-скрипт и возвращает результат.
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized")
        return self._driver.execute_script(script, *args)

    @staticmethod
    def sleep(seconds: float):
        """
        Безопасная пауза (обёртка над time.sleep).
        """
        time.sleep(seconds)

browser_manager = BrowserManager()