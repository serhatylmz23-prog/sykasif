import json

import pytest

from syk_core.entegrasyon.syk_otonom_islem_jurnali import (
    SYKOtonomIslemJurnali,
)


def test_olmayan_jurnal_gecerlidir(tmp_path):
    jurnal = SYKOtonomIslemJurnali(
        tmp_path / "islem_jurnali.json"
    )

    assert jurnal.bekleyen_islem() is None
    assert jurnal.dogrula() is True


def test_islem_baslatilir_ve_tamamlanir(tmp_path):
    jurnal = SYKOtonomIslemJurnali(
        tmp_path / "islem_jurnali.json"
    )

    baslayan = jurnal.baslat(
        islem_id="ISLEM-001",
        karar_id="OGD-CORE-080",
        olay_kimligi="CORE-080",
        islem_turu="TASLAK_OLUSTUR",
    )

    assert baslayan["durum"] == "HAZIRLANIYOR"
    assert baslayan["hata"] == ""
    assert len(baslayan["islem_hashi"]) == 64
    assert jurnal.bekleyen_islem()["islem_id"] == "ISLEM-001"

    tamamlanan = jurnal.tamamla("ISLEM-001")

    assert tamamlanan["durum"] == "TAMAMLANDI"
    assert tamamlanan["tamamlanma_zamani"]
    assert tamamlanan["hata"] == ""
    assert jurnal.bekleyen_islem() is None
    assert jurnal.dogrula() is True


def test_islem_basarisiz_olarak_kapatilir(tmp_path):
    jurnal = SYKOtonomIslemJurnali(
        tmp_path / "islem_jurnali.json"
    )

    jurnal.baslat(
        islem_id="ISLEM-002",
        karar_id="OGD-CORE-081",
        olay_kimligi="CORE-081",
        islem_turu="TASLAK_OLUSTUR",
    )

    sonuc = jurnal.basarisiz(
        islem_id="ISLEM-002",
        hata="Durum deposu yazilamadi",
    )

    assert sonuc["durum"] == "BASARISIZ"
    assert sonuc["hata"] == "Durum deposu yazilamadi"
    assert sonuc["tamamlanma_zamani"]
    assert jurnal.bekleyen_islem() is None
    assert jurnal.dogrula() is True


def test_bos_hata_aciklamasi_reddedilir(tmp_path):
    jurnal = SYKOtonomIslemJurnali(
        tmp_path / "islem_jurnali.json"
    )

    jurnal.baslat(
        islem_id="ISLEM-003",
        karar_id="OGD-CORE-082",
        olay_kimligi="CORE-082",
        islem_turu="KURUCU_ONAYI",
    )

    with pytest.raises(
        ValueError,
        match="hata aciklamasi zorunludur",
    ):
        jurnal.basarisiz(
            islem_id="ISLEM-003",
            hata="   ",
        )

    assert jurnal.bekleyen_islem()["islem_id"] == "ISLEM-003"


def test_tamamlanan_islem_basarisiz_yapilamaz(tmp_path):
    jurnal = SYKOtonomIslemJurnali(
        tmp_path / "islem_jurnali.json"
    )

    jurnal.baslat(
        islem_id="ISLEM-004",
        karar_id="OGD-CORE-083",
        olay_kimligi="CORE-083",
        islem_turu="KURUCU_ONAYI",
    )
    jurnal.tamamla("ISLEM-004")

    with pytest.raises(
        ValueError,
        match="kapatilabilir durumda degil",
    ):
        jurnal.basarisiz(
            islem_id="ISLEM-004",
            hata="Sonradan hata",
        )


def test_basarisiz_islemden_sonra_yeni_islem_baslatilabilir(tmp_path):
    jurnal = SYKOtonomIslemJurnali(
        tmp_path / "islem_jurnali.json"
    )

    jurnal.baslat(
        islem_id="ISLEM-005",
        karar_id="OGD-CORE-084",
        olay_kimligi="CORE-084",
        islem_turu="TASLAK_OLUSTUR",
    )
    jurnal.basarisiz(
        islem_id="ISLEM-005",
        hata="Birinci islem basarisiz",
    )

    yeni = jurnal.baslat(
        islem_id="ISLEM-006",
        karar_id="OGD-CORE-085",
        olay_kimligi="CORE-085",
        islem_turu="TASLAK_OLUSTUR",
    )

    assert yeni["durum"] == "HAZIRLANIYOR"
    assert yeni["islem_id"] == "ISLEM-006"


def test_farkli_islem_kimligiyle_tamamlanamaz(tmp_path):
    jurnal = SYKOtonomIslemJurnali(
        tmp_path / "islem_jurnali.json"
    )

    jurnal.baslat(
        islem_id="ISLEM-007",
        karar_id="OGD-CORE-086",
        olay_kimligi="CORE-086",
        islem_turu="KURUCU_ONAYI",
    )

    with pytest.raises(
        ValueError,
        match="Islem kimligi uyusmuyor",
    ):
        jurnal.tamamla("ISLEM-YANLIS")


def test_jurnal_degistirilirse_hash_hatasi_verir(tmp_path):
    dosya = tmp_path / "islem_jurnali.json"
    jurnal = SYKOtonomIslemJurnali(dosya)

    jurnal.baslat(
        islem_id="ISLEM-008",
        karar_id="OGD-CORE-087",
        olay_kimligi="CORE-087",
        islem_turu="TASLAK_OLUSTUR",
    )

    belge = json.loads(
        dosya.read_text(
            encoding="utf-8"
        )
    )
    belge["durum"] = "TAMAMLANDI"

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

    assert jurnal.dogrula() is False

    with pytest.raises(
        ValueError,
        match="hash dogrulamasi basarisiz",
    ):
        jurnal.yukle()


def test_jurnal_temizlenir(tmp_path):
    dosya = tmp_path / "islem_jurnali.json"
    jurnal = SYKOtonomIslemJurnali(dosya)

    jurnal.baslat(
        islem_id="ISLEM-009",
        karar_id="OGD-CORE-088",
        olay_kimligi="CORE-088",
        islem_turu="TASLAK_OLUSTUR",
    )

    jurnal.temizle()

    assert dosya.exists() is False
    assert jurnal.bekleyen_islem() is None
    assert jurnal.dogrula() is True
