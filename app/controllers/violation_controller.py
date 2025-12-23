from fastapi import APIRouter, Query
from sqlmodel import select
from ..database import async_session_maker
from ..models.transaction import Transaction
from ..services.models_service.violation_service import ViolationService

router = APIRouter(prefix="/violations", tags=["Violations"])

@router.get("/info")
async def get_violations(
        page: int = 1,
        page_size: int = 50,
        transponder: str = Query(default=""),
        date_from: str | None = Query(default=None),
        date_to: str | None = Query(default=None)
):
    async with async_session_maker() as session:
        service = ViolationService(session)
        tx_result = await session.execute(select(Transaction))
        transactions = tx_result.scalars().all()
        created = await service.process_transactions(transactions)
        items = await service.get_violations(page, page_size, transponder, date_from, date_to)
    return {
        "total": items["total"],
        "created": created,
        "page": page,
        "items": items["items"],
    }

@router.get("/stats")
async def get_violations_stats():
    async with async_session_maker() as session:
        service = ViolationService(session)
        return await service.get_stats()

@router.get("/transponders")
async def get_transponders():
    async with async_session_maker() as session:
        service = ViolationService(session)
        return {"items": await service.get_transponders()}