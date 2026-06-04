from fastapi import APIRouter

from app.api.routes import users, login
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)