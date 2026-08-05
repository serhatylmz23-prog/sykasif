$ErrorActionPreference = "Stop"

$env:PYTHONPATH = (Resolve-Path "src").Path
$python = (Resolve-Path ".venv\Scripts\python.exe").Path
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

$paketKlasoru = "src\syk_core\external_devices"

$baglantiModeli = Join-Path $paketKlasoru "connection_model.py"
$nmeaModeli = Join-Path $paketKlasoru "nmea_model.py"
$gercekGarmin = Join-Path $paketKlasoru "garmin_real_adapter.py"
$kesifServisi = Join-Path $paketKlasoru "device_discovery.py"
$initDosyasi = Join-Path $paketKlasoru "__init__.py"

$testDosyasi = "tests\test_garmin_real_connection_contract.py"

$artifactKlasoru = "artifacts\dsp_0019_05"
$dogrulama = Join-Path $artifactKlasoru "garmin_connection_contract_dogrula.py"
$rapor = Join-Path $artifactKlasoru "SYK_DSP_0019_05_GARMIN_GERCEK_CIHAZ_SOZLESMESI.txt"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $paketKlasoru, $artifactKlasoru |
    Out-Null

$baglantiModelKodu = @'
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class DeviceTransportType(StrEnum):
    SERIAL = "serial"
    USB = "usb"
    TCP = "tcp"
    UDP = "udp"
    NMEA_0183 = "nmea-0183"
    NMEA_2000_GATEWAY = "nmea-2000-gateway"
    FILE_REPLAY = "file-replay"
    MOCK = "mock"


class DeviceDataAuthority(StrEnum):
    SIMULATION = "simulation"
    EXTERNAL_LIVE = "external-live"
    EXTERNAL_REPLAY = "external-replay"
    MANUAL_IMPORT = "manual-import"


class RawDataAvailability(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DeviceEndpoint:
    transport: DeviceTransportType
    host: str | None = None
    port: int | None = None
    serial_port: str | None = None
    baud_rate: int | None = None
    source_path: str | None = None
    timeout_seconds: float = 5.0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError(
                "Bağlantı zaman aşımı sıfırdan büyük olmalıdır."
            )

        if self.port is not None:
            if not 1 <= self.port <= 65535:
                raise ValueError(
                    "Ağ portu 1 ile 65535 arasında olmalıdır."
                )

        if self.baud_rate is not None:
            if self.baud_rate <= 0:
                raise ValueError(
                    "Seri bağlantı hızı sıfırdan büyük olmalıdır."
                )

        if self.transport in {
            DeviceTransportType.TCP,
            DeviceTransportType.UDP,
        }:
            if not self.host or self.port is None:
                raise ValueError(
                    "Ağ bağlantısı için host ve port gereklidir."
                )

        if self.transport in {
            DeviceTransportType.SERIAL,
            DeviceTransportType.USB,
            DeviceTransportType.NMEA_0183,
        }:
            if not self.serial_port:
                raise ValueError(
                    "Seri bağlantı için port adı gereklidir."
                )

        if self.transport == DeviceTransportType.FILE_REPLAY:
            if not self.source_path:
                raise ValueError(
                    "Dosya tekrar oynatma için kaynak yolu gereklidir."
                )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["transport"] = self.transport.value

        return data


@dataclass(frozen=True, slots=True)
class DeviceProtocolProfile:
    protocol_name: str
    protocol_version: str | None
    authority: DeviceDataAuthority
    raw_data_availability: RawDataAvailability
    supports_depth: bool
    supports_water_temperature: bool
    supports_position: bool
    supports_targets: bool
    supports_bottom_profile: bool
    supports_vendor_raw_sonar: bool
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.protocol_name.strip():
            raise ValueError(
                "Protokol adı boş bırakılamaz."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_name": self.protocol_name,
            "protocol_version": self.protocol_version,
            "authority": self.authority.value,
            "raw_data_availability": (
                self.raw_data_availability.value
            ),
            "supports_depth": self.supports_depth,
            "supports_water_temperature": (
                self.supports_water_temperature
            ),
            "supports_position": self.supports_position,
            "supports_targets": self.supports_targets,
            "supports_bottom_profile": (
                self.supports_bottom_profile
            ),
            "supports_vendor_raw_sonar": (
                self.supports_vendor_raw_sonar
            ),
            "notes": list(self.notes),
        }
'@

$nmeaModelKodu = @'
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class NmeaParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NmeaSentence:
    talker: str
    sentence_type: str
    fields: tuple[str, ...]
    checksum: str | None
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "talker": self.talker,
            "sentence_type": self.sentence_type,
            "fields": list(self.fields),
            "checksum": self.checksum,
            "raw": self.raw,
        }


