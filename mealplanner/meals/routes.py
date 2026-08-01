from flask import Blueprint
from flask import render_template, url_for, flash, redirect, request, abort
from mealplanner import db
from mealplanner.meals.forms import PostForm
from mealplanner.models import Meal, Ingredient
from flask_login import current_user, login_required
from mealplanner.meals.utils import save_meal_picture

meals = Blueprint('meals', __name__)

@meals.route("/recipes")
@login_required
def recipes():
    filter_by = request.args.get('filter', 'mine')
    page = request.args.get('page', 1, type=int)

    if filter_by == 'following':
        followed_ids = [u.id for u in current_user.followed]
        meals = Meal.query.filter(
            Meal.user_id.in_(followed_ids),
            (Meal.visibility == 'public') | (Meal.visibility == 'followers')
        ).order_by(Meal.id.desc()).paginate(per_page=12, page=page)

    elif filter_by == 'public':
        meals = Meal.query.filter_by(visibility='public').order_by(Meal.id.desc()).paginate(per_page=12, page=page)

    else:  # 'mine'
        meals = Meal.query.filter_by(author=current_user).order_by(Meal.id.desc()).paginate(per_page=12, page=page)

    return render_template('meals/recipes.html', title='Recipes', meals=meals, filter_by=filter_by)

@meals.route("/mealpage")
def mealpage():
    return "<h1>About Page</h1>"

@meals.route("/meal/new", methods=['GET', 'POST'])
@login_required
def new_meal():
    form = PostForm()
    if form.validate_on_submit():
        meal = Meal(name=form.name.data, time=form.time.data, recipe=form.recipe.data, visibility=form.visibility.data, author=current_user)
        db.session.add(meal)
        db.session.flush()
        names = request.form.getlist('ingredient_name[]')
        essentials = request.form.getlist('ingredient_essential[]')
        substitutes = request.form.getlist('ingredient_substitute[]')
        for name, essential, substitute in zip(names, essentials, substitutes):
            name = name.strip()
            if not name:
                continue
            ingredient = Ingredient(
                meal_id=meal.id,
                name=name,
                essential=(essential == '1'),
                substitute=substitute.strip() if substitute.strip() else None
            )
            db.session.add(ingredient)
        db.session.commit()
        if form.picture.data:
            picture_file = save_meal_picture(form.picture.data)
            meal.image_file = picture_file
            db.session.commit()
        flash('Meal has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('meals/create_meal.html', title='New Meal', form=form, legend='New Meal')

@meals.route("/meal/<int:meal_id>")
def meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    return render_template('meals/meal.html', title=meal.name, meal=meal)

@meals.route("/meal/<int:meal_id>/update", methods=['GET', 'POST'])
@login_required
def update_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    if meal.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_meal_picture(form.picture.data)
            meal.image_file = picture_file
        meal.name = form.name.data
        meal.time = form.time.data
        meal.recipe = form.recipe.data
        meal.visibility = form.visibility.data
        Ingredient.query.filter_by(meal_id=meal.id).delete()
        names = request.form.getlist('ingredient_name[]')
        essentials = request.form.getlist('ingredient_essential[]')
        substitutes = request.form.getlist('ingredient_substitute[]')
        for name, essential, substitute in zip(names, essentials, substitutes):
            name = name.strip()
            if not name:
                continue
            ingredient = Ingredient(
                meal_id=meal.id,
                name=name,
                essential=(essential == '1'),
                substitute=substitute.strip() if substitute.strip() else None
            )
            db.session.add(ingredient)
        db.session.commit()
        flash('Meal has been updated!', 'success')
        return redirect(url_for('meals.meal', meal_id=meal.id))
    elif request.method == 'GET':
        form.name.data = meal.name
        form.time.data = meal.time
        form.recipe.data = meal.recipe
        form.visibility.data = meal.visibility
    return render_template('meals/create_meal.html', title='Update Meal', form=form, legend='Update Meal', meal=meal)

@meals.route("/meal/<int:meal_id>/delete", methods=['POST'])
@login_required
def delete_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    if meal.author != current_user and current_user.admin == False:
        abort(403)
    db.session.delete(meal)
    db.session.commit()
    flash('Meal has been deleted', 'success')
    return redirect(url_for('main.home'))


@meals.route("/meal/<day>", methods=['POST', 'GET'])
@login_required
def select_meal(day):
    see_all = request.args.get('see_all', 'false') == 'true'
    page = request.args.get('page', 1, type=int)
    meals = Meal.query.order_by(Meal.id.desc()).paginate(per_page=12, page=page)

    return render_template('meals/select_meal.html', title='Select Meal', meals=meals, see_all=see_all, day=day)

@meals.route("/meal/<day>/<int:meal_id>", methods=['POST', 'GET'])
@login_required
def choose_meal(day, meal_id):
    if meal_id == 0:
        setattr(current_user, day.lower(), 0)
        db.session.commit()
        display_day = day[:-1]
        flash(f'Meal removed from {display_day}!', 'success')
        return redirect(url_for('main.home'))
    meal = Meal.query.get_or_404(meal_id)
    if meal:
        setattr(current_user, day.lower(), meal_id)
        db.session.commit()
        display_day = day[:-1]
        flash(f'{meal.name} is selected for {display_day}!', 'success')
        return redirect(url_for('main.home'))

@meals.route("/meal/<int:meal_id>/default_pic", methods=['GET', 'POST'])
@login_required
def de_pic_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    if current_user.admin == False:
        abort(403)
    meal.image_file = 'default_meal.png'
    db.session.commit()
    flash('Meal has been updated!', 'success')
    return redirect(url_for('users.admin'))
