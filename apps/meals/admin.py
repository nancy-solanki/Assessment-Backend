from django.contrib import admin
from .models import Meal


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "calories",
        "protein_g",
        "carbs_g",
        "fat_g",
        "eaten_at",
    )

    list_filter = (
        "eaten_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "-eaten_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Meal Information",
            {
                "fields": (
                    "name",
                    "calories",
                    "protein_g",
                    "carbs_g",
                    "fat_g",
                    "tags",
                    "eaten_at",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
