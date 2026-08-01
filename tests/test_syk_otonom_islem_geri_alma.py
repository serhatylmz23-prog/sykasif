import pytest

from syk_core.entegrasyon.syk_otonom_guvenli_islem_motoru import (
    SYKOtonomGuvenliIslemMotoru,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def _yollar(tmp_path):
    return {
        "karar_defteri": tmp_path / "karar_defteri.jsonl",
        "durum_deposu": tmp_path / "karar_durumu.json",
        "islem_jurnali": tmp_path / "islem_jurnali.json",
    }


def test_taslak_defter_yazma_hatasinda_tam_geri_alinir(
    tmp_path,
    monkeypatch,
):
    yollar = _yollar(tmp_path)
    sistem = SYKOtonomGuvenliIslemMotoru(**yollar)

    def defter_hatasi(*args, **kwargs):
        raise OSError("Defter yazma hatasi")

    monkeypatch.setattr(
        sistem.motor,
        "_deftere_yaz",
        defter_hatasi,
    )

    with pytest.raises(
        OSError,
        match="Defter yazma hatasi",
    ):
        sistem.calistir(
            olay_kimligi="CORE-130",
            katmanlar=KATMANLAR_TAM,
        )

    assert sistem.motor.karar_taslaklari == {}
    assert sistem.motor.muhurlu_kararlar == {}
    assert yollar["karar_defteri"].exists() is False
    assert yollar["durum_deposu"].exists() is False
    assert sistem.jurnal.yukle()["durum"] == "BASARISIZ"
    assert sistem.butunluk_dogrula().gecerli is True

    yeniden_acilan = SYKOtonomGuvenliIslemMotoru(
        **yollar
    )

    assert yeniden_acilan.motor.karar_taslaklari == {}
    assert yeniden_acilan.butunluk_dogrula().gecerli is True


def test_onay_defter_hatasinda_taslak_geri_yuklenir(
    tmp_path,
    monkeypatch,
):
    yollar = _yollar(tmp_path)
    sistem = SYKOtonomGuvenliIslemMotoru(**yollar)

    taslak = sistem.calistir(
        olay_kimligi="CORE-131",
        katmanlar=KATMANLAR_TAM,
    )

    defter_once = yollar["karar_defteri"].read_bytes()
    depo_once = yollar["durum_deposu"].read_bytes()

    def defter_hatasi(*args, **kwargs):
        raise OSError("Onay defteri yazilamadi")

    monkeypatch.setattr(
        sistem.motor,
        "_deftere_yaz",
        defter_hatasi,
    )

    with pytest.raises(
        OSError,
        match="Onay defteri yazilamadi",
    ):
        sistem.karar_onayla(
            karar_id=taslak.karar_id,
            onaylayan="KURUCU_KAAN",
        )

    assert (
        yollar["karar_defteri"].read_bytes()
        == defter_once
    )
    assert (
        yollar["durum_deposu"].read_bytes()
        == depo_once
    )

    assert taslak.karar_id in sistem.motor.karar_taslaklari
    assert taslak.karar_id not in sistem.motor.muhurlu_kararlar
    assert (
        sistem.motor.karar_taslaklari[
            taslak.karar_id
        ]["durum"]
        == "TASLAK"
    )

    jurnal = sistem.jurnal.yukle()

    assert jurnal["durum"] == "BASARISIZ"
    assert "OSError" in jurnal["hata"]
    assert sistem.butunluk_dogrula().gecerli is True

    yeniden_acilan = SYKOtonomGuvenliIslemMotoru(
        **yollar
    )

    assert taslak.karar_id in (
        yeniden_acilan.motor.karar_taslaklari
    )
    assert yeniden_acilan.butunluk_dogrula().gecerli is True
