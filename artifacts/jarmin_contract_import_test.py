from syk_jarmin.runtime.runtime import JarminRuntime
from syk_jarmin.runtime.integration_runtime import JarminIntegrationRuntime

runtime = JarminRuntime()

assert runtime.assistant is runtime
assert callable(runtime.snapshot)

integration = JarminIntegrationRuntime()

print("JARMIN_RUNTIME_CONTRACT_OK")
print("JARMIN_INTEGRATION_RUNTIME_OK")
print("ASSISTANT_NAME", runtime.assistant_name)
