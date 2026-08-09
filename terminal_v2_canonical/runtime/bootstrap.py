from terminal_v2.runtime.kernel import RuntimeKernel
from terminal_v2.core.service_registry import ServiceRegistry

kernel=RuntimeKernel()

services=ServiceRegistry()

services.register(
    "kernel",
    kernel
)
