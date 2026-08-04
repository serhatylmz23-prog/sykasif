from syk_jarmin.runtime.runtime import JarminRuntime

runtime = JarminRuntime()

assert callable(runtime.configure)

result = runtime.configure(
    assistant_name="Kaşif",
    language="tr-TR",
    wake_words=[
        "Kaşif",
        "Babuş",
    ],
)

assert result["assistant_name"] == "Kaşif"
assert result["wake_words"] == [
    "Kaşif",
    "Babuş",
]

print("KASIF_CONFIGURE_OK")
print(
    "WAKE_WORDS",
    ",".join(result["wake_words"]),
)
