"""
Order endpoints: create order, list orders, get order details.
"""
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, status
from sqlmodel import select

from app.api.deps import DBSession, CurrentUser
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import (
    OrderCreate, 
    OrderResponse, 
    OrderListResponse,
    OrderItemResponse,
    AppliedDiscountResponse
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.services.discount_engine.engine import DiscountEngine


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    current_user: CurrentUser,
    session: DBSession
):
    """
    Create a new order with automatic discount calculation.
    """
    # Validate all products exist and have stock
    product_ids = [item.product_id for item in order_data.items]
    query = select(Product).where(Product.id.in_(product_ids), Product.is_active == True)
    result = session.exec(query)
    products = {p.id: p for p in result.all()}
    
    if len(products) != len(product_ids):
        missing = set(product_ids) - set(products.keys())
        raise NotFoundException(detail=f"Products not found: {missing}")
    
    # Check stock availability
    for item in order_data.items:
        product = products[item.product_id]
        if product.stock_quantity < item.quantity:
            raise BadRequestException(
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )
    
    # Create order
    order = Order(
        user_id=current_user.id,
        status=OrderStatus.PENDING,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("0.00")
    )
    session.add(order)
    session.flush()  # Get order.id
    
    # Create order items with denormalized data
    subtotal = Decimal("0.00")
    for item_data in order_data.items:
        product = products[item_data.product_id]
        item_subtotal = product.price * item_data.quantity
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_category_id=product.category_id,  # DENORMALIZED for performance
            unit_price=product.price,
            quantity=item_data.quantity,
            subtotal=item_subtotal,
            discount_amount=Decimal("0.00")
        )
        session.add(order_item)
        subtotal += item_subtotal
        
        # Decrement stock
        product.stock_quantity -= item_data.quantity
    
    order.subtotal = subtotal
    order.total_amount = subtotal
    
    session.commit()
    session.refresh(order)
    
    # Apply discount engine
    discount_engine = DiscountEngine(session)
    discount_result = discount_engine.apply_discounts(order, current_user)
    
    session.refresh(order)
    
    # Fetch order with relationships for response
    query = select(Order).where(Order.id == order.id)
    result = session.exec(query)
    order_with_relations = result.one()
    
    # Build response
    return OrderResponse(
        id=order_with_relations.id,
        user_id=order_with_relations.user_id,
        status=order_with_relations.status,
        subtotal=order_with_relations.subtotal,
        discount_amount=order_with_relations.discount_amount,
        tax_amount=order_with_relations.tax_amount,
        total_amount=order_with_relations.total_amount,
        created_at=str(order_with_relations.created_at),
        items=[OrderItemResponse.model_validate(item) for item in order_with_relations.items],
        applied_discounts=discount_result["applied_rules"]
    )


@router.get("/", response_model=list[OrderListResponse])
def list_orders(
    current_user: CurrentUser,
    session: DBSession,
    skip: int = 0,
    limit: int = 20
):
    """
    List all orders for the current user.
    
    Returns paginated list without order items (use GET /orders/{id} for details).
    """
    query = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = session.exec(query)
    orders = result.all()
    
    return [
        OrderListResponse(
            id=order.id,
            status=order.status,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            created_at=str(order.created_at),
            items_count=len(order.items)
        )
        for order in orders
    ]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    current_user: CurrentUser,
    session: DBSession
):
    """
    Get detailed order information with discount breakdown.
    
    Returns:
    - Order details
    - All order items
    - Applied discounts with calculation details
    """
    query = select(Order).where(Order.id == order_id)
    result = session.exec(query)
    order = result.one_or_none()
    
    if not order:
        raise NotFoundException(detail="Order not found")
    
    # Security: Users can only view their own orders
    if order.user_id != current_user.id:
        raise NotFoundException(detail="Order not found")
    
    # Build discount breakdown
    applied_discounts = [
        AppliedDiscountResponse(
            rule_name=ad.discount_rule.name,
            rule_type=ad.discount_rule.discount_type.value,
            discount_amount=float(ad.discount_amount),
            details=ad.calculation_details
        )
        for ad in order.applied_discounts
    ]
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        created_at=str(order.created_at),
        items=[OrderItemResponse.model_validate(item) for item in order.items],
        applied_discounts=applied_discounts
    )