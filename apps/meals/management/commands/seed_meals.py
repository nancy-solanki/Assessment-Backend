import json
import os
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from apps.meals.models import Meal
from django.conf import settings


class Command(BaseCommand):
    help = "Seeds database with meals from seed_meals.json"

    def handle(self, *args, **options):
        # Determine path to seed_meals.json
        possible_paths = [
            os.path.join(settings.BASE_DIR, "seed_meals.json"),
            os.path.join(settings.BASE_DIR, "apps", "meals", "fixtures", "seed_meals.json"),
        ]
        
        json_path = None
        for path in possible_paths:
            if os.path.exists(path):
                json_path = path
                break
                
        if not json_path:
            self.stdout.write(self.style.ERROR("Could not find seed_meals.json file."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found seed data at: {json_path}"))

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for item in data:
            eaten_at = parse_datetime(item["eaten_at"])
            # Use update_or_create to avoid duplicate entries when running command multiple times
            meal, created = Meal.objects.update_or_create(
                name=item["name"],
                eaten_at=eaten_at,
                defaults={
                    "calories": item["calories"],
                    "protein_g": item.get("protein_g", 0),
                    "carbs_g": item.get("carbs_g", 0),
                    "fat_g": item.get("fat_g", 0),
                    "tags": item.get("tags", []),
                }
            )
            if created:
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {count} new meals.")
        )
