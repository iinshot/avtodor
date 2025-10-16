from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, UTC

class Violation(SQLModel, table=True):
    id_violation: Optional[int] = Field(default=None, primary_key=True)
    id_transaction: Optional[int] = Field(default=None, foreign_key="transaction.id_transaction", description="ID транзакции")
    transponder: str = Field(nullable=False, description="Номер транспондера")
    occurred_at: datetime = Field(nullable=False, index=True, description="Дата и время нарушения")
    PVP_code: str = Field(nullable=False, description="Код ПВП")
    base_tariff: float = Field(nullable=False, description="Сумма нарушения")
    reason: Optional[str] = Field(default=None, description="Причина нарушения")
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))