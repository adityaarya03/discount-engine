# 🧪 Postman Testing Guide

## 🌐 Base URL

**Local Development:**
```
http://localhost:8000
```

**API Base:**
```
http://localhost:8000/api/v1
```

**Swagger Docs (Interactive):**
```
http://localhost:8000/docs
```

---

## 🚀 Quick Start

### 1. Start the Application

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Run the FastAPI app
uvicorn app.main:app --reload --port 8000

# Or if running from main.py
python -m app.main
```

### 2. Verify it's running

Open in browser: `http://localhost:8000`

Should see:
```json
{
  "status": "healthy",
  "app": "Discount Engine API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

## 📋 Postman Collection Structure

### Environment Variables (Set these first!)

Create a new Postman Environment with these variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:8000/api/v1` | API base URL |
| `admin_token` | *(will be set after login)* | Admin JWT token |
| `user_token` | *(will be set after login)* | Customer JWT token |

---

## 🧪 Test Scenarios

### 🔐 1. Authentication

#### 1.1 Register Admin User

**POST** `{{base_url}}/auth/register`

**Body (JSON):**
```json
{
  "email": "admin@example.com",
  "password": "admin123",
  "first_name": "Admin",
  "last_name": "User",
  "phone": "+919876543210",
  "role": "ADMIN"
}
```

**Expected Response (201):**
```json
{
  "id": "uuid",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "role": "ADMIN",
  "is_active": true
}
```

#### 1.2 Register Customer User

**POST** `{{base_url}}/auth/register`

**Body (JSON):**
```json
{
  "email": "customer@example.com",
  "password": "customer123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+919123456789",
  "role": "CUSTOMER"
}
```

#### 1.3 Login Admin

**POST** `{{base_url}}/auth/login`

**Body (JSON):**
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**⚠️ IMPORTANT:** Copy the `access_token` and set it as `{{admin_token}}` in your environment!

#### 1.4 Login Customer

**POST** `{{base_url}}/auth/login`

**Body (JSON):**
```json
{
  "email": "customer@example.com",
  "password": "customer123"
}
```

**⚠️ IMPORTANT:** Copy the `access_token` and set it as `{{user_token}}` in your environment!

---

### 📦 2. Products & Categories

#### 2.1 List Categories

**GET** `{{base_url}}/categories/`

**No auth required**

