# 🏗️ Architecture & Design Documentation

## Table of Contents
- [System Overview](#system-overview)
- [Design Patterns](#design-patterns)
- [Database Design](#database-design)
- [Stacking Logic](#stacking-logic)
- [Security Architecture](#security-architecture)
- [Scalability Considerations](#scalability-considerations)

---

## 🎯 System Overview

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│                       Client Layer                         │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐              │
│  │  Browser  │  │  Postman  │  │  Mobile  │              │
│  └─────┬─────┘  └─────┬─────┘  └────┬─────┘              │
└────────┼──────────────┼─────────────┼────────────────────┘
         │              │             │
         └──────────────┴─────────────┘
                        │
                   HTTP/REST (JSON)
                        │
         ┌──────────────▼─────────────────┐
         │    FastAPI Application         │
         │                                 │
         │  ┌──────────────────────────┐  │
         │  │   API Layer (Routers)    │  │
         │  │  - auth.py               │  │
         │  │  - orders.py             │  │
         │  │  - products.py           │  │
         │  │  - discounts.py          │  │
         │  └────────┬─────────────────┘  │
         │           │                     │
         │  ┌────────▼─────────────────┐  │
         │  │  Business Logic Layer    │  │
         │  │                          │  │
         │  │  ┌────────────────────┐  │  │
         │  │  │ Discount Engine    │  │  │
         │  │  │  ┌──────────────┐  │  │  │
         │  │  │  │  Strategies  │  │  │  │
         │  │  │  │  - Cart      │  │  │  │
         │  │  │  │  - Category  │  │  │  │
         │  │  │  │  - Product   │  │  │  │
         │  │  │  └──────────────┘  │  │  │
         │  │  │  ┌──────────────┐  │  │  │
         │  │  │  │  Conditions  │  │  │  │
         │  │  │  │  - MinCart   │  │  │  │
         │  │  │  │  - MinPurch  │  │  │  │
         │  │  │  │  - Category  │  │  │  │
         │  │  │  └──────────────┘  │  │  │
         │  │  │  ┌──────────────┐  │  │  │
         │  │  │  │   Stacking   │  │  │  │
         │  │  │  │    Logic     │  │  │  │
         │  │  │  └──────────────┘  │  │  │
         │  │  └────────────────────┘  │  │
         │  └──────────┬───────────────┘  │
         │             │                   │
         │  ┌──────────▼───────────────┐  │
         │  │  Data Access Layer       │  │
         │  │  (SQLModel ORM)          │  │
         │  │  - User                  │  │
         │  │  - Order                 │  │
         │  │  - Product               │  │
         │  │  - DiscountRule          │  │
         │  └──────────┬───────────────┘  │
         └─────────────┼───────────────────┘
                       │
         ┌─────────────▼───────────────┐
         │      PostgreSQL 16          │
         │                             │
         │  ┌─────────────────────┐   │
         │  │  Relational Tables  │   │
         │  │  + JSONB Columns    │   │
         │  └─────────────────────┘   │
         └─────────────────────────────┘
```

### Request Lifecycle

```
1. HTTP Request arrives
   │
   ├──> CORS Middleware (validates origin)
   │
   ├──> JWT Auth Middleware (if protected endpoint)
   │    │
   │    ├──> Extract token from Authorization header
   │    ├──> Verify signature & expiry
   │    └──> Inject user into request context
   │
   ├──> Pydantic Validation (request body/params)
   │    │
   │    ├──> Type checking
   │    ├──> Field validation
   │    └──> Return 422 if invalid
   │
   ├──> Route Handler (endpoint function)
   │    │
   │    ├──> Dependency Injection
   │    │    ├──> Database Session
   │    │    └──> Current User
   │    │
   │    ├──> Business Logic
   │    │    ├──> DiscountEngine.apply_discounts()
   │    │    ├──> Strategy Pattern execution
   │    │    └──> Stacking logic
   │    │
   │    ├──> Database Operations
   │    │    ├──> SQLModel queries
   │    │    ├──> Create/Update/Read
   │    │    └──> Commit transaction
   │    │
   │    └──> Return Response
   │
   ├──> Pydantic Serialization (response model)
   │
   └──> HTTP Response (JSON)
```

---

## 🎨 Design Patterns

### 1. Strategy Pattern

**File**: `app/services/discount_engine/strategies.py`

**Problem**: Different discount scopes (CART, CATEGORY, PRODUCT) require different calculation logic.

**Solution**: Encapsulate each calculation algorithm in its own class with a common interface.

```python
┌─────────────────────┐
│ DiscountStrategy    │ ← Abstract base
│ (Base Class)        │
├─────────────────────┤
│ + is_applicable()   │
│ + calculate()       │
└──────────┬──────────┘
           │
           ├──────────────────┬──────────────────┐
           │                  │                  │
┌──────────▼──────────┐ ┌────▼─────────┐ ┌─────▼──────────┐
│  CartStrategy       │ │CategoryStrat │ │ProductStrategy │
├─────────────────────┤ ├──────────────┤ ├────────────────┤
│ calculate():        │ │calculate():  │ │calculate():    │
│  base = order.total │ │  base = sum  │ │  base = sum    │
│  return discount    │ │  (filtered)  │ │  (filtered)    │
└─────────────────────┘ └──────────────┘ └────────────────┘
```

**Benefits**:
- ✅ Open/Closed Principle: Add new scope without modifying existing code
- ✅ Single Responsibility: Each strategy handles one calculation type
- ✅ Testability: Each strategy can be unit tested independently

**Usage**:
```python
strategy = get_strategy(discount_rule, session)
if strategy.is_applicable(order, user):
    result = strategy.calculate(order, user)
```

---

### 2. Chain of Responsibility

**File**: `app/services/discount_engine/conditions.py`

**Problem**: Discount rules have multiple independent conditions that must all pass.

**Solution**: Chain of condition checkers where each checker validates one aspect.

```python
┌────────────────────┐
│ ConditionChecker   │ ← Abstract base
│ (Base Class)       │
├────────────────────┤
│ + check()          │
│ + get_error()      │
└──────────┬─────────┘
           │
           ├─────────────────┬─────────────────┬────────────────┐
           │                 │                 │                │
┌──────────▼──────┐ ┌────────▼────────┐ ┌─────▼──────┐ ┌─────▼────────┐
│MinCartValue     │ │MinPurchases     │ │Category    │ │ProductFilter │
│Condition        │ │Condition        │ │Condition   │ │Condition     │
├─────────────────┤ ├─────────────────┤ ├────────────┤ ├──────────────┤
│check():         │ │check():         │ │check():    │ │check():      │
│ if cart < min:  │ │ count = query() │ │ items = [] │ │ items = []   │
│   return False  │ │ if count < min: │ │ if no items│ │ if no match  │
│ return True     │ │   return False  │ │   return F │ │   return F   │
└─────────────────┘ └─────────────────┘ └────────────┘ └──────────────┘

Flow:
condition1.check() → PASS → condition2.check() → PASS → condition3.check() → PASS → ✓
                   → FAIL →                                                           ✗
```

**Benefits**:
- ✅ Reusable: Same conditions can be used across multiple discount rules
- ✅ Composable: Easy to add new condition types
- ✅ Maintainable: Each condition is isolated and testable

**Usage**:
```python
condition_chain = ConditionChain()
all_passed, error = condition_chain.check_all(
    order, user, conditions, session
)
```

---

### 3. Dependency Injection

**Framework**: FastAPI's `Depends()`

**Problem**: Components need access to database sessions, current user, etc. without tight coupling.

**Solution**: FastAPI automatically injects dependencies into route handlers.

```python
# Dependencies
def get_session():
    with Session(engine) as session:
        yield session

def get_current_user(token: str, session: Session):
    # Verify JWT, return user
    return user

# Route Handler
@router.post("/orders/")
def create_order(
    order_data: OrderCreate,
    session: Session = Depends(get_session),        # ← Auto-injected
    current_user: User = Depends(get_current_user)  # ← Auto-injected
):
    # Use session and current_user
    ...
```

**Benefits**:
- ✅ Loose Coupling: Handler doesn't create dependencies
- ✅ Testability: Easy to inject mocks for testing
- ✅ Lifecycle Management: FastAPI handles cleanup (DB connections)

---

### 4. Repository Pattern (Implicit)

**Location**: SQLModel queries in endpoints

**Pattern**: Data access logic is centralized in models with class methods.

```python
# User model has business logic methods
class User(SQLModel, table=True):
    def is_loyalty_member(self, session: Session) -> bool:
        count = session.exec(
            select(func.count(Order.id))
            .where(Order.user_id == self.id)
            .where(Order.status == OrderStatus.COMPLETED)
        ).one()
        return count >= 10
```

**Benefits**:
- ✅ Encapsulation: Data access logic lives with the model
- ✅ Reusability: Same logic used across multiple endpoints
- ✅ Domain-Driven Design: Models have business logic, not just data

---

## 🗄️ Database Design

### Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id (PK)         │
│ email (unique)  │
│ password_hash   │
│ first_name      │
│ last_name       │
│ phone           │
│ role (enum)     │
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐       ┌──────────────────┐
│     Order       │       │    Category      │
├─────────────────┤       ├──────────────────┤
│ id (PK)         │       │ id (PK)          │
│ user_id (FK)    │       │ name (unique)    │
│ status (enum)   │       │ slug (unique)    │
│ subtotal        │       │ description      │
│ discount_amount │       │ is_active        │
│ tax_amount      │       │ created_at       │
│ total_amount    │       │ updated_at       │
│ created_at      │       └────────┬─────────┘
│ updated_at      │                │ 1
└────────┬────────┘                │
         │ 1                       │
         │                         │ N
         │ N               ┌───────▼──────────┐
┌────────▼────────┐        │     Product      │
│   OrderItem     │        ├──────────────────┤
├─────────────────┤        │ id (PK)          │
│ id (PK)         │ N      │ category_id (FK) │
│ order_id (FK)   ├────────┤ name             │
│ product_id (FK) │    1   │ description      │
│ product_name    │◄───────┤ price            │
│ category_id(*)  │        │ stock_quantity   │
│ unit_price(*)   │        │ sku (unique)     │
│ quantity        │        │ is_active        │
│ subtotal        │        │ created_at       │
│ discount_amt    │        │ updated_at       │
└─────────────────┘        └──────────────────┘
         │ N
         │
         │ N
┌────────▼────────┐        ┌──────────────────┐
│ AppliedDiscount │  N     │  DiscountRule    │
├─────────────────┤◄───────├──────────────────┤
│ id (PK)         │    1   │ id (PK)          │
│ order_id (FK)   │        │ name             │
│ rule_id (FK)    ├───────►│ scope (enum)     │
│ discount_amount │        │ value_type (enum)│
│ details (JSONB) │        │ value            │
│ created_at      │        │ config (JSONB)   │
└─────────────────┘        │ is_stackable     │
                           │ coupon_code      │
                           │ priority         │
                           │ is_active        │
                           │ created_at       │
                           │ updated_at       │
                           └──────────────────┘

(*) = Denormalized for performance
```

### Hybrid Design (SQL + JSONB)

**Why JSONB?**

Traditional approach would require separate tables for each discount type:
```
cart_discounts
category_discounts
product_discounts
bogo_discounts
...
```

**Problems**:
- Schema migration for every new discount type
- Complex queries with UNION
- Rigid structure

**Our Solution**: Hybrid Design

```python
# Fixed SQL columns (queryable, indexed)
name = "10% off cart > ₹5000"
scope = "CART"  # Enum for querying
value_type = "PERCENTAGE"
value = 10.0
is_active = True  # Indexed for fast filtering

# Flexible JSONB config (varies by type)
config = {
    "conditions": {
        "min_cart_value": 5000  # Cart-specific
    },
    "max_discount_amount": 1000,
    "loyalty_stacking_only": true
}
```

**Benefits**:
✅ **Flexibility**: Add new condition types without migrations
✅ **Queryability**: `WHERE is_active = true` is fast (uses index)
✅ **Type Safety**: Pydantic validates JSONB structure at API level
✅ **Future-Proof**: New discount types = just new config structure

### Denormalization Strategy

**OrderItem Denormalized Fields**:
```python
product_name: str           # Snapshot at purchase time
product_category_id: UUID   # For fast category filtering
unit_price: Decimal         # Price at purchase time
```

**Why?**
1. **Historical Accuracy**:
   - Product price changes over time
   - Order should reflect purchase-time state

2. **Performance**:
   - No JOIN needed for category discount filtering
   - Query: `WHERE product_category_id = ?` (indexed)

3. **Data Integrity**:
   - Even if product deleted, order remains valid

**Trade-off**:
- ❌ More storage
- ✅ Faster queries
- ✅ Historical accuracy

---

## 🧮 Stacking Logic

### Decision Tree

```
Is coupon applied?
├─ YES → Coupon Branch
│   │
│   ├─ Is coupon stackable?
│   │   ├─ NO → RETURN [coupon ONLY]
│   │   │
│   │   └─ YES → Coupon + Auto-Apply
│   │       │
│   │       ├─ Get all applicable auto-apply discounts
│   │       │
│   │       └─ For each auto-apply:
│   │           ├─ Is it stackable?
│   │           │   ├─ NO → SKIP
│   │           │   └─ YES → Continue
│   │           │
│   │           ├─ Does it require loyalty?
│   │           │   ├─ YES + not member → SKIP
│   │           │   └─ NO or is member → ADD
│   │           │
│   │           └─ RETURN [coupon + eligible auto-apply]
│
└─ NO → Auto-Apply Only
    │
    ├─ Get all applicable auto-apply discounts
    │
    ├─ Separate into stackable_for_user & non_stackable
    │   │
    │   └─ stackable_for_user considers loyalty_stacking_only flag
    │
    ├─ IF stackable_for_user has items:
    │   │
    │   ├─ total_stackable = SUM(stackable_for_user)
    │   ├─ best_single = MAX(all_applicable)
    │   │
    │   └─ IF total_stackable >= best_single:
    │       ├─ RETURN stackable_for_user
    │       └─ ELSE: RETURN [best_single]
    │
    └─ ELSE (no stackable):
        └─ RETURN [best_single]
```

### Stacking Algorithm Pseudocode

```python
def _handle_stacking(coupon, auto_apply_discounts, user):
    is_loyalty_member = user.is_loyalty_member()

    # CASE 1: Coupon exists
    if coupon:
        if not coupon.is_stackable:
            return [coupon]  # Non-stackable coupon wins

        # Stackable coupon - check auto-apply
        final = [coupon]

        for discount in auto_apply_discounts:
            # Must be stackable
            if not discount.is_stackable:
                continue

            # Check loyalty gate
            loyalty_only = discount.config.get("loyalty_stacking_only")
            if loyalty_only and not is_loyalty_member:
                continue

            final.append(discount)

        return final

    # CASE 2: No coupon
    else:
        stackable = []
        non_stackable = []

        for discount in auto_apply_discounts:
            if discount.is_stackable:
                loyalty_only = discount.config.get("loyalty_stacking_only")

                # Check if user qualifies for stacking
                if not loyalty_only or is_loyalty_member:
                    stackable.append(discount)
            else:
                non_stackable.append(discount)

        if stackable:
            total_stackable = sum(d.amount for d in stackable)
            best_single = max(auto_apply_discounts, key=lambda d: d.amount)

            # Return whichever is better
            if total_stackable >= best_single.amount:
                return stackable
            else:
                return [best_single]

        # No stackable - return best single
        if auto_apply_discounts:
            return [max(auto_apply_discounts, key=lambda d: d.amount)]

        return []
```

---

## 🔒 Security Architecture

### Authentication Flow

```
1. User Login
   ├─> POST /auth/login { email, password }
   │
   ├─> Verify password (bcrypt)
   │   ├─> Hash input password
   │   ├─> Compare with stored hash
   │   └─> Fail if mismatch
   │
   ├─> Generate JWT
   │   ├─> Payload: { user_id, role, exp }
   │   ├─> Sign with SECRET_KEY (HS256)
   │   └─> Return token
   │
   └─> Client stores token

2. Authenticated Request
   ├─> Request with header: Authorization: Bearer <token>
   │
   ├─> Extract token from header
   │
   ├─> Verify JWT
   │   ├─> Decode with SECRET_KEY
   │   ├─> Check expiry
   │   ├─> Validate signature
   │   └─> Fail if invalid
   │
   ├─> Query user from database (using user_id from token)
   │
   ├─> Check if user.is_active
   │
   └─> Inject user into request context
```

### Password Security

```python
# Registration
password = "user_password"
    │
    ├─> Bcrypt hashing
    │   ├─> Generate salt
    │   ├─> Hash password + salt
    │   └─> Store hash (NOT plain password)
    │
    └─> Save to database: password_hash

# Login
input_password = "user_password"
    │
    ├─> Retrieve password_hash from database
    │
    ├─> Bcrypt verify
    │   ├─> Hash input with same salt
    │   ├─> Compare hashes
    │   └─> Return True/False
    │
    └─> Generate JWT if verified
```

**Security Features**:
- ✅ Bcrypt hashing (CPU-intensive, resistant to brute force)
- ✅ Salted hashes (prevents rainbow table attacks)
- ✅ JWT stateless auth (no session storage)
- ✅ Token expiry (configurable TTL)
- ✅ HTTPS recommended in production

### Role-Based Access Control

```python
# Permission Matrix
┌───────────────┬──────────┬───────┐
│   Endpoint    │ CUSTOMER │ ADMIN │
├───────────────┼──────────┼───────┤
│ POST /orders/ │    ✓     │   ✓   │
│ GET /orders/  │  Own only│  All  │
│ POST/discounts│    ✗     │   ✓   │
│ DELETE/disc   │    ✗     │   ✓   │
└───────────────┴──────────┴───────┘
```

**Implementation**:
```python
# Admin-only decorator
def get_current_admin_user(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(403, "Admin access required")
    return current_user

# Usage
@router.post("/discounts/")
def create_discount(
    admin: User = Depends(get_current_admin_user)
):
    # Only admins reach here
    ...
```

---

## 📈 Scalability Considerations

### Current Architecture

**Strengths**:
- ✅ Stateless auth (horizontal scaling possible)
- ✅ JSONB flexibility (no schema migrations)
- ✅ Denormalized data (fewer JOINs)

**Bottlenecks**:
- ❌ No caching (DB hit on every request)
- ❌ N+1 queries possible
- ❌ No connection pooling config

### Scaling Roadmap

#### Phase 1: Caching Layer (Redis)
```
┌─────────┐     ┌───────┐     ┌──────────┐
│ FastAPI │────►│ Redis │────►│PostgreSQL│
└─────────┘     └───────┘     └──────────┘
                Cache           Database

Cache Strategy:
- Discount rules (TTL: 5 min, invalidate on update)
- User loyalty status (TTL: 1 hour)
- Product catalog (TTL: 10 min)
```

#### Phase 2: Read Replicas
```
┌─────────┐     ┌─────────────┐
│ FastAPI │────►│ Primary(W) │
│         │     └──────┬──────┘
│         │            │ Replication
│         │     ┌──────▼──────┐
│         │────►│ Replica(R)  │
└─────────┘     └─────────────┘

Reads: 90% → Replica
Writes: 10% → Primary
```

#### Phase 3: Microservices (Future)
```
┌──────────────┐
│ API Gateway  │
└───────┬──────┘
        │
        ├──────► Order Service
        ├──────► Discount Service
        ├──────► Auth Service
        └──────► Product Service
```

### Performance Optimizations

**Already Implemented**:
- ✅ Denormalized category_id in OrderItem
- ✅ Indexes on foreign keys
- ✅ Decimal for money (no float rounding)

**Future**:
- ⏳ Redis caching
- ⏳ Database query optimization (EXPLAIN ANALYZE)
- ⏳ Connection pooling (SQLAlchemy pool_size)
- ⏳ Async database driver (asyncpg)
- ⏳ Background jobs for heavy operations (Celery)

---

## 🧪 Testing Strategy

### Test Pyramid

```
        ┌──────────┐
        │   E2E    │  ← Few (Postman, full flow)
        └──────────┘
       ┌────────────┐
       │Integration │  ← Some (API + DB tests)
       └────────────┘
      ┌──────────────┐
      │  Unit Tests  │  ← Many (Logic, conditions, strategies)
      └──────────────┘
```

### Unit Test Coverage Goals

**Priority 1** (Core Logic):
- ✅ Stacking algorithm (`_handle_stacking`)
- ✅ Condition checkers (all conditions)
- ✅ Strategy calculations (all strategies)

**Priority 2** (Business Logic):
- ✅ Loyalty membership check
- ✅ Coupon validation
- ✅ Discount applicability

**Priority 3** (Integration):
- ✅ Full order flow (create → apply discounts → save)
- ✅ Auth flow (register → login → protected endpoint)

---

## 📚 References

**Design Patterns**:
- Strategy Pattern: Gang of Four
- Chain of Responsibility: Gang of Four
- Dependency Injection: Martin Fowler

**Architecture**:
- Clean Architecture: Robert C. Martin
- Domain-Driven Design: Eric Evans
- RESTful API Design: Roy Fielding

**FastAPI**:
- Official Documentation: https://fastapi.tiangolo.com/
- Dependency Injection: https://fastapi.tiangolo.com/tutorial/dependencies/

---

**Last Updated**: Dec 2025
**Author**: Assignment for Pragma.ai
**Version**: 1.0
