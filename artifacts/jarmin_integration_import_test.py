from syk_jarmin.runtime.runtime import (
    JarminRuntime,
)
from syk_jarmin.runtime.notification_router import (
    NotificationRouter,
)
from syk_jarmin.runtime.integration_runtime import (
    JarminIntegrationRuntime,
)

runtime = JarminRuntime()

assert isinstance(
    runtime.notifications,
    NotificationRouter,
)

assert (
    runtime.notifications
    is runtime.notification_router
)

integration = JarminIntegrationRuntime()

print("JARMIN_RUNTIME_OK")
print("NOTIFICATIONS_COMPATIBILITY_OK")
print("INTEGRATION_RUNTIME_OK")
