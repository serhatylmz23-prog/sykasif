import xml.etree.ElementTree as ET

from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi


def test_xml_olusturulur():
    servis = RuntimeServisi()

    xml = RuntimeXmlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    ).xml_uret()

    assert "<runtime>" in xml
    assert "<durum>" in xml


def test_xml_gecerlidir():
    servis = RuntimeServisi()

    xml = RuntimeXmlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    ).xml_uret()

    kok = ET.fromstring(xml)

    assert kok.tag == "runtime"


def test_xml_guncel_veriyi_icerir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=servis.durum.durum,
        aktif_modul="DSP",
        ilerleme_yuzdesi=80.0,
    )

    xml = RuntimeXmlSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    ).xml_uret()

    assert "DSP" in xml
    assert "80.0" in xml