def calculate_checksum(payload: str) -> str:
    value = 0

    for character in payload:
        value ^= ord(character)

    return f"{value:02X}"


def parse_nmea_sentence(
    sentence: str,
    *,
    validate_checksum: bool = True,
) -> NmeaSentence:
    clean = sentence.strip()

    if not clean.startswith("$"):
        raise NmeaParseError(
            "NMEA cümlesi '$' işaretiyle başlamalıdır."
        )

    body = clean[1:]
    checksum: str | None = None

    if "*" in body:
        body, checksum = body.rsplit("*", 1)
        checksum = checksum.upper()

        if len(checksum) != 2:
            raise NmeaParseError(
                "NMEA checksum uzunluğu hatalıdır."
            )

        if validate_checksum:
            expected = calculate_checksum(body)

            if checksum != expected:
                raise NmeaParseError(
                    "NMEA checksum doğrulaması başarısız."
                )

    parts = body.split(",")

    if not parts or len(parts[0]) < 5:
        raise NmeaParseError(
            "NMEA cümle başlığı geçersizdir."
        )

    header = parts[0]

    return NmeaSentence(
        talker=header[:2],
        sentence_type=header[2:],
        fields=tuple(parts[1:]),
        checksum=checksum,
        raw=clean,
    )


def parse_depth_meters(
    sentence: NmeaSentence,
) -> float | None:
    if sentence.sentence_type == "DPT":
        if not sentence.fields:
            return None

        return _to_float(
            sentence.fields[0]
        )

    if sentence.sentence_type == "DBT":
        if len(sentence.fields) >= 4:
            return _to_float(
                sentence.fields[3]
            )

    return None


def parse_water_temperature_c(
    sentence: NmeaSentence,
) -> float | None:
    if sentence.sentence_type != "MTW":
        return None

    if not sentence.fields:
        return None

    return _to_float(
        sentence.fields[0]
    )


def _to_float(
    value: str,
) -> float | None:
    clean = value.strip()

    if not clean:
        return None

    try:
        return float(clean)
    except ValueError as error:
        raise NmeaParseError(
            f"Sayısal NMEA alanı geçersiz: {clean}"
        ) from error
'@

$gercekGarminKodu = @'
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from threading import RLock
from typing import Any

from .connection_model import (
    DeviceDataAuthority,
    DeviceEndpoint,
    DeviceProtocolProfile,
    DeviceTransportType,
    RawDataAvailability,
)
from .device_model import (
    DeviceCapability,
    DeviceConnectionState,
    DeviceHealth,
    DeviceIdentity,
    DeviceProfile,
    ExternalDevice,
)
from .nmea_model import (
    NmeaSentence,
    parse_depth_meters,
    parse_nmea_sentence,
    parse_water_temperature_c,
)


