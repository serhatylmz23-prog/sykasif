from syk_jarmin.runtime.runtime import (
    JarminRuntime,
)

runtime = JarminRuntime()

result = runtime.configure(
    assistant_name="Kaşif",
    language="tr-TR",
    wake_words=[
        "Kaşif",
        "Babuş",
    ],
)

assert runtime.assistant is runtime
assert runtime.assistant.core is runtime
assert callable(
    runtime.assistant.configure
)
assert callable(
    runtime.voice.configure
)

assert result[
    "assistant_name"
] == "Kaşif"

print("KASIF_RUNTIME_CONFIGURE_OK")
print("KASIF_VOICE_CONFIGURE_OK")
print(
    "WAKE_WORDS",
    ",".join(
        result["wake_words"]
    ),
)

from syk_jarmin.runtime.integration_runtime import (
    JarminIntegrationRuntime,
)

integration = JarminIntegrationRuntime()

print("KASIF_INTEGRATION_RUNTIME_OK")
print(type(integration).__name__)
