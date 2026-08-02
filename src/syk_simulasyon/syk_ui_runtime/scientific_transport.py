from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Protocol


class ScientificTransportError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScientificDevice:
    id: str
    title: str
    transport: str
    address: str
    connected: bool
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ScientificTransportPacket:
    module_id: str
    live_value: float | int | str
    confidence: float
    status: str
    source: str
    metadata: dict[str, Any]


class SerialBackend(Protocol):
    def ports(self) -> list[dict[str, Any]]:
        ...

    def read_line(
        self,
        port: str,
        baud_rate: int,
        timeout: float,
    ) -> str:
        ...


class PySerialBackend:
    def _serial_modules(self):
        try:
            import serial
            from serial.tools import list_ports
        except ImportError as error:
            raise ScientificTransportError(
                "pyserial kurulu değil. "
                "Kurulum: python -m pip install pyserial"
            ) from error

        return serial, list_ports

    def ports(self) -> list[dict[str, Any]]:
        _, list_ports = self._serial_modules()

        result = []

        for port in list_ports.comports():
            result.append(
                {
                    "device": port.device,
                    "description": (
                        port.description
                        or "Seri Port Cihazı"
                    ),
                    "manufacturer": port.manufacturer,
                    "product": port.product,
                    "serial_number": port.serial_number,
                    "vid": port.vid,
                    "pid": port.pid,
                    "hwid": port.hwid,
                }
            )

        return result

    def read_line(
        self,
        port: str,
        baud_rate: int,
        timeout: float,
    ) -> str:
        serial, _ = self._serial_modules()

        try:
            with serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=timeout,
            ) as connection:
                raw = connection.readline()

        except Exception as error:
            raise ScientificTransportError(
                f"Seri port okunamadı: {port}"
            ) from error

        try:
            return raw.decode(
                "utf-8",
                errors="strict",
            ).strip()

        except UnicodeDecodeError as error:
            raise ScientificTransportError(
                "Seri port verisi UTF-8 değil."
            ) from error


class SerialScientificTransport:
    id = "serial"
    title = "Seri Port / USB-Seri Taşıma"

    def __init__(
        self,
        backend: SerialBackend | None = None,
    ) -> None:
        self._backend = backend or PySerialBackend()

    def discover(self) -> list[ScientificDevice]:
        result = []

        for item in self._backend.ports():
            address = str(item["device"])

            metadata = {
                key: value
                for key, value in item.items()
                if key != "device"
                and value is not None
            }

            result.append(
                ScientificDevice(
                    id=f"serial:{address}",
                    title=str(
                        item.get("description")
                        or address
                    ),
                    transport=self.id,
                    address=address,
                    connected=False,
                    metadata=metadata,
                )
            )

        return result

    def read_packet(
        self,
        *,
        port: str,
        baud_rate: int = 115200,
        timeout: float = 2.0,
    ) -> ScientificTransportPacket:
        raw_line = self._backend.read_line(
            port=port,
            baud_rate=baud_rate,
            timeout=timeout,
        )

        if not raw_line:
            raise ScientificTransportError(
                "Seri porttan boş veri geldi."
            )

        try:
            payload = json.loads(raw_line)

        except json.JSONDecodeError as error:
            raise ScientificTransportError(
                "Seri port verisi geçerli JSON değil."
            ) from error

        required = {
            "module_id",
            "live_value",
        }

        missing = required - payload.keys()

        if missing:
            names = ", ".join(sorted(missing))

            raise ScientificTransportError(
                f"Eksik seri veri alanları: {names}"
            )

        metadata = dict(
            payload.get("metadata", {})
        )

        metadata.update(
            {
                "port": port,
                "baud_rate": baud_rate,
                "transport": self.id,
            }
        )

        return ScientificTransportPacket(
            module_id=str(payload["module_id"]),
            live_value=payload["live_value"],
            confidence=float(
                payload.get("confidence", 50.0)
            ),
            status=str(
                payload.get("status", "preview")
            ),
            source=str(
                payload.get(
                    "source",
                    f"serial:{port}",
                )
            ),
            metadata=metadata,
        )

    def inventory(self) -> list[dict[str, Any]]:
        return [
            asdict(device)
            for device in self.discover()
        ]

