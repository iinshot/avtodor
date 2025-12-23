from selenium.webdriver.common.by import By
from ...config import settings

class AvtodorAuth:
    """
    Класс, реализующий логику авторизации в личном кабинете Avtodor.
    Для работы использует объект browser с методами BrowserManager.
    """

    def __init__(self, browser):
        self.browser = browser
        self.is_authenticated = False
        self._username = None

    def login(self, username: str, password: str, retries: int = 2) -> bool:
        """
        Выполняет авторизацию с заданными учетными данными.
        Возвращает True при успешной авторизации, иначе False.
        """
        last_exc = None
        for _ in range(retries):
            try:
                self.browser.init()
                self._username = username
                self.browser.get(settings.LOGIN_URL)
                self.browser.sleep(1)
                username_selectors = [
                    (By.ID, "username"),
                    (By.NAME, "username"),
                    (By.CSS_SELECTOR, "input[type='email']"),
                    (By.CSS_SELECTOR, "input[placeholder*='Логин']"),
                    (By.CSS_SELECTOR, "input[placeholder*='Email']")
                ]
                password_selectors = [
                    (By.ID, "password"),
                    (By.NAME, "password"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                    (By.CSS_SELECTOR, "input[placeholder*='Пароль']")
                ]
                username_input = None
                password_input = None
                for sel in username_selectors:
                    try:
                        username_input = self.browser.wait(sel, timeout=6)
                        if username_input:
                            break
                    except Exception:
                        continue
                for sel in password_selectors:
                    try:
                        password_input = self.browser.wait(sel, timeout=6)
                        if password_input:
                            break
                    except Exception:
                        continue
                if username_input is None or password_input is None:
                    raise RuntimeError("Login fields not found")
                username_input.clear()
                username_input.send_keys(username)
                password_input.clear()
                password_input.send_keys(password)
                try:
                    submit = self.browser.find("css selector", "button[type='submit'], input[type='submit']")
                    self.browser.wait_clickable(("css selector", "button[type='submit'], input[type='submit']"), timeout=6)
                except Exception:
                    submit = None
                    try:
                        buttons = self.browser.finds("tag name", "button")
                        for b in buttons:
                            txt = (b.text or "").strip().lower()
                            if "войти" in txt or "вход" in txt or "login" in txt:
                                submit = b
                                break
                    except Exception:
                        submit = None
                if submit is None:
                    raise RuntimeError("Submit element not found")
                try:
                    self.browser.js_click(submit)
                except Exception:
                    submit.click()
                self.browser.sleep(1)
                if self.check_session_active():
                    self.is_authenticated = True
                    return True
                else:
                    raise RuntimeError("Session not active after login")
            except Exception as exc:
                last_exc = exc
                try:
                    self.browser.close()
                except Exception:
                    pass
                self.browser.sleep(1)
        self.is_authenticated = False
        raise last_exc if last_exc is not None else RuntimeError("Login failed")

    def check_session_active(self) -> bool:
        """
        Проверяет активность текущей сессии, возвращает True если сессия активна.
        """
        try:
            self.browser.get("https://lk.avtodor-tr.ru/account/movement")
            self.browser.sleep(0.5)
            current = self.browser.driver.current_url
            return "lk.avtodor-tr.ru" in current and "auth" not in current
        except Exception:
            return False

    def logout(self):
        """
        Закрывает браузер и сбрасывает состояние авторизации.
        """
        self.browser.close()
        self.is_authenticated = False
        self._username = None
