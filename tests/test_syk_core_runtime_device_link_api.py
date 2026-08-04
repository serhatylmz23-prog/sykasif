from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_core.runtime_device_link import (
    CihazIletisimAgGecidi,
    CihazYetkisi,
    IslemYetkisi,
    YetkiliCihazKaydi,
    YetkiliCihazYoneticisi,
    cihaz_iletisim_ag_gecidini_bagla,
)


class ElleSaat:
    def __init__(
        self,
        simdi: datetime,
    ) -> None:
        self.simdi = simdi

    def oku(self) -> datetime:
        return self.simdi


def sistem_olustur():
    saat = ElleSaat(
        datetime(
            2026,
            8,
            5,
            3,
            0,
            tzinfo=UTC,
        )
    )

    yonetici = YetkiliCihazYoneticisi(
        saat=saat.oku
    )

    yonetici.cihaz_kaydet(
        YetkiliCihazKaydi(
            cihaz_kimligi="ANA-MASAUSTU",
            cihaz_parmak_izi="MASAUSTU-IZI",
            yetki=CihazYetkisi.KURUCU_KAAN,
            gizli_anahtar="MASAUSTU-ANAHTARI",
        )
    )

    yonetici.cihaz_kaydet(
        YetkiliCihazKaydi(
            cihaz_kimligi="SAMSUNG-TABLET",
            cihaz_parmak_izi="TABLET-IZI",
            yetki=CihazYetkisi.BILGE_KAAN,
            gizli_anahtar="TABLET-ANAHTARI",
        )
    )

    yonetici.cihaz_kaydet(
        YetkiliCihazKaydi(
            cihaz_kimligi="IPHONE-8-PLUS",
            cihaz_parmak_izi="IPHONE-IZI",
            yetki=CihazYetkisi.ISLETMEN,
            gizli_anahtar="IPHONE-ANAHTARI",
        )
    )

    yonetici.isleyici_kaydet(
        IslemYetkisi.DURUM_OKU,
        lambda komut: {
            "durum": "hazır",
            "hedef": (
                komut.hedef_cihaz_kimligi
            ),
        },
    )

    yonetici.isleyici_kaydet(
        IslemYetkisi.UYGULAMA_AC,
        lambda komut: {
            "uygulama": (
                komut.icerik.get(
                    "uygulama"
                )
            ),
            "durum": "açıldı",
        },
    )

    uygulama = FastAPI()

    ag_gecidi = (
        cihaz_iletisim_ag_gecidini_bagla(
            uygulama,
            yonetici,
        )
    )

    istemci = TestClient(
        uygulama
    )

    return (
        saat,
        yonetici,
        ag_gecidi,
        istemci,
    )


def tablet_oturumu_ac(
    istemci: TestClient,
) -> str:
    yanit = istemci.post(
        "/cihaz-iletisimi/oturumlar/ac",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "TABLET-IZI"
            ),
            "gizli_anahtar": (
                "TABLET-ANAHTARI"
            ),
        },
    )

    assert yanit.status_code == 201

    return yanit.json()[
        "oturum"
    ][
        "oturum_kimliği"
    ]


def test_saglik_yolu_calisir() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.get(
        "/cihaz-iletisimi/saglik"
    )

    assert yanit.status_code == 200
    assert yanit.json()["başarılı"]
    assert yanit.json()["durum"] == (
        "sağlıklı"
    )


def test_cihazlar_listelenir() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.get(
        "/cihaz-iletisimi/cihazlar"
    )

    assert yanit.status_code == 200
    assert len(
        yanit.json()["cihazlar"]
    ) == 3


def test_tablet_oturumu_http_uzerinden_acilir() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    oturum_kimligi = (
        tablet_oturumu_ac(
            istemci
        )
    )

    assert oturum_kimligi.startswith(
        "SYK-CIHAZ-OTURUM-"
    )


def test_yanlis_parmak_izi_reddedilir() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.post(
        "/cihaz-iletisimi/oturumlar/ac",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "YANLIS-IZ"
            ),
            "gizli_anahtar": (
                "TABLET-ANAHTARI"
            ),
        },
    )

    assert yanit.status_code == 401


def test_tablet_durum_komutu_gonderir() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    oturum_kimligi = (
        tablet_oturumu_ac(
            istemci
        )
    )

    yanit = istemci.post(
        "/cihaz-iletisimi/komutlar",
        json={
            "oturum_kimliği": (
                oturum_kimligi
            ),
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "işlem_yetkisi": (
                "durum_oku"
            ),
            "hemen_çalıştır": True,
        },
    )

    assert yanit.status_code == 201

    assert yanit.json()[
        "komut"
    ][
        "durum"
    ] == "tamamlandı"


def test_tablet_sykasif_uygulamasini_acar() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    oturum_kimligi = (
        tablet_oturumu_ac(
            istemci
        )
    )

    yanit = istemci.post(
        "/cihaz-iletisimi/komutlar",
        json={
            "oturum_kimliği": (
                oturum_kimligi
            ),
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "işlem_yetkisi": (
                "uygulama_aç"
            ),
            "içerik": {
                "uygulama": "SyKaşif",
            },
            "hemen_çalıştır": True,
        },
    )

    assert yanit.status_code == 201

    assert yanit.json()[
        "komut"
    ][
        "sonuç"
    ][
        "durum"
    ] == "açıldı"


def test_canlilik_yolu_calisir() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    oturum_kimligi = (
        tablet_oturumu_ac(
            istemci
        )
    )

    yanit = istemci.post(
        "/cihaz-iletisimi/canlilik",
        json={
            "oturum_kimliği": (
                oturum_kimligi
            )
        },
    )

    assert yanit.status_code == 200

    assert yanit.json()[
        "oturum"
    ][
        "durum"
    ] == "bağlı"


def test_durum_yolu_turkce_anahtarlar_tasir() -> None:
    _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.get(
        "/cihaz-iletisimi/durum"
    )

    assert yanit.status_code == 200

    assert "kayıtlı_cihaz_sayısı" in (
        yanit.json()["durum"]
    )


def test_ag_gecidi_uygulama_durumuna_kaydedilir() -> None:
    _, _, ag_gecidi, _ = (
        sistem_olustur()
    )

    assert (
        ag_gecidi.uygulama.state
        .cihaz_iletisim_ag_gecidi
        is ag_gecidi
    )


def test_sinif_dogrudan_olusturulabilir() -> None:
    _, yonetici, _, _ = (
        sistem_olustur()
    )

    ag_gecidi = CihazIletisimAgGecidi(
        yonetici
    )

    istemci = TestClient(
        ag_gecidi.uygulama
    )

    yanit = istemci.get(
        "/cihaz-iletisimi/saglik"
    )

    assert yanit.status_code == 200
