from syk_jarmin.runtime.runtime import (
    JarminRuntime,
)

runtime = JarminRuntime()

assert runtime.assistant is runtime
assert runtime.assistant.core is runtime
assert runtime.core is runtime
assert runtime.runtime is runtime
assert runtime.kasif is runtime
assert runtime.jarmin is runtime

assert (
    runtime.notifications
    is runtime.notification_router
)

assert (
    runtime.voice
    is runtime.voice_runtime
)

assert callable(runtime.snapshot)

print("JARMIN_RUNTIME_FULL_CONTRACT_OK")

from syk_jarmin.runtime.integration_runtime import (
    JarminIntegrationRuntime,
)

integration = JarminIntegrationRuntime()

print("JARMIN_INTEGRATION_RUNTIME_OK")
print("ASSISTANT_NAME", runtime.assistant_name)
