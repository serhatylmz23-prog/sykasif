from fastapi import APIRouter
from terminal_v2.core.connection_manager import ConnectionManager

router=APIRouter(prefix="/api")

cm=ConnectionManager()

@router.get("/health")
def health():
    return{
        "runtime":cm.state.get().runtime,
        "connected":cm.state.get().connected
    }

@router.post("/online")
def online():
    cm.online()
    return{"ok":True}

@router.post("/offline")
def offline():
    cm.offline()
    return{"ok":True}