class TcpBackend(Protocol):
    def receive(
        self,
        host: str,
        port: int,
        timeout: float,
    ) -> str:
        ...


class SocketTcpBackend:
    def receive(
        self,
        host: str,
        port: int,
        timeout: float,
    ) -> str:
        import socket

        try:
            with socket.create_connection(
                (host, port),
                timeout=timeout,
            ) as connection:
                connection.settimeout(timeout)

                chunks = bytearray()

                while True:
                    block = connection.recv(4096)

                    if not block:
                        break

                    chunks.extend(block)

                    if b"\n" in block:
                        break

        except OSError as error:
            raise ScientificTransportError(
                f"TCP cihazına bağlanılamadı: "
                f"{host}:{port}"
            ) from error

        try:
            return bytes(chunks).decode(
                "utf-8",
                errors="strict",
            ).strip()

        except UnicodeDecodeError as error:
            raise ScientificTransportError(
                "TCP cihaz verisi UTF-8 değil."
            ) from error


class TcpScientificTransport:
    id = "tcp"
    title = "TCP/IP Bilimsel Cihaz Taşıma"

    def __init__(
        self,
        backend: TcpBackend | None = None,
    ) -> None:
        self._backend = backend or SocketTcpBackend()

    def read_packet(
        self,
        *,
        host: str,
        port: int,
        timeout: float = 3.0,
    ) -> ScientificTransportPacket:
        if not host.strip():
            raise ScientificTransportError(
                "TCP cihaz adresi boş olamaz."
            )

        if not 1 <= port <= 65535:
            raise ScientificTransportError(
                "TCP portu 1-65535 aralığında olmalıdır."
            )

        raw_line = self._backend.receive(
            host=host,
            port=port,
            timeout=timeout,
        )

        if not raw_line:
            raise ScientificTransportError(
                "TCP cihazından boş veri geldi."
            )

        try:
            payload = json.loads(raw_line)

        except json.JSONDecodeError as error:
            raise ScientificTransportError(
                "TCP cihaz verisi geçerli JSON değil."
            ) from error

        required = {
            "module_id",
            "live_value",
        }

        missing = required - payload.keys()

        if missing:
            names = ", ".join(sorted(missing))

            raise ScientificTransportError(
                f"Eksik TCP veri alanları: {names}"
            )

        metadata = dict(
            payload.get("metadata", {})
        )

        metadata.update(
            {
                "host": host,
                "port": port,
                "transport": self.id,
            }
        )

        return ScientificTransportPacket(
            module_id=str(payload["module_id"]),
            live_value=payload["live_value"],
            confidence=float(
                payload.get("confidence", 50.0)
            ),
            status=str(
                payload.get("status", "preview")
            ),
            source=str(
                payload.get(
                    "source",
                    f"tcp:{host}:{port}",
                )
            ),
            metadata=metadata,
        )

class BleBackend(Protocol):
    async def discover(
        self,
        timeout: float,
    ) -> list[dict[str, Any]]:
        ...

    async def read_characteristic(
        self,
        address: str,
        characteristic_uuid: str,
        timeout: float,
    ) -> bytes:
        ...


