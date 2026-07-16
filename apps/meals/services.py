import datetime
from typing import Dict, Any

from django.utils import timezone
from django.conf import settings
from django.db.models import Sum, Count, Value, QuerySet
from django.db.models.functions import Coalesce, TruncDate
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg

from apps.meals.utils import fill_trends_gaps, calculate_trends_stats


class MealSummaryService:
    """
    Service class responsible for carrying out aggregated database analytics
    concerning meals. Runs inside exactly one query.
    """

    @staticmethod
    def get_summary(queryset: QuerySet) -> Dict[str, Any]:
        summary = queryset.aggregate(
            total_meals=Count("id"),
            total_calories=Coalesce(Sum("calories"), Value(0)),
            total_protein=Coalesce(Sum("protein_g"), Value(0)),
            total_carbs=Coalesce(Sum("carbs_g"), Value(0)),
            total_fat=Coalesce(Sum("fat_g"), Value(0)),
            meal_names=Coalesce(ArrayAgg("name", distinct=True), Value([])),
            tags_agg=Coalesce(JSONBAgg("tags"), Value([])),
        )

        # Flatten list of lists for tags_agg and query unique tag labels
        raw_tags = summary.get("tags_agg") or []
        unique_tags_set = set()
        for tags_list in raw_tags:
            if tags_list:
                for tag in tags_list:
                    if tag:
                        unique_tags_set.add(tag)
        unique_tags = sorted(list(unique_tags_set))

        total_calories = summary["total_calories"]

        return {
            "total_meals": summary["total_meals"],
            "total_calories": total_calories,
            "total_protein": summary["total_protein"],
            "total_carbs": summary["total_carbs"],
            "total_fat": summary["total_fat"],
            "meal_names": summary["meal_names"] or [],
            "unique_tags": unique_tags,
            "goal_kcal": settings.DAILY_GOAL_KCAL,
            "remaining_kcal": settings.DAILY_GOAL_KCAL - total_calories,
        }



class MealTrendsService:
    """
    Service class responsible for querying and formatting day-by-day trends
    over a window of N days.
    """

    @staticmethod
    def get_trends(
        queryset: QuerySet, days: int, goal: int, today: datetime.date
    ) -> Dict[str, Any]:
        start_date = today - datetime.timedelta(days=days - 1)

        start_datetime = datetime.datetime.combine(
            start_date, datetime.time.min, tzinfo=timezone.get_current_timezone()
        )
        end_datetime = datetime.datetime.combine(
            today, datetime.time.max, tzinfo=timezone.get_current_timezone()
        )

        # Apply timeframe filter
        ranged_queryset = queryset.filter(eaten_at__range=(start_datetime, end_datetime))

        # Query metrics grouped by date in EXACTLY one query
        daily_records = list(
            ranged_queryset.annotate(date=TruncDate("eaten_at"))
            .values("date")
            .annotate(
                total_calories=Sum("calories"),
                total_protein=Sum("protein_g"),
                total_carbs=Sum("carbs_g"),
                total_fat=Sum("fat_g"),
            )
            .order_by("date")
        )

        # Map results by date string
        daily_map = {}
        for rec in daily_records:
            if rec["date"]:
                date_str = rec["date"].strftime("%Y-%m-%d")
                daily_map[date_str] = rec

        # Carry out gap filling
        days_series = fill_trends_gaps(start_date, days, daily_map)

        # Compute higher level statistics
        stats = calculate_trends_stats(days_series, days, goal)

        return {"days": days_series, "stats": stats}
