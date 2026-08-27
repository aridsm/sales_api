from fastapi import APIRouter
from app.api.routes import users, products, other_expenses, categories, sales, sale_products, history, dashboard, stock_entries, stock_entry_products, companies

router = APIRouter()
router.include_router(users.router)
router.include_router(companies.router)
router.include_router(products.router)
router.include_router(other_expenses.router)
router.include_router(categories.router)
router.include_router(sales.router)
router.include_router(sale_products.router)
router.include_router(history.router)
router.include_router(dashboard.router)
router.include_router(stock_entries.router)
router.include_router(stock_entry_products.router)
