import datetime
from django.db.models import QuerySet


def filter_meals(queryset: QuerySet, query_params: dict) -> QuerySet:
    """
    Modular queryset filtering logic for Meals.
    Separates HTTP parameters from database layer extraction.
    """
    # 1. Search Query: case-insensitive search on name
    search = query_params.get("search")
    if search:
        queryset = queryset.filter(name__icontains=search.strip())

    # 2. Date Filters
    # Single date format (YYYY-MM-DD)
    date_param = query_params.get("date")
    if date_param:
        try:
            datetime.date.fromisoformat(date_param)
            queryset = queryset.filter(eaten_at__date=date_param)
        except ValueError:
            pass

    # Start date range (YYYY-MM-DD or date-time)
    start_date = query_params.get("start_date")
    if start_date:
        try:
            datetime.date.fromisoformat(start_date)
            queryset = queryset.filter(eaten_at__date__gte=start_date)
        except ValueError:
            queryset = queryset.filter(eaten_at__gte=start_date)

    # End date range (YYYY-MM-DD or date-time)
    end_date = query_params.get("end_date")
    if end_date:
        try:
            datetime.date.fromisoformat(end_date)
            queryset = queryset.filter(eaten_at__date__lte=end_date)
        except ValueError:
            queryset = queryset.filter(eaten_at__lte=end_date)

    # 3. Tag Filters: supports CSV strings (e.g. tags=vegan,vegetarian)
    tags_param = query_params.get("tags") or query_params.get("tag")
    if tags_param:
        tags_list = [t.strip() for t in tags_param.split(",") if t.strip()]
        if tags_list:
            # Query contains ALL specified tags
            queryset = queryset.filter(tags__contains=tags_list)

    return queryset