**Expected Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "Electronics",
    "slug": "electronics",
    "description": "Electronic gadgets"
  }
]
```

**💡 Tip:** Copy a `category_id` for creating category-based discounts later!

#### 2.2 List Products

**GET** `{{base_url}}/products/`

**No auth required**

**Query Parameters:**
- `category_id` (optional): Filter by category
- `skip` (optional): Pagination offset
- `limit` (optional): Items per page

**Example:**
```
GET {{base_url}}/products/?category_id=<uuid>&limit=10
```

---

### 💰 3. Discount Management (Admin Only)

#### 3.1 Create Cart-Level Percentage Discount

**POST** `{{base_url}}/discounts/`

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Body (JSON):**
```json
{
  "name": "10% off on orders above ₹5000 (max ₹1000)",
  "scope": "CART",
  "value_type": "PERCENTAGE",
  "value": 10.0,
  "conditions": {
    "min_cart_value": 5000
  },
  "max_discount_amount": 1000,
  "requires_loyalty": false,
  "is_stackable": false,
  "priority": 2,
  "coupon_code": null
}
```

**Expected Response (201):**
```json
{
  "id": "uuid",
  "name": "10% off on orders above ₹5000 (max ₹1000)",
  "scope": "CART",
  "value_type": "PERCENTAGE",
  "value": 10.0,
  "config": {
    "conditions": {
      "min_cart_value": 5000
    },
    "max_discount_amount": 1000,
    "requires_loyalty": false
  },
  "is_active": true,
  "created_at": "2025-01-01T00:00:00"
}
```

#### 3.2 Create Loyalty Reward (After 5 Purchases)

**POST** `{{base_url}}/discounts/`

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Body (JSON):**
```json
{
  "name": "₹500 Loyalty Reward (After 5 Purchases)",
  "scope": "CART",
  "value_type": "FLAT",
  "value": 500.0,
  "conditions": {
    "min_purchases": 5,
    "status_filter": ["COMPLETED"]
  },
  "requires_loyalty": false,
  "is_stackable": true,
  "priority": 1,
  "coupon_code": null
}
```

#### 3.3 Create Category-Based Discount

**POST** `{{base_url}}/discounts/`

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Body (JSON):**
```json
{
  "name": "5% off on 3+ Electronics items",
  "scope": "CATEGORY",
  "value_type": "PERCENTAGE",
  "value": 5.0,
  "conditions": {
    "category_id": "<paste-electronics-category-uuid-here>",
    "min_quantity": 3
  },
  "max_discount_amount": null,
  "requires_loyalty": false,
  "is_stackable": true,
  "priority": 3,
  "coupon_code": null
}
```

#### 3.4 Create Coupon Code

**POST** `{{base_url}}/discounts/`

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Body (JSON):**
```json
{
  "name": "₹500 Flat Off Coupon",
  "scope": "CART",
  "value_type": "FLAT",
  "value": 500.0,
  "conditions": {
    "min_cart_value": 2000
  },
  "requires_loyalty": false,
  "is_stackable": true,
  "priority": 2,
  "coupon_code": "FLAT500"
}
```

#### 3.5 List All Discounts

**GET** `{{base_url}}/discounts/`

**No auth required** (public endpoint)

**Query Parameters:**
- `is_active` (optional): Filter active/inactive rules
- `skip` (optional): Pagination
- `limit` (optional): Items per page

#### 3.6 Update Discount Rule

**PATCH** `{{base_url}}/discounts/<discount_id>`

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Body (JSON):**
```json
{
  "is_active": false
}
```

#### 3.7 Delete Discount Rule (Soft Delete)

**DELETE** `{{base_url}}/discounts/<discount_id>`

**Headers:**
```
Authorization: Bearer {{admin_token}}
```

**Expected Response (204):** No content

---

### 🛒 4. Order Management

#### 4.1 Create Order (Without Coupon)

**POST** `{{base_url}}/orders/`

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Body (JSON):**
```json
{
  "items": [
    {
      "product_id": "<paste-product-uuid-here>",
      "quantity": 2
    },
    {
      "product_id": "<paste-another-product-uuid-here>",
      "quantity": 1
    }
  ],
  "coupon_code": null
}
```

**Expected Response (201):**
```json
{
  "id": "order-uuid",
  "user_id": "user-uuid",
  "status": "PENDING",
  "subtotal": 6000.00,
  "discount_amount": 600.00,
  "tax_amount": 0.00,
  "total_amount": 5400.00,
  "created_at": "2025-01-01T00:00:00",
  "items": [
    {
      "id": "item-uuid",
      "product_name": "Smart Watch",
      "unit_price": 3000.00,
      "quantity": 2,
      "subtotal": 6000.00
    }
  ],
  "applied_discounts": [
    {
      "rule_name": "10% off on orders above ₹5000 (max ₹1000)",
      "rule_type": "CART:PERCENTAGE",
      "discount_amount": 600.00,
      "details": {
        "scope": "CART",
        "value_type": "percentage",
        "base_amount": 6000.00,
        "percentage": 10.0,
        "calculated_discount": 600.00,
        "discount_amount": 600.00
      }
    }
  ]
}
```

#### 4.2 Create Order (With Coupon)

**POST** `{{base_url}}/orders/`

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Body (JSON):**
```json
{
  "items": [
    {
      "product_id": "<product-uuid>",
      "quantity": 3
    }
  ],
  "coupon_code": "FLAT500"
}
```

#### 4.3 List My Orders

**GET** `{{base_url}}/orders/`

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Query Parameters:**
- `skip` (optional): Pagination offset
- `limit` (optional): Items per page (default: 20)

**Expected Response (200):**
```json
[
  {
    "id": "order-uuid",
    "status": "PENDING",
    "subtotal": 6000.00,
    "discount_amount": 600.00,
    "total_amount": 5400.00,
    "created_at": "2025-01-01T00:00:00",
    "items_count": 2
  }
]
```

#### 4.4 Get Order Details

**GET** `{{base_url}}/orders/<order_id>`

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Expected Response (200):**
```json
{
  "id": "order-uuid",
  "user_id": "user-uuid",
  "status": "PENDING",
  "subtotal": 6000.00,
  "discount_amount": 600.00,
  "total_amount": 5400.00,
  "items": [...],
  "applied_discounts": [...]
}
```

#### 4.5 Update Order Status (For Testing Loyalty)

**PATCH** `{{base_url}}/orders/<order_id>/status?new_status=COMPLETED`

**Headers:**
```
Authorization: Bearer {{user_token}}
```

**Query Parameters:**
- `new_status`: PENDING | CONFIRMED | COMPLETED | CANCELLED | RETURNED

**Example:**
```
PATCH {{base_url}}/orders/uuid-here/status?new_status=COMPLETED
```

**💡 Use this to complete 5+ orders and test the loyalty reward!**

---

## 🧪 Test Scenarios Step-by-Step

### Scenario 1: Test 10% Cart Discount

1. **Create discount rule** (admin)
   - POST `/discounts/` with cart percentage discount
2. **Create order > ₹5000** (customer)
   - POST `/orders/` with items totaling > ₹5000
3. **Verify discount applied**
   - Check `discount_amount` in response
   - Should be 10% of subtotal, capped at ₹1000

### Scenario 2: Test Loyalty Reward

1. **Create loyalty discount** (admin)
   - POST `/discounts/` with `min_purchases: 5`
2. **Create 5 orders** (customer)
   - POST `/orders/` 5 times
3. **Complete all 5 orders**
   - PATCH `/orders/<id>/status?new_status=COMPLETED` for each
4. **Create 6th order**
   - Should get ₹500 loyalty reward automatically!

### Scenario 3: Test Category Discount

1. **Get Electronics category ID**
   - GET `/categories/`
2. **Create category discount** (admin)
   - POST `/discounts/` with Electronics category_id
3. **Create order with 3+ Electronics**
   - POST `/orders/` with 3+ items from Electronics
4. **Verify 5% discount applied**

### Scenario 4: Test Coupon + Auto-Apply Stacking

1. **Create coupon** (admin)
   - POST `/discounts/` with `coupon_code: "FLAT500"`
2. **Create auto-apply discount** (admin)
   - POST `/discounts/` with `is_stackable: true`
3. **Create order with coupon** (customer)
   - POST `/orders/` with `coupon_code: "FLAT500"`
4. **Verify both discounts applied**
   - `applied_discounts` array should have 2 items

---

## 🔍 Common Issues & Fixes

### Issue 1: 401 Unauthorized

**Problem:** Token expired or invalid

**Fix:**
1. Login again: POST `/auth/login`
2. Copy new `access_token`
3. Update `{{admin_token}}` or `{{user_token}}` in environment

### Issue 2: 404 Not Found on `/discounts/`

**Problem:** Wrong base URL

**Fix:** Use `http://localhost:8000/api/v1/discounts/` (with `/api/v1` prefix)

