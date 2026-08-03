from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .module_registry import enabled_modules
from .scientific_adapter import (
    ScientificAdapterRegistry,
    ingest_transport_packet,
)
from .scientific_transport import (
    ScientificTransportError,
    BleScientificTransport,
    SerialScientificTransport,
    TcpScientificTransport,
)
from .scientific_analysis_syframe import (
    ScientificAnalysisSyFrameBridge,
)
from .syframe_manager import SyFrameManager
from .scientific_device_analysis import (
    ScientificDeviceAnalysisEngine,
)
from .scientific_device_evidence import DeviceEvidenceStore
from .scientific_device_package_seal import (
    DeviceEvidencePackageSeal,
)
from .scientific_device_evidence_package import (
    DeviceEvidencePackageBuilder,
)
from .scientific_device_hub import ScientificDeviceHub
from .scientific_device_manager import ScientificDeviceManager
from .scientific_device_recording_pipeline import (
    ScientificDeviceRecordingPipeline,
)
from .scientific_device_session import (
    ScientificDeviceSessionManager,
)
from .scientific_runtime import ScientificRuntime
from .ui_runtime_state import UIRuntimeState


router = APIRouter(
    prefix="/api/syk-ui",
    tags=["syk-ui"],
)

runtime_state = UIRuntimeState()
scientific_runtime = ScientificRuntime()
ble_transport = BleScientificTransport()
serial_transport = SerialScientificTransport()
tcp_transport = TcpScientificTransport()

scientific_adapters = ScientificAdapterRegistry(
    scientific_runtime
)

scientific_device_manager = ScientificDeviceManager(
    adapters=scientific_adapters,
    serial_transport=serial_transport,
    tcp_transport=tcp_transport,
    ble_transport=ble_transport,
)

scientific_device_hub = ScientificDeviceHub(
    scientific_device_manager
)

scientific_device_evidence = DeviceEvidenceStore()

scientific_device_package_builder = (
    DeviceEvidencePackageBuilder(
        evidence=scientific_device_evidence
    )
)

scientific_device_package_seal = (
    DeviceEvidencePackageSeal(
        packages=scientific_device_package_builder
    )
)

scientific_device_sessions = (
    ScientificDeviceSessionManager(
        scientific_device_hub
    )
)

scientific_device_recording_pipeline = (
    ScientificDeviceRecordingPipeline(
        sessions=scientific_device_sessions,
        evidence=scientific_device_evidence,
    )
)

scientific_device_analysis = (
    ScientificDeviceAnalysisEngine(
        sessions=scientific_device_sessions,
        evidence=scientific_device_evidence,
    )
)

scientific_analysis_syframe_manager = SyFrameManager()

scientific_analysis_syframe = (
    ScientificAnalysisSyFrameBridge(
        analysis=scientific_device_analysis,
        syframe=scientific_analysis_syframe_manager,
    )
)


@router.get("/runtime-state")
def get_runtime_state() -> dict:
    snapshot = runtime_state.snapshot()
    snapshot["modules"] = [
        {
            "id": module.id,
            "title": module.title,
            "enabled": module.enabled,
        }
        for module in enabled_modules()
    ]
    snapshot["syframe"] = (
        scientific_analysis_syframe.snapshot()
    )
    return snapshot


@router.websocket("/live")
async def live_runtime(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while True:
            snapshot = get_runtime_state()
            snapshot["connection"] = "live"

            await websocket.send_json(snapshot)
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        return

@router.get("/scientific-modules")
def get_scientific_modules() -> list[dict]:
    return scientific_runtime.inventory()


@router.get("/scientific-modules/{module_id}")
def get_scientific_module(module_id: str) -> dict:
    try:
        return scientific_runtime.get(module_id)
    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Unknown scientific module: {module_id}",
        ) from error

class ScientificUpdateRequest(BaseModel):
    live_value: float | int | str | None = None
    confidence: float | None = None
    status: str | None = None
    source: str | None = None


@router.patch("/scientific-modules/{module_id}")
def update_scientific_module(
    module_id: str,
    request: ScientificUpdateRequest,
) -> dict:
    try:
        return scientific_runtime.update(
            module_id,
            live_value=request.live_value,
            confidence=request.confidence,
            status=request.status,
            source=request.source,
        )
    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Unknown scientific module: {module_id}",
        ) from error


