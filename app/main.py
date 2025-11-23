import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .database import init_db
from .controllers import violation_controller, pvp_controller, transaction_controller
from .services.scraper_service import scraper_service
from .models.transaction import Transaction
from .models.violation import Violation
from sqlmodel import select
from .controllers.transaction_controller import get_today_range
from .database import async_session_maker

if getattr(sys, "frozen", False):
    base_path = Path(sys._MEIPASS) / "app"
else:
    base_path = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(base_path / "templates"))
static_dir = StaticFiles(directory=str(base_path / "static"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)
    await init_db()
    try:
        from .services.avtodor_manager import avtodor_manager
        success = await avtodor_manager.initialize()
        if success:
            print("Avtodor менеджер успешно инициализирован")
        else:
            print("Не удалось инициализировать Avtodor менеджер")
    except Exception as e:
        print(f"Ошибка инициализации Avtodor менеджера: {e}")

    yield

    # Shutdown - закрываем сессию
    try:
        from .services.avtodor_manager import avtodor_manager
        await avtodor_manager.close()
        print("✅ Avtodor сессия закрыта")
    except Exception as e:
        print(f"⚠️ Ошибка при закрытии сессии: {e}")

app = FastAPI(
    title="Autodor Monitor",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=str(base_path / "static")), name="static")

app.include_router(transaction_controller.router)
app.include_router(violation_controller.router)
app.include_router(pvp_controller.router)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/transactions")
async def transactions_page(request: Request):
    transactions = []
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "transactions": transactions
    })

@app.get("/violations")
async def violations_page(request: Request):
    violations = []
    return templates.TemplateResponse("violations.html", {
        "request": request,
        "violations": violations
    })

@app.get("/pvp")
async def pvp_page(request: Request):
    pass

@app.get("/balance")
async def balance_page(request: Request):
    pass

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    async with async_session_maker() as session:
        start, end = get_today_range()
        query_transaction = select(Transaction).where(
            Transaction.occurred_at >= start,
            Transaction.occurred_at <= end
        )
        result_transaction = await session.execute(query_transaction)
        today_transactions = len(result_transaction.all())

        query_violation = select(Violation).where(
            Violation.occurred_at >= start,
            Violation.occurred_at <= end
        )
        result_violation = await session.execute(query_violation)
        today_violations = len(result_violation.all())

        return {
            "balance": "Много денег",
            "today_transactions": today_transactions,
            "today_violations": today_violations,
            "active_pvp": "Наверное есть"
        }

@app.post("/upload")
async def upload_transactions_file(file: UploadFile = File(...)):
    return {"message": "Файл получен", "filename": file.filename}

@app.get("/check-avtodor-auth")
async def check_avtodor_authentication():
    """Проверка учетных данных Avtodor"""
    try:
        is_valid = await scraper_service.check_credentials()
        return {
            "valid": is_valid,
            "username_configured": bool(scraper_service.manager.username),
            "password_configured": bool(scraper_service.manager.password)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))