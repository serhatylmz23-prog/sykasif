import json

import pytest

from syk_core.entegrasyon.syk_otonom_karar_durum_deposu import (
    SYKOtonomKararDurumDeposu,
)


def test_olmayan_depo_bos_durum_dondurur(tmp_path):
    depo = SYKOtonomKararDurumDeposu(
        tmp_path / "karar_durumu.json"
    )

    durum = depo.yukle()

    assert durum["surum"] == "1.0"
    assert durum["karar_taslaklari"] == {}
    assert durum["muhurlu_kararlar"] == {}
    assert depo.dogrula() is True


def test_taslak_ve_muhurlu_kararlar_kalici_kaydedilir(tmp_path):
    dosya = tmp_path / "karar_durumu.json"
    depo = SYKOtonomKararDurumDeposu(dosya)

    durum_hashi = depo.kaydet(
        karar_taslaklari={
            "OGD-CORE-030": {
                "karar_id": "OGD-CORE-030",
                "durum": "TASLAK",
                "onay_durumu": "BEKLIYOR",
                "sha256": "a" * 64,
            },
        },
        muhurlu_kararlar={
            "OGD-CORE-031": {
                "karar_id": "OGD-CORE-031",
                "durum": "MUHURLENDI",
                "sha256": "b" * 64,
            },
        },
    )

    yeniden_acilan = SYKOtonomKararDurumDeposu(dosya)
    durum = yeniden_acilan.yukle()

    assert len(durum_hashi) == 64
    assert "OGD-CORE-030" in durum["karar_taslaklari"]
    assert "OGD-CORE-031" in durum["muhurlu_kararlar"]
    assert yeniden_acilan.dogrula() is True


def test_depo_degistirilirse_hash_dogrulamasi_basarisiz_olur(tmp_path):
    dosya = tmp_path / "karar_durumu.json"
    depo = SYKOtonomKararDurumDeposu(dosya)

    depo.kaydet(
        karar_taslaklari={
            "OGD-CORE-032": {
                "durum": "TASLAK",
            },
        },
        muhurlu_kararlar={},
    )

    belge = json.loads(
        dosya.read_text(
            encoding="utf-8"
        )
    )
    belge["karar_taslaklari"]["OGD-CORE-032"]["durum"] = (
        "MUHURLENDI"
    )

    dosya.write_text(
        json.dumps(
            belge,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    assert depo.dogrula() is False

    with pytest.raises(
        ValueError,
        match="hash dogrulamasi basarisiz",
    ):
        depo.yukle()


def test_gecersiz_json_reddedilir(tmp_path):
    dosya = tmp_path / "karar_durumu.json"
    dosya.write_text(
        "{gecersiz-json",
        encoding="utf-8",
    )

    depo = SYKOtonomKararDurumDeposu(dosya)

    assert depo.dogrula() is False

    with pytest.raises(
        ValueError,
        match="okunamadi",
    ):
        depo.yukle()


def test_desteklenmeyen_surum_reddedilir(tmp_path):
    dosya = tmp_path / "karar_durumu.json"

    veri = {
        "surum": "9.9",
        "karar_taslaklari": {},
        "muhurlu_kararlar": {},
    }

    belge = {
        **veri,
        "durum_hashi": SYKOtonomKararDurumDeposu._hash_hesapla(
            veri
        ),
    }

    dosya.write_text(
        json.dumps(
            belge,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    depo = SYKOtonomKararDurumDeposu(dosya)

    with pytest.raises(
        ValueError,
        match="Desteklenmeyen depo surumu",
    ):
        depo.yukle()


def test_kayit_guncellenirken_gecici_dosya_birakilmaz(tmp_path):
    dosya = tmp_path / "karar_durumu.json"
    depo = SYKOtonomKararDurumDeposu(dosya)

    depo.kaydet(
        karar_taslaklari={},
        muhurlu_kararlar={},
    )

    depo.kaydet(
        karar_taslaklari={
            "OGD-CORE-033": {
                "durum": "TASLAK",
            },
        },
        muhurlu_kararlar={},
    )

    gecici_dosyalar = list(
        tmp_path.glob("karar_durumu.json.*.tmp")
    )

    assert gecici_dosyalar == []
    assert depo.dogrula() is True
