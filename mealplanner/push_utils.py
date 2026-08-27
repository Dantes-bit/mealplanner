from pywebpush import webpush, WebPushException
from flask import current_app
import json
from datetime import date, timedelta
from mealplanner.models import StorageItem, PushSubscription
import os
import tempfile

def get_vapid_key_path():
    key_content = current_app.config['VAPID_PRIVATE_KEY']
    path = os.path.join(tempfile.gettempdir(), 'vapid_private_key.pem')
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(key_content)
    return path

def send_push_notification(subscription, title, body):
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            },
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=get_vapid_key_path(),
            vapid_claims={"sub": current_app.config['VAPID_CLAIM_EMAIL']}
        )
    except WebPushException as e:
        print(f"Push failed: {e}")

def notify_items_for_date(target_date, message_prefix):
    items = StorageItem.query.filter(
        StorageItem.expiration_date == target_date
    ).all()

    notified_users = {}
    for item in items:
        notified_users.setdefault(item.user_id, []).append(item.name)

    for user_id, item_names in notified_users.items():
        subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()
        names_text = ', '.join(item_names)
        for sub in subscriptions:
            send_push_notification(sub, "MealPlanner", f"{message_prefix}: {names_text}")

def notify_expiring_items(days_ahead=2):
    target_date = date.today() + timedelta(days=days_ahead)
    notify_items_for_date(target_date, "Expiring soon")

def notify_expired_items():
    today = date.today()
    notify_items_for_date(today, "Expired today")