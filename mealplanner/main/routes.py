import os
from flask import render_template, request, Blueprint, redirect, url_for, flash, send_from_directory, current_app
from flask_login import current_user, login_required
from mealplanner import db
from mealplanner.models import Meal, User, Ingredient, StorageItem
from datetime import date
from mealplanner.push_utils import send_push_notification
from mealplanner.models import PushSubscription

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    if not current_user.is_authenticated:
        return render_template('main/home.html')
    user = User.query.filter_by(username=current_user.username).first()
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_meals = {}
    week = 1
    for day in days:
        meal_id = getattr(user, day)
        day_meals[day] = Meal.query.get(meal_id) if meal_id else None
    return render_template('main/home.html', day_meals=day_meals, days=days, user=user, week=week)

@main.route("/next_week")
def next_week():
    if not current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.query.filter_by(id=current_user.id).first()
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    days = ['monday2', 'tuesday2', 'wednesday2', 'thursday2', 'friday2', 'saturday2', 'sunday2']
    day_meals = {}
    week = 2
    for day in days:
        meal_id = getattr(user, day)
        day_meals[day] = Meal.query.get(meal_id) if meal_id else None
    return render_template('main/next_week.html', day_meals=day_meals, days=weekdays, days2=days, user=user, week=week)

@main.route("/transfer_week", methods=['POST'])
@login_required
def transfer_week():
    user = User.query.filter_by(id=current_user.id).first()
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    days2 = ['monday2', 'tuesday2', 'wednesday2', 'thursday2', 'friday2', 'saturday2', 'sunday2']
    for day, day2 in zip(weekdays, days2):
        setattr(user, day, getattr(user, day2))
    for day2 in days2:
        setattr(user, day2, 0)
    db.session.commit()
    flash('Next weeks meals have been transferred to this week!', 'success')
    return redirect(url_for('main.home'))

@main.route("/search")
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('main/search.html', query=query, users=[], meals=[])
    users = User.query.filter(User.username.ilike(f'%{query}%')).limit(20).all()
    meal_filters = [Meal.visibility == 'public']
    if current_user.is_authenticated:
        followed_ids = [u.id for u in current_user.followed]
        meal_filters.append((Meal.visibility == 'followers') & (Meal.user_id.in_(followed_ids)))
        meal_filters.append(Meal.user_id == current_user.id)
    matching_ingredient_meal_ids = db.session.query(Ingredient.meal_id).filter(
        Ingredient.name.ilike(f'%{query}%')
    ).subquery()
    meals = Meal.query.filter(
        db.or_(
            Meal.name.ilike(f'%{query}%'),
            Meal.recipe.ilike(f'%{query}%'),
            Meal.id.in_(matching_ingredient_meal_ids)
        ),
        db.or_(*meal_filters)
    ).distinct().limit(20).all()
    return render_template('main/search.html', query=query, users=users, meals=meals)
@main.route("/find_by_ingredients")
def find_by_ingredients():
    query = request.args.get('ingredients', '').strip()
    storage_items = []
    used_storage = False
    expiration_lookup = {}
    if not query and current_user.is_authenticated:
        storage_items = StorageItem.query.filter_by(user_id=current_user.id).all()
        if storage_items:
            query = ', '.join(i.name for i in storage_items)
            used_storage = True
            expiration_lookup = {
                i.name.strip().lower(): i.expiration_date
                for i in storage_items if i.expiration_date
            }
    if not query:
        return render_template('main/find_by_ingredients.html', query='', exact_matches=[], near_matches=[], used_storage=False)
    searched = set(i.strip().lower() for i in query.split(',') if i.strip())
    meal_filters = [Meal.visibility == 'public']
    if current_user.is_authenticated:
        followed_ids = [u.id for u in current_user.followed]
        meal_filters.append((Meal.visibility == 'followers') & (Meal.user_id.in_(followed_ids)))
        meal_filters.append(Meal.user_id == current_user.id)
    candidates = Meal.query.filter(db.or_(*meal_filters)).all()
    exact_matches = []
    near_matches = []
    today = date.today()
    def earliest_expiration(meal):
        """Finn den snarest utløpende ingrediensen i dette måltidet, hvis noen"""
        dates = []
        for ing in meal.ingredient_list:
            exp = expiration_lookup.get(ing.name.strip().lower())
            if exp:
                dates.append(exp)
            if ing.substitute:
                exp_sub = expiration_lookup.get(ing.substitute.strip().lower())
                if exp_sub:
                    dates.append(exp_sub)
        return min(dates) if dates else None
    for meal in candidates:
        essential_ingredients = [i for i in meal.ingredient_list if i.essential]
        if not essential_ingredients:
            continue
        missing = []
        for ing in essential_ingredients:
            has_main = ing.name.lower() in searched
            has_substitute = ing.substitute and ing.substitute.lower() in searched
            if not (has_main or has_substitute):
                missing.append(ing.name)
        expiry = earliest_expiration(meal)
        if len(missing) == 0:
            exact_matches.append({'meal': meal, 'expiry': expiry})
        elif len(missing) <= 2:
            near_matches.append({'meal': meal, 'missing': missing, 'expiry': expiry})
    exact_matches.sort(key=lambda x: (x['expiry'] is None, x['expiry'] or date.max, x['meal'].name.lower()))
    near_matches.sort(key=lambda x: (len(x['missing']), x['expiry'] is None, x['expiry'] or date.max, x['meal'].name.lower()))
    return render_template('main/find_by_ingredients.html', query=query, exact_matches=exact_matches, near_matches=near_matches, used_storage=used_storage, today=today)

@main.route('/sw.js')
def service_worker():
    response = send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'sw.js'
    )
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Content-Type'] = 'application/javascript'
    return response

@main.route("/test-push")
@login_required
def test_push():
    subscriptions = PushSubscription.query.filter_by(user_id=current_user.id).all()

    if not subscriptions:
        return "Ingen push-subscription funnet for deg. Trykk 'Enable notifications' først."

    for sub in subscriptions:
        send_push_notification(sub, "Test varsel", "Dette er en test fra MealPlanner!")

    return f"Sendte testvarsel til {len(subscriptions)} subscription(s)."