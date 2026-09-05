"""
Product model.

`unit_price` is `Numeric(10,2)` — see Phase 2 design notes on why never
`Float` for money.

The `CheckConstraint` on `unit_price >= 0` is a database-level backstop.
The Pydantic schema (Phase 4) will also reject negative prices before the
request even reaches the database — this constraint exists in case that
layer is ever bypassed (e.g. a bulk import script, a future admin tool
that writes directly).
"""

from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.inventory import Inventory
    from app.models.purchase_order_item import PurchaseOrderItem
    from app.models.stock_movement import StockMovement


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_products_unit_price_non_negative"),
        CheckConstraint("reorder_level >= 0", name="ck_products_reorder_level_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reorder_level: Mapped[int] = mapped_column(default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products")
    inventory: Mapped[Optional["Inventory"]] = relationship(
        back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    purchase_order_items: Mapped[List["PurchaseOrderItem"]] = relationship(
        back_populates="product"
    )
    stock_movements: Mapped[List["StockMovement"]] = relationship(back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku!r}>"
