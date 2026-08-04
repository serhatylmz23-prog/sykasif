from pathlib import Path
import ast
import shutil


path = Path(
    "tests/test_pyproject_dagitim_sozlesmesi.py"
)

if not path.is_file():
    raise FileNotFoundError(
        f"Dağıtım sözleşmesi bulunamadı: {path}"
    )

yedek = Path(
    "artifacts/"
    "test_pyproject_dagitim_sozlesmesi_"
    "syfinans_onceki.py"
)

shutil.copy2(
    path,
    yedek,
)

text = path.read_text(
    encoding="utf-8",
)

old_packages = '''    assert paketler == [
        "syk_core/entegrasyon",
        "syk_jarmin",
        "syk_simulasyon",
    ]
'''

new_packages = '''    assert paketler == [
        "syk_core/entegrasyon",
        "syk_finans_otagi",
        "syk_jarmin",
        "syk_simulasyon",
    ]
'''

if old_packages in text:
    text = text.replace(
        old_packages,
        new_packages,
        1,
    )
elif (
    '"syk_finans_otagi",'
    not in text
):
    raise RuntimeError(
        "Beklenen dağıtım paket listesi bulunamadı."
    )


old_allowed = '''    izinli_urunler = {
        "syk_simulasyon",
        "syk_core",
        "syk_jarmin",
    }
'''

new_allowed = '''    izinli_urunler = {
        "syk_simulasyon",
        "syk_core",
        "syk_jarmin",
        "syk_finans_otagi",
    }
'''

if old_allowed in text:
    text = text.replace(
        old_allowed,
        new_allowed,
        1,
    )
else:
    tree = ast.parse(text)

    izinli_kume_bulundu = False
    finans_izinli = False

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Assign,
        ):
            continue

        if not any(
            isinstance(target, ast.Name)
            and target.id == "izinli_urunler"
            for target in node.targets
        ):
            continue

        izinli_kume_bulundu = True

        if isinstance(
            node.value,
            ast.Set,
        ):
            finans_izinli = any(
                isinstance(element, ast.Constant)
                and element.value
                == "syk_finans_otagi"
                for element in node.value.elts
            )

    if not izinli_kume_bulundu:
        raise RuntimeError(
            "İzinli ürünler kümesi bulunamadı."
        )

    if not finans_izinli:
        raise RuntimeError(
            "İzinli ürünler kümesi beklenen "
            "yapıda değil."
        )


path.write_text(
    text,
    encoding="utf-8",
)

updated = path.read_text(
    encoding="utf-8",
)

ast.parse(
    updated
)

if (
    '"syk_finans_otagi",'
    not in updated
):
    raise RuntimeError(
        "SyFinansOtağı dağıtım sözleşmesine "
        "eklenemedi."
    )

print(
    "SYFINANS_DAGITIM_SOZLESMESI_DUZELTILDI"
)

print(
    "YEDEK",
    yedek,
)