@router.websocket(
    "/scientific-modules/{module_id}/live"
)
async def scientific_module_live(
    websocket: WebSocket,
    module_id: str,
) -> None:
    if not scientific_runtime.exists(module_id):
        await websocket.close(
            code=4404,
            reason="Unknown scientific module",
        )
        return

    await websocket.accept()

    try:
        last_sequence = -1

        while True:
            payload = scientific_runtime.get(module_id)
            sequence = payload["state"]["sequence"]

            if sequence != last_sequence:
                await websocket.send_json(payload)
                last_sequence = sequence

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        return

class ScientificAdapterIngestRequest(BaseModel):
    live_value: float | int | str
    confidence: float = 50.0
    status: str = "preview"
    source: str | None = None
    metadata: dict = {}


@router.get("/scientific-adapters")
def get_scientific_adapters() -> list[dict]:
    return scientific_adapters.inventory()


@router.post(
    "/scientific-adapters/"
    "{adapter_id}/modules/{module_id}/ingest"
)
def ingest_scientific_adapter_data(
    adapter_id: str,
    module_id: str,
    request: ScientificAdapterIngestRequest,
) -> dict:
    try:
        payload = request.model_dump()

        if payload["source"] is None:
            payload["source"] = (
                f"{adapter_id}_adapter"
            )

        return scientific_adapters.ingest(
            adapter_id,
            module_id,
            payload,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Adapter veya modül bulunamadı: "
            f"{error.args[0]}",
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

class SerialReadRequest(BaseModel):
    port: str
    baud_rate: int = 115200
    timeout: float = 2.0


@router.get("/scientific-devices/serial")
def discover_serial_devices() -> list[dict]:
    try:
        return serial_transport.inventory()

    except ScientificTransportError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.post("/scientific-devices/serial/read")
def read_serial_device(
    request: SerialReadRequest,
) -> dict:
    try:
        packet = serial_transport.read_packet(
            port=request.port,
            baud_rate=request.baud_rate,
            timeout=request.timeout,
        )

        return ingest_transport_packet(
            scientific_adapters,
            packet,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                "Seri cihaz bilinmeyen bilimsel "
                f"modül gönderdi: {error.args[0]}"
            ),
        ) from error

    except ScientificTransportError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

class TcpReadRequest(BaseModel):
    host: str
    port: int
    timeout: float = 3.0


@router.post("/scientific-devices/tcp/read")
def read_tcp_device(
    request: TcpReadRequest,
) -> dict:
    try:
        packet = tcp_transport.read_packet(
            host=request.host,
            port=request.port,
            timeout=request.timeout,
        )

        return ingest_transport_packet(
            scientific_adapters,
            packet,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                "TCP cihazı bilinmeyen bilimsel "
                f"modül gönderdi: {error.args[0]}"
            ),
        ) from error

    except ScientificTransportError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

class BleDiscoveryRequest(BaseModel):
    timeout: float = 5.0


class BleReadRequest(BaseModel):
    address: str
    characteristic_uuid: str
    timeout: float = 5.0


@router.post("/scientific-devices/ble/discover")
async def discover_ble_devices(
    request: BleDiscoveryRequest,
) -> list[dict]:
    try:
        return await ble_transport.inventory(
            timeout=request.timeout
        )

    except ScientificTransportError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.post("/scientific-devices/ble/read")
async def read_ble_device(
    request: BleReadRequest,
) -> dict:
    try:
        packet = await ble_transport.read_packet(
            address=request.address,
            characteristic_uuid=(
                request.characteristic_uuid
            ),
            timeout=request.timeout,
        )

        return ingest_transport_packet(
            scientific_adapters,
            packet,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                "BLE cihazı bilinmeyen bilimsel "
                f"modül gönderdi: {error.args[0]}"
            ),
        ) from error

    except ScientificTransportError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

@router.get("/scientific-devices/transports")
def get_scientific_device_transports() -> list[dict]:
    return scientific_device_manager.transports()


@router.post("/scientific-devices/discover")
async def discover_all_scientific_devices(
    request: BleDiscoveryRequest,
) -> dict:
    return await scientific_device_manager.discover_all(
        ble_timeout=request.timeout
    )

class DeviceHubRegisterRequest(BaseModel):
    device_id: str
    title: str
    transport: str
    address: str
    module_id: str | None = None
    metadata: dict = {}


