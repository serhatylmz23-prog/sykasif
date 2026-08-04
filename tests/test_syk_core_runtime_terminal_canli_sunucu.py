from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import (
    Request,
    urlopen,
)

import pytest

from syk_core.runtime_terminal import (
    CalismaKipi,
    CanliSunucuAyarlari,
    CanliSunucuHatasi,
    CanliTerminalSunucusu,
    SyKasifTerminalUygulamasi,
    TerminalUygulamasiAyarlari,
    YetkiliCihazAyari,
)


class ElleSaat:
    def __init__(
        self,
        simdi: datetime,
    ) -> None:
        self.simdi = simdi

    def oku(self) -> datetime:
        return self.simdi


def ayarlar_olustur(
    tmp_path: Path,
) -> TerminalUygulamasiAyarlari:
    return TerminalUygulamasiAyarlari(
        calisma_kipi=(
            CalismaKipi.LABORATUVAR
        ),
        ana_makine="127.0.0.1",
        baglanti_noktasi=8014,
        panel_yolu="/terminal",
        panel_veri_yolu="/terminal/veri",
        dis_ag_erisimine_izin_ver=False,
        ana_makine_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        sykasif_uygulama_kimligi=(
            "SYKASIF"
        ),
        sykasif_calistirma_yolu=str(
            tmp_path
        ),
        durum_dosyasi=str(
            tmp_path
            / "canli_terminal_durumu.json"
        ),
        yetkili_cihazlar=(
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "ANA-MASAUSTU"
                ),
                ad="SyKaşif Ana Makine",
                cihaz_turu="masaüstü",
                yetki_seviyesi=(
                    "Kurucu Kaan"
                ),
                cihaz_parmak_izi=(
                    "MASAUSTU-IZI"
                ),
                baslangicta_bagli=True,
            ),
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "SAMSUNG-TABLET"
                ),
                ad=(
                    "Samsung Ana Saha Terminali"
                ),
                cihaz_turu="tablet",
                yetki_seviyesi=(
                    "Bilge Kaan"
                ),
                cihaz_parmak_izi=(
                    "TABLET-IZI"
                ),
                baslangicta_bagli=False,
            ),
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "IPHONE-8-PLUS"
                ),
                ad=(
                    "iPhone Yetkili Yardımcı Terminal"
                ),
                cihaz_turu="telefon",
                yetki_seviyesi="işletmen",
                cihaz_parmak_izi=(
                    "IPHONE-IZI"
                ),
                baslangicta_bagli=False,
            ),
        ),
    )


def sistem_olustur(
    tmp_path: Path,
):
    saat = ElleSaat(
        datetime(
            2026,
            8,
            5,
            2,
            0,
            tzinfo=UTC,
        )
    )

    sistem = SyKasifTerminalUygulamasi(
        ayarlar=ayarlar_olustur(
            tmp_path
        ),
        saat=saat.oku,
    )

    sunucu = CanliTerminalSunucusu(
        sistem.uygulama,
        ayarlar=CanliSunucuAyarlari(
            ana_makine="127.0.0.1",
            baglanti_noktasi=0,
            baslama_zaman_asimi_saniye=10,
            durma_zaman_asimi_saniye=10,
            gunluk_seviyesi="warning",
            erisim_gunlugu=False,
        ),
    )

    return saat, sistem, sunucu


def json_istegi(
    adres: str,
    *,
    yontem: str = "GET",
    veri: dict | None = None,
    basliklar: dict[str, str] | None = None,
) -> tuple[int, dict]:
    ham_veri = None

    birlesik_basliklar = {
        "Accept": "application/json",
    }

    if basliklar:
        birlesik_basliklar.update(
            basliklar
        )

    if veri is not None:
        ham_veri = json.dumps(
            veri,
            ensure_ascii=False,
        ).encode("utf-8")

        birlesik_basliklar[
            "Content-Type"
        ] = "application/json; charset=utf-8"

    istek = Request(
        adres,
        data=ham_veri,
        headers=birlesik_basliklar,
        method=yontem,
    )

    try:
        with urlopen(
            istek,
            timeout=5.0,
        ) as yanit:
            return (
                int(yanit.status),
                json.loads(
                    yanit.read().decode(
                        "utf-8"
                    )
                ),
            )

    except HTTPError as hata:
        return (
            int(hata.code),
            json.loads(
                hata.read().decode(
                    "utf-8"
                )
            ),
        )


