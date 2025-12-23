from sqlmodel import select, func
from typing import List
from datetime import datetime, date, time
from ...models.transaction import Transaction
from ...services.scraper_service import scraper_service
from ...services.normalize_files import normalize_transponder

class TransactionService:
    def __init__(self, session):
        self.session = session
        self.scraper = scraper_service

    async def get_transactions(
            self,
            page: int = 1,
            page_size: int = 50,
            transponder: str = "",
            date_from: str | None = None,
            date_to: str | None = None,
    ) -> dict:
        date_from = self.parse_date_optional(date_from)
        date_to = self.parse_date_optional(date_to)

        offset = (page - 1) * page_size

        count_query = select(func.count(Transaction.id_transaction))

        if transponder:
            count_query = count_query.where(Transaction.transponder == transponder)

        if date_from:
            count_query = count_query.where(
                Transaction.occurred_at >= datetime.combine(date_from, time.min)
            )

        if date_to:
            count_query = count_query.where(
                Transaction.occurred_at <= datetime.combine(date_to, time.max)
            )

        total = (await self.session.execute(count_query)).scalar()

        query = (
            select(Transaction)
            .order_by(Transaction.occurred_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        if transponder:
            query = query.where(Transaction.transponder == transponder)

        if date_from:
            query = query.where(
                Transaction.occurred_at >= datetime.combine(date_from, time.min)
            )

        if date_to:
            query = query.where(
                Transaction.occurred_at <= datetime.combine(date_to, time.max)
            )

        items = (await self.session.execute(query)).scalars().all()

        return {
            "total": total,
            "page": page,
            "items": items,
        }

    async def get_stats(self, start, end, start_month, end_month):
        sum_query = select(func.sum(Transaction.paid)).where(
            Transaction.occurred_at >= start_month,
            Transaction.occurred_at <= end_month
        )

        today_query = select(Transaction).where(
            Transaction.occurred_at >= start,
            Transaction.occurred_at <= end
        )

        month_query = select(Transaction).where(
            Transaction.occurred_at >= start_month,
            Transaction.occurred_at <= end_month
        )

        today_transactions = len((await self.session.execute(today_query)).all())
        month_transactions = len((await self.session.execute(month_query)).all())
        total_transactions = len((await self.session.execute(select(Transaction))).all())
        sum_transactions = (await self.session.execute(sum_query)).scalar()

        return {
            "month_transactions": month_transactions,
            "today_transactions": today_transactions,
            "total_transactions": total_transactions,
            "sum_transactions": sum_transactions
        }

    async def get_transponders(self) -> List[str]:
        query = (
            select(Transaction.transponder)
            .distinct()
            .order_by(Transaction.transponder)
        )

        rows = await self.session.execute(query)
        transponders = []
        for row in rows:
            if row[0]:
                transponders.append(normalize_transponder(str(row[0])))

        return sorted(transponders)

    @staticmethod
    def parse_date_optional(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return datetime.strptime(value, "%d.%m.%Y").date()

    @staticmethod
    def parse_date_required(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.strptime(value, "%d.%m.%Y")

    async def scrape_between(self, date_from: str, date_to: str):
        start = self.parse_date_required(date_from)
        end = self.parse_date_required(date_to)
        return await self.scraper.scrape_range(start, end)