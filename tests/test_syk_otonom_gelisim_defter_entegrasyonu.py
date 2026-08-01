import pytest

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def test_taslak_deftere_yazilir(tmp_path):
    defter_yolu = tmp_path / "otonom_karar_defteri.jsonl"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter_yolu
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-020",
        katmanlar=KATMANLAR_TAM,
    )

    kayitlar = sistem.karar_defteri.kayitlari_oku()

    assert len(kayitlar) == 1
    assert kayitlar[0].karar_id == sonuc.karar_id
    assert kayitlar[0].islem == "TASLAK_OLUSTURULDU"
    assert kayitlar[0].durum == "TASLAK"
    assert kayitlar[0].onaylayan == "SISTEM"
    assert sistem.karar_defteri.dogrula() is True


def test_kurucu_onayi_defter_zincirine_eklenir(tmp_path):
    defter_yolu = tmp_path / "otonom_karar_defteri.jsonl"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter_yolu
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-021",
        katmanlar=KATMANLAR_TAM,
    )

    karar = sistem.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    kayitlar = sistem.karar_defteri.kayitlari_oku()

    assert len(kayitlar) == 2
    assert kayitlar[0].islem == "TASLAK_OLUSTURULDU"
    assert kayitlar[1].islem == "KURUCU_ONAYI"
    assert kayitlar[1].durum == "MUHURLENDI"
    assert kayitlar[1].karar_sha256 == karar.sha256
    assert (
        kayitlar[1].onceki_kayit_hashi
        == kayitlar[0].kayit_hashi
    )
    assert sistem.karar_defteri.dogrula() is True


def test_kurucu_reddi_defter_zincirine_eklenir(tmp_path):
    defter_yolu = tmp_path / "otonom_karar_defteri.jsonl"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter_yolu
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-022",
        katmanlar=KATMANLAR_TAM,
    )

    reddedilen = sistem.karar_reddet(
        karar_id=sonuc.karar_id,
        reddeden="KURUCU_KAAN",
    )

    kayitlar = sistem.karar_defteri.kayitlari_oku()

    assert len(kayitlar) == 2
    assert kayitlar[1].islem == "KURUCU_REDDETTI"
    assert kayitlar[1].durum == "REDDEDILDI"
    assert kayitlar[1].karar_sha256 == reddedilen["sha256"]
    assert sistem.karar_defteri.dogrula() is True


def test_kurucu_disi_islem_deftere_yazilmaz(tmp_path):
    defter_yolu = tmp_path / "otonom_karar_defteri.jsonl"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter_yolu
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-023",
        katmanlar=KATMANLAR_TAM,
    )

    with pytest.raises(PermissionError):
        sistem.karar_onayla(
            karar_id=sonuc.karar_id,
            onaylayan="BILGE_KAAN",
        )

    kayitlar = sistem.karar_defteri.kayitlari_oku()

    assert len(kayitlar) == 1
    assert kayitlar[0].islem == "TASLAK_OLUSTURULDU"
    assert sistem.karar_defteri.dogrula() is True


def test_deftersiz_calisma_geriye_uyumludur():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-024",
        katmanlar=KATMANLAR_TAM,
    )

    assert sonuc.karar_durumu == "TASLAK"
    assert sistem.karar_defteri is None
