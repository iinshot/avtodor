import re
from typing import Optional
from sqlmodel import select, func
from datetime import datetime, date, time
from ...models.violation import Violation
from ...models.transaction import Transaction
from ...services.get_date import get_month_range, get_today_range

class ViolationService:
    FORBIDDEN_FULL = [
        "М4-1046км-Москва", "М4-1046км-Мск",
        "М4-1184-Мск", "М4-1184-Москва",
        "М4-1223-Мск", "М4-1223-Москва",
        "М4-1223-Крс", "М4-1223-Краснодар",
        "М4-1184-Крс", "М4-1184-Краснодар",
        "М4-1046км-Краснодар", "М4-1046км-Крс",
        "М4-1046км-Ростов", "М4-1046км-Рос",
        "М4-1184-Ростов", "М4-1184-Рос",
        "М4-1223-Ростов", "М4-1223-Рос",
        "М4-1223-Воронеж", "М4-1223-Вор",
        "М4-1184-Воронеж", "М4-1184-Вор",
        "М4-1046км-Воронеж", "М4-1046км-Вор",
    ]

    PVP_636_PATTERN = re.compile(r"м4[-\s]*636", re.IGNORECASE)

    def __init__(self, session):
        self.session = session
        self.NORMALIZED_FORBIDDEN = {self.normalize_pvp(x) for x in self.FORBIDDEN_FULL}

    @staticmethod
    def normalize_pvp(pvp: str) -> str:
        """Приводит ПВП к единому виду для точного сравнения."""
        pvp = pvp.lower().strip()
        pvp = re.sub(r"\s*-\s*", "-", pvp)
        pvp = re.sub(r"(км|km)", "", pvp)
        pvp = re.sub(r"-+", "-", pvp)
        pvp = pvp.strip("-")
        return pvp

    async def detect_violation(self, transaction) -> Optional[Violation]:
        """Проверка транзакции на нарушение."""
        if not transaction.PVP_code or not transaction.occurred_at:
            return None

        pvp_norm = self.normalize_pvp(transaction.PVP_code)

        if self.PVP_636_PATTERN.search(pvp_norm):
            return Violation(
                id_transaction=transaction.id_transaction,
                transponder=transaction.transponder,
                occurred_at=transaction.occurred_at,
                PVP_code=transaction.PVP_code,
                base_tariff=transaction.base_tariff,
                reason="Проезд через ПВП 636 км"
            )

        if pvp_norm in self.NORMALIZED_FORBIDDEN:
            return Violation(
                id_transaction=transaction.id_transaction,
                transponder=transaction.transponder,
                occurred_at=transaction.occurred_at,
                PVP_code=transaction.PVP_code,
                base_tariff=transaction.base_tariff,
                reason="Запрещённый пункт ПВП"
            )

        return None

    async def process_transactions(self, transactions: list[Transaction]):
        created = 0
        existing_result = await self.session.execute(select(Violation.id_transaction))
        existing_ids = {row[0] for row in existing_result.all()}

        for tx in transactions:
            if tx.id_transaction in existing_ids:
                continue
            violation = await self.detect_violation(tx)
            if violation:
                self.session.add(violation)
                created += 1
        await self.session.commit()
        return created

    async def get_violations(
            self,
            page: int,
            page_size: int,
            transponder: str = "",
            date_from: str | None = None,
            date_to: str | None = None,
    ):
        date_from = self.parse_date_optional(date_from)
        date_to = self.parse_date_optional(date_to)
        offset = (page - 1) * page_size

        base_query = (
            select(Violation)
            .join(Transaction, Transaction.id_transaction == Violation.id_transaction)
        )

        if transponder:
            base_query = base_query.where(Violation.transponder == transponder)

        if date_from:
            base_query = base_query.where(Violation.occurred_at >= datetime.combine(date_from, time.min))

        if date_to:
            base_query = base_query.where(Violation.occurred_at <= datetime.combine(date_to, time.max))

        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.session.execute(count_query)).scalar()

        query = (
            select(Violation, Transaction.discount, Transaction.paid)
            .join(Transaction, Transaction.id_transaction == Violation.id_transaction)
        )

        if transponder:
            query = query.where(Violation.transponder == transponder)

        if date_from:
            query = query.where(Violation.occurred_at >= datetime.combine(date_from, time.min))

        if date_to:
            query = query.where(Violation.occurred_at <= datetime.combine(date_to, time.max))

        query = (
            query
            .order_by(Violation.occurred_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(query)

        items = []
        for violation, discount, paid in result.all():
            v = violation.__dict__.copy()
            v["discount"] = discount
            v["paid"] = paid
            items.append(v)

        return {
            "items": items,
            "total": total,
        }

    async def get_stats(self):
        start, end = get_today_range()
        start_month, end_month = get_month_range()

        query_sum = (
            select(func.sum(Transaction.paid))
            .select_from(Violation)
            .join(Transaction, Transaction.id_transaction == Violation.id_transaction)
            .where(
                Violation.occurred_at >= start_month,
                Violation.occurred_at <= end_month
            )
        )

        query_today = select(Violation).where(
            Violation.occurred_at >= start,
            Violation.occurred_at <= end
        )

        query_month = select(Violation).where(
            Violation.occurred_at >= start_month,
            Violation.occurred_at <= end_month
        )

        result_total = await self.session.execute(select(Violation))
        result_sum = await self.session.execute(query_sum)
        result_today = await self.session.execute(query_today)
        result_month = await self.session.execute(query_month)

        return {
            "today_violations": len(result_today.all()),
            "month_violations": len(result_month.all()),
            "total_violations": len(result_total.all()),
            "sum_violations": result_sum.scalar()
        }

    async def get_transponders(self):
        result = await self.session.execute(
            select(Violation.transponder)
            .distinct()
            .order_by(Violation.transponder)
        )
        return [row[0] for row in result]

    @staticmethod
    def parse_date_optional(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return datetime.strptime(value, "%d.%m.%Y").date()