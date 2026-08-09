from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

# ---------- STATE ----------

@dataclass(slots=True)
class RuntimeState:
    runtime: str = "BOOT"
    tablet: bool = False
    connected: bool = False
    last_update: datetime = field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = field(default_factory=dict)

class StateManager:

    def __init__(self):
        self._state = RuntimeState()

    def get(self):
        return self._state

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self._state, k):
                setattr(self._state, k, v)
        self._state.last_update = datetime.utcnow()

# ---------- EVENT BUS ----------

class EventBus:

    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(self, event, callback):
        self._listeners[event].append(callback)

    def unsubscribe(self, event, callback):
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def emit(self, event, *args, **kwargs):
        for callback in list(self._listeners[event]):
            callback(*args, **kwargs)

# ---------- CONNECTION ----------

class ConnectionManager:

    def __init__(self):
        self.state = StateManager()
        self.bus = EventBus()

    def connect(self):
        self.state.update(runtime="ONLINE", connected=True)
        self.bus.emit("runtime.connected", self.state.get())

    def disconnect(self):
        self.state.update(runtime="OFFLINE", connected=False)
        self.bus.emit("runtime.disconnected", self.state.get())

    def heartbeat(self):
        self.bus.emit("runtime.heartbeat", self.state.get())
