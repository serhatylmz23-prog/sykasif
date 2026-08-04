from syk_jarmin.runtime.integration_runtime import (
    JarminIntegrationRuntime,
)

integration = JarminIntegrationRuntime()

print("JARMIN_INTEGRATION_RUNTIME_OK")
print(type(integration).__name__)
