from syk_finans_otagi.modeller import (
    VarlikTuru,
    YatirimKosulu,
)
from syk_finans_otagi.portfoy_analizi import (
    Kanit,
    PortfoyAnalizMotoru,
    VarlikAdayi,
)


def kanitlar(
    taban: float,
):
    return tuple(
        Kanit(
            kanit_id=f"K-{sira}",
            baslik=baslik,
            deger=min(
                100,
                taban + sira,
            ),
            agirlik=agirlik,
            kaynak=kaynak,
            guncellik=(
                "2026-08-03T21:00:00+03:00"
            ),
            olumlu=True,
            aciklama=baslik,
        )
        for sira, (
            baslik,
            agirlik,
            kaynak,
        ) in enumerate(
            [
                (
                    "KAP değerlendirmesi",
                    1.0,
                    "KAP",
                ),
                (
                    "Mali tablolar",
                    1.0,
                    "Şirket raporu",
                ),
                (
                    "Teknik görünüm",
                    0.8,
                    "Piyasa verisi",
                ),
                (
                    "Fon hareketi",
                    0.7,
                    "Fon verisi",
                ),
                (
                    "Sektör görünümü",
                    0.7,
                    "Sektör raporu",
                ),
                (
                    "Uzman görüş birliği",
                    0.5,
                    "Uzman havuzu",
                ),
            ],
            start=1,
        )
    )


def aday(
    sembol: str,
    sektor: str,
    puan: float,
    risk: float,
    *,
    agirlik: float = 0,
):
    return VarlikAdayi(
        sembol=sembol,
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        sektor=sektor,
        mevcut_fiyat=100,
        kanitlar=kanitlar(
            puan
        ),
        risk_puani=risk,
        mevcut_portfoyde=(
            agirlik > 0
        ),
        mevcut_agirlik=agirlik,
    )


def test_guven_ve_kanit_puani_uretilir():
    varlik = aday(
        "ASELS",
        "savunma",
        82,
        30,
    )

    assert varlik.kanit_gucu > 60
    assert varlik.guven_endeksi > 60
    assert varlik.karar in {
        "olumlu_aday",
        "izle",
    }


def test_en_fazla_yedi_aday_secilir():
    adaylar = [
        aday(
            f"SYK{sira}",
            f"sektor-{sira}",
            70 + sira,
            35,
        )
        for sira in range(
            10
        )
    ]

    sonuc = (
        PortfoyAnalizMotoru
        .degerlendir(
            toplam_butce=100_000,
            yatirim_kosulu=(
                YatirimKosulu
                .KASIF_ONERISI
            ),
            adaylar=adaylar,
            maksimum_aday=7,
        )
    )

    assert len(
        sonuc.secilenler
    ) == 7

    assert len(
        sonuc.degerlendirme_sha256
    ) == 64


def test_sektor_yogunlasmasi_sinirlanir():
    adaylar = [
        aday(
            "BANK1",
            "banka",
            90,
            25,
        ),
        aday(
            "BANK2",
            "banka",
            89,
            25,
        ),
        aday(
            "BANK3",
            "banka",
            88,
            25,
        ),
        aday(
            "SAV1",
            "savunma",
            85,
            30,
        ),
    ]

    sonuc = (
        PortfoyAnalizMotoru
        .degerlendir(
            toplam_butce=50_000,
            yatirim_kosulu=(
                YatirimKosulu
                .KASIF_ONERISI
            ),
            adaylar=adaylar,
            maksimum_aday=3,
        )
    )

    banka_sayisi = sum(
        aday.sektor == "banka"
        for aday in sonuc.secilenler
    )

    assert banka_sayisi <= 2


def test_mevcut_yuksek_agirlik_ceza_alir():
    normal = aday(
        "ASELS",
        "savunma",
        85,
        30,
    )

    yogun = aday(
        "ASELS",
        "savunma",
        85,
        30,
        agirlik=45,
    )

    assert (
        yogun.guven_endeksi
        < normal.guven_endeksi
    )

    assert (
        yogun.yogunlasma_cezasi
        > 0
    )


def test_portfoy_yogunlasma_uyarisi_uretilir():
    sonuc = (
        PortfoyAnalizMotoru
        .degerlendir(
            toplam_butce=100_000,
            yatirim_kosulu=(
                YatirimKosulu.SERBEST
            ),
            adaylar=[
                aday(
                    "ASELS",
                    "savunma",
                    88,
                    30,
                    agirlik=35,
                ),
                aday(
                    "THYAO",
                    "havacilik",
                    84,
                    35,
                ),
            ],
            maksimum_aday=2,
        )
    )

    assert any(
        "yoğunlaşması yüksek"
        in uyari
        for uyari
        in sonuc.portfoy_uyarilari
    )


def test_nihai_karar_kullaniciya_birakilir():
    sonuc = (
        PortfoyAnalizMotoru
        .degerlendir(
            toplam_butce=25_000,
            yatirim_kosulu=(
                YatirimKosulu
                .KENDI_SECIMI
            ),
            adaylar=[
                aday(
                    "FON1",
                    "fon",
                    80,
                    25,
                )
            ],
            maksimum_aday=1,
        )
    )

    veri = sonuc.as_dict()

    assert (
        veri["karar_yetkisi"]
        == "Nihai karar kullanıcıya aittir."
    )