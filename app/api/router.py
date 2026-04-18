from fastapi import APIRouter
from app.api.routes import users, products, other_expenses, categories


router = APIRouter()
router.include_router(users.router)
router.include_router(products.router)
router.include_router(other_expenses.router)
router.include_router(categories.router)