def test_canli_sunucu_bos_baglanti_noktasi_secer(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    assert sunucu.baglanti_noktasi == 0

    with sunucu:
        assert (
            sunucu.baglanti_noktasi
            > 0
        )

        assert sunucu.calisiyor_mu
        assert sunucu.saglikli_mi()


def test_canli_saglik_yolu_calisir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/saglik"
        )

        assert durum == 200
        assert veri[
            "başarılı"
        ] is True
        assert veri[
            "durum"
        ] == "sağlıklı"


def test_canli_terminal_paneli_acilir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        with urlopen(
            sunucu.ana_adres
            + "/terminal",
            timeout=5.0,
        ) as yanit:
            html = yanit.read().decode(
                "utf-8"
            )

        assert yanit.status == 200
        assert "SyKaşif Terminali" in html
        assert "Yetkili cihazlar" in html


def test_canli_panel_verisi_alinir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/terminal/veri"
        )

        assert durum == 200
        assert veri[
            "başarılı"
        ] is True

        assert veri[
            "panel"
        ][
            "toplam_cihaz_sayısı"
        ] == 3


def test_canli_tablet_oturumu_acilir(
    tmp_path: Path,
) -> None:
    _, sistem, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/oturumlar/ac",
            yontem="POST",
            veri={
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_parmak_izi": (
                    "TABLET-IZI"
                ),
            },
        )

        assert durum == 201

        assert veri[
            "oturum"
        ][
            "durum"
        ] == "bağlı"

        assert (
            sistem.terminal
            .cihaz_getir(
                "SAMSUNG-TABLET"
            )
            .bagli_mi
        )


def test_canli_yanlis_parmak_izi_reddedilir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/oturumlar/ac",
            yontem="POST",
            veri={
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_parmak_izi": (
                    "YANLIS-IZ"
                ),
            },
        )

        assert durum == 401
        assert veri[
            "başarılı"
        ] is False

        assert "doğrulanamadı" in veri[
            "hata"
        ]


def test_canli_tablet_sykasif_uygulamasini_acar(
    tmp_path: Path,
) -> None:
    _, sistem, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        oturum_durumu, oturum_verisi = (
            json_istegi(
                sunucu.ana_adres
                + "/oturumlar/ac",
                yontem="POST",
                veri={
                    "cihaz_kimliği": (
                        "SAMSUNG-TABLET"
                    ),
                    "cihaz_parmak_izi": (
                        "TABLET-IZI"
                    ),
                },
            )
        )

        assert oturum_durumu == 201

        oturum_kimligi = (
            oturum_verisi[
                "oturum"
            ][
                "oturum_kimliği"
            ]
        )

        komut_durumu, komut_verisi = (
            json_istegi(
                sunucu.ana_adres
                + "/komutlar",
                yontem="POST",
                veri={
                    "oturum_kimliği": (
                        oturum_kimligi
                    ),
                    "hedef_cihaz_kimliği": (
                        "ANA-MASAUSTU"
                    ),
                    "komut_türü": (
                        "uygulamayı_aç"
                    ),
                    "içerik": {
                        "uygulama_kimliği": (
                            "SYKASIF"
                        ),
                    },
                    "gerekçe": (
                        "Canlı laboratuvar doğrulaması"
                    ),
                    "hemen_çalıştır": True,
                },
            )
        )

        assert komut_durumu == 201

        assert komut_verisi[
            "komut"
        ][
            "durum"
        ] == "tamamlandı"

        assert (
            sistem.cihaz_araci
            .uygulama_durumu_getir(
                "SYKASIF"
            )
            .calisiyor_mu
        )