class DeviceHubConnectionRequest(BaseModel):
    connected: bool


class DeviceHubTelemetryRequest(BaseModel):
    battery: float | None = None
    signal_quality: float | None = None
    firmware: str | None = None
    module_id: str | None = None


@router.get("/device-hub")
def get_device_hub() -> dict:
    return {
        "devices": scientific_device_hub.inventory(),
        "transports": (
            scientific_device_hub.transports()
        ),
    }


@router.post("/device-hub/refresh")
async def refresh_device_hub(
    request: BleDiscoveryRequest,
) -> dict:
    return await scientific_device_hub.refresh(
        ble_timeout=request.timeout
    )


@router.post("/device-hub/register")
def register_device_hub_device(
    request: DeviceHubRegisterRequest,
) -> dict:
    try:
        return scientific_device_hub.register_manual(
            device_id=request.device_id,
            title=request.title,
            transport=request.transport,
            address=request.address,
            module_id=request.module_id,
            metadata=request.metadata,
        )

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/device-hub/{device_id}")
def get_device_hub_device(
    device_id: str,
) -> dict:
    try:
        return scientific_device_hub.get(
            device_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Cihaz bulunamadı: {device_id}",
        ) from error


@router.patch(
    "/device-hub/{device_id}/connection"
)
def update_device_hub_connection(
    device_id: str,
    request: DeviceHubConnectionRequest,
) -> dict:
    try:
        return scientific_device_hub.set_connection(
            device_id,
            connected=request.connected,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Cihaz bulunamadı: {device_id}",
        ) from error


@router.patch(
    "/device-hub/{device_id}/telemetry"
)
def update_device_hub_telemetry(
    device_id: str,
    request: DeviceHubTelemetryRequest,
) -> dict:
    try:
        return scientific_device_hub.update_telemetry(
            device_id,
            battery=request.battery,
            signal_quality=(
                request.signal_quality
            ),
            firmware=request.firmware,
            module_id=request.module_id,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Cihaz bulunamadı: {device_id}",
        ) from error

class DeviceSessionStartRequest(BaseModel):
    device_id: str
    module_id: str | None = None
    metadata: dict = {}


class DeviceSessionSampleRequest(BaseModel):
    count: int = 1


@router.get("/device-sessions")
def get_device_sessions() -> list[dict]:
    return scientific_device_sessions.inventory()


@router.post("/device-sessions/start")
def start_device_session(
    request: DeviceSessionStartRequest,
) -> dict:
    try:
        return scientific_device_sessions.start(
            device_id=request.device_id,
            module_id=request.module_id,
            metadata=request.metadata,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Cihaz bulunamadı: {error.args[0]}",
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@router.get("/device-sessions/{session_id}")
def get_device_session(
    session_id: str,
) -> dict:
    try:
        return scientific_device_sessions.get(
            session_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: {session_id}",
        ) from error


@router.post(
    "/device-sessions/{session_id}/samples"
)
def append_device_session_samples(
    session_id: str,
    request: DeviceSessionSampleRequest,
) -> dict:
    try:
        return scientific_device_sessions.append_sample(
            session_id,
            count=request.count,
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: {session_id}",
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


@router.post(
    "/device-sessions/{session_id}/stop"
)
def stop_device_session(
    session_id: str,
) -> dict:
    try:
        return scientific_device_sessions.stop(
            session_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: {session_id}",
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

class DeviceEvidenceAppendRequest(BaseModel):
    payload: dict


@router.post(
    "/device-sessions/{session_id}/evidence"
)
def append_device_session_evidence(
    session_id: str,
    request: DeviceEvidenceAppendRequest,
) -> dict:
    try:
        session = scientific_device_sessions.get(
            session_id
        )

        if session["state"] != "recording":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail=(
                    "Durdurulmuş oturuma "
                    "kanıt paketi eklenemez."
                ),
            )

        record = scientific_device_evidence.append(
            session_id=session_id,
            device_id=session["device_id"],
            module_id=session["module_id"],
            payload=request.payload,
        )

        scientific_device_sessions.append_sample(
            session_id,
            count=1,
        )

        return record

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: {session_id}",
        ) from error


@router.get(
    "/device-sessions/{session_id}/evidence"
)
def get_device_session_evidence(
    session_id: str,
) -> list[dict]:
    try:
        scientific_device_sessions.get(
            session_id
        )

        return scientific_device_evidence.records(
            session_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: {session_id}",
        ) from error


@router.get(
    "/device-sessions/{session_id}/evidence/verify"
)
def verify_device_session_evidence(
    session_id: str,
) -> dict:
    try:
        scientific_device_sessions.get(
            session_id
        )

        return scientific_device_evidence.verify(
            session_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: {session_id}",
        ) from error

class DevicePipelineIngestRequest(BaseModel):
    payload: dict


@router.post(
    "/device-hub/{device_id}/recording-ingest"
)
def ingest_device_recording_packet(
    device_id: str,
    request: DevicePipelineIngestRequest,
) -> dict:
    return scientific_device_recording_pipeline.ingest(
        device_id=device_id,
        payload=request.payload,
    )

@router.post(
    "/device-sessions/{session_id}/package"
)
def build_device_session_package(
    session_id: str,
) -> dict:
    try:
        session = scientific_device_sessions.get(
            session_id
        )

        if session["state"] == "recording":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail=(
                    "Paket üretmeden önce kayıt "
                    "oturumu durdurulmalıdır."
                ),
            )

        return (
            scientific_device_package_builder.build(
                session=session
            )
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                f"Oturum bulunamadı: "
                f"{session_id}"
            ),
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get(
    "/device-sessions/{session_id}/package/verify"
)
def verify_device_session_package(
    session_id: str,
) -> dict:
    try:
        scientific_device_sessions.get(
            session_id
        )

        return (
            scientific_device_package_builder.verify(
                session_id
            )
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                f"Oturum bulunamadı: "
                f"{session_id}"
            ),
        ) from error

