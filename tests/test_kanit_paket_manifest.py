from syk_core.entegrasyon.kanit_paket_manifest import (
    KanitPaketManifest,
)



def test_kanit_manifest_zinciri():

    sistem = KanitPaketManifest(
        "test_kanit_arsiv"
    )


    sonuc = sistem.paket_kaydet(
        "KANIT-040",
        "ALTIN-ORNEK-VERI",
    )


    assert (
        len(
            sonuc.sha256
        )
        ==
        64
    )


    assert (
        sistem.dogrula(
            "KANIT-040"
        )
        is True
    )
