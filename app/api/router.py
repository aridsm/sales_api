from fastapi import APIRouter
from app.api.routes import users, products, other_expenses, categories, sales, sale_products, history


router = APIRouter()
router.include_router(users.router)
router.include_router(products.router)
router.include_router(other_expenses.router)
router.include_router(categories.router)
router.include_router(sales.router)
router.include_router(sale_products.router)
router.include_router(history.router)
