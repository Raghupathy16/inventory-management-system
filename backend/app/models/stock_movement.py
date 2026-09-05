"""
StockMovement model — the immutable ledger (Rule 2).

`quantity` is SIGNED: positive for increases (PURCHASE, RETURN), negative
for decreases (SALE, DAMAGE, some ADJUSTMENTs). This makes the table a
true ledger — summing all movements for a product should always equal
that product's current `inventory.quantity`. We'll use exactly that
invariant in a Phase 9 reconciliation test.

`reference_type` + `reference_id` form a polymorphic reference (e.g.
reference_type=PURCHASE_ORDER, reference_id=42) rather than a hard foreign
key, because a stock movement can be caused by different kinds of source
records (a purchase order today; a sale order or manual adjustment later).
A real FK constraint can't point at "one of several possible tables," so
this is validated in the service layer instead — a deliberate, documented
trade-off, not an oversight.

Rows in this table are never updated or deleted by the application —
only inserted. There's no `updated_at` because a ledger entry, once
written, is a historical fact.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import MovementType, ReferenceType

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType, name="stock_movement_type"), nullable=False
    )
    reference_type: Mapped[Optional[ReferenceType]] = mapped_column(
        Enum(ReferenceType, name="stock_movement_reference_type"), nullable=True
    )
    reference_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="stock_movements")
    user: Mapped["User"] = relationship(back_populates="stock_movements")

    def __repr__(self) -> str:
        return (
            f"<StockMovement id={self.id} product_id={self.product_id} "
            f"qty={self.quantity} type={self.movement_type}>"
        )
