"""
Phase 2 tests: model structure and constraints.

CONCEPT: Testing against SQLite in-memory for structural tests
------------------------------------------------------------------
What it is: instead of spinning up real MySQL for every test run, we point
SQLAlchemy at `sqlite:///:memory:` — a database that exists only in RAM for
the duration of the test process.

Why we need it: these tests aren't testing business logic yet (that starts
Phase 3+, in the service layer, and will run against MySQL in Docker or a
dedicated test DB). Here we're only testing "did I define the models,
relationships, and constraints correctly?" SQLite is fast (no container
startup, no network) and portable (works in CI without a DB service).

Trade-off, stated explicitly: SQLite does not behave identically to MySQL
for every feature. Notably, SQLite enforces CHECK constraints and unique
constraints correctly (which is what we're testing here), but its handling
of some MySQL-specific types differs. That's fine for this phase — once we
get to service-layer business logic (Phase 6+), those tests will run
against real MySQL via Docker, not SQLite, specifically to avoid this gap
mattering for logic where it counts.

Where we use it: only in this file, only for Phase 2 structural checks.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models import (
    AuditLog,
    Category,
    Inventory,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Role,
    StockMovement,
    Supplier,
    User,
)
from app.models.enums import MovementType, PurchaseOrderStatus, RoleName


@pytest.fixture()
def db_session():
    """Fresh in-memory SQLite DB + session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def _make_role(session, name=RoleName.ADMIN.value):
    role = Role(name=name)
    session.add(role)
    session.commit()
    return role


def _make_user(session, role, email="admin@example.com"):
    user = User(email=email, password_hash="hashed", role_id=role.id)
    session.add(user)
    session.commit()
    return user


def _make_category(session, name="Electronics"):
    category = Category(name=name)
    session.add(category)
    session.commit()
    return category


def _make_product(session, category, sku="SKU-001", unit_price=Decimal("100.00")):
    product = Product(
        name="Laptop",
        sku=sku,
        category_id=category.id,
        unit_price=unit_price,
        reorder_level=10,
    )
    session.add(product)
    session.commit()
    return product


def _make_supplier(session, name="Acme Supplies"):
    supplier = Supplier(name=name, email="acme@example.com")
    session.add(supplier)
    session.commit()
    return supplier


class TestRoleAndUser:
    def test_create_role_and_user_relationship(self, db_session):
        role = _make_role(db_session)
        user = _make_user(db_session, role)

        assert user.role.name == RoleName.ADMIN.value
        assert user.id in [u.id for u in role.users]

    def test_duplicate_email_rejected(self, db_session):
        role = _make_role(db_session)
        _make_user(db_session, role, email="dupe@example.com")

        db_session.add(User(email="dupe@example.com", password_hash="x", role_id=role.id))
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestProduct:
    def test_create_product_with_category(self, db_session):
        category = _make_category(db_session)
        product = _make_product(db_session, category)

        assert product.category.name == "Electronics"
        assert product in category.products

    def test_duplicate_sku_rejected(self, db_session):
        category = _make_category(db_session)
        _make_product(db_session, category, sku="DUPLICATE-SKU")

        db_session.add(
            Product(
                name="Monitor",
                sku="DUPLICATE-SKU",
                category_id=category.id,
                unit_price=Decimal("50.00"),
                reorder_level=5,
            )
        )
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_negative_unit_price_rejected(self, db_session):
        category = _make_category(db_session)
        db_session.add(
            Product(
                name="Bad Product",
                sku="BAD-001",
                category_id=category.id,
                unit_price=Decimal("-10.00"),
                reorder_level=0,
            )
        )
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestInventory:
    def test_inventory_linked_to_product(self, db_session):
        category = _make_category(db_session)
        product = _make_product(db_session, category)

        inventory = Inventory(product_id=product.id, quantity=50)
        db_session.add(inventory)
        db_session.commit()

        assert product.inventory.quantity == 50

    def test_negative_inventory_quantity_rejected(self, db_session):
        category = _make_category(db_session)
        product = _make_product(db_session, category)

        db_session.add(Inventory(product_id=product.id, quantity=-5))
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestPurchaseOrderWorkflow:
    def test_purchase_order_with_items(self, db_session):
        role = _make_role(db_session)
        user = _make_user(db_session, role)
        supplier = _make_supplier(db_session)
        category = _make_category(db_session)
        product = _make_product(db_session, category)

        po = PurchaseOrder(
            supplier_id=supplier.id,
            status=PurchaseOrderStatus.DRAFT,
            order_date=date.today(),
            created_by=user.id,
        )
        db_session.add(po)
        db_session.commit()

        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=product.id,
            quantity=20,
            unit_price=Decimal("100.00"),
            total_price=Decimal("2000.00"),
        )
        db_session.add(item)
        db_session.commit()

        assert po.status == PurchaseOrderStatus.DRAFT
        assert po.items[0].total_price == Decimal("2000.00")
        assert po.items[0].quantity_received == 0  # default

    def test_zero_quantity_item_rejected(self, db_session):
        role = _make_role(db_session)
        user = _make_user(db_session, role)
        supplier = _make_supplier(db_session)
        category = _make_category(db_session)
        product = _make_product(db_session, category)

        po = PurchaseOrder(
            supplier_id=supplier.id,
            status=PurchaseOrderStatus.DRAFT,
            order_date=date.today(),
            created_by=user.id,
        )
        db_session.add(po)
        db_session.commit()

        db_session.add(
            PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=product.id,
                quantity=0,  # invalid: Rule "no invalid quantities"
                unit_price=Decimal("100.00"),
                total_price=Decimal("0.00"),
            )
        )
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestStockMovementLedger:
    def test_movement_recorded_with_signed_quantity(self, db_session):
        role = _make_role(db_session)
        user = _make_user(db_session, role)
        category = _make_category(db_session)
        product = _make_product(db_session, category)

        movement = StockMovement(
            product_id=product.id,
            quantity=20,
            movement_type=MovementType.PURCHASE,
            user_id=user.id,
        )
        db_session.add(movement)
        db_session.commit()

        assert movement.movement_type == MovementType.PURCHASE
        assert movement.quantity == 20


class TestAuditLog:
    def test_audit_log_extra_data_maps_to_metadata_column(self, db_session):
        role = _make_role(db_session)
        user = _make_user(db_session, role)

        log = AuditLog(
            user_id=user.id,
            action="PRODUCT_CREATED",
            entity="Product",
            entity_id=1,
            extra_data={"sku": "SKU-001"},
        )
        db_session.add(log)
        db_session.commit()

        # Confirm the actual DB column is named "metadata" even though the
        # Python attribute is "extra_data".
        assert AuditLog.__table__.columns["metadata"] is not None
        assert log.extra_data == {"sku": "SKU-001"}
