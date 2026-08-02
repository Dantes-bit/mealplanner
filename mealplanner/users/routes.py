from flask import render_template, url_for, flash, redirect, request, abort, Blueprint, jsonify
from mealplanner import db, bcrypt
from mealplanner.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                RequestResetForm, ResetPasswordForm, ChangeEmailForm,
                                UpdatePictureForm)
from mealplanner.models import User, Meal, PushSubscription, StorageItem
from flask_login import login_user, current_user, logout_user, login_required
from mealplanner.users.utils import save_picture, send_reset_email, send_shopping_email, send_change_email_request
from collections import Counter
import json
from datetime import datetime

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, terms_accepted_at=datetime.utcnow())
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome {form.username.data}!', 'success')
        return redirect(url_for('main.home'))
    return render_template('users/register.html', title='Register', form=form)

@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user_name = User.query.filter_by(username=form.username.data).first()
        user_mail = User.query.filter_by(email=form.username.data).first()
        if user_name and bcrypt.check_password_hash(user_name.password, form.password.data):
            login_user(user_name, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Hello {form.username.data}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        if user_mail and bcrypt.check_password_hash(user_mail.password, form.password.data):
            login_user(user_mail, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Hello {user_mail.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login failed. Please check username and password', 'danger')    
    return render_template('users/login.html', title='Login', form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@users.route("/account/<int:user_id>", methods=['GET', 'POST'])
@login_required
def account(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateAccountForm()
    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            user.image_file = picture_file
            db.session.commit()
            flash('Your picture has been updated!', 'success')
        return redirect(url_for('users.account', user_id=user.id))
    image_file = user.image_file

    meals = Meal.query.filter((Meal.visibility == 'public') | (Meal.visibility == 'followers')
    ).order_by(Meal.id.desc()).paginate(per_page=9, page=page)

    return render_template('users/account.html', title='Account', image_file=image_file, form=form, user=user, meals=meals)

@users.route("/account/<int:user_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_account(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateAccountForm()
    picture_form = UpdatePictureForm()
    if picture_form.validate_on_submit() and picture_form.picture.data:
        picture_file = save_picture(picture_form.picture.data)
        user.image_file = picture_file
        db.session.commit()
        flash('Your picture has been updated!', 'success')
        return redirect(url_for('users.account', user_id=user.id))
    if form.validate_on_submit():
        user.username = form.username.data
        user.bio = form.bio.data
        user.private = form.private.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account', user_id=user.id))
    elif request.method == 'GET':
        form.username.data = user.username
        form.bio.data = user.bio
        form.private.data = user.private
    image_file = user.image_file
    return render_template('users/edit_account.html', title='Account', image_file=image_file, form=form, picture_form=picture_form, user=user)

@users.route("/account/<int:user_id>/reset_email", methods=['GET', 'POST'])
@login_required
def change_email(user_id):
    user = User.query.get_or_404(user_id)
    form = ChangeEmailForm()
    if form.validate_on_submit():
        send_change_email_request(user, form.email.data)
        flash('Check your email, and click the link to verify!', 'success')
        return redirect(url_for('users.account', user_id=user.id))
    elif request.method == 'GET':
        form.email.data = user.email
    return render_template('users/change_email.html', title='Account', form=form, user=user)

@users.route("/user/<string:username>")
def user_meals(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    meals = Meal.query\
        .filter_by(author=user)\
        .order_by(Meal.id.desc())\
        .paginate(per_page=9, page=page)
    return render_template('users/user_meals.html', meals=meals, user=user)

@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions on how to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('users/reset_request.html', title='Reset Password', form=form)

@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token! Please try again' 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            login_user(user)
            flash(f'Hello {user.username}! Your password has been updated', 'success')
            return redirect(url_for('main.home'))
    return render_template('users/reset_token.html', title='Reset Password', form=form, user=user)

@users.route("/reset_email/<token>/<email>", methods=['GET', 'POST'])
def reset_email(token, email):
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token! Please try again' 'warning')
        return redirect(url_for('users.reset_request'))
    user.email = email
    db.session.commit()
    flash('Your email has been updated!', 'success')
    return redirect(url_for('users.account', user_id=user.id))

@users.route("/shopping_list/<username>")
@login_required
def shopping_list(username):
    use_saved = request.args.get('use_saved', 'true') == 'true'
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    meals = Meal.query.order_by(Meal.id.desc())

    if use_saved:
        if user.shopping_list:
            ingredients = json.loads(user.shopping_list)
        else:
            ingredients = []
    else:
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        selected_meal_ids = [getattr(user, day) for day in weekdays if getattr(user, day)]
        storage_names = {i.name.strip().lower() for i in StorageItem.query.filter_by(user_id=user.id).all()}
        ingredients = []
        for meal_id in selected_meal_ids:
            meal = Meal.query.get(meal_id)
            if meal:
                for ingredient in meal.ingredient_list:
                    if ingredient.name.strip().lower() not in storage_names:
                        ingredients.append(ingredient.name.strip())
    counted = Counter(ingredients)
    clean_list = []
    for item, count in counted.items():
        if count > 1:
            clean_list.append(f"{item} x{count}")
        else:
            clean_list.append(item)
    return render_template('users/shopping_list.html', meals=meals, user=user, ingredients=clean_list)

@users.route("/user/<int:user_id>/delete", methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user != current_user and current_user.admin == False:
        abort(403)
    db.session.delete(user)
    db.session.commit()
    flash('Account has been deleted', 'success')
    return redirect(url_for('main.home'))

@users.route("/admin", methods=['POST', 'GET'])
@login_required
def admin():
    if not current_user.admin:
        abort(403)
    users = User.query.order_by(User.id.asc())
    meals = Meal.query.order_by(Meal.id.asc())
    return render_template('users/admin.html', title='Admin', users=users, meals=meals)

@users.route("/make_admin/<int:user_id>", methods=['POST', 'GET'])
@login_required
def make_admin(user_id):
    if not current_user.admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    user.admin = True
    db.session.commit()
    flash(f'{user.username} is now an admin!', 'success')
    return redirect(url_for('users.admin'))

@users.route("/remove_admin/<int:user_id>", methods=['POST', 'GET'])
@login_required
def remove_admin(user_id):
    if not current_user.admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    user.admin = False
    db.session.commit()
    flash(f'{user.username} is no longer an admin!', 'success')
    return redirect(url_for('users.admin'))

@users.route("/save_or_share", methods=['POST'])
def save_or_share():
    remaining_ingredients = request.form.getlist('ingredients')
    action = request.form.get('action')

    if action == 'save':
        user = User.query.filter_by(id=current_user.id).first()
        user.shopping_list = json.dumps(remaining_ingredients)
        db.session.commit()
        flash(f'Your shopping list has been saved!', 'success')
        return redirect(url_for('users.shopping_list', username=user.username, use_saved='true'))
        
    elif action == 'share':
        message = "Shopping list:\n\n" + "\n".join(f"- {item}" for item in remaining_ingredients)
        send_shopping_email(current_user, message)
        flash(f'Your shopping list has been sent to {current_user.email}!', 'success')
    return redirect(url_for('main.home'))

@users.route("/follow/<int:user_id>")
@login_required
def follow(user_id):
    followed = User.query.filter_by(id=user_id).first_or_404()
    if current_user == followed:
        flash(f'You cant follow yourself!', 'danger')  
        return redirect(url_for('users.account', user_id=followed.id))

    if current_user.is_following(followed):
        flash(f"You're already following {followed.username}!", 'info')
        return redirect(url_for('users.account', user_id=followed.id))

    if followed.private:
        if current_user.has_requested(followed):
            flash(f'Follow request already sent to {followed.username}.', 'info')
        else:
            current_user.send_follow_request(followed)
            db.session.commit()
            flash(f'Follow request sent to {followed.username}!', 'success')
    else:
        current_user.follow(followed)
        db.session.commit()
        flash(f"You're now following {followed.username}!", 'success')
    return redirect(url_for('users.account', user_id=followed.id))  


@users.route("/unfollow/<int:user_id>")
@login_required
def unfollow(user_id):
    followed = User.query.filter_by(id=user_id).first_or_404()
    if current_user != followed:
        if current_user.is_following(followed):
            current_user.unfollow(followed)
            db.session.commit()
            flash(f"You're no longer following {followed.username}!", 'success')
            return redirect(url_for('users.account', user_id=followed.id)) 
        flash(f"You're not following {followed.username}!", 'failure')  
        return redirect(url_for('users.account', user_id=followed.id))
    flash(f'You cant follow yourself!', 'failure')  
    return redirect(url_for('users.account', user_id=followed.id))

@users.route("/follow_request/<int:requester_id>/accept")
@login_required
def accept_follow_request(requester_id):
    requester = User.query.filter_by(id=requester_id).first_or_404()

    if not requester.has_requested(current_user):
        abort(404)

    requester.cancel_follow_request(current_user)  # fjern fra pending
    requester.follow(current_user)                  # legg til i faktisk followers
    db.session.commit()
    flash(f'{requester.username} now follows you!', 'success')
    return redirect(url_for('users.account', user_id=current_user.id))


@users.route("/follow_request/<int:requester_id>/decline")
@login_required
def decline_follow_request(requester_id):
    requester = User.query.filter_by(id=requester_id).first_or_404()

    if not requester.has_requested(current_user):
        abort(404)

    requester.cancel_follow_request(current_user)
    db.session.commit()
    flash(f'Follow request from {requester.username} declined.', 'info')
    return redirect(url_for('users.account', user_id=current_user.id))

@users.route("/follow_request/<int:followed_id>/cancel")
@login_required
def cancel_follow_request(followed_id):
    followed = User.query.filter_by(id=followed_id).first_or_404()
    if not current_user.has_requested(followed):
        abort(404)
    current_user.cancel_follow_request(followed)
    db.session.commit()
    flash(f'Follow request to {followed.username} has been canceled.', 'info')
    return redirect(url_for('users.account', user_id=followed.id))

@users.route("/followers/<int:user_id>", methods=['GET', 'POST'])
@login_required
def followers(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', title='Follow requests', user=user)

@users.route("/followers/<int:user_id>/requests", methods=['GET', 'POST'])
@login_required
def follow_requests(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('users/follow_requests.html', title='Follow requests', user=user)

@users.route("/push/subscribe", methods=['POST'])
@login_required
def push_subscribe():
    data = request.get_json()

    existing = PushSubscription.query.filter_by(endpoint=data['endpoint']).first()
    if existing:
        return jsonify({'status': 'already subscribed'})

    subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=data['endpoint'],
        p256dh=data['keys']['p256dh'],
        auth=data['keys']['auth']
    )
    db.session.add(subscription)
    db.session.commit()
    return jsonify({'status': 'subscribed'})

@users.route("/storage/<username>", methods=['GET', 'POST'])
@login_required
def storage(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    if request.method == 'POST':
        names = request.form.getlist('storage_name')
        expirations = request.form.getlist('storage_expiration')
        StorageItem.query.filter_by(user_id=current_user.id).delete()
        for name, expiration in zip(names, expirations):
            name = name.strip()
            if not name:
                continue
            exp_date = None
            if expiration.strip():
                exp_date = datetime.strptime(expiration.strip(), '%Y-%m-%d').date()
            db.session.add(StorageItem(user_id=current_user.id, name=name, expiration_date=exp_date))
        db.session.commit()
        flash('Your storage has been updated!', 'success')
        return redirect(url_for('users.storage', username=user.username))
    items = StorageItem.query.filter_by(user_id=current_user.id).all()
    return render_template('users/storage.html', user=user, items=items)

@users.route("/push/unsubscribe", methods=['POST'])
@login_required
def push_unsubscribe():
    data = request.get_json()
    endpoint = data.get('endpoint')

    subscription = PushSubscription.query.filter_by(endpoint=endpoint, user_id=current_user.id).first()
    if subscription:
        db.session.delete(subscription)
        db.session.commit()

    return jsonify({'status': 'unsubscribed'})