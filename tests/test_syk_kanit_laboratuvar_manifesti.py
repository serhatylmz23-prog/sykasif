import json
from pathlib import Path

from syk_core.entegrasyon.syk_kanit_laboratuvar_manifesti import (
    SYKKanitLaboratuvarManifesti,
)


def _kok():
    return Path(__file__).resolve().parents[1]


def test_kanit_laboratuvar_manifesti_olusturulur(tmp_path):
    motor = SYKKanitLaboratuvarManifesti(_kok())
    cikti = tmp_path / "manifest.json"

    belge = motor.kaydet(cikti)

    assert belge["kaynak_sayisi"] == 7
    assert belge["test_dosyasi_sayisi"] == 7
    assert len(belge["manifest_sha256"]) == 64
    assert motor.dogrula(cikti) is True


def test_manifest_hashi_degistirilirse_reddedilir(tmp_path):
    motor = SYKKanitLaboratuvarManifesti(_kok())
    cikti = tmp_path / "manifest.json"
    motor.kaydet(cikti)

    belge = json.loads(
        cikti.read_text(encoding="utf-8")
    )
    belge["manifest_sha256"] = "0" * 64

    cikti.write_text(
        json.dumps(
            belge,
            ensure_ascii=True,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    assert motor.dogrula(cikti) is False


def test_kaynak_dosyasi_degistirilirse_reddedilir(tmp_path):
    proje = tmp_path / "proje"

    for goreli in (
        SYKKanitLaboratuvarManifesti.KAYNAKLAR
        + SYKKanitLaboratuvarManifesti.TESTLER
    ):
        tam_yol = proje / goreli
        tam_yol.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        tam_yol.write_text(
            goreli + "\n",
            encoding="utf-8",
        )

    motor = SYKKanitLaboratuvarManifesti(proje)
    cikti = tmp_path / "manifest.json"
    motor.kaydet(cikti)

    degisen = proje / motor.KAYNAKLAR[0]
    degisen.write_text(
        "degistirildi\n",
        encoding="utf-8",
    )

    assert motor.dogrula(cikti) is False


def test_eksik_dosya_manifest_olusturmayi_durdurur(tmp_path):
    motor = SYKKanitLaboratuvarManifesti(tmp_path)

    try:
        motor.olustur()
    except FileNotFoundError:
        pass
    else:
        raise AssertionError(
            "Eksik dosya reddedilmedi"
        )
