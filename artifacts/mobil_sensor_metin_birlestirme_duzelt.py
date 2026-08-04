from pathlib import Path
import re


path = Path(
    "src/syk_simulasyon/syk_ui_runtime/"
    "static/js/mobile_sensor_runtime.js"
)

text = path.read_text(
    encoding="utf-8",
)

pattern = re.compile(
    r'(?P<ilk>"(?:[^"\\]|\\.)*")'
    r'(?P<bosluk>\s*\n[ \t]*)'
    r'(?P<ikinci>"(?:[^"\\]|\\.)*")'
)

count = 0

while True:
    updated, replacements = pattern.subn(
        lambda match: (
            match.group("ilk")
            + " +"
            + match.group("bosluk")
            + match.group("ikinci")
        ),
        text,
    )

    count += replacements
    text = updated

    if replacements == 0:
        break

path.write_text(
    text,
    encoding="utf-8",
)

print(
    "MOBIL_SENSOR_METIN_BIRLESTIRME_DUZELTILDI"
)

print(
    "DUZELTILEN_NOKTA_SAYISI",
    count,
)
