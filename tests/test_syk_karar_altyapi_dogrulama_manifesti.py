import json
from pathlib import Path

from syk_core.entegrasyon.syk_karar_altyapi_dogrulama_manifesti import (
    SYKKararAltyapiDogrulamaManifesti,
)


def _proje_koku():
    return Path(__file__).resolve().parents[1]


def test_karar_altyapi_manifesti_olusturulur(tmp_path):
    motor = SYKKararAltyapiDogrulamaManifesti(
        _proje_koku()
    )
    cikti = tmp_path / "karar_altyapi_manifesti.json"

    belge = motor.kaydet(cikti)

    assert belge["surum"] == "1.0"
    assert len(belge["manifest_sha256"]) == 64
    assert set(belge["dosyalar"]) == set(motor.DOSYALAR)
    assert motor.dogrula(cikti) is True


def test_manifest_icerigi_degistirilirse_reddedilir(tmp_path):
    motor = SYKKararAltyapiDogrulamaManifesti(
        _proje_koku()
    )
    cikti = tmp_path / "karar_altyapi_manifesti.json"

    motor.kaydet(cikti)

    belge = json.loads(
        cikti.read_text(
            encoding="utf-8"
        )
    )
    belge["surum"] = "9.9"

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


def test_manifest_hashi_degistirilirse_reddedilir(tmp_path):
    motor = SYKKararAltyapiDogrulamaManifesti(
        _proje_koku()
    )
    cikti = tmp_path / "karar_altyapi_manifesti.json"

    motor.kaydet(cikti)

    belge = json.loads(
        cikti.read_text(
            encoding="utf-8"
        )
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


def test_kaynak_dosya_degistirilirse_manifest_reddedilir(
    tmp_path,
):
    proje = tmp_path / "proje"

    for goreli_yol in (
        SYKKararAltyapiDogrulamaManifesti.DOSYALAR
    ):
        tam_yol = proje / goreli_yol
        tam_yol.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        tam_yol.write_text(
            f"{goreli_yol}\n",
            encoding="utf-8",
        )

    motor = SYKKararAltyapiDogrulamaManifesti(proje)
    cikti = tmp_path / "manifest.json"

    motor.kaydet(cikti)

    degisen = proje / motor.DOSYALAR[0]
    degisen.write_text(
        "degistirildi\n",
        encoding="utf-8",
    )

    assert motor.dogrula(cikti) is False
