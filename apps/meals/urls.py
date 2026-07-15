from django.urls import path
from apps.meals.views import (
    MealListCreateView,
    MealDetailDeleteView,
    MealSummaryView,
    MealTrendsView,
)

urlpatterns = [
    path("meals/", MealListCreateView.as_view(), name="meal-list-create"),
    path("meals/summary/", MealSummaryView.as_view(), name="meal-summary"),
    path("meals/trends/", MealTrendsView.as_view(), name="meal-trends"),
    path("meals/<uuid:id>/", MealDetailDeleteView.as_view(), name="meal-detail-delete"),
]
