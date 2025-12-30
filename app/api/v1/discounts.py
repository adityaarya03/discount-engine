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
    Create a new discount rule.
    
    **Requires admin privileges.**
    
    The config field should contain:
    - conditions: When the discount applies
    - action: What discount to give
    
    Examples in DiscountRuleCreate schema documentation.
    """
    rule = DiscountRule(
        name=rule_data.name,
        discount_type=rule_data.discount_type,
        priority=rule_data.priority,
        is_active=rule_data.is_active,
        is_stackable=rule_data.is_stackable,
        config=rule_data.config,
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