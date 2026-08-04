from syk_core.entegrasyon.runtime_fastapi_core import (
    RuntimeFastApiCoreBaglantisi,
)


class SahteBaglanti:


    def olay_isle(
        self,
        olay,
    ):
        return {
            "aktarildi": True,
            "olay": olay,
        }



def test_fastapi_core_aktarimi():

    baglanti = RuntimeFastApiCoreBaglantisi(
        SahteBaglanti()
    )

    sonuc = baglanti.runtime_olayi_aktar(
        "FASTAPI-001"
    )

    assert (
        sonuc["aktarildi"]
        is True
    )

    assert (
        sonuc["olay"]
        ==
        "FASTAPI-001"
    )
