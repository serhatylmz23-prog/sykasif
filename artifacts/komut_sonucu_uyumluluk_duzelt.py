from pathlib import Path
import ast


path = Path(
    "src/syk_jarmin/runtime/command_router.py"
)

text = path.read_text(
    encoding="utf-8"
)

uyumluluk = '''

# Eski çekirdek katmanının kullandığı ad.
# Yeni gerçek sınıf CommandRouteResult'tır.
CommandResult = CommandRouteResult
'''

if (
    "CommandResult = CommandRouteResult"
    not in text
):
    anchor = (
        "\n\nclass CommandRouter:"
    )

    if anchor not in text:
        raise RuntimeError(
            "CommandRouter sınıfı bulunamadı."
        )

    text = text.replace(
        anchor,
        uyumluluk + anchor,
        1,
    )

path.write_text(
    text,
    encoding="utf-8",
)

ast.parse(
    path.read_text(
        encoding="utf-8"
    )
)

print(
    "KOMUT_SONUCU_UYUMLULUGU_EKLENDI"
)
