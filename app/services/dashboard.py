from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func
from app.database.models.sale import Sale
from app.database.models.sale_product import SaleProduct
from app.database.models.other_expense import OtherExpense
from app.api.schemas.dashboard import FrequencyEnum, ChartItem
from app.enums.sale import SaleStatus
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
            # February 29 on a non-leap year
            return dt.replace(year=dt.year - years, day=28)

    async def get_chart_data(
        self,
        user_id: str,
        frequency: FrequencyEnum,
        count: int = 7,
        previous: int = 0,
        timezone_offset: int = 0,
    ) -> list[ChartItem]:

        # User local timezone
        # timezone_offset is in minutes (e.g. 180 for UTC-3 or -180, we assume the JS offset where UTC-3 is +180)
        # Actually in JS: new Date().getTimezoneOffset() -> 180 for UTC-3.
        # So local_tz = timezone(timedelta(minutes=-timezone_offset))
        local_tz = timezone(timedelta(minutes=-timezone_offset))

        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        now_local = now_utc.astimezone(local_tz)

        # Calculate the end of the current period
        if frequency == FrequencyEnum.daily:
            current_period_end = now_local.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif frequency == FrequencyEnum.weekly:
            # End of current week (Saturday, since week starts on Sunday)
            days_to_saturday = (5 - now_local.weekday()) % 7
            current_period_end = (now_local + timedelta(days=days_to_saturday)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif frequency == FrequencyEnum.monthly:
            # End of current month
            last_day = monthrange(now_local.year, now_local.month)[1]
            current_period_end = now_local.replace(
                day=last_day, hour=23, minute=59, second=59, microsecond=999999
            )
        elif frequency == FrequencyEnum.yearly:
            current_period_end = now_local.replace(
                month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
            )

        # Calculate periods
        buckets = []
        for i in range(count):
            # The index from the end
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
                # Ensure end_dt is the last day of that month
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

        # Convert back to naive UTC for DB query since DB stores naive UTC
        global_start_utc = global_start_local.astimezone(timezone.utc).replace(
            tzinfo=None
        )
        global_end_utc = global_end_local.astimezone(timezone.utc).replace(tzinfo=None)

        # 1. Fetch Sales (Revenue)
        # Revenue is sum of sales.total
        sale_query = select(Sale.created_at, Sale.total).where(
            Sale.user_id == uuid.UUID(user_id),
            Sale.status == SaleStatus.DONE,
            Sale.created_at >= global_start_utc,
            Sale.created_at <= global_end_utc,
        )
        sales_result = await self.session.execute(sale_query)
        sales = sales_result.all()

        for sale_dt, sale_total in sales:
            # Convert naive UTC to local
            sale_dt_utc = sale_dt.replace(tzinfo=timezone.utc)
            sale_dt_local = sale_dt_utc.astimezone(local_tz)

            # Find the right bucket
            for b in buckets:
                if b["start"] <= sale_dt_local <= b["end"]:
                    b["revenue"] += float(sale_total)
                    break

        # 2. Fetch OtherExpenses
        expense_query = select(OtherExpense.date, OtherExpense.value).where(
            OtherExpense.user_id == uuid.UUID(user_id),
            OtherExpense.date >= global_start_utc,
            OtherExpense.date <= global_end_utc,
        )
        expenses_result = await self.session.execute(expense_query)
        expenses = expenses_result.all()

        for exp_dt, exp_value in expenses:
            exp_dt_utc = exp_dt.replace(tzinfo=timezone.utc)
            exp_dt_local = exp_dt_utc.astimezone(local_tz)

            for b in buckets:
                if b["start"] <= exp_dt_local <= b["end"]:
                    b["expenses"] += float(exp_value)
                    break

        # Format output
        chart_items = [
            ChartItem(name=b["name"], revenue=b["revenue"], expenses=b["expenses"])
            for b in buckets
        ]

        return chart_items
