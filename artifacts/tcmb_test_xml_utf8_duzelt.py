from pathlib import Path
import ast


path = Path(
    "tests/"
    "test_syfinans_tcmb_doviz_bagdastiricisi.py"
)

text = path.read_text(
    encoding="utf-8",
)

old_start = (
    'XML_ORNEGI = b"""'
)

new_start = (
    'XML_ORNEGI = """'
)

old_end = '''</Tarih_Date>
"""
'''

new_end = '''</Tarih_Date>
""".encode("utf-8")
'''

if old_start in text:
    text = text.replace(
        old_start,
        new_start,
        1,
    )
elif (
    'XML_ORNEGI = """'
    not in text
):
    raise RuntimeError(
        "XML örneği başlangıcı bulunamadı."
    )

if old_end in text:
    text = text.replace(
        old_end,
        new_end,
        1,
    )
elif (
    '""".encode("utf-8")'
    not in text
):
    raise RuntimeError(
        "XML örneği bitişi bulunamadı."
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
    "TCMB_TEST_XML_UTF8_DUZELTILDI"
)
