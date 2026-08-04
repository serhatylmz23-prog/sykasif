from syk_jarmin.runtime.runtime import (
    JarminRuntime,
)
from syk_jarmin.runtime.integration_runtime import (
    JarminIntegrationRuntime,
)

runtime = JarminRuntime()

assert runtime.assistant is runtime
assert runtime.notifications is runtime.notification_router

integration = JarminIntegrationRuntime()

print("JARMIN_ASSISTANT_COMPATIBILITY_OK")
print("JARMIN_INTEGRATION_RUNTIME_OK")
