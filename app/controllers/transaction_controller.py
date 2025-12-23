from fastapi import APIRouter, HTTPException, Query, UploadFile, File
import asyncio
from ..database import async_session_maker
from ..services.scraper_service import scraper_service
from ..services.get_date import get_month_range, get_today_range
from ..services.file_import import FileImport
from ..services.models_service.transaction_service import TransactionService
from ..services.progress_tracker import progress_tracker

router = APIRouter(prefix="/transactions", tags=["Transactions"])

async def run_scrape_range(date_from, date_to):
    async with async_session_maker() as session:
        service = TransactionService(session)
        await service.scrape_between(date_from, date_to)

@router.get("/info")
async def get_transactions(
        page: int = 1,
        page_size: int = 50,
        transponder: str = Query(default=""),
        date_from: str | None = Query(default=None),
        date_to: str | None = Query(default=None)
):
    async with async_session_maker() as session:
        service = TransactionService(session)
        return await service.get_transactions(
            page=page,
            page_size=page_size,
            transponder=transponder,
            date_from=date_from,
            date_to=date_to
        )

@router.get("/stats")
async def get_transactions_stats():
    async with async_session_maker() as session:
        service = TransactionService(session)
        start, end = get_today_range()
        start_month, end_month = get_month_range()
        return await service.get_stats(start, end, start_month, end_month)

@router.get("/transponders")
async def get_transponders():
    async with async_session_maker() as session:
        service = TransactionService(session)
        return {"items": await service.get_transponders()}

@router.post("/scrape-range")
async def scrape_range(date_from: str = Query(...), date_to: str = Query(...)):
    asyncio.create_task(run_scrape_range(date_from, date_to))
    return {"status": "started"}

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

@router.get("/progress")
async def get_scrape_progress():
    return await progress_tracker.get()