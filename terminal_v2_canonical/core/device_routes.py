from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from terminal_v2.core.trusted_devices import (
    trusted_device_registry,
)


router = APIRouter(
    prefix="/api/v2/devices",
    tags=["Terminal V2 Trusted Devices"],
)


class RegisterDeviceRequest(BaseModel):
    device_id: str | None = Field(
        default=None,
        max_length=128,
    )
    device_type: str = Field(
        min_length=2,
        max_length=32,
    )
    device_name: str = Field(
        min_length=1,
        max_length=120,
    )


class ReconnectDeviceRequest(BaseModel):
    device_id: str = Field(
        min_length=8,
        max_length=128,
    )
    trust_token: str = Field(
        min_length=24,
        max_length=256,
    )


def client_host(request: Request) -> str:
    return (
        request.client.host
        if request.client is not None
        else "unknown"
    )


@router.post("/register")
async def register_device(
    payload: RegisterDeviceRequest,
    request: Request,
) -> dict[str, object]:
    device, trust_token, created = (
        await trusted_device_registry.register(
            device_id=payload.device_id,
            device_type=payload.device_type,
            device_name=payload.device_name,
            client_host=client_host(request),
            user_agent=request.headers.get(
                "user-agent",
                "unknown",
            ),
        )
    )

    return {
        "status": (
            "DEVICE_REGISTERED"
            if created
            else "DEVICE_REFRESHED"
        ),
        "created": created,
        "device": device.public_export(),
        "trust_token": (
            trust_token
            if created
            else None
        ),
    }


@router.post("/reconnect")
async def reconnect_device(
    payload: ReconnectDeviceRequest,
    request: Request,
) -> dict[str, object]:
    device = await trusted_device_registry.authenticate(
        device_id=payload.device_id,
        trust_token=payload.trust_token,
        client_host=client_host(request),
        user_agent=request.headers.get(
            "user-agent",
            "unknown",
        ),
    )

    if device is None:
        raise HTTPException(
            status_code=401,
            detail="Güvenilir cihaz doğrulanamadı.",
        )

    return {
        "status": "DEVICE_RECONNECTED",
        "device": device.public_export(),
    }


@router.get("")
async def device_snapshot() -> dict[str, object]:
    return await trusted_device_registry.snapshot()


@router.get("/{device_id}")
async def get_device(
    device_id: str,
) -> dict[str, object]:
    device = await trusted_device_registry.get(
        device_id
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Cihaz bulunamadı.",
        )

    return device.public_export()


@router.delete("/{device_id}")
async def revoke_device(
    device_id: str,
) -> dict[str, object]:
    revoked = await trusted_device_registry.revoke(
        device_id
    )

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail="Cihaz bulunamadı.",
        )

    return {
        "status": "DEVICE_REVOKED",
        "device_id": device_id,
    }
