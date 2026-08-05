from __future__ import annotations

from fastapi import APIRouter

from .terminal_state import default_terminal_state


terminal_router = APIRouter(
    prefix="/api/syk-ui/terminal",
    tags=["syk-ui-terminal"],
)


@terminal_router.get("/state")
def terminal_state() -> dict[str, object]:
    return default_terminal_state().to_dict()