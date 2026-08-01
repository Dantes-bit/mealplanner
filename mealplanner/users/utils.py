from PIL import Image
from flask import url_for
from flask_mail import Message
from mealplanner import mail
import io
import cloudinary.uploader

def save_picture(form_picture):
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    buffer = io.BytesIO()
    img_format = i.format if i.format else 'PNG'
    i.save(buffer, format=img_format)
    buffer.seek(0)

    result = cloudinary.uploader.upload(buffer, folder="profile_pics")
    return result['secure_url']

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

