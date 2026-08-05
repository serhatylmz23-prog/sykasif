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
from .connection_model import (
    DeviceDataAuthority,
    DeviceEndpoint,
    DeviceProtocolProfile,
    DeviceTransportType,
    RawDataAvailability,
)
from .device_discovery import (
    DeviceDiscoveryService,
    DiscoveredDeviceEndpoint,
    device_discovery_service,
)
from .garmin_real_adapter import (
    GarminConnectionSnapshot,
    GarminRealAdapter,
)
from .nmea_model import (
    NmeaParseError,
    NmeaSentence,
    calculate_checksum,
    parse_depth_meters,
    parse_nmea_sentence,
    parse_water_temperature_c,
)