def test_canli_operator_kritik_komut_gonderemez(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        oturum_durumu, oturum_verisi = (
            json_istegi(
                sunucu.ana_adres
                + "/oturumlar/ac",
                yontem="POST",
                veri={
                    "cihaz_kimliği": (
                        "IPHONE-8-PLUS"
                    ),
                    "cihaz_parmak_izi": (
                        "IPHONE-IZI"
                    ),
                },
            )
        )

        assert oturum_durumu == 201

        oturum_kimligi = (
            oturum_verisi[
                "oturum"
            ][
                "oturum_kimliği"
            ]
        )

        komut_durumu, komut_verisi = (
            json_istegi(
                sunucu.ana_adres
                + "/komutlar",
                yontem="POST",
                veri={
                    "oturum_kimliği": (
                        oturum_kimligi
                    ),
                    "hedef_cihaz_kimliği": (
                        "ANA-MASAUSTU"
                    ),
                    "komut_türü": (
                        "masaüstünü_kapat"
                    ),
                    "gerekçe": "Deneme",
                    "onaylayan": (
                        "Bilge Kaan"
                    ),
                },
            )
        )

        assert komut_durumu == 400

        assert "Bilge Kaan" in (
            komut_verisi[
                "hata"
            ]
        )


def test_canli_bilge_kaan_kritik_komut_olusturur(
    tmp_path: Path,
) -> None:
    _, sistem, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        oturum_durumu, oturum_verisi = (
            json_istegi(
                sunucu.ana_adres
                + "/oturumlar/ac",
                yontem="POST",
                veri={
                    "cihaz_kimliği": (
                        "SAMSUNG-TABLET"
                    ),
                    "cihaz_parmak_izi": (
                        "TABLET-IZI"
                    ),
                },
            )
        )

        assert oturum_durumu == 201

        oturum_kimligi = (
            oturum_verisi[
                "oturum"
            ][
                "oturum_kimliği"
            ]
        )

        komut_durumu, komut_verisi = (
            json_istegi(
                sunucu.ana_adres
                + "/komutlar",
                yontem="POST",
                veri={
                    "oturum_kimliği": (
                        oturum_kimligi
                    ),
                    "hedef_cihaz_kimliği": (
                        "ANA-MASAUSTU"
                    ),
                    "komut_türü": (
                        "masaüstünü_kapat"
                    ),
                    "gerekçe": (
                        "Canlı doğrulama işlemi"
                    ),
                    "onaylayan": (
                        "Bilge Kaan"
                    ),
                    "hemen_çalıştır": True,
                },
            )
        )

        assert komut_durumu == 201

        assert komut_verisi[
            "komut"
        ][
            "durum"
        ] == "tamamlandı"

        assert (
            sistem.sistem_isletmeni
            .islem_gecmisi[-1]
            ["gerçek_işlem"]
            is False
        )


def test_canli_sunucu_durunca_lifespan_kapanisi_calisir(
    tmp_path: Path,
) -> None:
    _, sistem, sunucu = sistem_olustur(
        tmp_path
    )

    sunucu.baslat()

    durum, _ = json_istegi(
        sunucu.ana_adres
        + "/oturumlar/ac",
        yontem="POST",
        veri={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "TABLET-IZI"
            ),
        },
    )

    assert durum == 201

    sunucu.durdur()

    assert not sunucu.calisiyor_mu

    oturumlar = (
        sistem.oturum_yoneticisi
        .oturumlari_listele()
    )

    assert len(oturumlar) == 1
    assert oturumlar[0].sona_erdi_mi

    assert (
        sistem.cihaz_araci
        .durum.value
        == "durduruldu"
    )


def test_canli_sunucu_iki_kez_baslatilabilir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    sunucu.baslat()
    sunucu.baslat()

    assert sunucu.calisiyor_mu

    sunucu.durdur()
    sunucu.durdur()

    assert not sunucu.calisiyor_mu


def test_canli_sunucu_durum_ozeti_turkce(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        ozet = sunucu.durum_ozeti()

        assert ozet[
            "çalışıyor_mu"
        ] is True

        assert ozet[
            "sağlıklı_mı"
        ] is True

        assert ozet[
            "bağlantı_noktası"
        ] > 0

        assert ozet[
            "ana_adres"
        ].startswith(
            "http://127.0.0.1:"
        )


def test_gecersiz_canli_sunucu_ayari_reddedilir() -> None:
    with pytest.raises(
        ValueError,
        match="Bağlantı noktası",
    ):
        CanliSunucuAyarlari(
            baglanti_noktasi=70000
        )


def test_canli_sunucu_baglam_yoneticisi_calisir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu as etkin:
        assert etkin is sunucu
        assert etkin.calisiyor_mu
        assert etkin.saglikli_mi()

    assert not sunucu.calisiyor_mu


