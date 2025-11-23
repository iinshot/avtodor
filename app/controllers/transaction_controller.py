from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlmodel import select, func
from ..models.transaction import Transaction
from ..database import async_session_maker
from ..services.scraper_service import scraper_service
from datetime import datetime, time, date

router = APIRouter(prefix="/transactions", tags=["Transactions"])

def get_today_range():
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    return start, end

@router.get("/info")
async def get_transactions(page: int = 1, page_size: int = 50):
    offset = (page - 1) * page_size
    async with async_session_maker() as session:
        count_result = await session.execute(
            select(func.count(Transaction.id_transaction))
        )
        total = count_result.scalar()
        result = await session.execute(
            select(Transaction)
            .order_by(Transaction.occurred_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "items": items,
    }

@router.get("/stats")
async def get_transactions_stats():
    async with async_session_maker() as session:
        total_count = await session.execute(select(func.count(Transaction.id_transaction)))
        total = total_count.scalar()
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = await session.execute(
            select(func.count(Transaction.id_transaction))
            .where(Transaction.occurred_at >= today_start)
        )
        today = today_count.scalar()
        today_paid = await session.execute(
            select(func.sum(Transaction.paid))
            .where(Transaction.occurred_at >= today_start)
        )
        today_total_paid = today_paid.scalar() or 0
    return {
        "total_transactions": total,
        "today_transactions": today,
        "today_total_paid": today_total_paid
    }

@router.post("/scrape-avtodor")
async def scrape_avtodor_transactions(background_tasks: BackgroundTasks):
    try:
        result = await scraper_service.scrape_and_save_trips()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при получении данных из Avtodor: {str(e)}"
        )

@router.post("/scrape-avtodor-background")
async def scrape_avtodor_background(background_tasks: BackgroundTasks):
    """Запуск парсера в фоновом режиме"""
    background_tasks.add_task(scraper_service.scrape_and_save_trips)
    return {"message": "Парсинг данных Avtodor запущен в фоновом режиме"}

@router.get("/session-status")
async def get_session_status():
    """Получение статуса текущей сессии"""
    try:
        status = await scraper_service.get_session_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-session")
async def reset_session():
    """Сброс текущей сессии"""
    try:
        await scraper_service.reset_session()
        return {"message": "Сессия сброшена"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))