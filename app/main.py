import os
import sys
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select, func
from .database import init_db
from .controllers import violation_controller, transaction_controller
from .services.web_scraper.avtodor_session import avtodor_session
from .models.transaction import Transaction
from .models.violation import Violation
from .services.get_date import get_month_range, get_today_range
from .database import async_session_maker
from .config import settings
from .services.avtodor_manager import avtodor_manager
from .services.web_scraper.browser_manager import browser_manager

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
    async def init_avtodor():
        await asyncio.sleep(1)
        try:
            success = await browser_manager.init()
            if success:
                print("Avtodor менеджер успешно инициализирован")
            else:
                print("Не удалось инициализировать Avtodor менеджер")
        except Exception as e:
            print(f"Ошибка инициализации Avtodor менеджера: {e}")

    yield

    asyncio.create_task(init_avtodor())

    try:
        await browser_manager.close()
        print("Avtodor сессия закрыта")
    except Exception as e:
        print(f"Ошибка при закрытии сессии: {e}")

app = FastAPI(
    title="Autodor Monitor",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=str(base_path / "static")), name="static")

app.include_router(transaction_controller.router)
app.include_router(violation_controller.router)

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

@app.get("/stats")
async def get_dashboard_stats():
    async with async_session_maker() as session:
        start, end = get_today_range()
        start_month, end_month = get_month_range()

        today_violations = await session.scalar(
            select(func.count(Violation.id_transaction)).where(
                Violation.occurred_at >= start,
                Violation.occurred_at <= end
            )
        )

        month_violations = await session.scalar(
            select(func.count(Violation.id_transaction)).where(
                Violation.occurred_at >= start_month,
                Violation.occurred_at <= end_month
            )
        )

        today_transactions = await session.scalar(
            select(func.count(Transaction.id_transaction)).where(
                Transaction.occurred_at >= start,
                Transaction.occurred_at <= end
            )
        )

        month_transactions = await session.scalar(
            select(func.count(Transaction.id_transaction)).where(
                Transaction.occurred_at >= start_month,
                Transaction.occurred_at <= end_month
            )
        )

        return {
            "month_transactions": month_transactions,
            "today_transactions": today_transactions,
            "today_violations": today_violations,
            "month_violations": month_violations
        }

@app.get("/check-avtodor-auth")
async def check_avtodor_authentication():
    try:
        def ensure_authenticated():
            if not avtodor_session.is_authenticated():
                return browser_manager.init(headless=True)
            return True
        valid = await asyncio.to_thread(ensure_authenticated)
        return {"valid": valid}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/balance")
async def get_balance():
    try:
        if not avtodor_session.is_authenticated():
            success = await asyncio.to_thread(
                avtodor_session.login,
                settings.AVTODOR_USERNAME,
                settings.AVTODOR_PASSWORD
            )
            if not success:
                raise HTTPException(401, "Failed to authenticate")
        valid = await asyncio.to_thread(
            avtodor_session.has_balance
        )
        balance = await asyncio.to_thread(avtodor_session.get_balance)
        return {
            "balance": balance,
            "valid": valid,
        }

    except Exception as e:
        raise HTTPException(500, f"Error getting balance: {e}")
