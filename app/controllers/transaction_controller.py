from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from sqlmodel import select, func
from ..models.transaction import Transaction
from ..database import async_session_maker
from avtodor.app.services.scraper.scraper_service import scraper_service
from ..services.get_date import get_month_range, get_today_range
from datetime import datetime
from ..services.file_import import FileImport

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/info")
async def get_transactions(page: int = 1, page_size: int = 50, transponder: str = Query(default="")):
    offset = (page - 1) * page_size

    async with async_session_maker() as session:
        count_query = select(func.count(Transaction.id_transaction))
        if transponder:
            count_query = count_query.where(Transaction.transponder == transponder)
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        query = select(Transaction).order_by(Transaction.occurred_at.desc())
        if transponder:
            query = query.where(Transaction.transponder == transponder)
        query = query.offset(offset).limit(page_size)
        result = await session.execute(query)
        items = result.scalars().all()
        await session.commit()

    return {
        "total": total,
        "page": page,
        "items": items,
    }

@router.get("/stats")
async def get_transactions_stats():
    async with async_session_maker() as session:
        start, end = get_today_range()
        start_month, end_month = get_month_range()

        query_sum = select(func.sum(Transaction.paid)).where(
            Transaction.occurred_at >= start_month,
            Transaction.occurred_at <= end_month
        )

        query_transaction = select(Transaction).where(
            Transaction.occurred_at >= start,
            Transaction.occurred_at <= end
        )

        query_month = select(Transaction).where(
            Transaction.occurred_at >= start_month,
            Transaction.occurred_at <= end_month
        )

        result_total = await session.execute(select(Transaction))
        result_sum = await session.execute(query_sum)
        result_transaction = await session.execute(query_transaction)
        result_month_transaction = await session.execute(query_month)

        today_transactions = len(result_transaction.all())
        month_transactions = len(result_month_transaction.all())
        total_transactions = len(result_total.all())
        sum_transactions = result_sum.scalar()

        return {
            "month_transactions": month_transactions,
            "today_transactions": today_transactions,
            "total_transactions": total_transactions,
            "sum_transactions": sum_transactions
        }

@router.get("/transponders")
async def get_transponders():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Transaction.transponder)
            .distinct()
            .order_by(Transaction.transponder)
        )
        transponders = [row[0] for row in result]
    return {"items": transponders}

@router.post("/scrape-range")
async def scrape_range(date_from: str = Query(...), date_to: str = Query(...)):
    try:
        start = datetime.fromisoformat(date_from)  # формат YYYY-MM-DD
    except Exception:
        start = datetime.strptime(date_from, "%d.%m.%Y")  # fallback DD.MM.YYYY

    try:
        end = datetime.fromisoformat(date_to)
    except Exception:
        end = datetime.strptime(date_to, "%d.%m.%Y")

    result = await scraper_service.scrape_range(start, end)
    return result

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

@router.post("/import")
async def import_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    saved, total = await FileImport.import_file(ext, file.file)
    return {"saved": saved, "total": total}