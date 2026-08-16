import time

import httpx

from app.adapters.base import (
    PublishRequest,
    PublishResult,
    SocialPublisher,
)


class FakePlatformPublisher(SocialPublisher):
    platform: str

    def __init__(
        self,
        access_token: str,
        base_url: str = "http://127.0.0.1:9000",
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.max_retries = max_retries

    def publish(self, request: PublishRequest) -> PublishResult:
        url = f"{self.base_url}/publish"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Idempotency-Key": request.idempotency_key,
        }

        payload = {
            "platform": self.platform,
            "caption": request.caption,
            "image_path": request.image_path,
        }

        for attempt in range(self.max_retries + 1):
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=10,
            )

            if response.status_code == 429:
                if attempt >= self.max_retries:
                    response.raise_for_status()

                retry_after = int(
                    response.headers.get("Retry-After", "1")
                )

                time.sleep(retry_after)
                continue

            response.raise_for_status()

            data = response.json()

            return PublishResult(
                external_post_id=data["external_post_id"],
                status=data["status"],
            )

        raise RuntimeError("Publishing failed after retries.")