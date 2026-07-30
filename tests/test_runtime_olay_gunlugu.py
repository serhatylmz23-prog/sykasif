import json

import pytest

from syk_simulasyon.runtime_durumu import RuntimeDurumTuru
from syk_simulasyon.runtime_olay_gunlugu import (
    RuntimeOlayGunlugu,
    RuntimeOlayGunluguButunlukHatasi,
)
from syk_simulasyon.runtime_servisi import RuntimeServisi


def _olay_uret(
    servis: RuntimeServisi,
    *,
    deney: str,
    ilerleme: float,
):
    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP-0013",
        ilerleme_yuzdesi=ilerleme,
    )

    return servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi=deney,
    )


def test_olaylar_sha256_zinciriyle_yazilir(
    tmp_path,
):
    yol = tmp_path / "runtime-olaylari.jsonl"
    servis = RuntimeServisi(yol)

    _olay_uret(
        servis,
        deney="DSP0013-1",
        ilerleme=25,
    )
    _olay_uret(
        servis,
        deney="DSP0013-2",
        ilerleme=50,
    )

    satirlar = [
        json.loads(satir)
        for satir in yol.read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    assert len(satirlar) == 2
    assert satirlar[0]["onceki_hash"] == "0" * 64
    assert satirlar[1]["onceki_hash"] == (
        satirlar[0]["kayit_hash"]
    )
    assert RuntimeOlayGunlugu(
        yol
    ).butunlugu_dogrula()


def test_yeni_servis_kalici_gecmisi_yukler(
    tmp_path,
):
    yol = tmp_path / "runtime-olaylari.jsonl"
    birinci = RuntimeServisi(yol)

    olay = _olay_uret(
        birinci,
        deney="DSP0013",
        ilerleme=75,
    )

    ikinci = RuntimeServisi(yol)

    assert ikinci.olay_gecmisi() == (olay,)
    assert ikinci.son_olay() == olay


def test_degistirilen_kayit_reddedilir(
    tmp_path,
):
    yol = tmp_path / "runtime-olaylari.jsonl"
    servis = RuntimeServisi(yol)

    _olay_uret(
        servis,
        deney="DSP0013",
        ilerleme=40,
    )

    kayit = json.loads(
        yol.read_text(encoding="utf-8")
    )
    kayit["olay"]["ortak_veri"][
        "ilerleme_yuzdesi"
    ] = 99

    yol.write_text(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeOlayGunluguButunlukHatasi
    ):
        RuntimeServisi(yol)


def test_ozel_veri_hashi_bozuksa_reddedilir(
    tmp_path,
):
    yol = tmp_path / "runtime-olaylari.jsonl"
    servis = RuntimeServisi(yol)

    _olay_uret(
        servis,
        deney="DSP0013",
        ilerleme=60,
    )

    kayit = json.loads(
        yol.read_text(encoding="utf-8")
    )
    kayit["olay"]["ozel_veri_sha256"] = (
        "f" * 64
    )

    govde = {
        "surum": kayit["surum"],
        "onceki_hash": kayit["onceki_hash"],
        "olay": kayit["olay"],
    }

    kayit["kayit_hash"] = (
        RuntimeOlayGunlugu._hash_uret(govde)
    )

    yol.write_text(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeOlayGunluguButunlukHatasi
    ):
        RuntimeServisi(yol)


def test_yeniden_acilan_gunluk_zincire_devam_eder(
    tmp_path,
):
    yol = tmp_path / "runtime-olaylari.jsonl"

    birinci = RuntimeServisi(yol)
    _olay_uret(
        birinci,
        deney="DSP0013-1",
        ilerleme=20,
    )

    ikinci = RuntimeServisi(yol)
    _olay_uret(
        ikinci,
        deney="DSP0013-2",
        ilerleme=80,
    )

    gunluk = RuntimeOlayGunlugu(yol)
    olaylar = gunluk.olaylari_oku()

    assert len(olaylar) == 2
    assert gunluk.butunlugu_dogrula()
