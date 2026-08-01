import pytest

from syk_core.entegrasyon.syk_otonom_guvenli_islem_motoru import (
    SYKOtonomGuvenliIslemMotoru,
)
from syk_core.entegrasyon.syk_otonom_islem_jurnali import (
    SYKOtonomIslemJurnali,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def _sistem(tmp_path):
    return SYKOtonomGuvenliIslemMotoru(
        karar_defteri=tmp_path / "karar_defteri.jsonl",
        durum_deposu=tmp_path / "karar_durumu.json",
        islem_jurnali=tmp_path / "islem_jurnali.json",
    )


def test_taslak_islemi_jurnalde_tamamlanir(tmp_path):
    sistem = _sistem(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-090",
        katmanlar=KATMANLAR_TAM,
    )

    jurnal = sistem.jurnal.yukle()

    assert sonuc.karar_id == "OGD-CORE-090"
    assert sonuc.karar_durumu == "TASLAK"
    assert jurnal["karar_id"] == "OGD-CORE-090"
    assert jurnal["islem_turu"] == "TASLAK_OLUSTUR"
    assert jurnal["durum"] == "TAMAMLANDI"
    assert jurnal["hata"] == ""
    assert sistem.butunluk_dogrula().gecerli is True


def test_kurucu_onayi_jurnalde_tamamlanir(tmp_path):
    sistem = _sistem(tmp_path)

    taslak = sistem.calistir(
        olay_kimligi="CORE-091",
        katmanlar=KATMANLAR_TAM,
    )

    karar = sistem.karar_onayla(
        karar_id=taslak.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    jurnal = sistem.jurnal.yukle()

    assert karar.durum == "MUHURLENDI"
    assert jurnal["karar_id"] == taslak.karar_id
    assert jurnal["islem_turu"] == "KURUCU_ONAYI"
    assert jurnal["durum"] == "TAMAMLANDI"
    assert sistem.butunluk_dogrula().gecerli is True


def test_kurucu_reddi_jurnalde_tamamlanir(tmp_path):
    sistem = _sistem(tmp_path)

    taslak = sistem.calistir(
        olay_kimligi="CORE-092",
        katmanlar=KATMANLAR_TAM,
    )

    reddedilen = sistem.karar_reddet(
        karar_id=taslak.karar_id,
        reddeden="KURUCU_KAAN",
    )

    jurnal = sistem.jurnal.yukle()

    assert reddedilen["durum"] == "REDDEDILDI"
    assert jurnal["islem_turu"] == "KURUCU_REDDETTI"
    assert jurnal["durum"] == "TAMAMLANDI"
    assert sistem.butunluk_dogrula().gecerli is True


def test_basarisiz_onay_jurnalde_hatayla_kapatilir(tmp_path):
    sistem = _sistem(tmp_path)

    taslak = sistem.calistir(
        olay_kimligi="CORE-093",
        katmanlar=KATMANLAR_TAM,
    )

    with pytest.raises(PermissionError):
        sistem.karar_onayla(
            karar_id=taslak.karar_id,
            onaylayan="BILGE_KAAN",
        )

    jurnal = sistem.jurnal.yukle()

    assert jurnal["islem_turu"] == "KURUCU_ONAYI"
    assert jurnal["durum"] == "BASARISIZ"
    assert "PermissionError" in jurnal["hata"]
    assert sistem.butunluk_dogrula().gecerli is True


def test_tekrarlanan_karar_jurnalde_basarisiz_kapatilir(tmp_path):
    sistem = _sistem(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-094",
        katmanlar=KATMANLAR_TAM,
    )

    with pytest.raises(
        ValueError,
        match="Karar kimligi zaten mevcut",
    ):
        sistem.calistir(
            olay_kimligi="CORE-094",
            katmanlar=KATMANLAR_TAM,
        )

    jurnal = sistem.jurnal.yukle()

    assert jurnal["durum"] == "BASARISIZ"
    assert "ValueError" in jurnal["hata"]
    assert sistem.butunluk_dogrula().gecerli is True


def test_yarim_kalmis_islemle_sistem_baslatilamaz(tmp_path):
    jurnal_yolu = tmp_path / "islem_jurnali.json"

    jurnal = SYKOtonomIslemJurnali(jurnal_yolu)
    jurnal.baslat(
        islem_id="ISLEM-YARIM",
        karar_id="OGD-CORE-095",
        olay_kimligi="CORE-095",
        islem_turu="TASLAK_OLUSTUR",
    )

    with pytest.raises(
        RuntimeError,
        match="Tamamlanmamis islem nedeniyle sistem baslatilamadi",
    ):
        SYKOtonomGuvenliIslemMotoru(
            karar_defteri=tmp_path / "karar_defteri.jsonl",
            durum_deposu=tmp_path / "karar_durumu.json",
            islem_jurnali=jurnal_yolu,
        )


def test_basarisiz_jurnal_sonrasi_sistem_yeniden_acilir(tmp_path):
    yollar = {
        "karar_defteri": tmp_path / "karar_defteri.jsonl",
        "durum_deposu": tmp_path / "karar_durumu.json",
        "islem_jurnali": tmp_path / "islem_jurnali.json",
    }

    sistem = SYKOtonomGuvenliIslemMotoru(**yollar)

    with pytest.raises(KeyError):
        sistem.karar_onayla(
            karar_id="OGD-CORE-YOK",
            onaylayan="KURUCU_KAAN",
        )

    yeniden_acilan = SYKOtonomGuvenliIslemMotoru(
        **yollar
    )

    sonuc = yeniden_acilan.calistir(
        olay_kimligi="CORE-096",
        katmanlar=KATMANLAR_TAM,
    )

    assert sonuc.karar_durumu == "TASLAK"
    assert yeniden_acilan.jurnal.yukle()["durum"] == "TAMAMLANDI"
    assert yeniden_acilan.butunluk_dogrula().gecerli is True
