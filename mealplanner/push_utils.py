from pywebpush import webpush, WebPushException
from flask import current_app
import json

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