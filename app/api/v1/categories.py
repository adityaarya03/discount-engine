"""
Category management endpoints.
Public: List and view categories
Admin: Create, update, delete categories
"""
from uuid import UUID
from fastapi import APIRouter, status
from sqlmodel import select

from app.api.deps import DBSession, CurrentAdmin
from app.models.product import Category
from app.schemas.product import CategoryCreate, CategoryUpdate, CategoryResponse
from app.core.exceptions import NotFoundException, ConflictException


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    session: DBSession,
    skip: int = 0,
    limit: int = 100
):
    """
    List all categories.
    
    Returns categories with their parent relationships.
    """
    query = select(Category).offset(skip).limit(limit)
    result = session.exec(query)
    categories = result.all()
    
    return [CategoryResponse.model_validate(c) for c in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: UUID, session: DBSession):
    """
    Get a single category by ID.
    """
    query = select(Category).where(Category.id == category_id)
    result = session.exec(query)
    category = result.one_or_none()
    
    if not category:
        raise NotFoundException(detail=f"Category with id {category_id} not found")
    
    return CategoryResponse.model_validate(category)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Create a new category.
    
    **Requires admin privileges.**
    
    Can create subcategories by providing parent_category_id.
    """
    # Check if slug already exists
    query = select(Category).where(Category.slug == category_data.slug)
    result = session.exec(query)
    existing = result.one_or_none()
    
    if existing:
        raise ConflictException(detail=f"Category with slug '{category_data.slug}' already exists")
    
    # If parent_category_id provided, verify it exists
    if category_data.parent_category_id:
        query = select(Category).where(Category.id == category_data.parent_category_id)
        result = session.exec(query)
        parent = result.one_or_none()
        if not parent:
            raise NotFoundException(detail=f"Parent category with id {category_data.parent_category_id} not found")
    
    # Create category
    category = Category(
        name=category_data.name,
        slug=category_data.slug,
        parent_category_id=category_data.parent_category_id
    )
    
    session.add(category)
    session.commit()
    session.refresh(category)
    
    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Update a category.
    
    **Requires admin privileges.**
    
    Only provided fields will be updated.
    """
    # Fetch category
    query = select(Category).where(Category.id == category_id)
    result = session.exec(query)
    category = result.one_or_none()
    
    if not category:
        raise NotFoundException(detail=f"Category with id {category_id} not found")
    
    # Check slug uniqueness if updating slug
    if category_data.slug and category_data.slug != category.slug:
        query = select(Category).where(Category.slug == category_data.slug)
        result = session.exec(query)
        existing = result.one_or_none()
        if existing:
            raise ConflictException(detail=f"Category with slug '{category_data.slug}' already exists")
    
    # Verify parent category exists if updating
    if category_data.parent_category_id:
        if category_data.parent_category_id == category_id:
            raise ConflictException(detail="Category cannot be its own parent")
        
        query = select(Category).where(Category.id == category_data.parent_category_id)
        result = session.exec(query)
        parent = result.one_or_none()
        if not parent:
            raise NotFoundException(detail=f"Parent category with id {category_data.parent_category_id} not found")
    
    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    session.add(category)
    session.commit()
    session.refresh(category)
    
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    admin: CurrentAdmin,
    session: DBSession
):
    """
    Delete a category.
    
    **Requires admin privileges.**
    
    WARNING: This will fail if products reference this category.
    Consider soft-delete or moving products to another category first.
    """
    query = select(Category).where(Category.id == category_id)
    result = session.exec(query)
    category = result.one_or_none()
    
    if not category:
        raise NotFoundException(detail=f"Category with id {category_id} not found")
    
    # Hard delete (will fail if products reference it due to FK constraint)
    session.delete(category)
    session.commit()
    
    return None