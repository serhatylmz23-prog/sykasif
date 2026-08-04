from syk_jarmin.runtime.runtime import (
    JarminRuntime,
)

runtime = JarminRuntime()

runtime.configure(
    assistant_name="Kaşif",
    language="tr-TR",
    wake_words=[
        "Kaşif",
        "Babuş",
    ],
)

assert runtime.assistant is runtime
assert runtime.assistant.core is runtime
assert runtime.assistant.core.commands is not None
assert callable(runtime.assistant.configure)
assert callable(runtime.voice.configure)

print("KASIF_RUNTIME_SOZLESMESI_OK")

from syk_jarmin.runtime.integration_runtime import (
    JarminIntegrationRuntime,
)

integration = JarminIntegrationRuntime()

snapshot = integration.runtime.snapshot()

assert (
    snapshot["assistant_name"]
    == "Kaşif"
)

print("KASIF_INTEGRATION_RUNTIME_OK")
print("RUNTIME", type(integration).__name__)
print("ASSISTANT_NAME", snapshot["assistant_name"])
