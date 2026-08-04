from pathlib import Path
import ast


path = Path(
    "src/syk_finans_otagi/"
    "gercek_kaynak_sozlesmeleri.py"
)

text = path.read_text(
    encoding="utf-8",
)


old_import = (
    "from dataclasses import dataclass\n"
)

new_import = (
    "from dataclasses import dataclass, replace\n"
)

if old_import in text:
    text = text.replace(
        old_import,
        new_import,
        1,
    )
elif (
    "from dataclasses import dataclass, replace"
    not in text
):
    raise RuntimeError(
        "dataclasses içe aktarma satırı bulunamadı."
    )


old_block = '''        return KapBildirimi(
            **{
                **bildirim.__dict__,
                "dogrulanmis": True,
                "bildirim_sha256": sha256(
                    kodlu
                ).hexdigest(),
            }
        )
'''

new_block = '''        return replace(
            bildirim,
            dogrulanmis=True,
            bildirim_sha256=sha256(
                kodlu
            ).hexdigest(),
        )
'''

if old_block in text:
    text = text.replace(
        old_block,
        new_block,
        1,
    )
elif (
    "return replace("
    in text
    and "bildirim_sha256=sha256("
    in text
):
    print(
        "KAP_BILDIRIM_MUHURLEME_ZATEN_DUZELTILMIS"
    )
else:
    raise RuntimeError(
        "KAP bildirim mühürleme bölümü bulunamadı."
    )


path.write_text(
    text,
    encoding="utf-8",
)

ast.parse(
    path.read_text(
        encoding="utf-8",
    )
)

print(
    "KAP_BILDIRIM_MUHURLEME_DUZELTILDI"
)
