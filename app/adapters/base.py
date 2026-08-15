from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PublishRequest:
    caption: str
    image_path: str | None
    idempotency_key: str


@dataclass
class PublishResult:
    external_post_id: str
    status: str


class SocialPublisher(ABC):

    @abstractmethod
    def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to a social platform."""
        raise NotImplementedError