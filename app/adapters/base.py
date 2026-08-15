from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PublishRequest:
    caption: str
    image_path: str
    idempotency_key: str


@dataclass(frozen=True)
class PublishResult:
    external_post_id: str
    status: str


class SocialPublisher(ABC):

    @abstractmethod
    def publish(self, request: PublishRequest) -> PublishResult:
        raise NotImplementedError