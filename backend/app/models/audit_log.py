"""
AuditLog model — the immutable record of sensitive actions (Section 18).

Two deliberate naming/typing notes:

1. `metadata` naming collision: the Python attribute is `extra_data`, but
   the actual database column is still named `metadata` (via
   `mapped_column("metadata", ...)`), so external tools/DB inspection see
   exactly the column name your spec asked for. This is purely a
   Python-side naming constraint — `Base.metadata` is reserved by
   SQLAlchemy itself.

2. `action` and `entity` are plain strings, not enums — see the Phase 2
   design notes for why (the action vocabulary grows every phase; a DB
   enum would force a migration each time we add a new loggable action).

Like `stock_movements`, this table is insert-only. No service should ever
update or delete an audit log row — that would defeat its purpose.
"""

from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    extra_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r} entity={self.entity!r}>"
