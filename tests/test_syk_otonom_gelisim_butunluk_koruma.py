import json

import pytest

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def _yollar(tmp_path):
    return (
        tmp_path / "karar_defteri.jsonl",
        tmp_path / "karar_durumu.json",
    )


def _sistem(tmp_path):
    defter, depo = _yollar(tmp_path)

    return SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=defter,
        durum_deposu=depo,
    )


def test_bos_sistem_butunluk_kontrolunden_gecer(tmp_path):
    sistem = _sistem(tmp_path)

    sonuc = sistem.butunluk_dogrula()

    assert sonuc.gecerli is True
    assert sonuc.hatalar == []


def test_taslak_sonrasi_butunluk_gecerlidir(tmp_path):
    sistem = _sistem(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-060",
        katmanlar=KATMANLAR_TAM,
    )

    sonuc = sistem.butunluk_dogrula()

    assert sonuc.gecerli is True
    assert sonuc.taslak_sayisi == 1
    assert sonuc.defter_kayit_sayisi == 1


def test_onay_sonrasi_butunluk_gecerlidir(tmp_path):
    sistem = _sistem(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-061",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    butunluk = sistem.butunluk_dogrula()

    assert butunluk.gecerli is True
    assert butunluk.taslak_sayisi == 0
    assert butunluk.muhurlu_karar_sayisi == 1
    assert butunluk.defter_kayit_sayisi == 2


def test_bozuk_defterle_yeniden_baslatma_engellenir(tmp_path):
    sistem = _sistem(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-062",
        katmanlar=KATMANLAR_TAM,
    )

    defter_yolu, depo_yolu = _yollar(tmp_path)

    kayit = json.loads(
        defter_yolu.read_text(
            encoding="utf-8"
        ).strip()
    )
    kayit["durum"] = "MUHURLENDI"

    defter_yolu.write_text(
        json.dumps(
            kayit,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="Karar defteri hash zinciri gecersiz",
    ):
        SYKOtonomGelisimDogrulamaMotoru(
            karar_defteri=defter_yolu,
            durum_deposu=depo_yolu,
        )


def test_bozuk_depo_ile_islem_yapilamaz(tmp_path):
    sistem = _sistem(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-063",
        katmanlar=KATMANLAR_TAM,
    )

    _, depo_yolu = _yollar(tmp_path)

    belge = json.loads(
        depo_yolu.read_text(
            encoding="utf-8"
        )
    )
    belge["karar_taslaklari"]["OGD-CORE-063"]["durum"] = (
        "MUHURLENDI"
    )

    depo_yolu.write_text(
        json.dumps(
            belge,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="durum deposu hash dogrulamasi gecersiz",
    ):
        sistem.calistir(
            olay_kimligi="CORE-064",
            katmanlar=KATMANLAR_TAM,
        )


def test_tek_depo_kullanimi_geriye_uyumludur(tmp_path):
    sistem = SYKOtonomGelisimDogrulamaMotoru(
        durum_deposu=tmp_path / "karar_durumu.json"
    )

    sonuc = sistem.calistir(
        olay_kimligi="CORE-065",
        katmanlar=KATMANLAR_TAM,
    )

    assert sonuc.karar_durumu == "TASLAK"
    assert sistem.butunluk_dogrula() is None
