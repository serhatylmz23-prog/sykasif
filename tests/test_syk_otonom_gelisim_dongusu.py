import pytest

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
    SYKOtonomGelisimDongusu,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def test_otonom_gelisim_kaydi():
    sistem = SYKOtonomGelisimDongusu()

    sonuc = sistem.degerlendir(
        "CORE-001",
        "inceleme_gerekli",
    )

    assert sonuc.olay_kimligi == "CORE-001"
    assert (
        "Ek kanit ve yeniden dogrulama onerildi"
        in sonuc.gelisim_onerileri
    )
    assert sistem.getir("CORE-001") is sonuc


def test_kurucu_onayi_bekleyen_karar_taslak_kalir():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-002",
        katmanlar=KATMANLAR_TAM,
    )

    assert sonuc.dogrulama_durumu == "yeniden_dogrulandi"
    assert sonuc.karar_durumu == "TASLAK"
    assert sonuc.onay_durumu == "BEKLIYOR"
    assert sonuc.karar_id in sistem.karar_taslaklari
    assert sonuc.karar_id not in sistem.muhurlu_kararlar


def test_bekleyen_taslak_kurucu_onayiyla_muhurlenir():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-003",
        katmanlar=KATMANLAR_TAM,
    )

    karar = sistem.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    assert karar.durum == "MUHURLENDI"
    assert len(karar.sha256) == 64
    assert sonuc.karar_id not in sistem.karar_taslaklari
    assert sonuc.karar_id in sistem.muhurlu_kararlar


def test_kurucu_disi_onay_reddedilir():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-004",
        katmanlar=KATMANLAR_TAM,
    )

    with pytest.raises(
        PermissionError,
        match="KURUCU_KAAN",
    ):
        sistem.karar_onayla(
            karar_id=sonuc.karar_id,
            onaylayan="BILGE_KAAN",
        )


def test_kurucu_taslagi_reddeder():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-005",
        katmanlar=KATMANLAR_TAM,
    )

    reddedilen = sistem.karar_reddet(
        karar_id=sonuc.karar_id,
        reddeden="KURUCU_KAAN",
    )

    assert reddedilen["durum"] == "REDDEDILDI"
    assert reddedilen["onay_durumu"] == "REDDEDILDI"
    assert len(reddedilen["sha256"]) == 64


def test_reddedilen_taslak_sonradan_onaylanamaz():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-006",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_reddet(
        karar_id=sonuc.karar_id,
        reddeden="KURUCU_KAAN",
    )

    with pytest.raises(
        ValueError,
        match="Reddedilen karar onaylanamaz",
    ):
        sistem.karar_onayla(
            karar_id=sonuc.karar_id,
            onaylayan="KURUCU_KAAN",
        )


def test_muhurlu_karar_ikinci_kez_onaylanamaz():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-007",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    with pytest.raises(
        ValueError,
        match="zaten muhurlu",
    ):
        sistem.karar_onayla(
            karar_id=sonuc.karar_id,
            onaylayan="KURUCU_KAAN",
        )


def test_eksik_katman_veri_talebi_ve_taslak_olusturur():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-008",
        katmanlar={
            "SHA": True,
            "MANIFEST": False,
            "KANIT": True,
        },
        mevcut_veri="YETERSIZ",
        eksik_veri="MANIFEST",
        ek_cihaz_talebi="GEREKMIYOR",
    )

    assert sonuc.dogrulama_durumu == "inceleme_gerekli"
    assert "MANIFEST" in sonuc.eksikler
    assert sonuc.veri_talebi_sonucu == "EK_VERI_VEYA_CIHAZ_GEREKLI"
    assert sonuc.karar_durumu == "TASLAK"


def test_gecersiz_onay_durumu_reddedilir():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    with pytest.raises(
        ValueError,
        match="Gecersiz onay durumu",
    ):
        sistem.calistir(
            olay_kimligi="CORE-009",
            katmanlar=KATMANLAR_TAM,
            onay_durumu="OTOMATIK_ONAY",
        )
