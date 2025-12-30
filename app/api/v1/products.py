"""
Product management endpoints.
Public: List and view products
Admin: Create, update, delete products
"""
from uuid import UUID
from fastapi import APIRouter, status
from sqlmodel import select

from app.api.deps import DBSession, CurrentAdmin
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithCategoryResponse
)
from app.core.exceptions import NotFoundException, ConflictException


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductResponse])
def list_products(
    session: DBSession,
    skip: int = 0,
    limit: int = 50,
    category_id: UUID = None,
    is_active: bool = True
):
    """
    List all products.
    
    Query Parameters:
    - skip: Pagination offset
    - limit: Number of items to return
    - category_id: Filter by category
    - is_active: Show only active products (default: true)
    """
    query = select(Product)
    
    # Apply filters
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    query = query.offset(skip).limit(limit)
    
    result = session.exec(query)
    products = result.all()
    
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductWithCategoryResponse)
def get_product(product_id: UUID, session: DBSession):
    """
    Get a single product by ID with category details.
    """
    query = select(Product).where(Product.id == product_id)
    result = session.exec(query)
    product = result.one_or_none()
    
    if not product:
        raise NotFoundException(detail=f"Product with id {product_id} not found")
    
    return ProductWithCategoryResponse.model_validate(product)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Create a new product.
    
    **Requires admin privileges.**
    """
    # Check if SKU already exists
    query = select(Product).where(Product.sku == product_data.sku)
    result = session.exec(query)
    existing = result.one_or_none()
    
    if existing:
        raise ConflictException(detail=f"Product with SKU '{product_data.sku}' already exists")
    
    # Create product
    product = Product(
        category_id=product_data.category_id,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        sku=product_data.sku,
        stock_quantity=product_data.stock_quantity,
        is_active=True
    )
    
    session.add(product)
    session.commit()
    session.refresh(product)
    
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Update a product.
    
    **Requires admin privileges.**
    
    Only provided fields will be updated.
    """
    # Fetch product
    query = select(Product).where(Product.id == product_id)
    result = session.exec(query)
    product = result.one_or_none()
    
    if not product:
        raise NotFoundException(detail=f"Product with id {product_id} not found")
    
    # Check SKU uniqueness if updating SKU
    if product_data.sku and product_data.sku != product.sku:
        query = select(Product).where(Product.sku == product_data.sku)
        result = session.exec(query)
        existing = result.one_or_none()
        if existing:
            raise ConflictException(detail=f"Product with SKU '{product_data.sku}' already exists")
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    session.add(product)
    session.commit()
    session.refresh(product)
    
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Soft delete a product (sets is_active to False).
    
    **Requires admin privileges.**
    
    Soft delete is used to preserve order history.
    """
    query = select(Product).where(Product.id == product_id)
    result = session.exec(query)
    product = result.one_or_none()
    
    if not product:
        raise NotFoundException(detail=f"Product with id {product_id} not found")
    
    # Soft delete
    product.is_active = False
    session.add(product)
    session.commit()
    
    return None