from __future__ import annotations

from typing import Any
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    id: Any
    __name__: str

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # organizations, users, ledger_entries etc (se você definir __tablename__ no model, ele ganha)
        return cls.__name__.lower()