@dataclass(frozen=True, slots=True)
class GarminConnectionSnapshot:
    connected: bool
    endpoint: dict[str, Any]
    protocol: dict[str, Any]
    depth_m: float | None
    water_temperature_c: float | None
    sentence_count: int
    rejected_sentence_count: int
    real_device_data: bool
    vendor_raw_sonar_available: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "endpoint": dict(self.endpoint),
            "protocol": dict(self.protocol),
            "depth_m": self.depth_m,
            "water_temperature_c": (
                self.water_temperature_c
            ),
            "sentence_count": self.sentence_count,
            "rejected_sentence_count": (
                self.rejected_sentence_count
            ),
            "real_device_data": self.real_device_data,
            "vendor_raw_sonar_available": (
                self.vendor_raw_sonar_available
            ),
        }


class GarminRealAdapter(ExternalDevice):
    def __init__(
        self,
        *,
        identity: DeviceIdentity,
        endpoint: DeviceEndpoint,
        protocol: DeviceProtocolProfile | None = None,
    ) -> None:
        if endpoint.transport == DeviceTransportType.MOCK:
            raise ValueError(
                "Gerçek Garmin bağdaştırıcısı mock bağlantı kabul etmez."
            )

        profile = DeviceProfile(
            identity=identity,
            capabilities=(
                DeviceCapability.DEPTH,
                DeviceCapability.WATER_TEMPERATURE,
                DeviceCapability.GPS,
                DeviceCapability.BOTTOM_PROFILE,
                DeviceCapability.RECORDING,
            ),
            shallow_coast_priority_depth_m=2.0,
            metadata={
                "adapter_mode": "real-contract",
                "real_protocol_connected": False,
                "manufacturer_software_modified": False,
            },
        )

        super().__init__(profile)

        self._endpoint = endpoint
        self._protocol = protocol or (
            DeviceProtocolProfile(
                protocol_name="NMEA-compatible",
                protocol_version=None,
                authority=(
                    DeviceDataAuthority.EXTERNAL_LIVE
                ),
                raw_data_availability=(
                    RawDataAvailability.PARTIAL
                ),
                supports_depth=True,
                supports_water_temperature=True,
                supports_position=True,
                supports_targets=False,
                supports_bottom_profile=False,
                supports_vendor_raw_sonar=False,
                notes=(
                    "Yalnız desteklenen standart veri alanları işlenir.",
                    "Garmin kapalı yazılımına müdahale edilmez.",
                    "Ham üretici sonar akışı destekleniyor varsayılmaz.",
                ),
            )
        )

        self._lock = RLock()
        self._sentence_count = 0
        self._rejected_sentence_count = 0
        self._latest_depth_m: float | None = None
        self._latest_water_temperature_c: (
            float | None
        ) = None

    @property
    def endpoint(self) -> DeviceEndpoint:
        return self._endpoint

    @property
    def protocol(
        self,
    ) -> DeviceProtocolProfile:
        return self._protocol

    def connect(self) -> None:
        with self._lock:
            self._set_state(
                connection_state=(
                    DeviceConnectionState.CONNECTING
                ),
                health=DeviceHealth.UNKNOWN,
            )

            self._set_state(
                connection_state=(
                    DeviceConnectionState.CONNECTED
                ),
                health=DeviceHealth.HEALTHY,
            )

    def disconnect(self) -> None:
        with self._lock:
            self._set_state(
                connection_state=(
                    DeviceConnectionState.DISCONNECTED
                ),
                health=DeviceHealth.UNKNOWN,
            )

    def ingest_nmea(
        self,
        sentence: str,
        *,
        validate_checksum: bool = True,
    ) -> NmeaSentence:
        with self._lock:
            if (
                self.connection_state
                != DeviceConnectionState.CONNECTED
            ):
                raise RuntimeError(
                    "Gerçek Garmin bağdaştırıcısı bağlı değil."
                )

            try:
                parsed = parse_nmea_sentence(
                    sentence,
                    validate_checksum=validate_checksum,
                )
            except ValueError:
                self._rejected_sentence_count += 1
                self._set_state(
                    connection_state=(
                        DeviceConnectionState.DEGRADED
                    ),
                    health=DeviceHealth.WARNING,
                    last_error=(
                        "Geçersiz NMEA cümlesi reddedildi."
                    ),
                )
                raise

            self._sentence_count += 1

            depth_m = parse_depth_meters(
                parsed
            )

            if depth_m is not None:
                if depth_m < 0:
                    raise ValueError(
                        "Negatif derinlik kabul edilemez."
                    )

                self._latest_depth_m = depth_m

            water_temperature_c = (
                parse_water_temperature_c(
                    parsed
                )
            )

            if water_temperature_c is not None:
                self._latest_water_temperature_c = (
                    water_temperature_c
                )

            self._set_state(
                connection_state=(
                    DeviceConnectionState.CONNECTED
                ),
                health=DeviceHealth.HEALTHY,
            )

            return parsed

    def ingest_many(
        self,
        sentences: Iterable[str],
        *,
        validate_checksum: bool = True,
    ) -> tuple[NmeaSentence, ...]:
        return tuple(
            self.ingest_nmea(
                sentence,
                validate_checksum=validate_checksum,
            )
            for sentence in sentences
        )

    def connection_snapshot(
        self,
    ) -> GarminConnectionSnapshot:
        return GarminConnectionSnapshot(
            connected=(
                self.connection_state
                == DeviceConnectionState.CONNECTED
            ),
            endpoint=self.endpoint.to_dict(),
            protocol=self.protocol.to_dict(),
            depth_m=self._latest_depth_m,
            water_temperature_c=(
                self._latest_water_temperature_c
            ),
            sentence_count=self._sentence_count,
            rejected_sentence_count=(
                self._rejected_sentence_count
            ),
            real_device_data=True,
            vendor_raw_sonar_available=(
                self.protocol.supports_vendor_raw_sonar
            ),
        )

    def status_snapshot(self) -> dict[str, Any]:
        data = super().status_snapshot()

        data["endpoint"] = self.endpoint.to_dict()
        data["protocol"] = self.protocol.to_dict()
        data["connection_snapshot"] = (
            self.connection_snapshot().to_dict()
        )

        return data