class BleakBackend:
    def _bleak_modules(self):
        try:
            from bleak import BleakClient, BleakScanner
        except ImportError as error:
            raise ScientificTransportError(
                "bleak kurulu değil. "
                "Kurulum: python -m pip install bleak"
            ) from error

        return BleakClient, BleakScanner

    async def discover(
        self,
        timeout: float,
    ) -> list[dict[str, Any]]:
        _, BleakScanner = self._bleak_modules()

        try:
            devices = await BleakScanner.discover(
                timeout=timeout,
                return_adv=True,
            )
        except Exception as error:
            raise ScientificTransportError(
                "BLE cihaz taraması başarısız."
            ) from error

        result = []

        for address, item in devices.items():
            device, advertisement = item

            result.append(
                {
                    "address": address,
                    "name": (
                        device.name
                        or advertisement.local_name
                        or "BLE Bilimsel Cihaz"
                    ),
                    "rssi": advertisement.rssi,
                    "service_uuids": list(
                        advertisement.service_uuids
                        or []
                    ),
                    "manufacturer_data": {
                        str(key): value.hex()
                        for key, value
                        in advertisement.manufacturer_data.items()
                    },
                }
            )

        return result

    async def read_characteristic(
        self,
        address: str,
        characteristic_uuid: str,
        timeout: float,
    ) -> bytes:
        BleakClient, _ = self._bleak_modules()

        try:
            async with BleakClient(
                address,
                timeout=timeout,
            ) as client:
                if not client.is_connected:
                    raise ScientificTransportError(
                        "BLE cihaz bağlantısı kurulamadı."
                    )

                return await client.read_gatt_char(
                    characteristic_uuid
                )

        except ScientificTransportError:
            raise

        except Exception as error:
            raise ScientificTransportError(
                f"BLE cihaz verisi okunamadı: {address}"
            ) from error


class BleScientificTransport:
    id = "ble"
    title = "Bluetooth Low Energy Bilimsel Taşıma"

    def __init__(
        self,
        backend: BleBackend | None = None,
    ) -> None:
        self._backend = backend or BleakBackend()

    async def discover(
        self,
        *,
        timeout: float = 5.0,
    ) -> list[ScientificDevice]:
        if timeout <= 0:
            raise ScientificTransportError(
                "BLE tarama süresi sıfırdan büyük olmalıdır."
            )

        items = await self._backend.discover(
            timeout=timeout
        )

        result = []

        for item in items:
            address = str(item["address"])

            metadata = {
                key: value
                for key, value in item.items()
                if key not in {
                    "address",
                    "name",
                }
                and value is not None
            }

            result.append(
                ScientificDevice(
                    id=f"ble:{address}",
                    title=str(
                        item.get("name")
                        or address
                    ),
                    transport=self.id,
                    address=address,
                    connected=False,
                    metadata=metadata,
                )
            )

        return result

    async def inventory(
        self,
        *,
        timeout: float = 5.0,
    ) -> list[dict[str, Any]]:
        return [
            asdict(device)
            for device in await self.discover(
                timeout=timeout
            )
        ]

    async def read_packet(
        self,
        *,
        address: str,
        characteristic_uuid: str,
        timeout: float = 5.0,
    ) -> ScientificTransportPacket:
        if not address.strip():
            raise ScientificTransportError(
                "BLE cihaz adresi boş olamaz."
            )

        if not characteristic_uuid.strip():
            raise ScientificTransportError(
                "BLE karakteristik UUID boş olamaz."
            )

        raw = await self._backend.read_characteristic(
            address=address,
            characteristic_uuid=characteristic_uuid,
            timeout=timeout,
        )

        if not raw:
            raise ScientificTransportError(
                "BLE cihazından boş veri geldi."
            )

        try:
            raw_text = raw.decode(
                "utf-8",
                errors="strict",
            ).strip()

        except UnicodeDecodeError as error:
            raise ScientificTransportError(
                "BLE cihaz verisi UTF-8 değil."
            ) from error

        try:
            payload = json.loads(raw_text)

        except json.JSONDecodeError as error:
            raise ScientificTransportError(
                "BLE cihaz verisi geçerli JSON değil."
            ) from error

        required = {
            "module_id",
            "live_value",
        }

        missing = required - payload.keys()

        if missing:
            names = ", ".join(sorted(missing))

            raise ScientificTransportError(
                f"Eksik BLE veri alanları: {names}"
            )

        metadata = dict(
            payload.get("metadata", {})
        )

        metadata.update(
            {
                "address": address,
                "characteristic_uuid": (
                    characteristic_uuid
                ),
                "transport": self.id,
            }
        )

        return ScientificTransportPacket(
            module_id=str(payload["module_id"]),
            live_value=payload["live_value"],
            confidence=float(
                payload.get("confidence", 50.0)
            ),
            status=str(
                payload.get("status", "preview")
            ),
            source=str(
                payload.get(
                    "source",
                    f"ble:{address}",
                )
            ),
            metadata=metadata,
        )