"""
Shared column mixin.

CONCEPT: Mixins in SQLAlchemy
--------------------------------
What it is: a small class that isn't a table itself, but gets "mixed in"
to multiple model classes to give them shared columns.

Why we need it: almost every table needs `created_at` / `updated_at`.
Repeating the same two column definitions in all 10 model files would be
duplicate logic — if we ever change how we track timestamps (e.g. add
timezone awareness), we'd have to find and edit it in 10 places.

Where we use it: every model in this app inherits from `TimestampMixin`
alongside `Base`.

What problem it solves: DRY (Don't Repeat Yourself) without introducing a
heavyweight abstraction — this is a plain Python mixin, not a framework.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
