from pathlib import Path

path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

anchor = """        self.assistant_name = normalized_name
        self.maximum_history = maximum_history
"""

replacement = """        self.assistant_name = normalized_name

        # Eski entegrasyon katmanının
        # beklediği geriye dönük uyumluluk alanı.
        self.assistant = self

        self.maximum_history = maximum_history
"""

if "self.assistant = self" not in text:
    if anchor not in text:
        raise RuntimeError(
            "JarminRuntime assistant alanı "
            "eklenecek konum bulunamadı."
        )

    text = text.replace(
        anchor,
        replacement,
        1,
    )

path.write_text(
    text,
    encoding="utf-8",
)

print("JARMIN_ASSISTANT_PATCH_OK")
