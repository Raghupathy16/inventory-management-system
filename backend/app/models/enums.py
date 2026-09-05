"""
Shared enumerations.

CONCEPT: Enums for closed vocabularies
------------------------------------------
What it is: a fixed, named set of allowed values (e.g. a purchase order can
ONLY be one of DRAFT/SUBMITTED/APPROVED/... — never an arbitrary string).

Why we need it: without an enum, "status" would just be a free-text string
column, and nothing stops a bug (or a bad API request) from writing
"aproved" (typo) or "IN_PROGRESS" (a value that was never designed for).
An enum makes invalid values impossible to represent, both in Python (type
checkers catch it) and in the database (MySQL's ENUM column type rejects
anything outside the list at the storage layer).

Where we use it: `Role.name`, `PurchaseOrder.status`, `StockMovement.movement_type`,
`StockMovement.reference_type`.

What problem it solves: eliminates an entire category of "invalid state"
bugs at the earliest possible point (before the value is even stored),
rather than discovering bad data later during a report or a workflow step.

Note: `audit_logs.action` deliberately does NOT use an enum — see the
design notes in the Phase 2 explanation. That list grows every time we add
a new feature, and a DB enum would force a migration each time.
"""

import enum


class RoleName(str, enum.Enum):
    ADMIN = "ADMIN"
    PROCUREMENT_MANAGER = "PROCUREMENT_MANAGER"
    WAREHOUSE_EMPLOYEE = "WAREHOUSE_EMPLOYEE"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class MovementType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RETURN = "RETURN"
    DAMAGE = "DAMAGE"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"


class ReferenceType(str, enum.Enum):
    PURCHASE_ORDER = "PURCHASE_ORDER"
    MANUAL = "MANUAL"
    SALE_ORDER = "SALE_ORDER"  # reserved for future Sales module
