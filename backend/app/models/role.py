"""
Role model.

A small, mostly-static lookup table: three rows (ADMIN, PROCUREMENT_MANAGER,
WAREHOUSE_EMPLOYEE) that get seeded once. We model it as a real table
(rather than just an enum column on `users`) so that:
  1. Foreign key integrity is enforced by MySQL itself (a user can't
     reference a role_id that doesn't exist).
  2. We have a natural place to attach role metadata in the future
     (e.g., a "description" column) without touching the users table.
"""

from typing import List, TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"
