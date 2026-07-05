"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, customers, products,
    leads, opportunities, quotations, contracts,
    campaigns, tickets, dashboard, system,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(leads.router)
api_router.include_router(opportunities.router)
api_router.include_router(quotations.router)
api_router.include_router(contracts.router)
api_router.include_router(campaigns.router)
api_router.include_router(tickets.router)
api_router.include_router(dashboard.router)
api_router.include_router(dashboard.notify_router)
api_router.include_router(dashboard.log_router)
api_router.include_router(system.router)
