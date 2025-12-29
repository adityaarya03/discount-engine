"""
Main API router aggregator.
Combines all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1 import auth, orders


api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(orders.router)