"""
User model.

`password_hash` stores a bcrypt hash (Phase 3 implements the actual
hashing via `passlib`) — never a plaintext password. There is
intentionally no `password` column at all, so it's structurally impossible
to accidentally store one.
"""

from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.stock_movement import StockMovement
    from app.models.audit_log import AuditLog


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role: Mapped["Role"] = relationship(back_populates="users")

    created_purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        back_populates="creator",
        foreign_keys="PurchaseOrder.created_by",
    )
    approved_purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        back_populates="approver",
        foreign_keys="PurchaseOrder.approved_by",
    )
    stock_movements: Mapped[List["StockMovement"]] = relationship(back_populates="user")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
