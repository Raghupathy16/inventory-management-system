"""
Inventory model.

One row per product (`product_id` is unique) — this is the "current
on-hand quantity" snapshot. The full history of *how* it got to that
quantity lives in `stock_movements`, never here. This table only ever
answers "what do we have right now," which is why it has no `created_at`
(only `updated_at` — it's mutated, not appended to) and no direct API for
arbitrary writes (all changes to it are internal, mediated by
`inventory_service` in Phase 8, based on validated stock movements).

The `quantity >= 0` CHECK constraint is the database-level backstop for
Rule 1 (no negative stock). The service layer will be the primary
enforcement point (returning a proper 409 error), but this constraint
means the invariant holds even if application code has a bug.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), unique=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="inventory")

    def __repr__(self) -> str:
        return f"<Inventory product_id={self.product_id} quantity={self.quantity}>"
