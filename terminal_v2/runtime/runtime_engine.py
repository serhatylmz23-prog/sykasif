from terminal_v2.core.service_registry import ServiceRegistry
from terminal_v2.core.module_registry import ModuleRegistry
from terminal_v2.runtime.monitor import RuntimeMonitor
from terminal_v2.runtime.health_engine import HealthEngine

class RuntimeEngine:

    def __init__(self):

        self.services=ServiceRegistry()

        self.modules=ModuleRegistry()

        self.monitor=RuntimeMonitor()

        self.health=HealthEngine()

        self.running=False

    def boot(self):

        self.running=True

        self.monitor.start()

        self.modules.discover()

        self.modules.load()

    def shutdown(self):

        self.running=False

        self.monitor.stop()

    def status(self):

        return{

            "running":self.running,

            "health":self.health.health(),

            "services":self.services.names()

        }
