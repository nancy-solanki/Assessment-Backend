import datetime
from typing import List, Dict, Any


def fill_trends_gaps(
    start_date: datetime.date, days: int, daily_map: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Ensure every single day in the target N days range is represented in output series.
    Missing days are filled with zero-intake placeholders.
    """
    days_series = []
    for i in range(days):
        current_date = start_date + datetime.timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")

        if date_str in daily_map:
            rec = daily_map[date_str]
            days_series.append(
                {
                    "date": date_str,
                    "total_calories": rec["total_calories"] or 0,
                    "total_protein": rec["total_protein"] or 0,
                    "total_carbs": rec["total_carbs"] or 0,
                    "total_fat": rec["total_fat"] or 0,
                }
            )
        else:
            days_series.append(
                {
                    "date": date_str,
                    "total_calories": 0,
                    "total_protein": 0,
                    "total_carbs": 0,
                    "total_fat": 0,
                }
            )
    return days_series


def calculate_trends_stats(
    days_series: List[Dict[str, Any]], days: int, goal: int
) -> Dict[str, Any]:
    """
    Computes statistical bounds such as averages, maximum content,
    days over goal, and best consuming days over the generated series.
    """
    total_calories_all = sum(day["total_calories"] for day in days_series)
    total_protein_all = sum(day["total_protein"] for day in days_series)
    total_carbs_all = sum(day["total_carbs"] for day in days_series)
    total_fat_all = sum(day["total_fat"] for day in days_series)

    average_calories = round(total_calories_all / days, 2)
    average_protein = round(total_protein_all / days, 2)
    average_carbs = round(total_carbs_all / days, 2)
    average_fat = round(total_fat_all / days, 2)

    max_calories = max((day["total_calories"] for day in days_series), default=0)

    best_day = None
    if days_series:
        best_day_record = max(days_series, key=lambda x: x["total_calories"])
        if best_day_record["total_calories"] > 0:
            best_day = {
                "date": best_day_record["date"],
                "calories": best_day_record["total_calories"],
            }

    days_over_goal = sum(
        1 for day in days_series if day["total_calories"] > goal
    )

    return {
        "average_calories": average_calories,
        "average_protein": average_protein,
        "average_carbs": average_carbs,
        "average_fat": average_fat,
        "max_calories": max_calories,
        "best_day": best_day,
        "days_over_goal": days_over_goal,
    }
