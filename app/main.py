import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sys
from .database import init_db
from .controllers import transaction_controller
from .controllers import violation_controller
from .controllers import pvp_controller

if getattr(sys, "frozen", False):
    base_path = Path(sys._MEIPASS) / "app"
else:
    base_path = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(base_path / "templates"))
static_dir = StaticFiles(directory=str(base_path / "static"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - выполняется при запуске приложения
    os.makedirs("data", exist_ok=True)
    await init_db()
    yield
    # Shutdown - выполняется при остановке приложения

app = FastAPI(
    title="Autodor Monitor",
    lifespan=lifespan
)

app.include_router(transaction_controller.router)
app.include_router(violation_controller.router)
app.include_router(pvp_controller.router)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/transactions")
async def transactions_page(request: Request):
    # Здесь будет логика получения транзакций из БД
    transactions = []  # Заглушка
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "transactions": transactions
    })

@app.get("/violations")
async def violations_page(request: Request):
    # Здесь будет логика получения нарушений из БД
    violations = []  # Заглушка
    return templates.TemplateResponse("violations.html", {
        "request": request,
        "violations": violations,
        "total_violations": len(violations),
        "total_amount": sum(v.base_tariff for v in violations),
        "affected_pvp_count": len(set(v.PVP_code for v in violations))
    })

@app.get("/pvp")
async def pvp_page(request: Request):
    return templates.TemplateResponse("pvp.html", {"request": request})

@app.get("/balance")
async def balance_page(request: Request):
    return templates.TemplateResponse("balance.html", {"request": request})

# API endpoints для фронтенда
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    return {
        "balance": 45000,
        "today_transactions": 15,
        "today_violations": 3,
        "active_pvp": 8
    }

@app.get("/violations")
async def get_recent_violations():
    return [
        {
            "transponder": "TP123456",
            "PVP_code": "1223",
            "occurred_at": "2024-01-15 10:30:00",
            "base_tariff": 250
        }
    ]

@app.post("/api/transactions/upload")
async def upload_transactions_file(file: UploadFile = File(...)):
    # Логика обработки загруженного файла
    return {"message": "Файл получен", "filename": file.filename}