### Issue 3: 422 Validation Error

**Problem:** Invalid request body

**Fix:** Check error details in response. Common issues:
- Missing required fields
- Wrong UUID format
- Wrong scope/conditions mismatch

**Example Error:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "conditions", "category_id"],
      "msg": "Field required"
    }
  ]
}
```

### Issue 4: Discount Not Applied

**Problem:** Conditions not met

**Fix:** Check:
- Cart value meets `min_cart_value`
- User has enough completed orders for loyalty
- Category/product IDs are correct
- Discount rule is `is_active: true`

---

## 📦 Export Postman Collection

I recommend creating a Postman collection with these requests:

```
Discount Engine API/
├── 🔐 Auth/
│   ├── Register Admin
│   ├── Register Customer
│   ├── Login Admin
│   └── Login Customer
├── 📦 Products/
│   ├── List Categories
│   └── List Products
├── 💰 Discounts (Admin)/
│   ├── Create Cart Percentage
│   ├── Create Loyalty Reward
│   ├── Create Category Discount
│   ├── Create Coupon
│   ├── List Discounts
│   ├── Update Discount
│   └── Delete Discount
└── 🛒 Orders/
    ├── Create Order (No Coupon)
    ├── Create Order (With Coupon)
    ├── List My Orders
    ├── Get Order Details
    └── Update Order Status
```

---

## 🎯 Quick Testing Checklist

- [ ] Health check: GET `http://localhost:8000/`
- [ ] Register admin user
- [ ] Login admin → save token
- [ ] Register customer user
- [ ] Login customer → save token
- [ ] List categories → copy category_id
- [ ] List products → copy product_ids
- [ ] Create 3 discount rules (cart, loyalty, category)
- [ ] Create order as customer
- [ ] Verify discounts applied
- [ ] Create 5 orders and complete them
- [ ] Create 6th order → verify loyalty reward
- [ ] Test coupon code

---

## 🚀 Pro Tips

1. **Use Postman Environment Variables**
   - Set `base_url`, `admin_token`, `user_token`
   - Easier to switch between dev/prod

2. **Use Pre-request Scripts for Auto-Login**
   ```javascript
   // In folder/collection pre-request script
   if (!pm.environment.get("admin_token")) {
       pm.sendRequest({
           url: pm.environment.get("base_url") + "/auth/login",
           method: "POST",
           body: {
               mode: "raw",
               raw: JSON.stringify({
                   email: "admin@example.com",
                   password: "admin123"
               })
           }
       }, (err, res) => {
           pm.environment.set("admin_token", res.json().access_token);
       });
   }
   ```

3. **Use Tests to Auto-Extract IDs**
   ```javascript
   // In "Tests" tab of request
   const response = pm.response.json();
   pm.environment.set("order_id", response.id);
   ```

4. **Check Swagger UI for Examples**
   - Open `http://localhost:8000/docs`
   - Try endpoints interactively
   - Copy working examples to Postman

---

## 📚 See Also

- [API_EXAMPLES.md](API_EXAMPLES.md) - Detailed discount creation examples
- [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md) - System design review
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
