
from syk_simulasyon.arastirma_veri_bankasi import ArastirmaVeriBankasi
from syk_simulasyon.hedef_sicili import (
    FizikselOzellik,
    HedefAilesi,
    HedefAltSinifi,
)
from syk_simulasyon.model import (
    KaynakReferansi,
    SimulasyonKaydi,
    VeriKaynagi,
)


def test_karar_zinciri_degistirilen_kaydi_reddeder():
    banka = ArastirmaVeriBankasi()
    arastirma_id = banka.arastirma_ac("R-01", "A-01")

    karar_id = banka.karar_ekle(
        arastirma_id,
        "ONERI",
        "ilk gerek?e",
        True,
        False,
    )

    assert banka.karar_zincirini_dogrula()

    banka.db.execute(
        """
        UPDATE karar_defteri
        SET gerekce = ?
        WHERE karar_kimligi = ?
        """,
        ("de?i?tirilmi? gerek?e", karar_id),
    )
    banka.db.commit()

    assert not banka.karar_zincirini_dogrula()


def test_hedef_icerik_hashi_ayni_veride_sabittir():
    hedef = HedefAltSinifi(
        hedef_id="HX-91",
        aile=HedefAilesi.MALZEME,
        ad="Test malzemesi",
        ozellikler=[
            FizikselOzellik(
                "iletkenlik",
                1.25,
                "S/m",
                "ZX-17",
            )
        ],
    )

    assert hedef.icerik_sha256() == hedef.icerik_sha256()
    assert len(hedef.icerik_sha256()) == 64


def test_hedef_icerigi_degistiginde_hash_degisir():
    birinci = HedefAltSinifi(
        "HX-91",
        HedefAilesi.MALZEME,
        "Test malzemesi",
        ozellikler=[
            FizikselOzellik(
                "iletkenlik",
                1.25,
                "S/m",
                "ZX-17",
            )
        ],
    )

    ikinci = HedefAltSinifi(
        "HX-91",
        HedefAilesi.MALZEME,
        "Test malzemesi",
        ozellikler=[
            FizikselOzellik(
                "iletkenlik",
                1.50,
                "S/m",
                "ZX-17",
            )
        ],
    )

    assert birinci.icerik_sha256() != ikinci.icerik_sha256()


def test_simulasyon_ozeti_degistiginde_hash_degisir():
    kaynak = KaynakReferansi(
        tur=VeriKaynagi.SIMULASYON,
        kimlik="QX-804",
        guven_puani=0.80,
    )

    birinci = SimulasyonKaydi(
        hedef_sinifi="malzeme",
        derinlik_m=1.00,
        kaynaklar=[kaynak],
        ortam={"nem": 40},
        sensor={"kazanc": 2},
    )

    ikinci = SimulasyonKaydi(
        hedef_sinifi="malzeme",
        derinlik_m=1.00,
        kaynaklar=[kaynak],
        ortam={"nem": 45},
        sensor={"kazanc": 2},
    )

    assert (
        birinci.icerik_ozeti_sha256()
        != ikinci.icerik_ozeti_sha256()
    )
