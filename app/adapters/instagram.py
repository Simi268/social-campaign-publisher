from app.adapters.fake_base import FakePlatformPublisher


class FakeInstagramPublisher(FakePlatformPublisher):
    platform = "instagram"