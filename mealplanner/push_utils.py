from pywebpush import webpush, WebPushException
from flask import current_app
import json
from datetime import date, timedelta
from mealplanner.models import User, StorageItem, PushSubscription

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
            vapid_private_key = current_app.config['VAPID_PRIVATE_KEY'],
            vapid_claims={"sub": current_app.config['VAPID_CLAIM_EMAIL']}
        )
    except WebPushException as e:
        print(f"Push failed: {e}")

def notify_expiring_items(days_ahead=2):
    target_date = date.today() + timedelta(days=days_ahead)

    expiring_items = StorageItem.query.filter(
        StorageItem.expiration_date == target_date
    ).all()

    notified_users = {}
    for item in expiring_items:
        notified_users.setdefault(item.user_id, []).append(item.name)

    for user_id, item_names in notified_users.items():
        subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()
        names_text = ', '.join(item_names)
        for sub in subscriptions:
            send_push_notification(sub, "MealPlanner", f"Expiring soon: {names_text}")