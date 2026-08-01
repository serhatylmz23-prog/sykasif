from syk_core.entegrasyon.core_olay_koprusu import (
    CoreOlayKoprusu,
)


def test_olay_koprusu_baslatilir():

    kopru = CoreOlayKoprusu()

    sonuc = kopru.olay_baslat(
        "OLAY-001"
    )

    assert (
        sonuc.olay_kimligi
        ==
        "OLAY-001"
    )


def test_core_katmanlari_baglanir():

    kopru = CoreOlayKoprusu()

    kopru.olay_baslat(
        "OLAY-002"
    )

    kopru.kanit_bagla(
        "OLAY-002",
        "KANIT-001",
    )

    kopru.goruntu_bagla(
        "OLAY-002",
        "GOR-001",
    )

    kopru.materyal_bagla(
        "OLAY-002",
        "MAT-001",
    )

    kopru.konsensus_bagla(
        "OLAY-002",
        "KON-001",
    )

    sonuc = kopru.getir(
        "OLAY-002"
    )

    assert len(
        sonuc.kanit_kaydi
    ) == 1

    assert len(
        sonuc.goruntu_kaydi
    ) == 1

    assert len(
        sonuc.materyal_kaydi
    ) == 1

    assert len(
        sonuc.konsensus_kaydi
    ) == 1


def test_olay_tamamlanir():

    kopru = CoreOlayKoprusu()

    kopru.olay_baslat(
        "OLAY-003"
    )

    kopru.tamamla(
        "OLAY-003"
    )

    assert (
        kopru.getir(
            "OLAY-003"
        ).durum
        ==
        "hazir"
    )