'@

$kesifServisiKodu = @'
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .connection_model import (
    DeviceEndpoint,
    DeviceTransportType,
)


@dataclass(frozen=True, slots=True)
class DiscoveredDeviceEndpoint:
    discovery_id: str
    manufacturer_hint: str
    model_hint: str
    endpoint: DeviceEndpoint
    verified: bool
    discovery_source: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["endpoint"] = (
            self.endpoint.to_dict()
        )

        return data


class DeviceDiscoveryService:
    def discover(
        self,
        *,
        include_mock_candidates: bool = False,
    ) -> tuple[DiscoveredDeviceEndpoint, ...]:
        candidates: list[
            DiscoveredDeviceEndpoint
        ] = []

        if include_mock_candidates:
            candidates.append(
                DiscoveredDeviceEndpoint(
                    discovery_id=(
                        "discovery-garmin-file-replay"
                    ),
                    manufacturer_hint="Garmin",
                    model_hint="NMEA Replay Candidate",
                    endpoint=DeviceEndpoint(
                        transport=(
                            DeviceTransportType.FILE_REPLAY
                        ),
                        source_path=(
                            "artifacts/device_replay/"
                            "garmin_nmea_sample.log"
                        ),
                        metadata={
                            "simulation_only": True,
                        },
                    ),
                    verified=False,
                    discovery_source=(
                        "deterministic-development-profile"
                    ),
                    metadata={
                        "real_device": False,
                        "automatic_connection": False,
                    },
                )
            )

        return tuple(candidates)


device_discovery_service = DeviceDiscoveryService()
'@

$testKodu = @'
from __future__ import annotations

import pytest

from syk_core.external_devices.connection_model import (
    DeviceDataAuthority,
    DeviceEndpoint,
    DeviceProtocolProfile,
    DeviceTransportType,
    RawDataAvailability,
)
from syk_core.external_devices.device_model import (
    DeviceConnectionState,
    DeviceIdentity,
)
from syk_core.external_devices.device_discovery import (
    device_discovery_service,
)
from syk_core.external_devices.garmin_real_adapter import (
    GarminRealAdapter,
)
from syk_core.external_devices.nmea_model import (
    NmeaParseError,
    calculate_checksum,
    parse_nmea_sentence,
)


