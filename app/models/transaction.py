from sqlmodel import SQLModel, Field, JSON, Column
from typing import Optional
from datetime import datetime, UTC

class Transaction(SQLModel, table=True):
    id_transaction: Optional[int] = Field(default=None, primary_key=True)
    occurred_at: datetime = Field(nullable=False, index=True, description="Дата и время проезда ПВП")
    PVP_code: str = Field(nullable=False, index=True, description="Код ПВП")
    transponder: str = Field(nullable=False, index=True, description="Номер транспондера")
    vehicle_class: Optional[int] = Field(default=None, description="Класс транспортного средства")
    base_tariff: Optional[float] = Field(default=None, description="Базовая стоимость дороги")
    discount: Optional[int] = Field(default=None, description="Скидка на дорогу")
    paid: Optional[float] = Field(default=None, description="Итоговая стоимость проезда")
    raw_row: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Полученная строка CSV")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))