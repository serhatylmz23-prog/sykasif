from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from .mobile_device_runtime import (
    DeviceCapabilities,
    DeviceViewport,
    MobileDeviceRuntime,
    mobile_device_runtime,
)


router = APIRouter(
    prefix="/mobile-runtime",
    tags=["telefon-tablet-runtime"],
)


class ViewportRequest(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    pixel_ratio: float = Field(
        default=1.0,
        gt=0.0,
    )
    orientation: str = "unknown"


class CapabilitiesRequest(BaseModel):
    touch: bool = False
    camera: bool = False
    microphone: bool = False
    location: bool = False
    notification: bool = False
    vibration: bool = False
    fullscreen: bool = False
    wake_lock: bool = False
    online: bool = True
    input_mode: str = "unknown"


class DeviceRegistrationRequest(BaseModel):
    device_id: str | None = None
    device_type: str
    title: str
    platform: str
    user_agent: str = ""
    language: str = "tr-TR"
    timezone: str = "Europe/Istanbul"
    viewport: ViewportRequest
    capabilities: CapabilitiesRequest
    trusted: bool = False


class DeviceUpdateRequest(BaseModel):
    viewport: ViewportRequest
    capabilities: CapabilitiesRequest


class DeviceTrustRequest(BaseModel):
    trusted: bool


class LayoutResolveRequest(BaseModel):
    device_type: str
    viewport: ViewportRequest
    capabilities: CapabilitiesRequest


def _viewport(
    request: ViewportRequest,
) -> DeviceViewport:
    return DeviceViewport(
        width=request.width,
        height=request.height,
        pixel_ratio=request.pixel_ratio,
        orientation=request.orientation,
    )


def _capabilities(
    request: CapabilitiesRequest,
) -> DeviceCapabilities:
    return DeviceCapabilities(
        touch=request.touch,
        camera=request.camera,
        microphone=request.microphone,
        location=request.location,
        notification=request.notification,
        vibration=request.vibration,
        fullscreen=request.fullscreen,
        wake_lock=request.wake_lock,
        online=request.online,
        input_mode=request.input_mode,
    )


@router.get("")
def get_mobile_runtime() -> dict:
    return mobile_device_runtime.snapshot()


@router.post("/devices")
def register_mobile_device(
    request: DeviceRegistrationRequest,
) -> dict:
    try:
        return mobile_device_runtime.register(
            device_id=request.device_id,
            device_type=(
                request.device_type
            ),
            title=request.title,
            platform=request.platform,
            user_agent=request.user_agent,
            language=request.language,
            timezone=request.timezone,
            viewport=_viewport(
                request.viewport
            ),
            capabilities=_capabilities(
                request.capabilities
            ),
            trusted=request.trusted,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/devices")
def list_mobile_devices(
    active_only: bool = False,
) -> list[dict]:
    return mobile_device_runtime.list(
        active_only=active_only
    )


@router.get("/devices/{device_id}")
def get_mobile_device(
    device_id: str,
) -> dict:
    try:
        return mobile_device_runtime.get(
            device_id
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.patch("/devices/{device_id}")
def update_mobile_device(
    device_id: str,
    request: DeviceUpdateRequest,
) -> dict:
    try:
        mobile_device_runtime \
            .update_capabilities(
                device_id,
                capabilities=_capabilities(
                    request.capabilities
                ),
            )

        return mobile_device_runtime \
            .update_viewport(
                device_id,
                viewport=_viewport(
                    request.viewport
                ),
            )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.patch(
    "/devices/{device_id}/trust"
)
def trust_mobile_device(
    device_id: str,
    request: DeviceTrustRequest,
) -> dict:
    try:
        return mobile_device_runtime.trust(
            device_id,
            trusted=request.trusted,
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.delete("/devices/{device_id}")
def deactivate_mobile_device(
    device_id: str,
) -> dict:
    try:
        return mobile_device_runtime \
            .deactivate(
                device_id
            )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.post("/layout")
def resolve_mobile_layout(
    request: LayoutResolveRequest,
) -> dict:
    try:
        return mobile_device_runtime \
            .layout_for(
                device_type=(
                    request.device_type
                ),
                viewport=_viewport(
                    request.viewport
                ),
                capabilities=_capabilities(
                    request.capabilities
                ),
            ) \
            .as_dict()

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error