def sentence(payload: str) -> str:
    return (
        f"${payload}*"
        f"{calculate_checksum(payload)}"
    )


def create_adapter() -> GarminRealAdapter:
    return GarminRealAdapter(
        identity=DeviceIdentity(
            manufacturer="Garmin",
            model="External NMEA Device",
            serial_number="GARMIN-REAL-CONTRACT-001",
            device_id="garmin-real-contract-001",
        ),
        endpoint=DeviceEndpoint(
            transport=DeviceTransportType.TCP,
            host="127.0.0.1",
            port=10110,
            timeout_seconds=2.0,
        ),
    )


def test_real_garmin_contract_full_flow() -> None:
    adapter = create_adapter()

    assert (
        adapter.connection_state
        == DeviceConnectionState.DISCONNECTED
    )

    adapter.connect()

    adapter.ingest_many(
        (
            sentence("SDDPT,1.42,0.00"),
            sentence("YXMTW,19.8,C"),
        )
    )

    snapshot = adapter.connection_snapshot()

    assert snapshot.connected is True
    assert snapshot.depth_m == 1.42
    assert snapshot.water_temperature_c == 19.8
    assert snapshot.sentence_count == 2
    assert snapshot.real_device_data is True
    assert (
        snapshot.vendor_raw_sonar_available
        is False
    )

    assert (
        snapshot.protocol["authority"]
        == "external-live"
    )

    assert (
        snapshot.protocol[
            "raw_data_availability"
        ]
        == "partial"
    )

    adapter.disconnect()

    assert (
        adapter.connection_state
        == DeviceConnectionState.DISCONNECTED
    )


def test_invalid_nmea_degrades_health() -> None:
    adapter = create_adapter()
    adapter.connect()

    with pytest.raises(
        NmeaParseError,
        match="checksum",
    ):
        adapter.ingest_nmea(
            "$SDDPT,1.42,0.00*00"
        )

    snapshot = adapter.connection_snapshot()

    assert snapshot.rejected_sentence_count == 1
    assert adapter.health.value == "warning"


def test_network_endpoint_requires_host_and_port() -> None:
    with pytest.raises(
        ValueError,
        match="host ve port",
    ):
        DeviceEndpoint(
            transport=DeviceTransportType.TCP,
        )


def test_vendor_raw_data_is_not_assumed() -> None:
    profile = DeviceProtocolProfile(
        protocol_name="NMEA 0183",
        protocol_version="4.x",
        authority=DeviceDataAuthority.EXTERNAL_LIVE,
        raw_data_availability=(
            RawDataAvailability.PARTIAL
        ),
        supports_depth=True,
        supports_water_temperature=True,
        supports_position=True,
        supports_targets=False,
        supports_bottom_profile=False,
        supports_vendor_raw_sonar=False,
    )

    assert profile.supports_vendor_raw_sonar is False
    assert profile.supports_targets is False


def test_discovery_never_claims_real_device() -> None:
    candidates = (
        device_discovery_service.discover(
            include_mock_candidates=True
        )
    )

    assert len(candidates) == 1
    assert candidates[0].verified is False
    assert (
        candidates[0].metadata["real_device"]
        is False
    )


def test_nmea_parser() -> None:
    payload = "SDDPT,1.84,0.00"
    parsed = parse_nmea_sentence(
        sentence(payload)
    )

    assert parsed.talker == "SD"
    assert parsed.sentence_type == "DPT"
    assert parsed.fields[0] == "1.84"
'@

$initEklemeKodu = @'

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
'@

$dogrulamaKodu = @'
from __future__ import annotations

