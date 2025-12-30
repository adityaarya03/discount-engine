"""
Seed database with sample data:
- Categories
- Products
- Discount rules
- Admin user
"""
from decimal import Decimal
from uuid import uuid4
from sqlmodel import Session, select

from app.core.database import engine, create_db_and_tables
from app.models.user import User, UserRole
from app.models.product import Category, Product
from app.models.discount import DiscountRule, DiscountScope, DiscountValueType
from app.core.security import get_password_hash


def seed_categories(session: Session) -> dict:
    """Create product categories."""
    print("📦 Seeding categories...")
    
    electronics = Category(
        id=uuid4(),
        name="Electronics",
        slug="electronics"
    )
    
    fashion = Category(
        id=uuid4(),
        name="Fashion",
        slug="fashion"
    )
    
    home = Category(
        id=uuid4(),
        name="Home & Kitchen",
        slug="home-kitchen"
    )
    
    session.add_all([electronics, fashion, home])
    session.commit()
    
    print(f"   ✅ Created {electronics.name}, {fashion.name}, {home.name}")
    
    return {
        "electronics": electronics,
        "fashion": fashion,
        "home": home
    }


def seed_products(session: Session, categories: dict):
    """Create sample products."""
    print("🛍️  Seeding products...")
    
    products = [
        # Electronics
        Product(
            category_id=categories["electronics"].id,
            name="Wireless Headphones",
            description="Premium noise-cancelling headphones",
            price=Decimal("2999.00"),
            sku="ELEC-HEAD-001",
            stock_quantity=50
        ),
        Product(
            category_id=categories["electronics"].id,
            name="Smart Watch",
            description="Fitness tracker with heart rate monitor",
            price=Decimal("4999.00"),
            sku="ELEC-WATCH-001",
            stock_quantity=30
        ),
        Product(
            category_id=categories["electronics"].id,
            name="Laptop Stand",
            description="Ergonomic aluminum laptop stand",
            price=Decimal("1299.00"),
            sku="ELEC-STAND-001",
            stock_quantity=100
        ),
        
        # Fashion
        Product(
            category_id=categories["fashion"].id,
            name="Cotton T-Shirt",
            description="Premium cotton crew neck t-shirt",
            price=Decimal("599.00"),
            sku="FASH-SHIRT-001",
            stock_quantity=200
        ),
        Product(
            category_id=categories["fashion"].id,
            name="Denim Jeans",
            description="Classic fit denim jeans",
            price=Decimal("1499.00"),
            sku="FASH-JEANS-001",
            stock_quantity=150
        ),
        
        # Home
        Product(
            category_id=categories["home"].id,
            name="Coffee Maker",
            description="Automatic drip coffee maker",
            price=Decimal("3499.00"),
            sku="HOME-COFFEE-001",
            stock_quantity=40
        ),
    ]
    
    session.add_all(products)
    session.commit()
    
    print(f"   ✅ Created {len(products)} products")


