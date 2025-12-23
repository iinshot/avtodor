from typing import List, Dict, Optional
from datetime import datetime
from sqlmodel import select, delete, tuple_, and_
from ..models.transaction import Transaction
from ..database import async_session_maker

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
                if existing:
                    return existing
                session.add(transaction)
                await session.commit()
                await session.refresh(transaction)
                return transaction
        except Exception:
            await session.rollback()
            return None

    @staticmethod
    async def bulk_create_transactions(transactions_data: List[Dict]) -> int:
        """Массовое создание транзакций с проверкой дубликатов батчем"""
        if not transactions_data:
            return 0

        async with async_session_maker() as session:
            # 1. Получаем ключи всех новых транзакций
            new_keys = [
                (t["transponder"], t["occurred_at"], t["PVP_code"])
                for t in transactions_data
            ]

            # 2. Выбираем уже существующие транзакции по этим ключам
            stmt = select(Transaction.transponder, Transaction.occurred_at, Transaction.PVP_code).where(
                tuple_(Transaction.transponder, Transaction.occurred_at, Transaction.PVP_code).in_(new_keys)
            )
            result = await session.execute(stmt)
            existing_keys = set(result.all())

            # 3. Фильтруем только новые транзакции
            to_insert = [
                Transaction(**t)
                for t, key in zip(transactions_data, new_keys)
                if key not in existing_keys
            ]

            # 4. Добавляем батчем
            session.add_all(to_insert)
            await session.commit()

        return len(to_insert)

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
            and_(
                Transaction.transponder == transponder,
                Transaction.occurred_at == occurred_at,
                Transaction.PVP_code == pvp_code
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def delete_in_range(date_from: datetime, date_to: datetime):
        async with async_session_maker() as session:
            stmt = delete(Transaction).where(
                Transaction.occurred_at >= date_from,
                Transaction.occurred_at <= date_to
            )
            await session.execute(stmt)
            await session.commit()
