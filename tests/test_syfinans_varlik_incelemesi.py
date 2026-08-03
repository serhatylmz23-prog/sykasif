import pytest

from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriGuncelligi,
)
from syk_finans_otagi.portfoy_analizi import (
    Kanit,
    VarlikAdayi,
)
from syk_finans_otagi.varlik_incelemesi import (
    IncelemeBolumu,
    PiyasaDavranisi,
    VarlikIncelemeMotoru,
)


def kanit(
    kimlik: str,
    *,
    olumlu: bool = True,
    deger: float = 85,
    kaynak: str = "KAP",
) -> Kanit:
    return Kanit(
        kanit_id=kimlik,
        baslik=f"Kanıt {kimlik}",
        deger=deger,
        agirlik=1.0,
        kaynak=kaynak,
        guncellik=(
            "2026-08-03T21:00:00+03:00"
        ),
        olumlu=olumlu,
        aciklama="Deneme kanıtı",
    )


def aday() -> VarlikAdayi:
    return VarlikAdayi(
        sembol="ASELS",
        varlik_turu=VarlikTuru.HISSE,
        sektor="savunma",
        mevcut_fiyat=300,
        kanitlar=(
            kanit(
                "KAP",
                kaynak="KAP",
            ),
            kanit(
                "MALI",
                kaynak="Mali tablo",
            ),
            kanit(
                "TEKNIK",
                kaynak="Piyasa",
            ),
            kanit(
                "FON",
                kaynak="Fon akışı",
            ),
            kanit(
                "RISK",
                olumlu=False,
                deger=45,
                kaynak="Risk verisi",
            ),
        ),
        risk_puani=35,
    )


def bolumler():
    return (
        IncelemeBolumu(
            bolum_id="kap",
            baslik="KAP",
            kisa_ozet=(
                "Son açıklamalar incelendi."
            ),
            ayrintili_aciklama=(
                "Şirket bildirimleri ve "
                "yatırım açıklamaları."
            ),
            kanitlar=(
                kanit("KAP-1"),
            ),
            varsayilan_acik=True,
        ),
        IncelemeBolumu(
            bolum_id="grafik",
            baslik="Grafik",
            kisa_ozet=(
                "Trend görünümü olumlu."
            ),
            ayrintili_aciklama=(
                "Fiyat, hacim ve destek "
                "bölgeleri birlikte incelendi."
            ),
            kanitlar=(
                kanit(
                    "GRAFIK-1",
                    kaynak="Piyasa verisi",
                ),
            ),
            goruntuleme_turu="grafik",
        ),
        IncelemeBolumu(
            bolum_id="uzmanlar",
            baslik="Uzman Görüşleri",
            kisa_ozet=(
                "Görüş birliği ölçülü olumlu."
            ),
            ayrintili_aciklama=(
                "Uzmanların geçmiş davranış ve "
                "isabet kayıtları karşılaştırıldı."
            ),
            kanitlar=(
                kanit(
                    "UZMAN-1",
                    kaynak="Uzman havuzu",
                ),
            ),
        ),
    )


def davranis():
    return PiyasaDavranisi(
        hacim_puani=82,
        emir_yogunlugu_puani=78,
        toplama_olasiligi=72,
        dagitma_olasiligi=28,
        baskilama_olasiligi=35,
        sahte_kirilim_riski=30,
        likidite_puani=80,
        oynaklik_puani=40,
        aciklama=(
            "Hacim ve emir davranışı "
            "toplama olasılığını destekliyor."
        ),
    )


def rapor():
    return (
        VarlikIncelemeMotoru
        .olustur(
            aday=aday(),
            bolumler=bolumler(),
            piyasa_davranisi=(
                davranis()
            ),
            veri_guncelligi=(
                VeriGuncelligi.anlik(
                    kaynak=(
                        "Deneme piyasa kaynağı"
                    )
                )
            ),
        )
    )


def test_kisa_gorunum_sade_bilgi_dondurur():
    veri = rapor().kisa_gorunum()

    assert veri["sembol"] == "ASELS"
    assert veri["ayrinti_mevcut"]
    assert "guven_endeksi" in veri
    assert len(
        veri["bolumler"]
    ) == 3

    assert (
        "kanitlar"
        not in veri["bolumler"][0]
    )


def test_ayrintili_gorunum_kanitlari_dondurur():
    veri = (
        rapor()
        .ayrintili_gorunum()
    )

    assert (
        "kanitlar"
        in veri["bolumler"][0]
    )

    assert (
        "ayrintili_yorum"
        in veri["kasif_yorumu"]
    )


def test_kullanici_diledigi_bolumleri_secer():
    veri = (
        rapor()
        .ayrintili_gorunum(
            secilen_bolumler=[
                "kap",
                "grafik",
            ]
        )
    )

    assert [
        bolum["bolum_id"]
        for bolum in veri["bolumler"]
    ] == [
        "kap",
        "grafik",
    ]


def test_piyasa_davranisi_kesin_hukum_vermez():
    veri = (
        davranis()
        .as_dict()
    )

    assert (
        veri["baskin_davranis"]
        == "toplama"
    )

    assert "olasılığıdır" in veri["uyari"]


def test_veri_guncelligi_kisa_ekranda_gorunur():
    veri = rapor().kisa_gorunum()

    assert (
        veri["veri_guncelligi"][
            "durum"
        ]
        == "anlik"
    )

    assert (
        "Anlık"
        in veri["veri_guncelligi"][
            "aciklama"
        ]
    )


def test_rapor_sha256_uretir():
    sonuc = rapor()

    assert len(
        sonuc.rapor_sha256
    ) == 64


def test_gecersiz_bolum_reddedilir():
    with pytest.raises(
        ValueError,
        match="Geçersiz",
    ):
        (
            VarlikIncelemeMotoru
            .olustur(
                aday=aday(),
                bolumler=[
                    IncelemeBolumu(
                        bolum_id="gecersiz",
                        baslik="Geçersiz",
                        kisa_ozet="",
                        ayrintili_aciklama="",
                        kanitlar=(),
                    )
                ],
                piyasa_davranisi=(
                    davranis()
                ),
                veri_guncelligi=(
                    VeriGuncelligi.anlik(
                        kaynak="Deneme"
                    )
                ),
            )
        )