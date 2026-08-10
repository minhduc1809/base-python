from typing import Any, Dict, List, Optional
import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging import logger
from app.modules.notification.models import NotificationModel


class NotificationService:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.model = NotificationModel(db)

    async def create_notification(
        self,
        title: str,
        content: str,
        receiver_type: str,
        sender_id: str,
        sender_name: str,
        users: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        player_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Tạo thông báo trong DB và kích hoạt gửi Push qua OneSignal."""
        doc = await self.model.create_notification(
            title=title,
            content=content,
            receiver_type=receiver_type,
            sender_id=sender_id,
            sender_name=sender_name,
            users=users,
            topics=topics,
        )

        if player_ids:
            await self.send_onesignal_push(title=title, contents=content, player_ids=player_ids)

        return doc

    async def send_onesignal_push(
        self, title: str, contents: str, player_ids: List[str]
    ) -> bool:
        """Gửi Push Notification thông qua OneSignal REST API."""
        one_signal_app_id = getattr(settings, "ONE_SIGNAL_APP_ID", None)
        one_signal_api_key = getattr(settings, "ONE_SIGNAL_API_KEY", None)

        if not one_signal_app_id or not one_signal_api_key:
            logger.warn("OneSignal credentials not configured")
            return False

        url = "https://onesignal.com/api/v1/notifications"
        headers = {
            "Authorization": f"Basic {one_signal_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "app_id": one_signal_app_id,
            "headings": {"en": title, "vi": title},
            "contents": {"en": contents, "vi": contents},
            "include_player_ids": player_ids,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    logger.info("OneSignal push notification sent successfully")
                    return True
                else:
                    logger.error("Failed to send OneSignal push", status=resp.status_code, response=resp.text)
                    return False
        except Exception as e:
            logger.error("OneSignal HTTP call error", error=str(e))
            return False
