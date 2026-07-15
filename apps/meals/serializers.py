from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from apps.meals.models import Meal


class DuplicateMealException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "A meal with this name and eaten_at timestamp already exists."
    default_code = "duplicate_meal"


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = [
            "id",
            "name",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "tags",
            "eaten_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name is required.")
        
        stripped_value = value.strip()
        if len(stripped_value) == 0:
            raise serializers.ValidationError("Name cannot be empty or whitespace only.")
        if len(stripped_value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        if len(stripped_value) > 100:
            raise serializers.ValidationError("Name must be at most 100 characters long.")
        return stripped_value

    def validate_calories(self, value):
        if value < 1 or value > 5000:
            raise serializers.ValidationError("Calories must be between 1 and 5000.")
        return value

    def validate_protein_g(self, value):
        if value < 0:
            raise serializers.ValidationError("Protein must be a non-negative integer.")
        return value

    def validate_carbs_g(self, value):
        if value < 0:
            raise serializers.ValidationError("Carbs must be a non-negative integer.")
        return value

    def validate_fat_g(self, value):
        if value < 0:
            raise serializers.ValidationError("Fat must be a non-negative integer.")
        return value

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list of strings.")
            
        valid_choices = [choice[0] for choice in Meal.TagChoices.choices]
        invalid_tags = [t for t in value if t not in valid_choices]
        
        if invalid_tags:
            raise serializers.ValidationError(
                f"Selected tags {invalid_tags} are invalid. Character choices are: {valid_choices}."
            )
        return value

    def validate_eaten_at(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("eaten_at timestamp cannot be in the future.")
        return value

    def validate(self, attrs):
        # Perform cross-field duplicate guard
        # A meal with the same name (stripped) and eaten_at already exists
        name = attrs.get("name")
        eaten_at = attrs.get("eaten_at")

        # Handle validation for both create and update instances
        instance = self.instance

        if name and eaten_at:
            duplicate_query = Meal.objects.filter(name=name, eaten_at=eaten_at)
            if instance:
                duplicate_query = duplicate_query.exclude(id=instance.id)

            if duplicate_query.exists():
                raise DuplicateMealException()

        return attrs
