from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.indexes import GinIndex
from apps.core.models import BaseModel

class Meal(BaseModel):
    class TagChoices(models.TextChoices):
        VEGETARIAN = ("vegetarian", "Vegetarian")
        NON_VEGETARIAN = ("non-vegetarian", "Non Vegetarian")
        VEGAN = ("vegan", "Vegan")
        HIGH_PROTEIN = ("high-protein", "High Protein")
        LOW_CARB = ("low-carb", "Low Carb")
        SNACK = ("snack", "Snack")

    name = models.CharField(max_length=100, db_index=True)
    calories = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5000),
        ]
    )
    protein_g = models.PositiveIntegerField(default=0)
    carbs_g = models.PositiveIntegerField(default=0)
    fat_g = models.PositiveIntegerField(default=0)
    tags = ArrayField(
        models.CharField(
            max_length=30,
            choices=TagChoices.choices,
        ),
        default=list,
        blank=True,
    )
    eaten_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-eaten_at"]
        indexes = [
            models.Index(fields=["eaten_at"]),
            models.Index(fields=["name"]),
            GinIndex(fields=["tags"]),
        ]

    def __str__(self):
        return self.name
