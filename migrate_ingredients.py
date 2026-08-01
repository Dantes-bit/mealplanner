from mealplanner import db, create_app
from mealplanner.models import Meal, Ingredient

app = create_app()

with app.app_context():
    meals = Meal.query.all()
    converted_count = 0
    skipped_count = 0

    for meal in meals:
        if not meal.ingredients:
            skipped_count += 1
            continue

        # unngå duplikat-konvertering hvis scriptet kjøres flere ganger
        if meal.ingredient_list:
            skipped_count += 1
            continue

        raw_items = meal.ingredients.split(',')
        for raw in raw_items:
            name = raw.strip()
            if not name:
                continue

            ingredient = Ingredient(
                meal_id=meal.id,
                name=name,
                essential=True,        # default: alt essensielt inntil du markerer noe manuelt senere
                substitute_group=None
            )
            db.session.add(ingredient)

        converted_count += 1

    db.session.commit()
    print(f"Konvertert {converted_count} måltider.")
    print(f"Hoppet over {skipped_count} måltider (tomme eller allerede konvertert).")