# 📝 Discount API Examples - Type-Safe Conditions

## ✅ What Changed?

The discount creation API now uses **type-safe Pydantic models** for conditions instead of raw JSON.

**Benefits:**
- ✅ FastAPI validates conditions at API level
- ✅ Clear error messages if fields are missing/invalid
- ✅ Auto-generated OpenAPI docs show exact structure
- ✅ No more silent failures from invalid conditions

---

## 🎯 Creating Discounts

### Endpoint
```
POST /api/v1/discounts/
Authorization: Bearer <admin_token>
```

---

## 📋 Examples by Scope

### 1. CART Scope - Percentage Discount with Max Cap

**Use Case:** 10% off on orders above ₹5000, capped at ₹1000

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

**Validation:**
- ✅ `conditions` validated as `CartConditions`
- ✅ `min_cart_value` must be >= 0 (or omitted)
- ✅ FastAPI returns 422 if invalid

---

### 2. CART Scope - Flat Loyalty Reward

**Use Case:** ₹500 off after 5 completed purchases (rewarded buyer offer)

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

**Validation:**
- ✅ `min_purchases` must be >= 1
- ✅ `status_filter` is optional (defaults to ["COMPLETED"])

---

### 3. CART Scope - Flat Coupon

**Use Case:** ₹500 off coupon for cart > ₹2000

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

---

### 4. CATEGORY Scope - Percentage Discount

**Use Case:** 5% off on 3+ Electronics items

```json
{
  "name": "5% off on 3+ Electronics items",
  "scope": "CATEGORY",
  "value_type": "PERCENTAGE",
  "value": 5.0,
  "conditions": {
    "category_id": "b15f3e65-0e05-4b4d-bce7-ce8a3186de83",
    "min_quantity": 3
  },
  "max_discount_amount": null,
  "requires_loyalty": false,
  "is_stackable": true,
  "priority": 3,
  "coupon_code": null
}
```

**Validation:**
- ✅ `category_id` is REQUIRED for CATEGORY scope
- ✅ Must be valid UUID format
- ✅ `min_quantity` defaults to 1 if omitted

---

### 5. CATEGORY Scope - Percentage Coupon with Max Cap

**Use Case:** ELEC15 coupon - 15% off Electronics (max ₹600)

```json
{
  "name": "Electronics Bonanza - 15% Off (max ₹600)",
  "scope": "CATEGORY",
  "value_type": "PERCENTAGE",
  "value": 15.0,
  "conditions": {
    "category_id": "b15f3e65-0e05-4b4d-bce7-ce8a3186de83",
    "min_quantity": 1
  },
  "max_discount_amount": 600,
  "requires_loyalty": false,
  "is_stackable": true,
  "priority": 3,
  "coupon_code": "ELEC15"
}
```

---

### 6. PRODUCT Scope - Specific Products Discount

**Use Case:** 20% off on specific products

```json
{
  "name": "20% off Selected Products",
  "scope": "PRODUCT",
  "value_type": "PERCENTAGE",
  "value": 20.0,
  "conditions": {
    "product_ids": [
      "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    ],
    "min_quantity": 1
  },
  "max_discount_amount": 500,
  "is_stackable": true,
  "coupon_code": "PROD20"
}
```

**Validation:**
- ✅ `product_ids` is REQUIRED for PRODUCT scope
- ✅ Must contain at least 1 UUID
- ✅ All UUIDs must be valid format

---

## ❌ Error Examples

### Missing Required Field

```json
// ❌ CATEGORY scope without category_id
{
  "scope": "CATEGORY",
  "conditions": {
    "min_quantity": 3
  }
}

// Response: 422 Unprocessable Entity
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

---

### Invalid UUID Format

```json
// ❌ Invalid category_id
{
  "scope": "CATEGORY",
  "conditions": {
    "category_id": "invalid-uuid",
    "min_quantity": 3
  }
}

// Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": ["body", "conditions", "category_id"],
      "msg": "Input should be a valid UUID"
    }
  ]
}
```

---

### Wrong Condition Type for Scope

```json
// ❌ Using CartConditions for CATEGORY scope
{
  "scope": "CATEGORY",
  "conditions": {
    "min_cart_value": 5000  // Wrong! Should be category_id
  }
}

// Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Scope 'CATEGORY' requires CategoryConditions but got CartConditions"
    }
  ]
}
```

---

## 📊 Condition Fields Reference

### CartConditions (for CART scope)

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `min_cart_value` | int | No | >= 0 | Minimum cart subtotal in ₹ |
| `min_purchases` | int | No | >= 1 | Min completed orders (for loyalty rewards) |
| `status_filter` | array | No | - | Order statuses to count (default: ["COMPLETED"]) |

### CategoryConditions (for CATEGORY scope)

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `category_id` | UUID | **Yes** | Valid UUID | Target category |
| `min_quantity` | int | No | >= 1 | Min items from category (default: 1) |

### ProductConditions (for PRODUCT scope)

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `product_ids` | array | **Yes** | Min 1 UUID | List of target products |
| `min_quantity` | int | No | >= 1 | Min matching products (default: 1) |

---

## 🎯 Additional Fields (All Scopes)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `max_discount_amount` | int | No | Maximum discount cap in ₹ (for PERCENTAGE) |
| `requires_loyalty` | bool | No | Whether discount requires loyalty membership (default: false) |
| `is_stackable` | bool | No | Can combine with other discounts (default: false) |
| `coupon_code` | string | No | NULL = auto-apply, non-NULL = manual entry |
| `priority` | int | No | Lower = higher priority (default: 0) |
| `is_active` | bool | No | Enable/disable rule (default: true) |

---

## 🔍 Getting Category/Product IDs

### Get Categories
```bash
GET /api/v1/categories/

Response:
[
  {
    "id": "b15f3e65-0e05-4b4d-bce7-ce8a3186de83",
    "name": "Electronics",
    "slug": "electronics"
  }
]
```

### Get Products
```bash
GET /api/v1/products/

Response:
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Smart Watch",
    "category_id": "b15f3e65-0e05-4b4d-bce7-ce8a3186de83"
  }
]
```

---

## 📖 OpenAPI Docs

View auto-generated examples at:
```
http://localhost:8000/docs#/Discounts/create_discount_rule_api_v1_discounts__post
```

FastAPI automatically shows the correct condition structure for each scope!

---

## ✨ Key Takeaways

1. **Type Safety**: Conditions are validated by Pydantic before reaching database
2. **Self-Documenting**: OpenAPI schema shows exact structure
3. **Clear Errors**: FastAPI returns precise error messages
4. **Defensive Runtime**: Strategy code also validates (safety net)
5. **Flexible Storage**: Still stored as JSONB (no schema changes needed)

This is the **production-standard approach** used by Shopify, Stripe, and other major APIs!
