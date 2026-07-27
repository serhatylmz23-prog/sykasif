from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


def test_yaml_olusturulur():
    servis = RuntimeServisi()

    yaml = RuntimeYamlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    ).yaml_uret()

    assert "durum:" in yaml
    assert "olay_sayisi:" in yaml


def test_yaml_satirlar_icerir():
    servis = RuntimeServisi()

    yaml = RuntimeYamlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    ).yaml_uret()

    assert len(yaml.splitlines()) > 1


def test_yaml_guncel_veriyi_icerir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=servis.durum.durum,
        aktif_modul="DSP",
        ilerleme_yuzdesi=90.0,
    )

    yaml = RuntimeYamlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    ).yaml_uret()

    assert "DSP" in yaml
    assert "90.0" in yaml