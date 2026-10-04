"""Camera module with hardware/mock samplers and privacy masking."""

from roastbot.camera.sampler import BaseCameraSampler, WebcamSampler, MockCameraSampler
from roastbot.camera.privacy import PrivacyEngine

__all__ = ["BaseCameraSampler", "WebcamSampler", "MockCameraSampler", "PrivacyEngine"]
