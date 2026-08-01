import pytest

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
)
from syk_core.entegrasyon.syk_otonom_guvenli_islem_motoru import (
    SYKOtonomGuvenliIslemMotoru,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def test_calistir_icinden_dogrudan_onay_verilemez():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    with pytest.raises(
        PermissionError,
        match="dogrudan onaylanamaz veya reddedilemez",
    ):
        sistem.calistir(
            olay_kimligi="CORE-120",
            katmanlar=KATMANLAR_TAM,
            onay_durumu="ONAYLANDI",
        )

    assert sistem.karar_taslaklari == {}
    assert sistem.muhurlu_kararlar == {}


def test_calistir_icinden_dogrudan_red_verilemez():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    with pytest.raises(
        PermissionError,
        match="dogrudan onaylanamaz veya reddedilemez",
    ):
        sistem.calistir(
            olay_kimligi="CORE-121",
            katmanlar=KATMANLAR_TAM,
            onay_durumu="REDDEDILDI",
        )

    assert sistem.karar_taslaklari == {}
    assert sistem.muhurlu_kararlar == {}


def test_guvenli_motor_dogrudan_onay_girisimini_jurnale_yazar(
    tmp_path,
):
    sistem = SYKOtonomGuvenliIslemMotoru(
        karar_defteri=tmp_path / "karar_defteri.jsonl",
        durum_deposu=tmp_path / "karar_durumu.json",
        islem_jurnali=tmp_path / "islem_jurnali.json",
    )

    with pytest.raises(
        PermissionError,
        match="dogrudan onaylanamaz veya reddedilemez",
    ):
        sistem.calistir(
            olay_kimligi="CORE-122",
            katmanlar=KATMANLAR_TAM,
            onay_durumu="ONAYLANDI",
        )

    jurnal = sistem.jurnal.yukle()

    assert jurnal["durum"] == "BASARISIZ"
    assert jurnal["islem_turu"] == "TASLAK_OLUSTUR"
    assert "PermissionError" in jurnal["hata"]
    assert sistem.butunluk_dogrula().gecerli is True


def test_normal_taslak_kurucu_metoduyla_onaylanir(tmp_path):
    sistem = SYKOtonomGuvenliIslemMotoru(
        karar_defteri=tmp_path / "karar_defteri.jsonl",
        durum_deposu=tmp_path / "karar_durumu.json",
        islem_jurnali=tmp_path / "islem_jurnali.json",
    )

    taslak = sistem.calistir(
        olay_kimligi="CORE-123",
        katmanlar=KATMANLAR_TAM,
    )

    karar = sistem.karar_onayla(
        karar_id=taslak.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    assert karar.durum == "MUHURLENDI"
    assert sistem.jurnal.yukle()["durum"] == "TAMAMLANDI"
    assert sistem.butunluk_dogrula().gecerli is True
