import os
from dotenv import load_dotenv

class Config:
    load_dotenv()
    SECRET_KEY = os.environ.get('SECRET_KEY')

    database_url = os.environ.get('DATABASE_URL') or os.environ.get('DB_URI')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY_PATH = os.environ.get('VAPID_PRIVATE_KEY_PATH')
    VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL')