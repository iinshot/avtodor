import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class AvtodorScraper:
    """
    Класс, реализующий парсинг данных из личного кабинета Avtodor.
    Требует предварительной авторизации через AvtodorAuth.
    """

    def __init__(self, browser, auth):
        self.browser = browser
        self.auth = auth

    def _scroll_to_load_all(self, pause: float = 0.5, timeout: int = 120):
        start = time.time()
        try:
            container = self.browser.find(By.CSS_SELECTOR, ".el-table.el-table--fit.el-table--enable-row-hover.el-table--enable-row-transition")
        except Exception:
            try:
                container = self.browser.find(By.CSS_SELECTOR, "div.el-table__body-wrapper")
            except Exception:
                container = None
        last_count = -1
        stable = 0
        max_stable = 5
        while True:
            try:
                rows = self.browser.finds(By.CSS_SELECTOR, ".el-table__row")
                count = len(rows)
            except Exception:
                count = 0
            if count == last_count:
                stable += 1
            else:
                stable = 0
            if stable >= max_stable:
                break
            last_count = count
            try:
                if container is not None:
                    self.browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                else:
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except Exception:
                pass
            self.browser.sleep(pause)
            if time.time() - start > timeout:
                break

    def get_balance(self) -> str:
        """
        Возвращает строку с балансом пользователя.
        Требует, чтобы auth.is_authenticated был True.
        """
        if not self.auth.is_authenticated:
            raise RuntimeError("Session is not authenticated")
        self.browser.get("https://lk.avtodor-tr.ru/account")
        try:
            el = self.browser.wait((By.CSS_SELECTOR, "div.green"), timeout=10)
            return el.text.strip()
        except Exception:
            try:
                alt = self.browser.wait((By.CSS_SELECTOR, ".balance, .user-balance"), timeout=5)
                return alt.text.strip()
            except Exception:
                return "N/A"

    def _click_ok_button(self):
        """Кликает кнопку OK в календаре"""
        try:
            calendar = self.browser.wait((By.CSS_SELECTOR, ".el-date-picker, [class*='date-picker']"), timeout=2)
            ok_btn = calendar.find_element(By.XPATH, ".//button[span[text()='OK'] or contains(text(), 'OK')]")
            self.browser.js_click(ok_btn)
        except Exception:
            pass

    def _enter_date(self, element, value: str):
        try:
            self.browser.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()
            self.browser.sleep(0.2)
            element.clear()
            element.send_keys(value)
            element.send_keys(Keys.ENTER)
            self.browser.sleep(0.2)
        except Exception:
            self.browser.execute_script("arguments[0].click();", element)
            self.browser.sleep(0.2)
            element.clear()
            element.send_keys(value)
            self.browser.sleep(0.2)

    def get_trips(self, date_from: str, date_to: str) -> list:
        """
        Возвращает список поездок за диапазон дат date_from..date_to в формате DD.MM.YYYY.
        Требует, чтобы auth.is_authenticated был True.
        """
        if not self.auth.is_authenticated:
            raise RuntimeError("Session is not authenticated")
        try:
            self.browser.get("https://lk.avtodor-tr.ru/account/movement")
            self.browser.sleep(0.5)
            try:
                date_from_input = self.browser.find(By.XPATH,
                                                    "//label[contains(text(),'Дата с')]/following-sibling::div//input")
                date_to_input = self.browser.find(By.XPATH,
                                                  "//label[contains(text(),'Дата по')]/following-sibling::div//input")
            except Exception:
                date_from_input = self.browser.find(By.CSS_SELECTOR,
                                                    "input[name='date_from'], input[data-test='date-from']")
                date_to_input = self.browser.find(By.CSS_SELECTOR,
                                                      "input[name='date_to'], input[data-test='date-to']")

            self._enter_date(date_from_input, date_from)
            time.sleep(0.5)
            self._click_ok_button()
            self._enter_date(date_to_input, date_to)
            time.sleep(0.5)
            self._click_ok_button()
            time.sleep(1)
        except Exception:
            pass
        try:
            self.browser.wait((By.CSS_SELECTOR, ".el-table__row"), timeout=15)
        except Exception:
            self.browser.sleep(0.5)
        self._scroll_to_load_all()
        self.browser.sleep(1)
        try:
            wrapper = self.browser.find(By.CSS_SELECTOR, "div.el-table__body-wrapper")
            rows = wrapper.find_elements(By.CSS_SELECTOR, "tbody tr.el-table__row")
        except Exception:
            rows = self.browser.finds(By.CSS_SELECTOR, ".el-table__row")
        trips = []
        for row in rows:
            try:
                cols = row.find_elements(By.CSS_SELECTOR, "td, .cell")
                def col(i):
                    try:
                        return cols[i].text.strip()
                    except Exception:
                        return "N/A"
                trip = {
                    "road": col(2),
                    "transponder": col(4),
                    "date": col(6),
                    "amount": col(8),
                    "discount": col(10),
                    "paid": col(12),
                }
                if any(v and v != "N/A" for v in trip.values()):
                    trips.append(trip)
            except Exception:
                continue
        return trips