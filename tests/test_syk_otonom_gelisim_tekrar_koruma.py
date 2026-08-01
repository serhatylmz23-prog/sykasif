import pytest

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def _sistem(tmp_path):
    return SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=tmp_path / "karar_defteri.jsonl",
        durum_deposu=tmp_path / "karar_durumu.json",
    )


def test_ayni_olay_icin_ikinci_taslak_olusturulamaz(tmp_path):
    sistem = _sistem(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-070",
        katmanlar=KATMANLAR_TAM,
    )

    with pytest.raises(
        ValueError,
        match="Karar kimligi zaten mevcut: OGD-CORE-070",
    ):
        sistem.calistir(
            olay_kimligi="CORE-070",
            katmanlar=KATMANLAR_TAM,
        )

    kayitlar = sistem.karar_defteri.kayitlari_oku()

    assert len(kayitlar) == 1
    assert sistem.butunluk_dogrula().gecerli is True


def test_muhurlu_olay_icin_yeni_karar_olusturulamaz(tmp_path):
    sistem = _sistem(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-071",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    with pytest.raises(
        ValueError,
        match="Karar kimligi zaten mevcut: OGD-CORE-071",
    ):
        sistem.calistir(
            olay_kimligi="CORE-071",
            katmanlar=KATMANLAR_TAM,
        )

    kayitlar = sistem.karar_defteri.kayitlari_oku()

    assert len(kayitlar) == 2
    assert sistem.butunluk_dogrula().gecerli is True


def test_reddedilen_olay_icin_yeni_karar_olusturulamaz(tmp_path):
    sistem = _sistem(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-072",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_reddet(
        karar_id=sonuc.karar_id,
        reddeden="KURUCU_KAAN",
    )

    with pytest.raises(
        ValueError,
        match="Karar kimligi zaten mevcut: OGD-CORE-072",
    ):
        sistem.calistir(
            olay_kimligi="CORE-072",
            katmanlar=KATMANLAR_TAM,
        )

    kayitlar = sistem.karar_defteri.kayitlari_oku()

    assert len(kayitlar) == 2
    assert sistem.butunluk_dogrula().gecerli is True


def test_yeniden_baslatma_sonrasi_tekrar_korunur(tmp_path):
    sistem = _sistem(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-073",
        katmanlar=KATMANLAR_TAM,
    )

    yeniden_acilan = _sistem(tmp_path)

    with pytest.raises(
        ValueError,
        match="Karar kimligi zaten mevcut: OGD-CORE-073",
    ):
        yeniden_acilan.calistir(
            olay_kimligi="CORE-073",
            katmanlar=KATMANLAR_TAM,
        )

    assert yeniden_acilan.butunluk_dogrula().gecerli is True


def test_farkli_olay_kimlikleri_ayri_karar_olusturur(tmp_path):
    sistem = _sistem(tmp_path)

    ilk = sistem.calistir(
        olay_kimligi="CORE-074",
        katmanlar=KATMANLAR_TAM,
    )

    ikinci = sistem.calistir(
        olay_kimligi="CORE-075",
        katmanlar=KATMANLAR_TAM,
    )

    assert ilk.karar_id == "OGD-CORE-074"
    assert ikinci.karar_id == "OGD-CORE-075"
    assert len(sistem.karar_taslaklari) == 2
    assert len(sistem.karar_defteri.kayitlari_oku()) == 2
    assert sistem.butunluk_dogrula().gecerli is True
