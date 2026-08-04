from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from syk_core.runtime_device_link import (
    TerminalCihazAnahtarlari,
    terminale_cihaz_iletisimini_bagla,
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
            baglanti_noktasi=8414,
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
                / "canli_cihaz_iletisimi.json"
            ),
            yetkili_cihazlar=(
                varsayilan.yetkili_cihazlar
            ),
        )
    )

    kopru = terminale_cihaz_iletisimini_bagla(
        terminal,
        anahtarlar=TerminalCihazAnahtarlari(
            ana_masaustu="MASAUSTU-ANAHTARI",
            samsung_tablet="TABLET-ANAHTARI",
            iphone="IPHONE-ANAHTARI",
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


def tablet_oturumu_ac(
    ana_adres: str,
) -> str:
    durum, veri = json_istegi(
        ana_adres
        + "/cihaz-iletisimi/oturumlar/ac",
        yontem="POST",
        veri={
            "cihaz_kimliği": "SAMSUNG-TABLET",
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "gizli_anahtar": (
                "TABLET-ANAHTARI"
            ),
        },
    )

    assert durum == 201

    return veri[
        "oturum"
    ][
        "oturum_kimliği"
    ]


def test_canli_cihaz_saglik_yolu(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/cihaz-iletisimi/saglik"
        )

        assert durum == 200
        assert veri["durum"] == "sağlıklı"


def test_canli_tablet_oturumu(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        oturum_kimligi = tablet_oturumu_ac(
            sunucu.ana_adres
        )

        assert oturum_kimligi.startswith(
            "SYK-CIHAZ-OTURUM-"
        )


def test_canli_tablet_runtime_durumu_okur(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        oturum_kimligi = tablet_oturumu_ac(
            sunucu.ana_adres
        )

        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/cihaz-iletisimi/komutlar",
            yontem="POST",
            veri={
                "oturum_kimliği": oturum_kimligi,
                "hedef_cihaz_kimliği": (
                    "ANA-MASAUSTU"
                ),
                "işlem_yetkisi": "durum_oku",
                "hemen_çalıştır": True,
            },
        )

        assert durum == 201

        assert veri[
            "komut"
        ][
            "durum"
        ] == "tamamlandı"


def test_canli_tablet_sykasif_acar(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        oturum_kimligi = tablet_oturumu_ac(
            sunucu.ana_adres
        )

        durum, veri = json_istegi(
            sunucu.ana_adres
            + "/cihaz-iletisimi/komutlar",
            yontem="POST",
            veri={
                "oturum_kimliği": oturum_kimligi,
                "hedef_cihaz_kimliği": (
                    "ANA-MASAUSTU"
                ),
                "işlem_yetkisi": "uygulama_aç",
                "içerik": {
                    "uygulama_kimliği": "SYKASIF",
                },
                "hemen_çalıştır": True,
            },
        )

        assert durum == 201

        sonuc = veri[
            "komut"
        ][
            "sonuç"
        ]

        assert sonuc["durum"] == "açıldı"
        assert sonuc["gerçek_işlem"] is False


def test_canli_yanlis_tablet_anahtari_reddedilir(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, _ = json_istegi(
            sunucu.ana_adres
            + "/cihaz-iletisimi/oturumlar/ac",
            yontem="POST",
            veri={
                "cihaz_kimliği": "SAMSUNG-TABLET",
                "cihaz_parmak_izi": (
                    "SAMSUNG-TABLET-PARMAK-IZI"
                ),
                "gizli_anahtar": "YANLIS",
            },
        )

        assert durum == 401


def test_canli_iphone_kritik_komut_gonderemez(
    tmp_path: Path,
) -> None:
    _, _, sunucu = sistem_olustur(
        tmp_path
    )

    with sunucu:
        durum, oturum = json_istegi(
            sunucu.ana_adres
            + "/cihaz-iletisimi/oturumlar/ac",
            yontem="POST",
            veri={
                "cihaz_kimliği": "IPHONE-8-PLUS",
                "cihaz_parmak_izi": (
                    "IPHONE-8-PLUS-PARMAK-IZI"
                ),
                "gizli_anahtar": (
                    "IPHONE-ANAHTARI"
                ),
            },
        )

        assert durum == 201

        oturum_kimligi = oturum[
            "oturum"
        ][
            "oturum_kimliği"
        ]

        durum, _ = json_istegi(
            sunucu.ana_adres
            + "/cihaz-iletisimi/komutlar",
            yontem="POST",
            veri={
                "oturum_kimliği": oturum_kimligi,
                "hedef_cihaz_kimliği": (
                    "ANA-MASAUSTU"
                ),
                "işlem_yetkisi": (
                    "sistemi_durdur"
                ),
                "gerekçe": "Deneme",
                "insan_onayı": "Bilge Kaan",
            },
        )

        assert durum == 403


def test_canli_sunucu_kapanisi_oturumu_sonlandirir(
    tmp_path: Path,
) -> None:
    _, kopru, sunucu = sistem_olustur(
        tmp_path
    )

    sunucu.baslat()

    tablet_oturumu_ac(
        sunucu.ana_adres
    )

    sunucu.durdur()

    oturumlar = (
        kopru.yonetici
        .baglanti
        .oturumlari_listele()
    )

    assert len(oturumlar) == 1
