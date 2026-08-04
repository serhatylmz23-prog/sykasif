from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from syk_core.runtime_field_link import (
    terminale_saha_cihazlarini_bagla,
)
from syk_core.runtime_terminal import (
    CanliSunucuAyarlari,
    CanliTerminalSunucusu,
    SyKasifTerminalUygulamasi,
    TerminalUygulamasiAyarlari,
)


def json_istegi(
    adres: str,
    *,
    yontem: str = "GET",
    veri: dict | None = None,
) -> tuple[int, dict]:
    ham_veri = None
    basliklar = {
        "Accept": "application/json",
    }

    if veri is not None:
        ham_veri = json.dumps(
            veri,
            ensure_ascii=False,
        ).encode("utf-8")

        basliklar["Content-Type"] = (
            "application/json; charset=utf-8"
        )

    istek = Request(
        adres,
        data=ham_veri,
        headers=basliklar,
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
                    yanit.read().decode("utf-8")
                ),
            )

    except HTTPError as hata:
        return (
            int(hata.code),
            json.loads(
                hata.read().decode("utf-8")
            ),
        )


def sistem_olustur(
    tmp_path: Path,
):
    varsayilan = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    terminal = SyKasifTerminalUygulamasi(
        ayarlar=TerminalUygulamasiAyarlari(
            ana_makine="127.0.0.1",
            baglanti_noktasi=8614,
            panel_yolu="/terminal",
            panel_veri_yolu="/terminal/veri",
            dis_ag_erisimine_izin_ver=False,
            ana_makine_cihaz_kimligi=(
                varsayilan
                .ana_makine_cihaz_kimligi
            ),
            sykasif_uygulama_kimligi=(
                varsayilan
                .sykasif_uygulama_kimligi
            ),
            sykasif_calistirma_yolu=str(
                tmp_path
            ),
            durum_dosyasi=str(
                tmp_path
                / "canli_saha_terminali.json"
            ),
            yetkili_cihazlar=(
                varsayilan.yetkili_cihazlar
            ),
        )
    )

    kopru = terminale_saha_cihazlarini_bagla(
        terminal,
        ana_gizli_deger=(
            "SPR-008-CANLI-SAHA-GIZLI"
        ),
    )

    sunucu = CanliTerminalSunucusu(
        terminal.uygulama,
        ayarlar=CanliSunucuAyarlari(
            ana_makine="127.0.0.1",
            baglanti_noktasi=0,
            baslama_zaman_asimi_saniye=10,
            durma_zaman_asimi_saniye=10,
            gunluk_seviyesi="warning",
            erisim_gunlugu=False,
        ),
    )

    return terminal, kopru, sunucu


def eslestir(
    ana_adres: str,
) -> tuple[str, str]:
    durum, baslangic = json_istegi(
        ana_adres
        + "/saha-cihazlari/eslestirme",
        yontem="POST",
        veri={
            "cihaz_kimliği": "SAMSUNG-TABLET",
            "cihaz_adı": (
                "Samsung Ana Saha Terminali"
            ),
            "cihaz_türü": "tablet",
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "yerel_ağ_adresi": (
                "192.168.1.20"
            ),
            "yetenekler": [
                "terminal",
                "kamera",
                "konum",
                "bildirim",
            ],
        },
    )

    assert durum == 201

    istek_kimligi = baslangic[
        "eşleştirme"
    ][
        "istek_kimliği"
    ]

    kod = baslangic[
        "tek_kullanımlık_kod"
    ]

    durum, _ = json_istegi(
        ana_adres
        + "/saha-cihazlari/eslestirme/"
        + istek_kimligi
        + "/onayla",
        yontem="POST",
        veri={
            "onaylayan": "Bilge Kaan"
        },
    )

    assert durum == 200

    durum, tamamlanan = json_istegi(
        ana_adres
        + "/saha-cihazlari/eslestirme/"
        + istek_kimligi
        + "/tamamla",
        yontem="POST",
        veri={
            "kod": kod,
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "ağ_adresi": "192.168.1.20",
            "hizmet_noktası": 8014,
        },
    )

    assert durum == 200

    return (
        tamamlanan["cihaz"][
            "cihaz_kimliği"
        ],
        tamamlanan[
            "oturum_anahtarı"
        ],
    )


def test_canli_saha_saglik_yolu(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/saglik"
        )

        assert durum == 200
        assert veri["durum"] == "sağlıklı"


def test_canli_tablet_eslestirilir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        cihaz_kimligi, anahtar = eslestir(
            sunucu.ana_adres
        )

        assert cihaz_kimligi == (
            "SAMSUNG-TABLET"
        )

        assert anahtar


def test_canli_durumda_tablet_bagli_gorunur(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        eslestir(
            sunucu.ana_adres
        )

        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/durum"
        )

        assert durum == 200

        assert veri[
            "durum"
        ][
            "keşif"
        ][
            "bağlı_cihaz_sayısı"
        ] == 1


def test_canli_yanlis_kod_reddedilir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, baslangic = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/eslestirme",
            yontem="POST",
            veri={
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_adı": (
                    "Samsung Ana Saha Terminali"
                ),
                "cihaz_türü": "tablet",
                "cihaz_parmak_izi": (
                    "SAMSUNG-TABLET-PARMAK-IZI"
                ),
            },
        )

        assert durum == 201

        istek_kimligi = baslangic[
            "eşleştirme"
        ][
            "istek_kimliği"
        ]

        durum, _ = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/eslestirme/"
            + istek_kimligi
            + "/onayla",
            yontem="POST",
            veri={
                "onaylayan": "Bilge Kaan"
            },
        )

        assert durum == 200

        durum, _ = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/eslestirme/"
            + istek_kimligi
            + "/tamamla",
            yontem="POST",
            veri={
                "kod": "000000",
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_parmak_izi": (
                    "SAMSUNG-TABLET-PARMAK-IZI"
                ),
                "ağ_adresi": (
                    "192.168.1.20"
                ),
                "hizmet_noktası": 8014,
            },
        )

        assert durum == 400


def test_canli_yetkisiz_onay_reddedilir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, baslangic = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/eslestirme",
            yontem="POST",
            veri={
                "cihaz_kimliği": (
                    "IPHONE-8-PLUS"
                ),
                "cihaz_adı": "iPhone 8 Plus",
                "cihaz_türü": "telefon",
                "cihaz_parmak_izi": (
                    "IPHONE-8-PLUS-PARMAK-IZI"
                ),
            },
        )

        assert durum == 201

        istek_kimligi = baslangic[
            "eşleştirme"
        ][
            "istek_kimliği"
        ]

        durum, _ = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/eslestirme/"
            + istek_kimligi
            + "/onayla",
            yontem="POST",
            veri={
                "onaylayan": "işletmen"
            },
        )

        assert durum == 403


def test_canli_sunucu_guvenli_kapanir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    sunucu.baslat()

    durum, _ = json_istegi(
        sunucu.ana_adres
        + "/saha-cihazlari/saglik"
    )

    assert durum == 200

    sunucu.durdur()

    assert not sunucu.calisiyor_mu
