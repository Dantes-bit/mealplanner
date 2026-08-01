import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from mealplanner import mail


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                sender='mail.mealplanner@gmail.com',
                recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}
    
If you did not make this request, then simply ignore this email.
'''
    mail.send(msg)


def send_shopping_email(user, message):
    msg = Message('Shopping list',
                sender='mail.mealplanner@gmail.com',
                recipients=[user.email])
    msg.body = message
    mail.send(msg)

def send_change_email_request(user, email):
    token = user.get_reset_token()
    msg = Message('Email Change Request',
                sender='mail.mealplanner@gmail.com',
                recipients=[email])
    msg.body = f'''To change your email, click the following link:
{url_for('users.reset_email', token=token, email=email, _external=True)}
    
If you did not make this request, then simply ignore this email.
'''
    mail.send(msg)

