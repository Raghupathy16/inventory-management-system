"""
PurchaseOrder model.

`status` uses the `PurchaseOrderStatus` enum (Rule 4 — controlled states).
This column only tracks *what* the current state is; validating which
*transitions* are legal (e.g. DRAFT -> SUBMITTED is fine, DRAFT -> RECEIVED
is not) is business logic that belongs in `purchase_service.py` (Phase 6/7),
not in the model. The model's job is to store data correctly; the service
layer's job is to enforce workflow rules.

`total_amount` is calculated and written by the service layer from the sum
of line items — never trusted from a client request (Rule from Section 9).

`approved_by` / `approved_at` are nullable because a DRAFT order has no
approver yet.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import PurchaseOrderStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.supplier import Supplier
    from app.models.user import User
    from app.models.purchase_order_item import PurchaseOrderItem


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="purchase_order_status"),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="purchase_orders")
    creator: Mapped["User"] = relationship(
        back_populates="created_purchase_orders", foreign_keys=[created_by]
    )
    approver: Mapped[Optional["User"]] = relationship(
        back_populates="approved_purchase_orders", foreign_keys=[approved_by]
    )
    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder id={self.id} status={self.status}>"
