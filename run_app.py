import os
import sys
import webbrowser
import time
from tkinter import Tk, filedialog
import threading
import uvicorn
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = Path("config_path.txt")

if getattr(sys, "frozen", False):
    BASE_PATH = Path(sys._MEIPASS)
else:
    BASE_PATH = CURRENT_DIR
APP_PATH = BASE_PATH / "app"
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

def choose_data_dir_once():
    """Выбирает папку, если путь не сохранён ранее"""
    if CONFIG_FILE.exists():
        saved_path = CONFIG_FILE.read_text(encoding="utf-8").strip()
        if os.path.exists(saved_path):
            return saved_path

    Tk().withdraw()
    folder = filedialog.askdirectory(title="Выберите папку для хранения данных")
    if not folder:
        sys.exit(0)
    CONFIG_FILE.write_text(folder, encoding="utf-8")
    os.makedirs(os.path.join(folder, "data"), exist_ok=True)
    return folder

def update_env_path(data_dir):
    """Создаёт .env с настройками в выбранной пользователем папке"""
    env_path = os.path.join(data_dir, ".env")
    os.environ["ENV_FILE_PATH"] = env_path
    return env_path

def run_server_in_thread(data_dir):
    """Запускает uvicorn в отдельном потоке"""

    def start():
        try:
            env_path = os.path.join(data_dir, ".env")
            os.environ["ENV_FILE_PATH"] = env_path
            from app.main import app
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=8000,
                reload=False,
                log_level="info",
            )
        except Exception as e:
            print(f"Ошибка при запуске сервера: {e}")
            import traceback
            traceback.print_exc()

    thread = threading.Thread(target=start, daemon=True)
    thread.start()

def main():
    data_dir = choose_data_dir_once()
    update_env_path(data_dir)
    os.environ["ENV_FILE"] = os.path.join(data_dir, ".env")
    run_server_in_thread(data_dir)
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")
    print("Приложение запущено")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()