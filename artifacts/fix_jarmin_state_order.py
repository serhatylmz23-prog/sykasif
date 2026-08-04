from pathlib import Path


path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

# Sözleşme içindeki erken status atamasını kaldır.
text = text.replace(
    "        self.status = self._state\n",
    "",
)

# _state oluşturulduktan hemen sonra status ekle.
anchor = """        self._state = "ready"
        self._history: list[JarminRuntimeResult] = []
"""

replacement = """        self._state = "ready"
        self.status = self._state
        self._history: list[JarminRuntimeResult] = []
"""

if anchor not in text:
    raise RuntimeError(
        "_state başlangıç bölümü bulunamadı."
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

print("JARMIN_STATE_ORDER_FIXED")
