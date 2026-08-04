from syk_jarmin.runtime.runtime import JarminRuntime
from syk_jarmin.runtime.integration_runtime import JarminIntegrationRuntime

runtime = JarminRuntime()

result = runtime.execute(
    "Sistem durumunu kontrol et."
)

print("JARMIN_RUNTIME_IMPORT_OK")
print(result.intent)
print(result.status)
print(result.result_sha256)
print("INTEGRATION_RUNTIME_IMPORT_OK")
