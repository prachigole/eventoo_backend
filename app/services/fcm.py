"""FCM push notification helper.

Uses the firebase-admin SDK already in requirements.txt.
Silently swallows all errors — a failed notification must never fail an API response.
"""
import logging

from firebase_admin import messaging

from ..auth import _get_app

logger = logging.getLogger(__name__)


def send_push(
    *,
    token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> None:
    """Send a single FCM push to a device token. Never raises."""
    if not token:
        return
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    sound="default",
                    channel_id="eventoo_tasks",
                ),
                priority="high",
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default"),
                ),
            ),
            data=data or {},
            token=token,
        )
        messaging.send(message, app=_get_app())
    except Exception as exc:
        logger.warning("FCM push failed: %s", exc)
