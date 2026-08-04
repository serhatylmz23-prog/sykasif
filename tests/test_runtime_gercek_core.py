from syk_core.entegrasyon.runtime_gercek_core import (
    GercekRuntimeCoreEntegrasyonu,
)


class SahteRuntime:


    class SahteOlay:

        arastirma_kimligi = (
            "TEST-001"
        )

        class Tur:

            value = "gozlem"

        tur = Tur()


    def olay_uret(
        self,
        *,
        arastirma_kimligi,
    ):
        return self.SahteOlay()



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



def test_gercek_runtime_zinciri():

    entegrasyon = (
        GercekRuntimeCoreEntegrasyonu(
            SahteRuntime(),
            SahteAktarici(),
        )
    )

    sonuc = (
        entegrasyon.olay_uret_ve_aktar(
            "TEST-001"
        )
    )

    assert (
        sonuc["kimlik"]
        ==
        "TEST-001"
    )

    assert (
        sonuc["durum"]
        ==
        "gozlem"
    )
