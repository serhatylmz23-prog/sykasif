import json

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
)
from syk_core.entegrasyon.syk_otonom_karar_tutarlilik_dogrulayici import (
    SYKOtonomKararTutarlilikDogrulayici,
)


KATMANLAR_TAM = {
    "SHA": True,
    "MANIFEST": True,
    "KANIT": True,
}


def _sistem_olustur(tmp_path):
    return SYKOtonomGelisimDogrulamaMotoru(
        karar_defteri=tmp_path / "karar_defteri.jsonl",
        durum_deposu=tmp_path / "karar_durumu.json",
    )


def _dogrulayici_olustur(tmp_path):
    return SYKOtonomKararTutarlilikDogrulayici(
        karar_defteri=tmp_path / "karar_defteri.jsonl",
        durum_deposu=tmp_path / "karar_durumu.json",
    )


def test_taslak_defter_ve_depo_tutarlidir(tmp_path):
    sistem = _sistem_olustur(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-050",
        katmanlar=KATMANLAR_TAM,
    )

    sonuc = _dogrulayici_olustur(tmp_path).dogrula()

    assert sonuc.gecerli is True
    assert sonuc.hatalar == []
    assert sonuc.defter_kayit_sayisi == 1
    assert sonuc.taslak_sayisi == 1
    assert sonuc.muhurlu_karar_sayisi == 0


def test_muhurlu_karar_defter_ve_depo_tutarlidir(tmp_path):
    sistem = _sistem_olustur(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-051",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_onayla(
        karar_id=sonuc.karar_id,
        onaylayan="KURUCU_KAAN",
    )

    dogrulama = _dogrulayici_olustur(tmp_path).dogrula()

    assert dogrulama.gecerli is True
    assert dogrulama.hatalar == []
    assert dogrulama.defter_kayit_sayisi == 2
    assert dogrulama.taslak_sayisi == 0
    assert dogrulama.muhurlu_karar_sayisi == 1


def test_reddedilen_karar_defter_ve_depo_tutarlidir(tmp_path):
    sistem = _sistem_olustur(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-052",
        katmanlar=KATMANLAR_TAM,
    )

    sistem.karar_reddet(
        karar_id=sonuc.karar_id,
        reddeden="KURUCU_KAAN",
    )

    dogrulama = _dogrulayici_olustur(tmp_path).dogrula()

    assert dogrulama.gecerli is True
    assert dogrulama.hatalar == []
    assert dogrulama.defter_kayit_sayisi == 2
    assert dogrulama.taslak_sayisi == 1
    assert dogrulama.muhurlu_karar_sayisi == 0


def test_depodaki_taslak_sha_degistirilirse_tespit_edilir(tmp_path):
    sistem = _sistem_olustur(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-053",
        katmanlar=KATMANLAR_TAM,
    )

    depo_yolu = tmp_path / "karar_durumu.json"
    belge = json.loads(
        depo_yolu.read_text(
            encoding="utf-8"
        )
    )

    belge["karar_taslaklari"][sonuc.karar_id]["sha256"] = (
        "9" * 64
    )

    veri = {
        "surum": belge["surum"],
        "karar_taslaklari": belge["karar_taslaklari"],
        "muhurlu_kararlar": belge["muhurlu_kararlar"],
    }

    from syk_core.entegrasyon.syk_otonom_karar_durum_deposu import (
        SYKOtonomKararDurumDeposu,
    )

    belge["durum_hashi"] = (
        SYKOtonomKararDurumDeposu._hash_hesapla(veri)
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

    dogrulama = _dogrulayici_olustur(tmp_path).dogrula()

    assert dogrulama.gecerli is False
    assert (
        f"Taslak SHA uyusmazligi: {sonuc.karar_id}"
        in dogrulama.hatalar
    )


def test_defter_hash_zinciri_bozulursa_tespit_edilir(tmp_path):
    sistem = _sistem_olustur(tmp_path)

    sistem.calistir(
        olay_kimligi="CORE-054",
        katmanlar=KATMANLAR_TAM,
    )

    defter_yolu = tmp_path / "karar_defteri.jsonl"
    satir = json.loads(
        defter_yolu.read_text(
            encoding="utf-8"
        ).strip()
    )
    satir["durum"] = "MUHURLENDI"

    defter_yolu.write_text(
        json.dumps(
            satir,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    dogrulama = _dogrulayici_olustur(tmp_path).dogrula()

    assert dogrulama.gecerli is False
    assert (
        "Karar defteri hash zinciri gecersiz"
        in dogrulama.hatalar
    )


def test_karar_hem_taslak_hem_muhurlu_olamaz(tmp_path):
    sistem = _sistem_olustur(tmp_path)

    sonuc = sistem.calistir(
        olay_kimligi="CORE-055",
        katmanlar=KATMANLAR_TAM,
    )

    depo_yolu = tmp_path / "karar_durumu.json"
    belge = json.loads(
        depo_yolu.read_text(
            encoding="utf-8"
        )
    )

    belge["muhurlu_kararlar"][sonuc.karar_id] = {
        "karar_id": sonuc.karar_id,
        "durum": "MUHURLENDI",
        "sha256": sonuc.karar_sha256,
    }

    veri = {
        "surum": belge["surum"],
        "karar_taslaklari": belge["karar_taslaklari"],
        "muhurlu_kararlar": belge["muhurlu_kararlar"],
    }

    from syk_core.entegrasyon.syk_otonom_karar_durum_deposu import (
        SYKOtonomKararDurumDeposu,
    )

    belge["durum_hashi"] = (
        SYKOtonomKararDurumDeposu._hash_hesapla(veri)
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

    dogrulama = _dogrulayici_olustur(tmp_path).dogrula()

    assert dogrulama.gecerli is False
    assert (
        f"Karar hem taslak hem muhurlu durumda: {sonuc.karar_id}"
        in dogrulama.hatalar
    )