def seed_discount_rules(session: Session, categories: dict):
    """Create discount rules using generic scope + value_type design."""
    print("💰 Seeding discount rules...")

    rules = [

        # 1. CART-level PERCENTAGE discount with max cap (Assignment Scenario 1)
        # Can stack with Rewarded Buyer ONLY if user is loyalty member
        DiscountRule(
            name="10% off on orders above ₹5000 (max ₹1000)",
            scope=DiscountScope.CART,
            value_type=DiscountValueType.PERCENTAGE,
            value=Decimal("10.00"),
            priority=2,
            is_active=True,
            is_stackable=True,  # Can stack
            coupon_code=None,  # Auto-apply
            config={
                "conditions": {"min_cart_value": 5000},
                "max_discount_amount": 1000,
                "loyalty_stacking_only": True  # But ONLY for loyalty members (10+ orders)
            }
        ),

        # 2. CART-level FLAT loyalty reward (Assignment Scenario 2)
        # After 5 completed purchases, user gets ₹500 off on 6th transaction
        # Can stack with 10% discount ONLY if user is loyalty member
        # NOTE: Without usage_count tracking, this applies on every order after 5 purchases
        # In production, you'd track discount usage or mark as used after first application
        DiscountRule(
            name="₹500 Loyalty Reward (After 5 Purchases)",
            scope=DiscountScope.CART,
            value_type=DiscountValueType.FLAT,
            value=Decimal("500.00"),
            priority=1,
            is_active=True,
            is_stackable=True,  # Can stack
            coupon_code=None,  # Auto-apply
            config={
                "conditions": {
                    "min_purchases": 5,  # Must have 5+ COMPLETED orders
                    "status_filter": ["COMPLETED"]
                },
                "loyalty_stacking_only": True  # Can ONLY stack for loyalty members (10+ orders)
            }
        ),

        # 3. CATEGORY-level PERCENTAGE discount (Assignment Scenario 3)
        DiscountRule(
            name="5% off on 3+ Electronics items",
            scope=DiscountScope.CATEGORY,
            value_type=DiscountValueType.PERCENTAGE,
            value=Decimal("5.00"),
            priority=3,
            is_active=True,
            is_stackable=False,
            coupon_code=None,  # Auto-apply
            config={
                "conditions": {
                    "category_id": str(categories["electronics"].id),
                    "min_quantity": 3
                },
                "max_discount_amount": None,
                "loyalty_stacking_only": False  # Can stack for any user
            }
        ),

        # ============================================
        # COUPON CODES (Manual Entry)
        # ============================================

        # 4. CART-level FLAT coupon
        DiscountRule(
            name="₹500 Flat Off Coupon",
            scope=DiscountScope.CART,
            value_type=DiscountValueType.FLAT,
            value=Decimal("500.00"),
            priority=2,
            is_active=True,
            is_stackable=True,
            coupon_code="FLAT500",
            config={
                "conditions": {"min_cart_value": 2000},
                "loyalty_stacking_only": False  # Can stack for any user
            }
        ),

        # 5. CART-level PERCENTAGE coupon with max cap
        DiscountRule(
            name="20% Off - Save Big (max ₹800)",
            scope=DiscountScope.CART,
            value_type=DiscountValueType.PERCENTAGE,
            value=Decimal("20.00"),
            priority=2,
            is_active=True,
            is_stackable=False,
            coupon_code="SAVE20",
            config={
                "conditions": {"min_cart_value": 3000},
                "max_discount_amount": 800,
                "loyalty_stacking_only": False
            }
        ),

        # 6. CATEGORY-level PERCENTAGE coupon (Electronics)
        DiscountRule(
            name="Electronics Bonanza - 15% Off (max ₹600)",
            scope=DiscountScope.CATEGORY,
            value_type=DiscountValueType.PERCENTAGE,
            value=Decimal("15.00"),
            priority=3,
            is_active=True,
            is_stackable=False,
            coupon_code="ELEC15",
            config={
                "conditions": {
                    "category_id": str(categories["electronics"].id),
                    "min_quantity": 1
                },
                "max_discount_amount": 600,
                "loyalty_stacking_only": False  # Can stack for any user
            }
        ),

        # 7. CART-level FLAT VIP coupon for loyalty members
        DiscountRule(
            name="VIP Loyalty Reward ₹1000",
            scope=DiscountScope.CART,
            value_type=DiscountValueType.FLAT,
            value=Decimal("1000.00"),
            priority=1,
            is_active=True,
            is_stackable=True,
            coupon_code="VIP1000",
            config={
                "conditions": {},
                "loyalty_stacking_only": True  # Can ONLY stack for loyalty members (10+ orders)
            }
        ),

        # 8. CART-level FLAT Fashion coupon
        DiscountRule(
            name="Fashion Week - ₹300 Off",
            scope=DiscountScope.CART,
            value_type=DiscountValueType.FLAT,
            value=Decimal("300.00"),
            priority=3,
            is_active=True,
            is_stackable=True,
            coupon_code="FASHION300",
            config={
                "conditions": {"min_cart_value": 1500},
                "loyalty_stacking_only": False  # Can stack for any user
            }
        ),
    ]

    session.add_all(rules)
    session.commit()

    print(f"   ✅ Created {len(rules)} discount rules (3 auto-apply + 5 coupons)")


def seed_admin_user(session: Session):
    """Create admin user."""
    print("👤 Seeding admin user...")
    
    # Check if admin already exists
    query = select(User).where(User.email == "admin@pragma.ai")
    result = session.exec(query)
    existing = result.one_or_none()
    
    if existing:
        print("   ⚠️  Admin user already exists")
        return
    
    admin = User(
        email="admin@pragma.ai",
        password_hash=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        role=UserRole.ADMIN
    )
    
    session.add(admin)
    session.commit()
    
    print(f"   ✅ Created admin user (email: admin@pragma.ai, password: admin123)")


def seed_test_user(session: Session):
    """Create test user."""
    print("👤 Seeding test user...")
    
    query = select(User).where(User.email == "test@example.com")
    result = session.exec(query)
    existing = result.one_or_none()
    
    if existing:
        print("   ⚠️  Test user already exists")
        return
    
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("test123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        role=UserRole.CUSTOMER
    )
    
    session.add(user)
    session.commit()
    
    print(f"   ✅ Created test user (email: test@example.com, password: test123)")


def main():
    """Main seeding function."""
    print("\n🌱 Starting database seeding...\n")
    
    # Create tables first
    create_db_and_tables()
    
    with Session(engine) as session:
        # Seed in order
        categories = seed_categories(session)
        seed_products(session, categories)
        seed_discount_rules(session, categories)
        seed_admin_user(session)
        seed_test_user(session)
    
    print("\n✨ Database seeding completed!\n")
    print("You can now:")
    print("  1. Start the API: uvicorn app.main:app --reload")
    print("  2. Login as test user: test@example.com / test123 (CUSTOMER role)")
    print("  3. Login as admin: admin@pragma.ai / admin123 (ADMIN role)")
    print("  4. Visit docs: http://localhost:8000/docs\n")


if __name__ == "__main__":
    main()