# app/services/transaction_service.py
import logging
from typing import List, Dict, Optional
from sqlmodel import select
from ..models.transaction import Transaction
from ..database import async_session_maker
from datetime import datetime

class AvtodorDB:
    @staticmethod
    async def create_transaction(transaction_data: Dict) -> Optional[Transaction]:
        """Создает новую транзакцию"""
        try:
            async with async_session_maker() as session:
                transaction = Transaction(**transaction_data)
                existing = await AvtodorDB._find_duplicate(
                    session,
                    transaction.transponder,
                    transaction.occurred_at,
                    transaction.PVP_code
                )
                session.add(transaction)
                await session.commit()
                await session.refresh(transaction)
                return transaction
        except Exception:
            await session.rollback()
            return None

    @staticmethod
    async def bulk_create_transactions(transactions_data: List[Dict]) -> int:
        """Массовое создание транзакций"""
        if not transactions_data:
            return 0

        saved_count = 0
        async with async_session_maker() as session:
            for data in transactions_data:
                transaction = Transaction(**data)
                existing = await AvtodorDB._find_duplicate(
                    session,
                    transaction.transponder,
                    transaction.occurred_at,
                    transaction.PVP_code
                )
                if not existing:
                    session.add(transaction)
                    saved_count += 1
            await session.commit()
        return saved_count

    @staticmethod
    async def get_all_transactions() -> List[Transaction]:
        """Получает все транзакции"""
        async with async_session_maker() as session:
            stmt = select(Transaction).order_by(Transaction.occurred_at.desc())
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_transactions_count() -> int:
        """Возвращает количество транзакций"""
        async with async_session_maker() as session:
            stmt = select(Transaction)
            result = await session.execute(stmt)
            return len(result.scalars().all())

    @staticmethod
    async def _find_duplicate(session, transponder: str, occurred_at: datetime, pvp_code: str) -> Optional[Transaction]:
        """Ищет дубликат транзакции"""
        stmt = select(Transaction).where(
            Transaction.transponder == transponder,
            Transaction.occurred_at == occurred_at,
            Transaction.PVP_code == pvp_code
        )
        result = await session.execute(stmt)
        return result.scalars().first()