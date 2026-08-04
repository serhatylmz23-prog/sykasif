from pathlib import Path
import ast


path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

old = '''    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-kasif-voice-compatibility/v1"
            ),
            "assistant_name": "Kaşif",
            "settings": dict(
                self.settings
            ),
            "status": "ready",
        }
'''

new = '''    def snapshot(self) -> dict[str, Any]:
        settings = dict(
            self.settings
        )

        return {
            "schema": (
                "sykasif-kasif-voice-compatibility/v1"
            ),
            "assistant_name": "Kaşif",
            **settings,
            "settings": settings,
            "status": "ready",
        }
'''

if old not in text:
    if (
        '"sykasif-kasif-voice-compatibility/v1"'
        not in text
    ):
        raise RuntimeError(
            "Kaşif ses çalışma bölümü bulunamadı."
        )

    if "**settings," in text:
        print(
            "KASIF_SES_PROFILI_ZATEN_DUZELTILMIS"
        )
    else:
        raise RuntimeError(
            "Ses durum çıktısı beklenen yapıda değil."
        )
else:
    text = text.replace(
        old,
        new,
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
    "KASIF_SES_PROFILI_CIKTISI_DUZELTILDI"
)
