from .state_manager import StateManager
from .event_bus import EventBus

class ConnectionManager:

    def __init__(self):
        self.state=StateManager()
        self.bus=EventBus()

    def online(self):
        self.state.update(runtime="ONLINE",connected=True)
        self.bus.emit("runtime.online",self.state.get())

    def offline(self):
        self.state.update(runtime="OFFLINE",connected=False)
        self.bus.emit("runtime.offline",self.state.get())
