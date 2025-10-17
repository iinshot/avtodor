from sqlmodel import SQLModel, Field
from typing import Optional

class PVPPoint(SQLModel, table=True):
    id_PVP: Optional[int] = Field(default=None, primary_key=True, description="ID запрещенного ПВП")
    code: str = Field(nullable=False, description="Код ПВП")
    description: Optional[str] = Field(default=None, description="Описание нарушения")