@router.post(
    "/device-sessions/{session_id}/seal"
)
def seal_device_session_package(
    session_id: str,
) -> dict:
    try:
        session = scientific_device_sessions.get(
            session_id
        )

        if session["state"] == "recording":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail=(
                    "Mühürleme öncesinde kayıt "
                    "oturumu durdurulmalıdır."
                ),
            )

        package_verification = (
            scientific_device_package_builder.verify(
                session_id
            )
        )

        if not package_verification["valid"]:
            scientific_device_package_builder.build(
                session=session
            )

        return (
            scientific_device_package_seal.create(
                session=session
            )
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                f"Oturum bulunamadı: "
                f"{session_id}"
            ),
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get(
    "/device-sessions/{session_id}/seal/verify"
)
def verify_device_session_seal(
    session_id: str,
) -> dict:
    try:
        scientific_device_sessions.get(
            session_id
        )

        return (
            scientific_device_package_seal.verify(
                session_id
            )
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                f"Oturum bulunamadı: "
                f"{session_id}"
            ),
        ) from error

@router.post(
    "/device-sessions/{session_id}/analysis"
)
def analyze_device_session(
    session_id: str,
) -> dict:
    try:
        return scientific_device_analysis.analyze(
            session_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: {session_id}",
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get(
    "/device-sessions/{session_id}/analysis"
)
def get_device_session_analysis(
    session_id: str,
) -> dict:
    try:
        return scientific_device_analysis.get(
            session_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Analiz bulunamadı: {session_id}",
        ) from error


@router.get(
    "/device-sessions/{session_id}/analysis/verify"
)
def verify_device_session_analysis(
    session_id: str,
) -> dict:
    return scientific_device_analysis.verify(
        session_id
    )

@router.post(
    "/device-sessions/{session_id}/syframe"
)
def apply_device_analysis_to_syframe(
    session_id: str,
) -> dict:
    try:
        return scientific_analysis_syframe.apply(
            session_id
        )

    except KeyError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=(
                f"Analiz bulunamadı: "
                f"{session_id}"
            ),
        ) from error

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/syframe/analysis-state")
def get_analysis_syframe_state() -> dict:
    return scientific_analysis_syframe.snapshot()

from .dtse_attention_routes import (
    router as dtse_attention_router,
)

router.include_router(
    dtse_attention_router
)

from .goruntu_dtse_routes import (
    router as goruntu_dtse_router,
)

router.include_router(
    goruntu_dtse_router
)
from .media_upload_routes import (
    router as media_upload_router,
)

router.include_router(
    media_upload_router,
)