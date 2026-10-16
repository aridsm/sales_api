from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func, case
from app.database.models.sale import Sale
from app.database.models.sale_product import SaleProduct
from app.database.models.product import Product
from app.database.models.category import Category
from app.database.models.other_expense import OtherExpense
from app.database.models.stock_entry import StockEntry
from app.api.schemas.dashboard import FrequencyEnum, ChartItem, TopProductItem
from app.enums.sale import SaleStatus
from app.enums.stock_entry import StockEntryStatus
import uuid
from datetime import datetime, timedelta, timezone
from calendar import monthrange


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _subtract_months(self, dt: datetime, months: int) -> datetime:
        month = dt.month - 1 - months
        year = dt.year + month // 12
        month = month % 12 + 1
        day = min(dt.day, monthrange(year, month)[1])
        return dt.replace(year=year, month=month, day=day)

    def _subtract_years(self, dt: datetime, years: int) -> datetime:
        try:
            return dt.replace(year=dt.year - years)
        except ValueError:
            return dt.replace(year=dt.year - years, day=28)

    async def get_chart_data(
        self,
        company_id: str,
        frequency: FrequencyEnum,
        count: int = 7,
        previous: int = 0,
        timezone_offset: int = 0,
    ) -> list[ChartItem]:

        local_tz = timezone(timedelta(minutes=-timezone_offset))

        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(local_tz)

        if frequency == FrequencyEnum.daily:
            current_period_end = now_local.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif frequency == FrequencyEnum.weekly:
            days_to_saturday = (5 - now_local.weekday()) % 7
            current_period_end = (now_local + timedelta(days=days_to_saturday)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif frequency == FrequencyEnum.monthly:
            last_day = monthrange(now_local.year, now_local.month)[1]
            current_period_end = now_local.replace(
                day=last_day, hour=23, minute=59, second=59, microsecond=999999
            )
        elif frequency == FrequencyEnum.yearly:
            current_period_end = now_local.replace(
                month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
            )

        buckets = []
        for i in range(count):
            offset_idx = previous * count + (count - 1 - i)

            if frequency == FrequencyEnum.daily:
                end_dt = current_period_end - timedelta(days=offset_idx)
                start_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                name = start_dt.strftime("%d/%m")
            elif frequency == FrequencyEnum.weekly:
                end_dt = current_period_end - timedelta(weeks=offset_idx)
                start_dt = (end_dt - timedelta(days=6)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                name = f"{start_dt.strftime('%d/%m')} - {end_dt.strftime('%d/%m')}"
            elif frequency == FrequencyEnum.monthly:
                end_dt = self._subtract_months(current_period_end, offset_idx)
                last_day = monthrange(end_dt.year, end_dt.month)[1]
                end_dt = end_dt.replace(day=last_day)
                start_dt = end_dt.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
                name = start_dt.strftime("%m/%Y")
            elif frequency == FrequencyEnum.yearly:
                end_dt = self._subtract_years(current_period_end, offset_idx)
                start_dt = end_dt.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                )
                name = start_dt.strftime("%Y")

            buckets.append(
                {
                    "start": start_dt,
                    "end": end_dt,
                    "name": name,
                    "revenue": 0.0,
                    "expenses": 0.0,
                }
            )

        if not buckets:
            return []

        global_start_local = buckets[0]["start"]
        global_end_local = buckets[-1]["end"]

        global_start_utc = global_start_local.astimezone(timezone.utc)
        global_end_utc = global_end_local.astimezone(timezone.utc)

        sale_query = select(Sale.date, Sale.total).where(
            Sale.company_id == uuid.UUID(company_id),
            Sale.status == SaleStatus.DONE,
            Sale.date >= global_start_utc,
            Sale.date <= global_end_utc,
        )
        sales_result = await self.session.execute(sale_query)
        sales = sales_result.all()

        for sale_dt, sale_total in sales:
            sale_dt_local = sale_dt.astimezone(local_tz)

            for b in buckets:
                if b["start"] <= sale_dt_local <= b["end"]:
                    b["revenue"] += float(sale_total)
                    break

        expense_query = select(OtherExpense.date, OtherExpense.value).where(
            OtherExpense.company_id == uuid.UUID(company_id),
            OtherExpense.date >= global_start_utc,
            OtherExpense.date <= global_end_utc,
        )
        expenses_result = await self.session.execute(expense_query)
        expenses = expenses_result.all()

        for exp_dt, exp_value in expenses:
            exp_dt_local = exp_dt.astimezone(local_tz)

            for b in buckets:
                if b["start"] <= exp_dt_local <= b["end"]:
                    b["expenses"] += float(exp_value)
                    break

        stock_entry_query = select(StockEntry.date, StockEntry.total).where(
            StockEntry.company_id == uuid.UUID(company_id),
            StockEntry.status == StockEntryStatus.OPEN,
            StockEntry.date >= global_start_utc,
            StockEntry.date <= global_end_utc,
        )
        stock_entries_result = await self.session.execute(stock_entry_query)
        stock_entries = stock_entries_result.all()

        for st_dt, st_total in stock_entries:
            st_dt_local = st_dt.astimezone(local_tz)

            for b in buckets:
                if b["start"] <= st_dt_local <= b["end"]:
                    b["expenses"] += float(st_total)
                    break

        chart_items = [
            ChartItem(name=b["name"], revenue=b["revenue"], expenses=b["expenses"])
            for b in buckets
        ]

        return chart_items

    async def get_budgets(
        self,
        company_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:

        total_sales_query = select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.company_id == uuid.UUID(company_id),
            Sale.status == SaleStatus.DONE,
        )
        total_sales_result = await self.session.execute(total_sales_query)
        total_sales = float(total_sales_result.scalar())

        total_expenses_query = select(
            func.coalesce(func.sum(OtherExpense.value), 0)
        ).where(
            OtherExpense.company_id == uuid.UUID(company_id),
        )
        total_expenses_result = await self.session.execute(total_expenses_query)
        total_expenses = float(total_expenses_result.scalar())

        total_stock_entries_query = select(
            func.coalesce(func.sum(StockEntry.total), 0)
        ).where(
            StockEntry.company_id == uuid.UUID(company_id),
            StockEntry.status == StockEntryStatus.OPEN,
        )
        total_stock_entries_result = await self.session.execute(total_stock_entries_query)
        total_expenses += float(total_stock_entries_result.scalar())

        current_balance = total_sales - total_expenses

        revenue_query = select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.company_id == uuid.UUID(company_id),
            Sale.status == SaleStatus.DONE,
        )
        if start_date:
            revenue_query = revenue_query.where(Sale.date >= start_date)
        if end_date:
            revenue_query = revenue_query.where(Sale.date <= end_date)

        revenue_result = await self.session.execute(revenue_query)
        revenue = float(revenue_result.scalar())

        expenses_query = select(func.coalesce(func.sum(OtherExpense.value), 0)).where(
            OtherExpense.company_id == uuid.UUID(company_id),
        )
        if start_date:
            expenses_query = expenses_query.where(OtherExpense.date >= start_date)
        if end_date:
            expenses_query = expenses_query.where(OtherExpense.date <= end_date)

        expenses_result = await self.session.execute(expenses_query)
        expenses = float(expenses_result.scalar())

        stock_expenses_query = select(func.coalesce(func.sum(StockEntry.total), 0)).where(
            StockEntry.company_id == uuid.UUID(company_id),
            StockEntry.status == StockEntryStatus.OPEN,
        )
        if start_date:
            stock_expenses_query = stock_expenses_query.where(StockEntry.date >= start_date)
        if end_date:
            stock_expenses_query = stock_expenses_query.where(StockEntry.date <= end_date)

        stock_expenses_result = await self.session.execute(stock_expenses_query)
        expenses += float(stock_expenses_result.scalar())

        net_profit = revenue - expenses

        return {
            "current_balance": current_balance,
            "net_profit": net_profit,
            "revenue": revenue,
            "expenses": expenses,
        }

    async def get_top_products(
        self,
        company_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 5,
    ) -> list[TopProductItem]:
        item_gross = SaleProduct.quantity * SaleProduct.unit_price
        sale_subtotal = Sale.total + func.coalesce(Sale.discount, 0.0)
        net_revenue_expr = case(
            (
                sale_subtotal > 0,
                item_gross * (Sale.total / sale_subtotal),
            ),
            else_=0.0,
        )

        query = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Category.name.label("category_name"),
                Category.color.label("category_color"),
                func.sum(SaleProduct.quantity).label("quantity_sold"),
                func.sum(net_revenue_expr).label("total_revenue"),
            )
            .join(SaleProduct, SaleProduct.product_id == Product.id)
            .join(Sale, Sale.id == SaleProduct.sale_id)
            .outerjoin(Category, Category.id == Product.category_id)
            .where(
                Sale.company_id == uuid.UUID(company_id),
                Sale.status == SaleStatus.DONE,
            )
        )
        if start_date:
            query = query.where(Sale.date >= start_date)
        if end_date:
            query = query.where(Sale.date <= end_date)

        query = (
            query.group_by(Product.id, Product.name, Category.name, Category.color)
            .order_by(func.sum(SaleProduct.quantity).desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        rows = result.all()
        return [
            TopProductItem(
                product_id=row.product_id,
                product_name=row.product_name,
                category_name=row.category_name or "Sem categoria",
                category_color=row.category_color,
                quantity_sold=int(row.quantity_sold or 0),
                total_revenue=round(float(row.total_revenue or 0.0), 2),
            )
            for row in rows
        ]
