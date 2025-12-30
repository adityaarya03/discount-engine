"""
Discount rule management endpoints.
Public: View active discount rules
Admin: Create, update, delete discount rules
"""
from uuid import UUID
from fastapi import APIRouter, status
from sqlmodel import select

from app.api.deps import DBSession, CurrentAdmin
from app.models.discount import DiscountRule
from app.schemas.discount import (
    DiscountRuleCreate,
    DiscountRuleUpdate,
    DiscountRuleResponse
)
from app.core.exceptions import NotFoundException


router = APIRouter(prefix="/discounts", tags=["Discounts"])


@router.get("/", response_model=list[DiscountRuleResponse])
def list_discount_rules(
    session: DBSession,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 50
):
    """
    List discount rules.
    
    By default, only shows active rules.
    Set is_active=null to see all rules.
    
    Query Parameters:
    - is_active: Filter by active status (default: true)
    - skip: Pagination offset
    - limit: Number of items to return
    """
    query = select(DiscountRule)
    
    if is_active is not None:
        query = query.where(DiscountRule.is_active == is_active)
    
    query = query.order_by(DiscountRule.priority.asc()).offset(skip).limit(limit)
    
    result = session.exec(query)
    rules = result.all()
    
    return [DiscountRuleResponse.model_validate(r) for r in rules]


@router.get("/{rule_id}", response_model=DiscountRuleResponse)
def get_discount_rule(rule_id: UUID, session: DBSession):
    """
    Get a single discount rule by ID.
    
    Shows the complete configuration including conditions and actions.
    """
    query = select(DiscountRule).where(DiscountRule.id == rule_id)
    result = session.exec(query)
    rule = result.one_or_none()
    
    if not rule:
        raise NotFoundException(detail=f"Discount rule with id {rule_id} not found")
    
    return DiscountRuleResponse.model_validate(rule)


@router.post("/", response_model=DiscountRuleResponse, status_code=status.HTTP_201_CREATED)
def create_discount_rule(
    rule_data: DiscountRuleCreate,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Create a new discount rule with type-safe conditions.

    **Requires admin privileges.**

    The API validates conditions based on scope:
    - CART scope: requires CartConditions (min_cart_value, min_purchases)
    - CATEGORY scope: requires CategoryConditions (category_id, min_quantity)
    - PRODUCT scope: requires ProductConditions (product_ids)

    Examples:

    1. Cart-level 10% discount:
    ```json
    {
      "name": "10% off cart > ₹5000",
      "scope": "CART",
      "value_type": "PERCENTAGE",
      "value": 10.0,
      "conditions": {"min_cart_value": 5000},
      "max_discount_amount": 1000,
      "is_stackable": false
    }
    ```

    2. Category-level 5% discount:
    ```json
    {
      "name": "5% off Electronics",
      "scope": "CATEGORY",
      "value_type": "PERCENTAGE",
      "value": 5.0,
      "conditions": {
        "category_id": "uuid-here",
        "min_quantity": 3
      },
      "is_stackable": true
    }
    ```
    """
    rule = DiscountRule(
        name=rule_data.name,
        scope=rule_data.scope,
        value_type=rule_data.value_type,
        value=rule_data.value,
        priority=rule_data.priority,
        is_active=rule_data.is_active,
        is_stackable=rule_data.is_stackable,
        coupon_code=rule_data.coupon_code,
        config=rule_data.to_db_config(),  # Convert Pydantic → JSONB
        start_date=rule_data.start_date,
        end_date=rule_data.end_date
    )

    session.add(rule)
    session.commit()
    session.refresh(rule)
    
    return DiscountRuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=DiscountRuleResponse)
def update_discount_rule(
    rule_id: UUID,
    rule_data: DiscountRuleUpdate,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Update a discount rule.
    
    **Requires admin privileges.**
    
    Only provided fields will be updated.
    Common use case: Deactivate a rule by setting is_active=false.
    """
    # Fetch rule
    query = select(DiscountRule).where(DiscountRule.id == rule_id)
    result = session.exec(query)
    rule = result.one_or_none()
    
    if not rule:
        raise NotFoundException(detail=f"Discount rule with id {rule_id} not found")
    
    # Update fields
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    session.add(rule)
    session.commit()
    session.refresh(rule)
    
    return DiscountRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discount_rule(
    rule_id: UUID,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Soft delete a discount rule (sets is_active to False).
    
    **Requires admin privileges.**
    
    Soft delete is used to preserve historical data.
    The rule will no longer apply to new orders.
    """
    query = select(DiscountRule).where(DiscountRule.id == rule_id)
    result = session.exec(query)
    rule = result.one_or_none()
    
    if not rule:
        raise NotFoundException(detail=f"Discount rule with id {rule_id} not found")
    
    # Soft delete - just deactivate
    rule.is_active = False
    session.add(rule)
    session.commit()
    
    return None