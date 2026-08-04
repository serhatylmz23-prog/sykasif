from syk_core.entegrasyon.core_olay_koprusu import (
    CoreOlayKoprusu,
)

from syk_core.entegrasyon.runtime_core_aktarim import (
    RuntimeCoreAktarici,
)


def test_runtime_core_aktarimi():

    kopru = CoreOlayKoprusu()

    aktarici = RuntimeCoreAktarici(
        kopru
    )

    sonuc = aktarici.olay_aktar(
        "RUNTIME-001",
        "tamamlandi",
    )

    assert (
        sonuc.aktarim_durumu
        ==
        "aktarildi"
    )

    assert (
        kopru.getir(
            "RUNTIME-001"
        ).durum
        ==
        "hazir"
    )
