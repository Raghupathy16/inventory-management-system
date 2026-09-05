"""
PurchaseOrderItem model.

`quantity_received` is the addition flagged in Phase 0 (Section 7 open
question #2, approved). It's what lets the receiving service (Phase 8)
answer "how much of this line is still outstanding?" via
`quantity - quantity_received`, and enforce Rule 3 (can't receive more
than ordered) with a simple, indexed comparison instead of re-summing
every stock_movement row tied to this PO on every receipt.

`total_price` is `quantity * unit_price`, computed and stored by the
service layer at creation time — not trusted from the client, and not a
SQL-generated column, because we want it frozen at the price agreed upon
when the PO was created even if the product's `unit_price` changes later.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.product import Product


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_po_items_quantity_positive"),
        CheckConstraint(
            "quantity_received >= 0", name="ck_po_items_quantity_received_non_negative"
        ),
        CheckConstraint("unit_price >= 0", name="ck_po_items_unit_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    quantity_received: Mapped[int] = mapped_column(default=0, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="purchase_order_items")

    def __repr__(self) -> str:
        return f"<PurchaseOrderItem id={self.id} product_id={self.product_id} qty={self.quantity}>"