from syk_core.external_devices.connection_model import (
    DeviceEndpoint,
    DeviceTransportType,
)
from syk_core.external_devices.device_model import (
    DeviceIdentity,
)
from syk_core.external_devices.garmin_real_adapter import (
    GarminRealAdapter,
)
from syk_core.external_devices.nmea_model import (
    calculate_checksum,
)


def sentence(payload: str) -> str:
    return (
        f"${payload}*"
        f"{calculate_checksum(payload)}"
    )


adapter = GarminRealAdapter(
    identity=DeviceIdentity(
        manufacturer="Garmin",
        model="Contract Verification Device",
        serial_number="VERIFY-001",
        device_id="garmin-contract-verify-001",
    ),
    endpoint=DeviceEndpoint(
        transport=DeviceTransportType.TCP,
        host="127.0.0.1",
        port=10110,
    ),
)

adapter.connect()

adapter.ingest_many(
    (
        sentence("SDDPT,1.36,0.00"),
        sentence("YXMTW,20.1,C"),
    )
)

snapshot = adapter.connection_snapshot()

print(
    "REAL_DEVICE_DATA",
    snapshot.real_device_data,
)

print(
    "DEPTH_M",
    snapshot.depth_m,
)

print(
    "WATER_TEMPERATURE_C",
    snapshot.water_temperature_c,
)

print(
    "RAW_VENDOR_SONAR",
    snapshot.vendor_raw_sonar_available,
)

if snapshot.depth_m != 1.36:
    raise RuntimeError(
        "Derinlik sözleşmesi doğrulanamadı."
    )

if snapshot.water_temperature_c != 20.1:
    raise RuntimeError(
        "Su sıcaklığı sözleşmesi doğrulanamadı."
    )

if snapshot.vendor_raw_sonar_available:
    raise RuntimeError(
        "Desteklenmeyen ham sonar verisi "
        "yanlışlıkla etkin gösterildi."
    )

adapter.disconnect()

print(
    "GARMIN_REAL_CONNECTION_CONTRACT_OK"
)
'@

[System.IO.File]::WriteAllText(
    $baglantiModeli,
    $baglantiModelKodu,
    $utf8NoBom
)

[System.IO.File]::WriteAllText(
    $nmeaModeli,
    $nmeaModelKodu,
    $utf8NoBom
)

[System.IO.File]::WriteAllText(
    $gercekGarmin,
    $gercekGarminKodu,
    $utf8NoBom
)

[System.IO.File]::WriteAllText(
    $kesifServisi,
    $kesifServisiKodu,
    $utf8NoBom
)

[System.IO.File]::WriteAllText(
    $testDosyasi,
    $testKodu,
    $utf8NoBom
)

[System.IO.File]::WriteAllText(
    $dogrulama,
    $dogrulamaKodu,
    $utf8NoBom
)

$initMetni = Get-Content `
    -LiteralPath $initDosyasi `
    -Raw `
    -Encoding UTF8

if (
    $initMetni -notmatch
    "GarminRealAdapter"
) {
    $initMetni = @(
    $initMetni.TrimEnd()
    $initEklemeKodu.Trim()
    ""
) -join "`n"

    [System.IO.File]::WriteAllText(
        $initDosyasi,
        $initMetni,
        $utf8NoBom
    )
}

$raporSatirlari = (
    [System.Collections.Generic.List[string]]::new()
)

function Rapor-Yaz {
    param(
        [AllowEmptyString()]
        [string]$Metin = ""
    )

    Write-Host $Metin
    $raporSatirlari.Add($Metin)
}

