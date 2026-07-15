from django.utils import timezone
from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.meals.models import Meal
from apps.meals.serializers import MealSerializer
from apps.meals.filters import filter_meals
from apps.meals.services import MealSummaryService, MealTrendsService


class MealPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class MealListCreateView(generics.ListCreateAPIView):
    """
    API 1 & 2: POST /api/meals/ and GET /api/meals
    Handles list filtering, sorting, pagination, and meal creation.
    Delegates querying filters to the filter layer.
    """
    serializer_class = MealSerializer
    pagination_class = MealPagination

    def get_queryset(self):
        queryset = Meal.objects.all()
        queryset = filter_meals(queryset, self.request.query_params)

        # Ordering
        ordering = self.request.query_params.get("ordering", "-eaten_at")
        valid_fields = [
            "name",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "eaten_at",
            "created_at",
            "updated_at",
        ]

        ordering_fields = [f.strip() for f in ordering.split(",")]
        validated_ordering = []
        for field in ordering_fields:
            desc = field.startswith("-")
            clean_field = field.lstrip("-")
            if clean_field in valid_fields:
                validated_ordering.append(f"-{clean_field}" if desc else clean_field)

        if validated_ordering:
            queryset = queryset.order_by(*validated_ordering)
        else:
            queryset = queryset.order_by("-eaten_at")

        return queryset


class MealDetailDeleteView(generics.RetrieveDestroyAPIView):
    """
    API 3: DELETE /api/meals/{id}
    Retrieves or soft-deletes a specific meal (returns 404 if deleted/non-existent).
    """
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    lookup_field = "id"


class MealSummaryView(views.APIView):
    """
    API 4: GET /api/meals/summary
    Aggregates statistical information of filtered meals.
    Delegates calculation details to the summary service.
    """

    def get(self, request, *args, **kwargs):
        queryset = Meal.objects.all()
        filtered_queryset = filter_meals(queryset, request.query_params)
        summary_data = MealSummaryService.get_summary(filtered_queryset)
        return Response(summary_data, status=status.HTTP_200_OK)


class MealTrendsView(views.APIView):
    """
    API 5: GET /api/meals/trends
    Deduces eating habits over the last N days.
    Delegates aggregation and calculations to the trends service.
    """

    def get(self, request, *args, **kwargs):
        try:
            days = int(request.query_params.get("days", 7))
            if days <= 0:
                days = 7
        except ValueError:
            days = 7

        try:
            goal = int(request.query_params.get("goal", 2000))
        except ValueError:
            goal = 2000

        queryset = Meal.objects.all()
        # Filter queryset by search strings / tags first
        filtered_queryset = filter_meals(queryset, request.query_params)

        today = timezone.localdate()
        trends_data = MealTrendsService.get_trends(
            filtered_queryset, days, goal, today
        )
        return Response(trends_data, status=status.HTTP_200_OK)
