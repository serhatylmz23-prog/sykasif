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