import pytest
from syk_simulasyon.otonomi import BilgeKaanTeknikOnayi


def test_teknik_onay_kanita_dayali_olmalidir():
    onay = BilgeKaanTeknikOnayi("BK-1", "frekans matrisi", "Kaynaklar incelendi", ("KNT-1",))
    assert onay.onaylayan == "Bilge Kaan Kontrollü Otonom"


def test_kanitsiz_teknik_onay_reddedilir():
    with pytest.raises(ValueError):
        BilgeKaanTeknikOnayi("BK-1", "frekans matrisi", "Gerekçe", ())
