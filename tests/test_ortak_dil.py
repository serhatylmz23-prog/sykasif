import pytest
from syk_simulasyon.ortak_dil import Katman, IletiTuru, KatmanYetkisi, OrtakIleti


def test_katman_yalniz_kendine_gelen_iletiyi_gorur():
    ileti = OrtakIleti.olustur(arastirma_kimligi="AK-X", tur=IletiTuru.ONERI,
        kaynak_katman=Katman.SIMULASYON, hedef_katman=Katman.ANALIZ,
        ozet_kodu="O-17", guven=.7, icerik_ozeti="kodlanmış özet", ozel_icerik={"yorum":"gizli"})
    yetki = KatmanYetkisi(Katman.ANALIZ, frozenset({IletiTuru.ONERI}))
    gorunum = ileti.ortak_gorunum(yetki)
    assert "yorum" not in gorunum and "_ozel_icerik" not in gorunum
    with pytest.raises(PermissionError):
        ileti.ortak_gorunum(KatmanYetkisi(Katman.GORSEL, frozenset({IletiTuru.ONERI})))


def test_yabanci_katman_ozel_icerigi_acamaz():
    ileti = OrtakIleti.olustur(arastirma_kimligi="AK-X", tur=IletiTuru.KANIT,
        kaynak_katman=Katman.SENSOR, hedef_katman=Katman.ANALIZ,
        ozet_kodu="K-01", guven=.9, icerik_ozeti="özet", ozel_icerik={"ham":123})
    with pytest.raises(PermissionError):
        ileti.ozel_icerigi_ac(KatmanYetkisi(Katman.GORSEL, frozenset({IletiTuru.KANIT})))
    assert ileti.ozel_icerigi_ac(KatmanYetkisi(Katman.BILGE_KAAN, frozenset()))["ham"] == 123
