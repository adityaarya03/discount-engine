"""
Main API router aggregator.
Combines all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth, orders, products, categories, discounts


api_router = APIRouter()

# Authentication
api_router.include_router(auth.router)

# Public/Customer endpoints
api_router.include_router(products.router)
api_router.include_router(categories.router)
api_router.include_router(discounts.router)
api_router.include_router(orders.router)