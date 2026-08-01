import json

from syk_core.entegrasyon.syk_otonom_karar_defteri import (
    SYKOtonomKararDefteri,
)


def test_bos_defter_gecerlidir(tmp_path):
    defter = SYKOtonomKararDefteri(
        tmp_path / "karar_defteri.jsonl"
    )

    assert defter.kayitlari_oku() == []
    assert defter.dogrula() is True


def test_kararlar_hash_zinciriyle_kaydedilir(tmp_path):
    defter = SYKOtonomKararDefteri(
        tmp_path / "karar_defteri.jsonl"
    )

    ilk = defter.ekle(
        olay_kimligi="CORE-010",
        karar_id="OGD-CORE-010",
        islem="TASLAK_OLUSTURULDU",
        durum="TASLAK",
        onaylayan="SISTEM",
        karar_sha256="a" * 64,
    )

    ikinci = defter.ekle(
        olay_kimligi="CORE-010",
        karar_id="OGD-CORE-010",
        islem="KURUCU_ONAYI",
        durum="MUHURLENDI",
        onaylayan="KURUCU_KAAN",
        karar_sha256="b" * 64,
    )

    assert ilk.sira == 1
    assert ikinci.sira == 2
    assert ikinci.onceki_kayit_hashi == ilk.kayit_hashi
    assert len(ilk.kayit_hashi) == 64
    assert len(ikinci.kayit_hashi) == 64
    assert defter.dogrula() is True


def test_defter_yeniden_acildiginda_kayitlar_korunur(tmp_path):
    dosya = tmp_path / "karar_defteri.jsonl"

    defter = SYKOtonomKararDefteri(dosya)
    defter.ekle(
        olay_kimligi="CORE-011",
        karar_id="OGD-CORE-011",
        islem="TASLAK_OLUSTURULDU",
        durum="TASLAK",
        onaylayan="SISTEM",
        karar_sha256="c" * 64,
    )

    yeniden_acilan = SYKOtonomKararDefteri(dosya)
    kayitlar = yeniden_acilan.kayitlari_oku()

    assert len(kayitlar) == 1
    assert kayitlar[0].karar_id == "OGD-CORE-011"
    assert yeniden_acilan.dogrula() is True


def test_degistirilen_kayit_tespit_edilir(tmp_path):
    dosya = tmp_path / "karar_defteri.jsonl"
    defter = SYKOtonomKararDefteri(dosya)

    defter.ekle(
        olay_kimligi="CORE-012",
        karar_id="OGD-CORE-012",
        islem="TASLAK_OLUSTURULDU",
        durum="TASLAK",
        onaylayan="SISTEM",
        karar_sha256="d" * 64,
    )

    veri = json.loads(
        dosya.read_text(
            encoding="utf-8"
        ).strip()
    )
    veri["durum"] = "MUHURLENDI"

    dosya.write_text(
        json.dumps(
            veri,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    assert defter.dogrula() is False


def test_zincir_baglantisi_bozulursa_tespit_edilir(tmp_path):
    dosya = tmp_path / "karar_defteri.jsonl"
    defter = SYKOtonomKararDefteri(dosya)

    defter.ekle(
        olay_kimligi="CORE-013",
        karar_id="OGD-CORE-013",
        islem="TASLAK_OLUSTURULDU",
        durum="TASLAK",
        onaylayan="SISTEM",
        karar_sha256="e" * 64,
    )
    defter.ekle(
        olay_kimligi="CORE-013",
        karar_id="OGD-CORE-013",
        islem="KURUCU_REDDETTI",
        durum="REDDEDILDI",
        onaylayan="KURUCU_KAAN",
        karar_sha256="f" * 64,
    )

    satirlar = dosya.read_text(
        encoding="utf-8"
    ).splitlines()

    ikinci = json.loads(satirlar[1])
    ikinci["onceki_kayit_hashi"] = "9" * 64
    satirlar[1] = json.dumps(
        ikinci,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )

    dosya.write_text(
        "\n".join(satirlar) + "\n",
        encoding="utf-8",
    )

    assert defter.dogrula() is False
