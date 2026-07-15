import datetime
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.meals.models import Meal
from apps.meals.serializers import MealSerializer, DuplicateMealException


class MealSerializerValidationTestCase(APITestCase):
    def setUp(self):
        # We need a clean timezone-aware timestamp for reference
        self.base_time = timezone.now() - datetime.timedelta(hours=2)

    def test_valid_serializer(self):
        data = {
            "name": "Grilled Chicken and Rice",
            "calories": 650,
            "protein_g": 45,
            "carbs_g": 55,
            "fat_g": 15,
            "tags": ["high-protein", "low-carb"],
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "Grilled Chicken and Rice")

    def test_name_validation(self):
        # Empty name
        data_empty = {
            "name": "   ",
            "calories": 100,
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data_empty)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

        # Name too short
        data_short = {
            "name": "A",
            "calories": 100,
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data_short)
        self.assertFalse(serializer.is_valid())
        
        # Name too long
        data_long = {
            "name": "A" * 101,
            "calories": 100,
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data_long)
        self.assertFalse(serializer.is_valid())

    def test_calories_validation(self):
        # Zero calories
        data_zero = {
            "name": "Apple",
            "calories": 0,
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data_zero)
        self.assertFalse(serializer.is_valid())

        # Too many calories
        data_too_high = {
            "name": "Mega Feast",
            "calories": 5001,
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data_too_high)
        self.assertFalse(serializer.is_valid())

    def test_macros_validation(self):
        # Negative protein
        data = {
            "name": "Shake",
            "calories": 200,
            "protein_g": -5,
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("protein_g", serializer.errors)

    def test_invalid_tags(self):
        # Tags not in choice list
        data = {
            "name": "Salad",
            "calories": 200,
            "tags": ["junk-food", "vegetarian"],
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tags", serializer.errors)

    def test_future_date_validation(self):
        future_time = timezone.now() + datetime.timedelta(days=1)
        data = {
            "name": "Tomorrow Breakfast",
            "calories": 400,
            "eaten_at": future_time.isoformat(),
        }
        serializer = MealSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("eaten_at", serializer.errors)

    def test_duplicate_guard(self):
        # Create a meal in DB
        Meal.objects.create(
            name="Unbelievable Salad",
            calories=180,
            eaten_at=self.base_time,
        )

        # Attempt to validate a serializer with same name and eaten_at
        data = {
            "name": "Unbelievable Salad",
            "calories": 250,
            "eaten_at": self.base_time.isoformat(),
        }
        serializer = MealSerializer(data=data)
        with self.assertRaises(DuplicateMealException):
            serializer.is_valid(raise_exception=True)


class MealAPITestCase(APITestCase):
    def setUp(self):
        self.list_create_url = reverse("meal-list-create")
        self.summary_url = reverse("meal-summary")
        self.trends_url = reverse("meal-trends")

        # Set up a few dates for range tests
        self.today = timezone.localdate()
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.three_days_ago = self.today - datetime.timedelta(days=3)

        # Make timezones aware
        self.t_today = datetime.datetime.combine(
            self.today, datetime.time(12, 0), tzinfo=timezone.get_current_timezone()
        )
        self.t_yesterday = datetime.datetime.combine(
            self.yesterday, datetime.time(12, 0), tzinfo=timezone.get_current_timezone()
        )
        self.t_three_days_ago = datetime.datetime.combine(
            self.three_days_ago, datetime.time(12, 0), tzinfo=timezone.get_current_timezone()
        )

        # Create seed data for API runs
        self.meal1 = Meal.objects.create(
            name="Oatmeal breakfast",
            calories=350,
            protein_g=10,
            carbs_g=50,
            fat_g=5,
            tags=["vegetarian", "vegan"],
            eaten_at=self.t_today,
        )

        self.meal2 = Meal.objects.create(
            name="Salmon lunch",
            calories=550,
            protein_g=40,
            carbs_g=10,
            fat_g=25,
            tags=["high-protein", "low-carb"],
            eaten_at=self.t_yesterday,
        )

        self.meal3 = Meal.objects.create(
            name="Greek Yogurt snack",
            calories=200,
            protein_g=15,
            carbs_g=12,
            fat_g=4,
            tags=["vegetarian", "snack"],
            eaten_at=self.t_three_days_ago,
        )

    # API 1: POST
    def test_post_meal_success(self):
        new_time = timezone.now() - datetime.timedelta(minutes=10)
        data = {
            "name": "Tofu Bowl",
            "calories": 420,
            "protein_g": 20,
            "carbs_g": 35,
            "fat_g": 12,
            "tags": ["vegetarian", "vegan"],
            "eaten_at": new_time.isoformat(),
        }
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Tofu Bowl")
        self.assertTrue(Meal.objects.filter(name="Tofu Bowl").exists())

    def test_post_meal_duplicate(self):
        data = {
            "name": "Oatmeal breakfast",
            "calories": 350,
            "eaten_at": self.t_today.isoformat(),
        }
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_post_meal_invalid_data(self):
        data = {
            "name": "",
            "calories": 9999,
            "eaten_at": self.t_today.isoformat(),
        }
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # API 2: GET with Pagination, Search, Date range, Tags, and Ordering
    def test_get_meals_list_paginated(self):
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 3)

    def test_get_meals_search(self):
        response = self.client.get(f"{self.list_create_url}?search=oatmeal")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Oatmeal breakfast")

    def test_get_meals_tag_filter(self):
        response = self.client.get(f"{self.list_create_url}?tags=vegetarian")
        self.assertEqual(len(response.data["results"]), 2)

        response = self.client.get(f"{self.list_create_url}?tags=vegetarian,vegan")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Oatmeal breakfast")

    def test_get_meals_date_filter(self):
        # Exact date
        date_str = self.yesterday.strftime("%Y-%m-%d")
        response = self.client.get(f"{self.list_create_url}?date={date_str}")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Salmon lunch")

        # Range
        start_str = self.yesterday.strftime("%Y-%m-%d")
        response = self.client.get(f"{self.list_create_url}?start_date={start_str}")
        self.assertEqual(len(response.data["results"]), 2)  # Today and Yesterday

    def test_get_meals_ordering(self):
        # Calories asc
        response = self.client.get(f"{self.list_create_url}?ordering=calories")
        self.assertEqual(response.data["results"][0]["name"], "Greek Yogurt snack")

        # Calories desc
        response = self.client.get(f"{self.list_create_url}?ordering=-calories")
        self.assertEqual(response.data["results"][0]["name"], "Salmon lunch")

    # API 3: DELETE soft-delete
    def test_delete_meal_success(self):
        url = reverse("meal-detail-delete", args=[self.meal1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Ensure it is soft-deleted
        self.assertFalse(Meal.objects.filter(id=self.meal1.id).exists())
        # Make sure it still exists in DB as soft deleted
        self.assertTrue(Meal.all_objects.filter(id=self.meal1.id).exists())
        self.assertTrue(Meal.all_objects.get(id=self.meal1.id).is_deleted)

        # Deleting it again should return 404
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # API 4: Summary GET (aggregate Sum, Count, ArrayAgg)
    def test_summary_api(self):
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_meals"], 3)
        self.assertEqual(response.data["total_calories"], 1100)  # 350 + 550 + 200
        self.assertEqual(response.data["total_protein"], 65)  # 10 + 40 + 15
        self.assertEqual(response.data["total_carbs"], 72)  # 50 + 10 + 12
        self.assertEqual(response.data["total_fat"], 34)  # 5 + 25 + 4
        self.assertIn("Salmon lunch", response.data["meal_names"])
        self.assertIn("vegetarian", response.data["unique_tags"])

    # API 5: Trends GET (Gap filling, Stats, Constant Database query)
    def test_trends_api(self):
        # Retrieve trends for last 5 days
        response = self.client.get(f"{self.trends_url}?days=5&goal=400")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check gap filling: last 5 days, so there should be exactly 5 records in "days"
        self.assertEqual(len(response.data["days"]), 5)

        # Verify order is chronological
        dates = [d["date"] for d in response.data["days"]]
        self.assertEqual(dates, sorted(dates))

        # Check today, yesterday, and 3 days ago are filled, 2 days ago and 4 days ago are zero
        # Today
        today_str = self.today.strftime("%Y-%m-%d")
        today_data = next(d for d in response.data["days"] if d["date"] == today_str)
        self.assertEqual(today_data["total_calories"], 350)

        # Yesterday
        yesterday_str = self.yesterday.strftime("%Y-%m-%d")
        yesterday_data = next(d for d in response.data["days"] if d["date"] == yesterday_str)
        self.assertEqual(yesterday_data["total_calories"], 550)

        # 2 days ago (gap-filled)
        two_days_ago_str = (self.today - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        two_days_ago_data = next(d for d in response.data["days"] if d["date"] == two_days_ago_str)
        self.assertEqual(two_days_ago_data["total_calories"], 0)

        # 3 days ago
        three_days_ago_str = self.three_days_ago.strftime("%Y-%m-%d")
        three_days_ago_data = next(d for d in response.data["days"] if d["date"] == three_days_ago_str)
        self.assertEqual(three_days_ago_data["total_calories"], 200)

        # Stats checks
        # Average calories: (350 + 550 + 200) / 5 days = 220
        self.assertEqual(response.data["stats"]["average_calories"], 220.0)
        # Max calories
        self.assertEqual(response.data["stats"]["max_calories"], 550)
        # Best day
        self.assertEqual(response.data["stats"]["best_day"]["date"], yesterday_str)
        self.assertEqual(response.data["stats"]["best_day"]["calories"], 550)
        # Days over goal (goal=400, only yesterday has 550)
        self.assertEqual(response.data["stats"]["days_over_goal"], 1)

    def test_trends_api_empty(self):
        # Clear database
        Meal.objects.all().delete()
        response = self.client.get(f"{self.trends_url}?days=3")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["days"]), 3)
        self.assertEqual(response.data["stats"]["average_calories"], 0.0)
        self.assertEqual(response.data["stats"]["max_calories"], 0)
        self.assertIsNone(response.data["stats"]["best_day"])
