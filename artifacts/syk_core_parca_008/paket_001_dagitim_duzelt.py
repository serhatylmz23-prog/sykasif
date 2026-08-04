from pathlib import Path

dosya = Path("tests/test_pyproject_dagitim_sozlesmesi.py")
icerik = dosya.read_text(encoding="utf-8-sig")

yeni_paket = '"syk_core/runtime_field_link",'
hedef = '"syk_core/runtime_kernel",'

if yeni_paket not in icerik:
    satirlar = icerik.splitlines()
    sonuc = []
    eklendi = False

    for satir in satirlar:
        if hedef in satir and not eklendi:
            girinti = satir[:len(satir) - len(satir.lstrip())]
            sonuc.append(girinti + yeni_paket)
            eklendi = True

        sonuc.append(satir)

    if not eklendi:
        raise RuntimeError(
            "runtime_kernel paket satırı bulunamadı."
        )

    dosya.write_text(
        "\n".join(sonuc) + "\n",
        encoding="utf-8",
    )

print("RUNTIME_FIELD_LINK_DAGITIM_LISTESINE_EKLENDI")
