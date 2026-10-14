from fastapi import APIRouter

from app.api.v1 import (
    admin_conversations,
    admin_investor_requests,
    auth,
    conversations,
    investor_requests,
)

api_router = APIRouter()
api_router.include_router(auth.auth_router)
api_router.include_router(auth.users_router)
api_router.include_router(conversations.router)
api_router.include_router(admin_conversations.router)
api_router.include_router(investor_requests.router)
api_router.include_router(admin_investor_requests.router)
