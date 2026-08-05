from .device_model import (
    DeviceCapability,
    DeviceConnectionState,
    DeviceHealth,
    DeviceIdentity,
    DeviceProfile,
    ExternalDevice,
)
from .device_registry import (
    DeviceRegistry,
    device_registry,
)
from .garmin_adapter import (
    GarminAdapter,
    GarminMockConfiguration,
)
from .gps_model import (
    GpsFix,
    GpsFixQuality,
)
from .sonar_model import (
    BottomClassification,
    SonarFrame,
    SonarTarget,
    SonarTargetType,
)

__all__ = [
    "BottomClassification",
    "DeviceCapability",
    "DeviceConnectionState",
    "DeviceHealth",
    "DeviceIdentity",
    "DeviceProfile",
    "DeviceRegistry",
    "ExternalDevice",
    "GarminAdapter",
    "GarminMockConfiguration",
    "GpsFix",
    "GpsFixQuality",
    "SonarFrame",
    "SonarTarget",
    "SonarTargetType",
    "device_registry",
]