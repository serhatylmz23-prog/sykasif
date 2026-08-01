import json

import pytest

from syk_core.entegrasyon.syk_otonom_karar_defteri import (
    SYKOtonomKararDefteri,
)


def _ilk_kaydi_ekle(defter):
    return defter.ekle(
        olay_kimligi="CORE-110",
        karar_id="OGD-CORE-110",
        islem="TASLAK_OLUSTURULDU",
        durum="TASLAK",
        onaylayan="SISTEM",
        karar_sha256="a" * 64,
    )


def test_bozuk_deftere_yeni_kayit_eklenemez(tmp_path):
    dosya = tmp_path / "karar_defteri.jsonl"
    defter = SYKOtonomKararDefteri(dosya)

    _ilk_kaydi_ekle(defter)

    kayit = json.loads(
        dosya.read_text(
            encoding="utf-8"
        ).strip()
    )
    kayit["durum"] = "MUHURLENDI"

    dosya.write_text(
        json.dumps(
            kayit,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    onceki_icerik = dosya.read_text(
        encoding="utf-8"
    )

    with pytest.raises(
        ValueError,
        match="Karar defteri butunlugu bozuk",
    ):
        defter.ekle(
            olay_kimligi="CORE-111",
            karar_id="OGD-CORE-111",
            islem="TASLAK_OLUSTURULDU",
            durum="TASLAK",
            onaylayan="SISTEM",
            karar_sha256="b" * 64,
        )

    sonraki_icerik = dosya.read_text(
        encoding="utf-8"
    )

    assert sonraki_icerik == onceki_icerik
    assert len(sonraki_icerik.splitlines()) == 1
    assert defter.dogrula() is False


def test_gecerli_deftere_yeni_kayit_eklenebilir(tmp_path):
    dosya = tmp_path / "karar_defteri.jsonl"
    defter = SYKOtonomKararDefteri(dosya)

    ilk = _ilk_kaydi_ekle(defter)

    ikinci = defter.ekle(
        olay_kimligi="CORE-112",
        karar_id="OGD-CORE-112",
        islem="TASLAK_OLUSTURULDU",
        durum="TASLAK",
        onaylayan="SISTEM",
        karar_sha256="c" * 64,
    )

    kayitlar = defter.kayitlari_oku()

    assert len(kayitlar) == 2
    assert ikinci.onceki_kayit_hashi == ilk.kayit_hashi
    assert defter.dogrula() is True
