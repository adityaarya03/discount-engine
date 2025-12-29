"""
Example tests for order endpoints.
Run with: pytest tests/test_orders.py -v
"""
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlmodel import Session, select

from app.main import app
from app.models.user import User
from app.models.product import Product, Category
from app.models.order import Order, OrderStatus
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
async def client():
    """Async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user(session: Session):
    """Create test user."""
    user = User(
        email="testuser@example.com",
        password_hash=get_password_hash("testpass123"),
        first_name="Test",
        last_name="User",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User):
    """Create JWT token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def test_products(session: Session):
    """Create test products."""
    # Create category
    electronics = Category(name="Electronics", slug="electronics")
    session.add(electronics)
    session.commit()
    
    # Create products
    products = [
        Product(
            category_id=electronics.id,
            name="Laptop",
            price=Decimal("55000.00"),
            sku="ELEC-001",
            stock_quantity=10
        ),
        Product(
            category_id=electronics.id,
            name="Mouse",
            price=Decimal("500.00"),
            sku="ELEC-002",
            stock_quantity=50
        ),
    ]
    
    session.add_all(products)
    session.commit()
    
    return products


@pytest.mark.asyncio
async def test_create_order_success(
    client: AsyncClient,
    auth_token: str,
    test_products: list[Product]
):
    """Test successful order creation."""
    response = await client.post(
        "/api/v1/orders/",
        json={
            "items": [
                {"product_id": str(test_products[0].id), "quantity": 1}
            ]
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "id" in data
    assert data["status"] == OrderStatus.PENDING.value
    assert Decimal(data["subtotal"]) == test_products[0].price
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_create_order_with_discount(
    client: AsyncClient,
    auth_token: str,
    test_products: list[Product],
    session: Session
):
    """Test order creation triggers discount calculation."""
    # Order value > 5000 should get 10% discount
    response = await client.post(
        "/api/v1/orders/",
        json={
            "items": [
                {"product_id": str(test_products[0].id), "quantity": 1}  # ₹55000
            ]
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Should have percentage discount applied
    assert Decimal(data["discount_amount"]) > 0
    assert len(data["applied_discounts"]) > 0
    assert data["applied_discounts"][0]["rule_type"] == "PERCENTAGE"


@pytest.mark.asyncio
async def test_list_orders(
    client: AsyncClient,
    auth_token: str,
    test_user: User,
    session: Session
):
    """Test listing user's orders."""
    # Create a test order
    order = Order(
        user_id=test_user.id,
        status=OrderStatus.COMPLETED,
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )
    session.add(order)
    session.commit()
    
    # List orders
    response = await client.get(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_order_unauthorized(
    client: AsyncClient,
    auth_token: str,
    session: Session
):
    """Test that users can't access other users' orders."""
    # Create order for different user
    other_user = User(
        email="other@example.com",
        password_hash=get_password_hash("pass123"),
        first_name="Other",
        last_name="User"
    )
    session.add(other_user)
    session.commit()
    
    order = Order(
        user_id=other_user.id,
        status=OrderStatus.PENDING,
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )
    session.add(order)
    session.commit()
    
    # Try to access other user's order
    response = await client.get(
        f"/api/v1/orders/{order.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404  # Order not found (security)


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(
    client: AsyncClient,
    auth_token: str,
    test_products: list[Product]
):
    """Test order creation fails with insufficient stock."""
    response = await client.post(
        "/api/v1/orders/",
        json={
            "items": [
                {"product_id": str(test_products[0].id), "quantity": 999}  # More than stock
            ]
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


# Add more tests:
# - test_loyalty_discount_after_5_orders()
# - test_category_discount_on_3_electronics()
# - test_discount_stacking()
# - test_best_discount_selection()