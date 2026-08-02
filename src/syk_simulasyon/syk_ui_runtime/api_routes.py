from fastapi import APIRouter

from .ui_runtime_state import UIRuntimeState


router = APIRouter(
    prefix="/api/syk-ui",
    tags=["syk-ui"],
)

runtime_state = UIRuntimeState()


@router.get("/runtime-state")
def get_runtime_state() -> dict:
    return runtime_state.snapshot()