try {
    Rapor-Yaz "=== 1. GERÇEK CİHAZ BAĞLANTI SÖZLEŞMESİ ==="

    $kaynakDosyalari = @(
        $initDosyasi,
        $baglantiModeli,
        $nmeaModeli,
        $gercekGarmin,
        $kesifServisi,
        $testDosyasi
    )

    foreach ($dosya in $kaynakDosyalari) {
        if (-not (Test-Path $dosya)) {
            throw "Gerekli dosya bulunamadı: $dosya"
        }
    }

    & $python -m py_compile `
        $kaynakDosyalari `
        $dogrulama

    if ($LASTEXITCODE -ne 0) {
        throw "Python yazım doğrulaması başarısız."
    }

    Rapor-Yaz "GARMIN_CONNECTION_CONTRACT_YAZIM_OK"
    Rapor-Yaz ""
    Rapor-Yaz "=== 2. HEDEF TESTLER ==="

    & $python -m pytest `
        $testDosyasi `
        -v

    if ($LASTEXITCODE -ne 0) {
        throw "Gerçek cihaz bağlantı testleri başarısız."
    }

    Rapor-Yaz "GARMIN_CONNECTION_TESTLERI_6_6_OK"
    Rapor-Yaz ""
    Rapor-Yaz "=== 3. SÖZLEŞME DOĞRULAMASI ==="

    & $python $dogrulama

    if ($LASTEXITCODE -ne 0) {
        throw "Garmin bağlantı sözleşmesi doğrulanamadı."
    }

    Rapor-Yaz "GARMIN_REAL_CONNECTION_CONTRACT_OK"
    Rapor-Yaz ""
    Rapor-Yaz "=== 4. REGRESYON TESTLERİ ==="

    & $python -m pytest `
        "tests\test_external_device_adapter.py" `
        "tests\test_external_device_runtime_api.py" `
        "tests\test_sonar_session_runtime.py" `
        $testDosyasi `
        -q

    if ($LASTEXITCODE -ne 0) {
        throw "Garmin bağlantı regresyon testleri başarısız."
    }

    Rapor-Yaz "GARMIN_CONNECTION_REGRESYON_OK"
    Rapor-Yaz ""
    Rapor-Yaz "=== 5. GİT BİÇİM KONTROLÜ ==="

    git diff --check -- $kaynakDosyalari

    if ($LASTEXITCODE -ne 0) {
        throw "Git biçim kontrolü başarısız."
    }

    Rapor-Yaz "GIT_BICIM_KONTROLU_OK"
    Rapor-Yaz ""
    Rapor-Yaz "=== 6. GİT KAYDI ==="

    git add -- $kaynakDosyalari

    $hazirlanan = @(
        git diff --cached --name-only
    )

    if ($hazirlanan.Count -gt 0) {
        git commit -m `
            "feat(devices): garmin gercek cihaz baglanti sozlesmesini ekle"

        if ($LASTEXITCODE -ne 0) {
            throw "Git commit başarısız."
        }

        Rapor-Yaz "GIT_COMMIT_OK"
    }
    else {
        Rapor-Yaz "YENI_COMMIT_GEREKMIYOR"
    }

    $sonCommit = git --no-pager log -1 --oneline
    $gitDurumu = @(git status --short)

    Rapor-Yaz "SON_COMMIT=$sonCommit"
    Rapor-Yaz "CALISMA_AGACI_KAYIT_SAYISI=$($gitDurumu.Count)"
    Rapor-Yaz ""
    Rapor-Yaz "SYK_DSP_0019_05_GARMIN_GERCEK_CIHAZ_SOZLESMESI_OK"
}
catch {
    Rapor-Yaz ""
    Rapor-Yaz "SYK_DSP_0019_05_GARMIN_GERCEK_CIHAZ_SOZLESMESI_HATA"
    Rapor-Yaz "HATA=$($_.Exception.Message)"
    throw
}
finally {
    $raporSatirlari |
        Set-Content `
            -LiteralPath $rapor `
            -Encoding UTF8
}

Write-Host ""
Write-Host "=== RAPOR SHA256 ===" `
    -ForegroundColor Cyan

Get-FileHash `
    -Algorithm SHA256 `
    -LiteralPath $rapor |
    Format-List

Write-Host ""
Write-Host "SYK_DSP_0019_05_TAMAMLANDI" `
    -ForegroundColor Green