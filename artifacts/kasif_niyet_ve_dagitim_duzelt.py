from __future__ import annotations

import ast
from pathlib import Path
import shutil


intent_path = Path(
    "src/syk_jarmin/runtime/intent_engine.py"
)

test_path = Path(
    "tests/test_pyproject_dagitim_sozlesmesi.py"
)

if not intent_path.is_file():
    raise FileNotFoundError(intent_path)

if not test_path.is_file():
    raise FileNotFoundError(test_path)


shutil.copy2(
    intent_path,
    Path(
        "artifacts/intent_engine_onceki.py"
    ),
)

shutil.copy2(
    test_path,
    Path(
        "artifacts/"
        "test_pyproject_dagitim_sozlesmesi_onceki.py"
    ),
)


# =========================================================
# TÜRKÇE TEMA DEĞİŞTİRME NİYETİ
# =========================================================

text = intent_path.read_text(
    encoding="utf-8",
)

tree = ast.parse(text)
lines = text.splitlines()

target_class = None
target_method = None

for node in tree.body:
    if (
        isinstance(node, ast.ClassDef)
        and node.name == "IntentEngine"
    ):
        target_class = node
        break

if target_class is None:
    raise RuntimeError(
        "IntentEngine sınıfı bulunamadı."
    )

for node in target_class.body:
    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "resolve"
    ):
        target_method = node
        break

if target_method is None:
    raise RuntimeError(
        "IntentEngine.resolve metodu bulunamadı."
    )

if len(target_method.args.args) < 2:
    raise RuntimeError(
        "resolve metninin giriş değişkeni bulunamadı."
    )

input_name = target_method.args.args[1].arg

marker = "SYK_TURKCE_TEMA_NIYETI"

if marker not in text:
    insertion_line = (
        target_method.body[0].lineno - 1
    )

    if (
        isinstance(
            target_method.body[0],
            ast.Expr,
        )
        and isinstance(
            target_method.body[0].value,
            ast.Constant,
        )
        and isinstance(
            target_method.body[0].value.value,
            str,
        )
    ):
        insertion_line = (
            target_method.body[0].end_lineno
        )

    block = f'''
        # {marker}
        tema_metni = str(
            {input_name} or ""
        ).strip().casefold()

        tema_adlari = {{
            "altın": "gold",
            "altin": "gold",
            "gümüş": "silver",
            "gumus": "silver",
            "koyu": "dark",
            "karanlık": "dark",
            "karanlik": "dark",
            "mavi": "blue",
            "yeşil": "green",
            "yesil": "green",
            "kırmızı": "red",
            "kirmizi": "red",
        }}

        tema_eylemleri = (
            "temaya geç",
            "temaya gec",
            "tema yap",
            "temayı değiştir",
            "temayi degistir",
            "tema değiştir",
            "tema degistir",
        )

        secilen_tema = next(
            (
                tema_kodu
                for tema_adi, tema_kodu
                in tema_adlari.items()
                if tema_adi in tema_metni
            ),
            None,
        )

        if (
            secilen_tema is not None
            and any(
                eylem in tema_metni
                for eylem in tema_eylemleri
            )
        ):
            return IntentResult(
                intent_id="theme_change",
                confidence=99.0,
                normalized_text=tema_metni,
                entities={{
                    "theme_id": secilen_tema,
                }},
                requires_confirmation=False,
                user_message=(
                    "İstenen tema uygulanıyor."
                ),
            )
'''.strip("\n").splitlines()

    lines[
        insertion_line:insertion_line
    ] = block

    text = "\n".join(lines) + "\n"

    intent_path.write_text(
        text,
        encoding="utf-8",
    )

ast.parse(
    intent_path.read_text(
        encoding="utf-8",
    )
)


# =========================================================
# DAĞITIM SÖZLEŞMESİNE KAŞİF İÇ PAKETİNİ EKLE
# =========================================================

test_text = test_path.read_text(
    encoding="utf-8",
)

old_packages = '''    assert paketler == [
        "syk_core/entegrasyon",
        "syk_simulasyon",
    ]
'''

new_packages = '''    assert paketler == [
        "syk_core/entegrasyon",
        "syk_jarmin",
        "syk_simulasyon",
    ]
'''

if old_packages in test_text:
    test_text = test_text.replace(
        old_packages,
        new_packages,
        1,
    )
elif '"syk_jarmin",' not in test_text:
    raise RuntimeError(
        "Beklenen paket listesi bulunamadı."
    )


old_allowed = '''    izinli_urunler = {
        "syk_simulasyon",
        "syk_core",
    }
'''

new_allowed = '''    izinli_urunler = {
        "syk_simulasyon",
        "syk_core",
        "syk_jarmin",
    }
'''

if old_allowed in test_text:
    test_text = test_text.replace(
        old_allowed,
        new_allowed,
        1,
    )
elif '"syk_jarmin",' not in test_text:
    raise RuntimeError(
        "İzinli paket kümesi bulunamadı."
    )

test_path.write_text(
    test_text,
    encoding="utf-8",
)

ast.parse(
    test_path.read_text(
        encoding="utf-8",
    )
)

print(
    "TURKCE_TEMA_NIYETI_DUZELTILDI"
)

print(
    "KASIF_DAGITIM_SOZLESMESINE_EKLENDI"
)
