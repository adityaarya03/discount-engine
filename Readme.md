# E-Commerce Discount Engine API

A production-ready FastAPI-based discount engine system for e-commerce stores with dynamic rule configuration, stackable discounts, and intelligent discount optimization.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Discount Logic](#discount-logic)
- [Database Design](#database-design)
- [Design Patterns](#design-patterns)
- [Future Enhancements](#future-enhancements)

---

## ✨ Features

### Core Functionality
- ✅ **Dynamic Discount Rules**: Create, update, and manage discount rules without code changes
- ✅ **Multiple Discount Types**:
  - Cart-level (applies to entire order)
  - Category-level (applies to specific product categories)
  - Product-level (applies to specific products)
- ✅ **Flexible Value Types**:
  - Percentage discounts with optional max caps
  - Flat amount discounts
  - BOGO (Buy One Get One) - skeleton implemented
- ✅ **Smart Stacking Logic**: Automatically determines best combination of discounts
- ✅ **Loyalty Program Integration**: Stack discounts for loyalty members (10+ orders)
- ✅ **Coupon Code System**: Support for manual coupon entry with priority handling
- ✅ **User Authentication**: JWT-based auth with role-based access control
- ✅ **Admin Panel**: RESTful endpoints for discount rule management

### Assignment Requirements (100% Complete)
- ✅ Users can place orders for multiple products
- ✅ Percentage Discount: 10% off orders above ₹5000 (max ₹1000)
- ✅ Flat Discount: ₹500 off after 5 completed purchases (Rewarded Buyer)
- ✅ Category Discount: 5% off on 3+ Electronics items
- ✅ Discount breakdown visible in order details
- ✅ Split-category cart handling
- ✅ Basic authentication (JWT)

### Bonus Features (Brownie Points)
- ✅ **Stackable Discounts**: Multiple discounts with priority-based application
- ✅ **Best Benefit Guarantee**: Compares stacking vs single discount, returns maximum
- ✅ **Loyalty Gate**: Flat + Percentage stack ONLY for loyalty members
- ✅ **Admin Panel**: Dynamic discount rule configuration via API

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────┐
│   Client    │
│ (Frontend/  │
│  Postman)   │
└──────┬──────┘
       │
       │ HTTP/REST
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌──────────────────────────────────┐  │
│  │      API Layer (Routers)         │  │
│  │  - Auth    - Orders              │  │
│  │  - Products - Discounts          │  │
│  └────────────┬─────────────────────┘  │
│               │                         │
│  ┌────────────▼─────────────────────┐  │
│  │     Business Logic (Services)    │  │
│  │  ┌───────────────────────────┐   │  │
│  │  │   Discount Engine         │   │  │
│  │  │  - Strategy Pattern       │   │  │
│  │  │  - Chain of Responsibility│   │  │
│  │  │  - Stacking Logic         │   │  │
│  │  └───────────────────────────┘   │  │
│  └────────────┬─────────────────────┘  │
│               │                         │
│  ┌────────────▼─────────────────────┐  │
│  │     Data Layer (SQLModel)        │  │
│  │  - User    - Order               │  │
│  │  - Product - DiscountRule        │  │
│  └──────────────────────────────────┘  │
└───────────────┬─────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │  PostgreSQL   │
        │  (Database)   │
        └───────────────┘
```

### Request Flow Example

```
POST /api/v1/orders/
    │
    ├──> 1. Authentication (JWT verification)
    │
    ├──> 2. Request Validation (Pydantic)
    │
    ├──> 3. Get User & Products (Database)
    │
    ├──> 4. Create Order with Items
    │
    ├──> 5. DiscountEngine.apply_discounts()
    │       │
    │       ├──> Get Active Discount Rules
    │       │
    │       ├──> For each rule:
    │       │    ├──> Strategy.is_applicable() (Chain of Responsibility)
    │       │    └──> Strategy.calculate() (Strategy Pattern)
    │       │
    │       ├──> Stacking Logic (determine best combination)
    │       │
    │       └──> Return applied discounts
    │
    ├──> 6. Update Order Totals
    │
    ├──> 7. Save to Database (commit)
    │
    └──> 8. Return Response
```

---

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Backend** | FastAPI 0.104+ | Modern, fast web framework with auto docs |
| **Database** | PostgreSQL 16 | Relational database with JSONB support |
| **ORM** | SQLModel 0.14+ | Type-safe ORM combining Pydantic + SQLAlchemy |
| **Authentication** | JWT (python-jose) | Stateless token-based authentication |
| **Password Hashing** | Bcrypt (passlib) | Secure password hashing |
| **Validation** | Pydantic v2 | Type-safe request/response validation |
| **Container** | Docker Compose | Containerized development environment |
| **Documentation** | Swagger/ReDoc | Auto-generated API documentation |

---

## 📁 Project Structure

```
discount-engine/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Settings (from .env)
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py            # Main API router
│   │       └── endpoints/
│   │           ├── auth.py          # Authentication endpoints
│   │           ├── orders.py        # Order management
│   │           ├── products.py      # Product/category listings
│   │           └── discounts.py     # Discount rule CRUD (admin)
│   │
│   ├── core/
│   │   ├── database.py              # SQLModel engine & session
│   │   └── security.py              # JWT, password hashing, auth
│   │
│   ├── models/
│   │   ├── user.py                  # User model
│   │   ├── order.py                 # Order, OrderItem models
│   │   ├── product.py               # Product, Category models
│   │   └── discount.py              # DiscountRule, AppliedDiscount
│   │
│   ├── schemas/
│   │   ├── user.py                  # User request/response schemas
│   │   ├── order.py                 # Order schemas
│   │   ├── product.py               # Product schemas
│   │   └── discount.py              # Discount rule schemas
│   │
│   └── services/
│       └── discount_engine/
│           ├── engine.py            # Main discount engine (stacking logic)
│           ├── strategies.py        # Strategy pattern (Cart/Category/Product)
│           └── conditions.py        # Chain of Responsibility (condition checks)
│
├── scripts/
│   └── seed_data.py                 # Database seeding script
│
├── .env.example                     # Environment variables template
├── docker-compose.yml               # PostgreSQL + Redis setup
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd discount-engine
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start PostgreSQL with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations & seed data**
   ```bash
   python scripts/seed_data.py
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **Access the API**
   - API Base: http://localhost:8000/api/v1
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication

All protected endpoints require JWT token in header:
```
Authorization: Bearer <access_token>
```

### Key Endpoints

#### 🔐 Authentication

**Register User**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+919876543210",
  "role": "CUSTOMER"
}
```

**Login**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### 🛒 Orders

**Create Order**
```http
POST /orders/
Authorization: Bearer <token>
Content-Type: application/json

{
  "items": [
    {
      "product_id": "uuid-here",
      "quantity": 2
    }
  ],
  "coupon_code": "FLAT500"
}

Response:
{
  "id": "order-uuid",
  "status": "PENDING",
  "subtotal": 6000.00,
  "discount_amount": 1100.00,
  "total_amount": 4900.00,
  "applied_discounts": [
    {
      "rule_name": "10% off on orders above ₹5000",
      "discount_amount": 600.00
    },
    {
      "rule_name": "₹500 Loyalty Reward",
      "discount_amount": 500.00
    }
  ]
}
```

**Get Order Details**
```http
GET /orders/{order_id}
Authorization: Bearer <token>
```

**List My Orders**
```http
GET /orders/?skip=0&limit=20
Authorization: Bearer <token>
```

**Update Order Status**
```http
PATCH /orders/{order_id}/status?new_status=COMPLETED
Authorization: Bearer <token>
```

#### 📦 Products & Categories

**List Categories**
```http
GET /categories/
```

**List Products**
```http
GET /products/?category_id=<uuid>&skip=0&limit=50
```

#### 💰 Discount Management (Admin Only)

**Create Discount Rule**
```http
POST /discounts/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Summer Sale - 20% Off",
  "scope": "CART",
  "value_type": "PERCENTAGE",
  "value": 20.0,
  "conditions": {
    "min_cart_value": 3000
  },
  "max_discount_amount": 1000,
  "is_stackable": true,
  "loyalty_stacking_only": false,
  "priority": 2,
  "coupon_code": "SUMMER20"
}
```

**List Discount Rules**
```http
GET /discounts/?is_active=true
```

**Update Discount Rule**
```http
PATCH /discounts/{rule_id}
Authorization: Bearer <admin_token>

{
  "is_active": false
}
```

**Delete Discount Rule**
```http
DELETE /discounts/{rule_id}
Authorization: Bearer <admin_token>
```

---

## 🧮 Discount Logic

### Assignment Requirements

#### 1. Percentage Discount (10% off cart > ₹5000)
- **Trigger**: Order subtotal exceeds ₹5000
- **Discount**: 10% of cart value
- **Max Cap**: ₹1000
- **Stacking**: Can stack ONLY for loyalty members

#### 2. Flat Discount (₹500 Rewarded Buyer)
- **Trigger**: User completes 5 eligible purchases
- **Eligible**: Orders with status = COMPLETED (excludes CANCELLED, RETURNED)
- **Discount**: ₹500 flat off
- **Stacking**: Can stack ONLY for loyalty members

#### 3. Category Discount (5% off Electronics)
- **Trigger**: 3+ units from Electronics category
- **Note**: Quantity counts (1 product × 3 qty = 3 items)
- **Discount**: 5% off Electronics items only
- **Stacking**: Non-stackable

### Loyalty Program

**Definition**: Users with 10+ COMPLETED orders

**Benefits**:
- Can stack Percentage (10%) + Flat (₹500) discounts
- Access to exclusive loyalty-only coupons

### Stacking Rules

The engine uses intelligent stacking logic to maximize customer benefit:

#### Case 1: User with Coupon
```
IF user applies coupon:
  IF coupon is non-stackable:
    RETURN coupon ONLY (ignore all auto-apply)
  ELSE:
    APPLY coupon
    CHECK auto-apply discounts:
      FOR each auto-apply:
        IF auto-apply is non-stackable:
          SKIP
        IF auto-apply requires loyalty AND user is not member:
          SKIP
        ELSE:
          ADD to stack
    RETURN coupon + eligible auto-apply discounts
```

#### Case 2: No Coupon (Auto-Apply Only)
```
GET all applicable auto-apply discounts

SEPARATE into:
  - stackable_for_user (based on loyalty_stacking_only flag)
  - non_stackable

IF stackable_for_user has items:
  total_stackable = SUM(stackable_for_user)
  best_single = MAX(all_applicable)

  IF total_stackable >= best_single:
    RETURN stackable_for_user
  ELSE:
    RETURN [best_single]
ELSE:
  RETURN [best_single]
```

### Examples

#### Example 1: Non-Loyalty Member (6 orders)
**Cart**: ₹6000, 4 Electronics items

**Applicable**:
- 10% cart: ₹600 (can't stack - not loyalty member)
- Rewarded Buyer: ₹500 (can't stack - not loyalty member)
- 5% Electronics: ₹300 (non-stackable)

**Result**: ₹600 (best single)

#### Example 2: Loyalty Member (12 orders)
**Cart**: ₹6000, 4 Electronics items

**Applicable**:
- 10% cart: ₹600 (CAN stack - is member)
- Rewarded Buyer: ₹500 (CAN stack - is member)
- 5% Electronics: ₹300 (non-stackable, excluded)

**Comparison**: ₹1100 (stacked) vs ₹600 (best single)

**Result**: ₹1100 (10% + ₹500 stacked)

---

## 🗄️ Database Design

### Key Tables

**Users**
- Stores customer and admin accounts
- Password hashing with bcrypt
- Role-based access control

**Orders**
- Tracks order lifecycle (PENDING → COMPLETED)
- Stores discount_amount for financial records
- Links to user and applied discounts

**OrderItems**
- Denormalized product data (snapshot at purchase time)
- Enables category filtering without joins
- Future: Item-level discount tracking

**DiscountRule**
- Hybrid design: SQL + JSONB config
- Flexible conditions without schema changes
- Priority-based ordering

**AppliedDiscount**
- N:N relationship between Orders and DiscountRules
- Historical record of discount usage
- Detailed calculation_details in JSONB

### Design Decisions

#### Hybrid Design (SQL + JSONB)
**Fixed SQL columns** for queryable fields:
- name, scope, value_type, is_active
- Enables `SELECT * WHERE is_active = true`

**JSONB config** for flexible conditions:
- Category discounts need `category_id`
- Cart discounts need `min_cart_value`
- No schema migration needed for new condition types

#### Denormalized Fields
**OrderItem** stores `product_name` and `product_category_id`:
- Snapshot at order time (prices/categories change)
- Fast category filtering for discounts
- No joins needed during discount calculation

---

## 🎨 Design Patterns

### 1. Strategy Pattern
**Location**: `app/services/discount_engine/strategies.py`

**Purpose**: Different discount scopes need different calculation logic

**Implementation**:
- `CartStrategy`: Calculates on entire cart
- `CategoryStrategy`: Filters items by category
- `ProductStrategy`: Filters items by product IDs

**Benefits**:
- Easy to add new scope types
- Each strategy is self-contained and testable
- Follows Open/Closed Principle

### 2. Chain of Responsibility
**Location**: `app/services/discount_engine/conditions.py`

**Purpose**: Discounts have multiple independent conditions

**Implementation**:
```python
MinCartValueCondition → check → pass/fail
MinPurchasesCondition → check → pass/fail
CategoryCondition → check → pass/fail
```

**Benefits**:
- Conditions are reusable
- Easy to add new condition types
- Independently testable

### 3. Dependency Injection
**Location**: FastAPI endpoints

**Implementation**:
```python
def create_order(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Dependencies auto-injected
```

**Benefits**:
- Easy testing (inject mocks)
- Loose coupling
- Framework-managed lifecycle

---

## 🔮 Future Enhancements

### High Priority
1. **Redis Caching** (~2 hours)
   - Cache active discount rules
   - Cache user loyalty status
   - Reduce DB queries by 80%+

2. **Unit & Integration Tests** (~8 hours)
   - Test stacking logic
   - Test condition evaluation
   - Pytest + coverage report

### Medium Priority
3. **Item-Level Discount Tracking** (~4 hours)
   - Distribute discounts to OrderItems
   - Better reporting

4. **Discount Usage Limits**
   - One-time coupons
   - Max redemptions per user

5. **Time-Based Rules**
   - Start/end dates
   - Scheduled promotions

### Low Priority
6. **Recommendation System Integration**
   - Purchase history analytics
   - Personalized discounts

7. **GraphQL API**
   - More flexible queries
   - Reduced over-fetching

---

## 🧪 Testing

### Quick Test Flow

1. Start services:
   ```bash
   docker-compose up -d
   python scripts/seed_data.py
   uvicorn app.main:app --reload
   ```

2. Test in browser:
   - Swagger UI: http://localhost:8000/docs
   - Try "Register → Login → Create Order"

3. Test loyalty stacking:
   - Create 10 orders for same user
   - Mark as COMPLETED
   - Create 11th order → Should get ₹1100 discount

---

## 📄 License

MIT License - feel free to use for learning purposes.

---

## 🙏 Acknowledgments

- **Pragma.ai** for the coding challenge
- **FastAPI** for the framework
- **SQLModel** for the elegant ORM

---

**Built with ❤️ using FastAPI, PostgreSQL, and modern Python practices**
