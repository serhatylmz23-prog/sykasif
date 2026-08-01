import pytest

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def test_taslak_yeniden_baslatmada_korunur(tmp_path):
    depo_yolu = tmp_path / "karar_durumu.json"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=depo_yolu
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-040",
        katmanlar=KATMANLAR_TAM,
    )

    yeniden_acilan = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=depo_yolu
    )

    assert sonuc.karar_id in yeniden_acilan.karar_taslaklari
    assert yeniden_acilan.durum_deposu.dogrula() is True


def test_yeniden_acilan_taslak_kurucu_tarafindan_onaylanir(tmp_path):
    depo_yolu = tmp_path / "karar_durumu.json"
    defter_yolu = tmp_path / "karar_defteri.jsonl"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter_yolu,
        durum_deposu=depo_yolu,
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-041",
        katmanlar=KATMANLAR_TAM,
    )

    yeniden_acilan = SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter_yolu,
        durum_deposu=depo_yolu,
    )

    karar = yeniden_acilan.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    son_acilis = SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter_yolu,
        durum_deposu=depo_yolu,
    )

    assert karar.durum == "MUHURLENDI"
    assert sonuc.karar_id not in son_acilis.karar_taslaklari
    assert sonuc.karar_id in son_acilis.muhurlu_kararlar
    assert son_acilis.durum_deposu.dogrula() is True
    assert son_acilis.karar_defteri.dogrula() is True


def test_yeniden_acilan_taslak_reddedilebilir(tmp_path):
    depo_yolu = tmp_path / "karar_durumu.json"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=depo_yolu
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-042",
        katmanlar=KATMANLAR_TAM,
    )

    yeniden_acilan = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=depo_yolu
    )

    yeniden_acilan.karar_reddet(
        karar_id=sonuc.karar_id,
        reddeden="KURUCU_KAAN",
    )

    son_acilis = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=depo_yolu
    )

    taslak = son_acilis.karar_taslaklari[sonuc.karar_id]

    assert taslak["durum"] == "REDDEDILDI"
    assert taslak["onay_durumu"] == "REDDEDILDI"
    assert son_acilis.durum_deposu.dogrula() is True


def test_muhurlu_karar_yeniden_baslatmada_ikinci_kez_onaylanamaz(
    tmp_path,
):
    depo_yolu = tmp_path / "karar_durumu.json"

    sistem = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=depo_yolu
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-043",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    yeniden_acilan = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=depo_yolu
    )

    with pytest.raises(
        ValueError,
        match="zaten muhurlu",
    ):
        yeniden_acilan.karar_onayla(
            karar_id=sonuc.karar_id,
            onaylayan="KURUCU_KAAN",
        )


def test_bozuk_durum_deposuyla_motor_baslatilamaz(tmp_path):
    depo_yolu = tmp_path / "karar_durumu.json"
    depo_yolu.write_text(
        "{bozuk-json",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="okunamadi",
    ):
        SYKOtonomGelisimDogrulamaMotoru(
            durum_deposu=depo_yolu
        )


def test_deposuz_calisma_geriye_uyumludur():
    sistem = SYKOtonomGelisimDogrulamaMotoru()

    sonuc = sistem.calistir(
        olay_kimligi="CORE-044",
        katmanlar=KATMANLAR_TAM,
    )

    assert sonuc.karar_durumu == "TASLAK"
    assert sistem.durum_deposu is None
