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


def _yollar(tmp_path):
    return {
        "karar_defteri": tmp_path / "karar_defteri.jsonl",
        "durum_deposu": tmp_path / "karar_durumu.json",
        "islem_jurnali": tmp_path / "islem_jurnali.json",
    }


def test_tamamlanmis_taslak_yarim_jurnalden_kurtarilir(
    tmp_path,
):
    yollar = _yollar(tmp_path)

    sistem = SYKOtonomGuvenliIslemMotoru(**yollar)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-100",
        katmanlar=KATMANLAR_TAM,
    )

    jurnal = SYKOtonomIslemJurnali(
        yollar["islem_jurnali"]
    )

    jurnal.baslat(
        islem_id="ISLEM-KURTAR-001",
        karar_id=sonuc.karar_id,
        olay_kimligi="CORE-100",
        islem_turu="TASLAK_OLUSTUR",
    )

    yeniden_acilan = SYKOtonomGuvenliIslemMotoru(
        **yollar,
        otomatik_kurtarma=True,
    )

    kurtarilan = yeniden_acilan.jurnal.yukle()

    assert kurtarilan["durum"] == "TAMAMLANDI"
    assert kurtarilan["islem_id"] == "ISLEM-KURTAR-001"
    assert yeniden_acilan.butunluk_dogrula().gecerli is True


def test_tamamlanmis_kurucu_onayi_kurtarilir(tmp_path):
    yollar = _yollar(tmp_path)

    sistem = SYKOtonomGuvenliIslemMotoru(**yollar)

    taslak = sistem.calistir(
        olay_kimligi="CORE-101",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_onayla(
        karar_id=taslak.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    jurnal = SYKOtonomIslemJurnali(
        yollar["islem_jurnali"]
    )

    jurnal.baslat(
        islem_id="ISLEM-KURTAR-002",
        karar_id=taslak.karar_id,
        olay_kimligi="CORE-101",
        islem_turu="KURUCU_ONAYI",
    )

    yeniden_acilan = SYKOtonomGuvenliIslemMotoru(
        **yollar,
        otomatik_kurtarma=True,
    )

    kurtarilan = yeniden_acilan.jurnal.yukle()

    assert kurtarilan["durum"] == "TAMAMLANDI"
    assert yeniden_acilan.butunluk_dogrula().gecerli is True


def test_tamamlanmis_kurucu_reddi_kurtarilir(tmp_path):
    yollar = _yollar(tmp_path)

    sistem = SYKOtonomGuvenliIslemMotoru(**yollar)

    taslak = sistem.calistir(
        olay_kimligi="CORE-102",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_reddet(
        karar_id=taslak.karar_id,
        reddeden="KURUCU_KAAN",
    )

    jurnal = SYKOtonomIslemJurnali(
        yollar["islem_jurnali"]
    )

    jurnal.baslat(
        islem_id="ISLEM-KURTAR-003",
        karar_id=taslak.karar_id,
        olay_kimligi="CORE-102",
        islem_turu="KURUCU_REDDETTI",
    )

    yeniden_acilan = SYKOtonomGuvenliIslemMotoru(
        **yollar,
        otomatik_kurtarma=True,
    )

    kurtarilan = yeniden_acilan.jurnal.yukle()

    assert kurtarilan["durum"] == "TAMAMLANDI"
    assert yeniden_acilan.butunluk_dogrula().gecerli is True


def test_karsiligi_olmayan_yarim_islem_basarisiz_kapatilir(
    tmp_path,
):
    yollar = _yollar(tmp_path)

    jurnal = SYKOtonomIslemJurnali(
        yollar["islem_jurnali"]
    )

    jurnal.baslat(
        islem_id="ISLEM-KURTAR-004",
        karar_id="OGD-CORE-103",
        olay_kimligi="CORE-103",
        islem_turu="TASLAK_OLUSTUR",
    )

    sistem = SYKOtonomGuvenliIslemMotoru(
        **yollar,
        otomatik_kurtarma=True,
    )

    kurtarilan = sistem.jurnal.yukle()

    assert kurtarilan["durum"] == "BASARISIZ"
    assert "tamamlanmis bulunamadi" in kurtarilan["hata"]
    assert sistem.butunluk_dogrula().gecerli is True


def test_kurtarma_sonrasi_yeni_islem_yapilabilir(tmp_path):
    yollar = _yollar(tmp_path)

    jurnal = SYKOtonomIslemJurnali(
        yollar["islem_jurnali"]
    )

    jurnal.baslat(
        islem_id="ISLEM-KURTAR-005",
        karar_id="OGD-CORE-104",
        olay_kimligi="CORE-104",
        islem_turu="TASLAK_OLUSTUR",
    )

    sistem = SYKOtonomGuvenliIslemMotoru(
        **yollar,
        otomatik_kurtarma=True,
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-105",
        katmanlar=KATMANLAR_TAM,
    )

    assert sonuc.karar_durumu == "TASLAK"
    assert sistem.jurnal.yukle()["durum"] == "TAMAMLANDI"
    assert sistem.butunluk_dogrula().gecerli is True
