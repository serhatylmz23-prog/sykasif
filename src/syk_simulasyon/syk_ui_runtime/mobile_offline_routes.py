from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from .mobile_offline_runtime import (
    mobile_offline_runtime,
)


router = APIRouter(
    prefix="/mobile-offline",
    tags=["telefon-tablet-cevrimdisi"],
)


class OnlineStateRequest(BaseModel):
    online: bool


class QueueRequest(BaseModel):
    item_id: str | None = None
    item_type: str
    device_id: str
    endpoint: str
    method: str
    payload: dict[str, Any]
    maximum_attempts: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class QueueFailureRequest(BaseModel):
    error_message: str = Field(
        min_length=1,
        max_length=2000,
    )


class PairingCreateRequest(BaseModel):
    requesting_device_id: str
    requesting_device_title: str
    target_role: str = (
        "trusted_terminal"
    )


class PairingConfirmRequest(BaseModel):
    pairing_code: str
    paired_device_id: str


class PairingVerifyRequest(BaseModel):
    pairing_id: str
    pairing_token: str


class CachePutRequest(BaseModel):
    cache_key: str
    category: str
    value: dict[str, Any]
    lifetime_seconds: int | None = Field(
        default=None,
        ge=1,
    )


@router.get("")
def get_offline_runtime() -> dict:
    return mobile_offline_runtime \
        .snapshot()


@router.patch("/online")
def set_online_state(
    request: OnlineStateRequest,
) -> dict:
    return mobile_offline_runtime \
        .set_online(
            request.online
        )


@router.post("/queue")
def enqueue_offline_item(
    request: QueueRequest,
) -> dict:
    try:
        return mobile_offline_runtime \
            .enqueue(
                item_id=request.item_id,
                item_type=(
                    request.item_type
                ),
                device_id=(
                    request.device_id
                ),
                endpoint=(
                    request.endpoint
                ),
                method=request.method,
                payload=request.payload,
                maximum_attempts=(
                    request
                    .maximum_attempts
                ),
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/queue")
def list_offline_queue(
    device_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    try:
        return mobile_offline_runtime \
            .pending(
                device_id=device_id,
                limit=limit,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.post(
    "/queue/{item_id}/begin"
)
def begin_offline_item(
    item_id: str,
) -> dict:
    try:
        return mobile_offline_runtime \
            .begin_processing(
                item_id
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


@router.post(
    "/queue/{item_id}/complete"
)
def complete_offline_item(
    item_id: str,
) -> dict:
    try:
        return mobile_offline_runtime \
            .complete(
                item_id
            )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.post(
    "/queue/{item_id}/fail"
)
def fail_offline_item(
    item_id: str,
    request: QueueFailureRequest,
) -> dict:
    try:
        return mobile_offline_runtime \
            .fail(
                item_id,
                error_message=(
                    request.error_message
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


@router.delete(
    "/queue/{item_id}"
)
def cancel_offline_item(
    item_id: str,
) -> dict:
    try:
        return mobile_offline_runtime \
            .cancel(
                item_id
            )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.delete("/queue")
def remove_completed_items() -> dict:
    removed = mobile_offline_runtime \
        .remove_completed()

    return {
        "removed_count": removed,
    }


@router.post("/pairings")
def create_pairing(
    request: PairingCreateRequest,
) -> dict:
    try:
        return mobile_offline_runtime \
            .create_pairing(
                requesting_device_id=(
                    request
                    .requesting_device_id
                ),
                requesting_device_title=(
                    request
                    .requesting_device_title
                ),
                target_role=(
                    request.target_role
                ),
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.post("/pairings/confirm")
def confirm_pairing(
    request: PairingConfirmRequest,
) -> dict:
    try:
        return mobile_offline_runtime \
            .confirm_pairing(
                pairing_code=(
                    request.pairing_code
                ),
                paired_device_id=(
                    request
                    .paired_device_id
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


@router.post("/pairings/verify")
def verify_pairing(
    request: PairingVerifyRequest,
) -> dict:
    valid = mobile_offline_runtime \
        .verify_pairing_token(
            pairing_id=(
                request.pairing_id
            ),
            pairing_token=(
                request.pairing_token
            ),
        )

    return {
        "valid": valid,
        "pairing_id": (
            request.pairing_id
        ),
    }


@router.get("/pairings")
def list_pairings(
    status: str | None = None,
) -> list[dict]:
    try:
        return mobile_offline_runtime \
            .list_pairings(
                status=status
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.delete(
    "/pairings/{pairing_id}"
)
def revoke_pairing(
    pairing_id: str,
) -> dict:
    try:
        return mobile_offline_runtime \
            .revoke_pairing(
                pairing_id
            )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.put("/cache")
def put_cache(
    request: CachePutRequest,
) -> dict:
    try:
        return mobile_offline_runtime \
            .cache_put(
                cache_key=(
                    request.cache_key
                ),
                category=(
                    request.category
                ),
                value=request.value,
                lifetime_seconds=(
                    request
                    .lifetime_seconds
                ),
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/cache/{cache_key}")
def get_cache(
    cache_key: str,
) -> dict:
    result = mobile_offline_runtime \
        .cache_get(
            cache_key
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Önbellek kaydı bulunamadı."
            ),
        )

    return result


@router.get("/cache")
def list_cache(
    category: str | None = None,
) -> list[dict]:
    return mobile_offline_runtime \
        .cache_list(
            category=category
        )


@router.delete("/cache/{cache_key}")
def delete_cache(
    cache_key: str,
) -> dict:
    return {
        "deleted": (
            mobile_offline_runtime
            .cache_delete(
                cache_key
            )
        )
    }