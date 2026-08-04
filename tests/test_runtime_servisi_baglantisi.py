from syk_core.entegrasyon.runtime_servisi_baglantisi import (
    RuntimeServisiCoreBaglantisi,
)


class SahteAktarici:


    def olay_aktar(
        self,
        kimlik,
        durum,
    ):
        return {
            "kimlik": kimlik,
            "durum": durum,
        }


class SahteOlay:


    arastirma_kimligi = "ARASTIRMA-001"


    class Tur:

        value = "gozlem"


    tur = Tur()



def test_runtime_servisi_olayi_corea_aktarilir():

    baglanti = RuntimeServisiCoreBaglantisi(
        SahteAktarici()
    )

    sonuc = baglanti.olay_isle(
        SahteOlay()
    )

    assert (
        sonuc["kimlik"]
        ==
        "ARASTIRMA-001"
    )

    assert (
        sonuc["durum"]
        ==
        "gozlem"
    )
