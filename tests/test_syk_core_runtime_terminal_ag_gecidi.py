from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from syk_core.runtime_terminal import (
    AgGecidiAyarlari,
    BildirimTuru,
    CalismaTerminali,
    CihazTuru,
    KomutTuru,
    TerminalAgGecidi,
    TerminalOturumYoneticisi,
    YetkiliCihazTanimi,
    YetkiSeviyesi,
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
            4,
            23,
            0,
            tzinfo=UTC,
        )
    )

    terminal = CalismaTerminali(
        saat=saat.oku
    )

    terminal.cihaz_kaydet(
        YetkiliCihazTanimi(
            cihaz_kimligi="ANA-MASAUSTU",
            ad="SyKaşif Ana Makine",
            cihaz_turu=CihazTuru.MASAUSTU,
            yetki_seviyesi=(
                YetkiSeviyesi.KURUCU_KAAN
            ),
            cihaz_parmak_izi=(
                "MASAUSTU-PARMAK-IZI"
            ),
        )
    )

    terminal.cihaz_bagla(
        "ANA-MASAUSTU",
        cihaz_parmak_izi=(
            "MASAUSTU-PARMAK-IZI"
        ),
    )

    oturum_yoneticisi = (
        TerminalOturumYoneticisi(
            terminal,
            saat=saat.oku,
        )
    )

    gecit = TerminalAgGecidi(
        terminal,
        oturum_yoneticisi,
        saat=saat.oku,
        ayarlar=AgGecidiAyarlari(
            oturum_anahtarini_yanitta_goster=True
        ),
    )

    istemci = TestClient(
        gecit.uygulama
    )

    return (
        saat,
        terminal,
        oturum_yoneticisi,
        gecit,
        istemci,
    )


def tablet_kaydet(
    istemci: TestClient,
):
    return istemci.post(
        "/cihazlar/kaydet",
        json={
            "cihaz_kimliği": "SAMSUNG-TABLET",
            "ad": "Samsung Ana Saha Terminali",
            "cihaz_türü": "tablet",
            "yetki_seviyesi": "Bilge Kaan",
            "cihaz_parmak_izi": (
                "TABLET-PARMAK-IZI"
            ),
        },
    )


def tablet_oturumu_ac(
    istemci: TestClient,
):
    yanit = istemci.post(
        "/oturumlar/ac",
        json={
            "cihaz_kimliği": "SAMSUNG-TABLET",
            "cihaz_parmak_izi": (
                "TABLET-PARMAK-IZI"
            ),
        },
    )

    assert yanit.status_code == 201

    return yanit.json()[
        "oturum"
    ]["oturum_kimliği"]


def test_ana_sayfa_turkce_bilgi_dondurur() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.get("/")

    assert yanit.status_code == 200
    assert yanit.json()["sistem"] == "SyKaşif"
    assert yanit.json()["dil"] == "Türkçe"


def test_saglik_yolu_calisir() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.get("/saglik")

    assert yanit.status_code == 200
    assert yanit.json()["durum"] == "sağlıklı"


def test_yetkili_tablet_kaydedilir() -> None:
    _, terminal, _, _, istemci = (
        sistem_olustur()
    )

    yanit = tablet_kaydet(
        istemci
    )

    assert yanit.status_code == 201
    assert yanit.json()["başarılı"] is True
    assert terminal.cihaz_getir(
        "SAMSUNG-TABLET"
    ).tanim.ad == (
        "Samsung Ana Saha Terminali"
    )


def test_ayni_cihaz_tekrar_kaydedilemez() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    ikinci = tablet_kaydet(istemci)

    assert ikinci.status_code == 400
    assert ikinci.json()["başarılı"] is False
    assert "zaten kayıtlı" in ikinci.json()["hata"]


def test_bilinmeyen_alan_reddedilir() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.post(
        "/cihazlar/kaydet",
        json={
            "cihaz_kimliği": "TABLET",
            "ad": "Tablet",
            "cihaz_türü": "tablet",
            "yetki_seviyesi": "Bilge Kaan",
            "cihaz_parmak_izi": "IZ",
            "bilinmeyen": True,
        },
    )

    assert yanit.status_code == 422


def test_yetkili_cihaz_oturum_acar() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)

    yanit = istemci.post(
        "/oturumlar/ac",
        json={
            "cihaz_kimliği": "SAMSUNG-TABLET",
            "cihaz_parmak_izi": (
                "TABLET-PARMAK-IZI"
            ),
        },
    )

    assert yanit.status_code == 201
    assert yanit.json()["başarılı"] is True
    assert yanit.json()[
        "oturum"
    ]["durum"] == "bağlı"
    assert yanit.json()["oturum_anahtarı"]


def test_yanlis_parmak_izi_oturumu_reddeder() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)

    yanit = istemci.post(
        "/oturumlar/ac",
        json={
            "cihaz_kimliği": "SAMSUNG-TABLET",
            "cihaz_parmak_izi": "YANLIS",
        },
    )

    assert yanit.status_code == 401
    assert "doğrulanamadı" in yanit.json()["hata"]


def test_canlilik_bildirimi_alinir() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.post(
        "/oturumlar/canlilik",
        json={
            "oturum_kimliği": oturum_kimligi,
        },
    )

    assert yanit.status_code == 200
    assert yanit.json()[
        "oturum"
    ]["durum"] == "bağlı"


def test_oturum_olmadan_cihaz_listesi_alinamaz() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.get(
        "/cihazlar",
        headers={
            "X-Oturum-Kimligi": "BILINMEYEN",
        },
    )

    assert yanit.status_code == 401


def test_oturumla_cihaz_listesi_alinir() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.get(
        "/cihazlar",
        headers={
            "X-Oturum-Kimligi": (
                oturum_kimligi
            ),
        },
    )

    assert yanit.status_code == 200
    assert len(yanit.json()["cihazlar"]) == 2


def test_durum_komutu_kuyruga_alinir() -> None:
    _, terminal, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    terminal.isleyici_kaydet(
        KomutTuru.DURUM_ISTE,
        lambda komut: {
            "durum": "hazır",
        },
    )

    yanit = istemci.post(
        "/komutlar",
        json={
            "oturum_kimliği": oturum_kimligi,
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "komut_türü": "durum_iste",
            "hemen_çalıştır": True,
        },
    )

    assert yanit.status_code == 201
    assert yanit.json()[
        "komut"
    ]["durum"] == "tamamlandı"


def test_kritik_komut_insan_onayi_ister() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.post(
        "/komutlar",
        json={
            "oturum_kimliği": oturum_kimligi,
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "komut_türü": (
                "masaüstünü_kapat"
            ),
            "gerekçe": "Saha çıkışı",
        },
    )

    assert yanit.status_code == 400
    assert "insan onayı" in yanit.json()["hata"]


def test_komutlar_listelenir() -> None:
    _, terminal, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    terminal.isleyici_kaydet(
        KomutTuru.DURUM_ISTE,
        lambda komut: {
            "durum": "hazır",
        },
    )

    istemci.post(
        "/komutlar",
        json={
            "oturum_kimliği": oturum_kimligi,
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "komut_türü": "durum_iste",
        },
    )

    yanit = istemci.get(
        "/komutlar",
        headers={
            "X-Oturum-Kimligi": (
                oturum_kimligi
            ),
        },
    )

    assert yanit.status_code == 200
    assert len(yanit.json()["komutlar"]) == 1


def test_bildirim_olusturulur() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.post(
        "/bildirimler",
        json={
            "oturum_kimliği": oturum_kimligi,
            "bildirim_türü": (
                BildirimTuru.YENI_KANIT.value
            ),
            "başlık": "Yeni kanıt",
            "açıklama": (
                "Yeni kanıt incelemeye hazır."
            ),
            "hedef_cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
        },
    )

    assert yanit.status_code == 201
    assert yanit.json()[
        "bildirim"
    ]["başlık"] == "Yeni kanıt"


def test_bildirimler_listelenir() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    istemci.post(
        "/bildirimler",
        json={
            "oturum_kimliği": oturum_kimligi,
            "bildirim_türü": "bilgi",
            "başlık": "Sistem",
            "açıklama": "Terminal hazır.",
        },
    )

    yanit = istemci.get(
        "/bildirimler",
        headers={
            "X-Oturum-Kimligi": (
                oturum_kimligi
            ),
        },
    )

    assert yanit.status_code == 200
    assert len(
        yanit.json()["bildirimler"]
    ) == 1


def test_oturum_kapatilir() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.post(
        "/oturumlar/kapat",
        json={
            "oturum_kimliği": oturum_kimligi,
            "gerekçe": "Kullanıcı çıkışı",
        },
    )

    assert yanit.status_code == 200
    assert yanit.json()[
        "oturum"
    ]["durum"] == "sona_erdi"


def test_kapatilmis_oturumla_islem_yapilamaz() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    istemci.post(
        "/oturumlar/kapat",
        json={
            "oturum_kimliği": oturum_kimligi,
            "gerekçe": "Kullanıcı çıkışı",
        },
    )

    yanit = istemci.get(
        "/cihazlar",
        headers={
            "X-Oturum-Kimligi": (
                oturum_kimligi
            ),
        },
    )

    assert yanit.status_code == 401


def test_istek_gecmisi_tutulur() -> None:
    _, _, _, gecit, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    tablet_oturumu_ac(istemci)

    istekler = gecit.istekleri_listele()

    assert len(istekler) == 2
    assert all(
        istek.durum.value == "işlendi"
        for istek in istekler
    )


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    _, _, _, gecit, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)
    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.get(
        "/durum",
        headers={
            "X-Oturum-Kimligi": (
                oturum_kimligi
            ),
        },
    )

    assert yanit.status_code == 200

    ozet = yanit.json()["durum"]

    assert ozet["ağ_geçidi"] == "hazır"
    assert ozet["toplam_istek_sayısı"] == 2
    assert "terminal" in ozet
    assert "oturumlar" in ozet


def test_ag_olaylari_yayinlanir() -> None:
    _, _, _, gecit, istemci = (
        sistem_olustur()
    )

    tablet_kaydet(istemci)

    konular = [
        olay.topic
        for olay in gecit.olay_hatti.history
    ]

    assert "terminal.ag.istek_alindi" in konular
    assert "terminal.ag.istek_islendi" in konular


def test_aciklama_belgesi_turkce_baslik_tasir() -> None:
    _, _, _, _, istemci = (
        sistem_olustur()
    )

    yanit = istemci.get(
        "/aciklama.json"
    )

    assert yanit.status_code == 200
    assert yanit.json()[
        "info"
    ]["title"] == (
        "SyKaşif Terminal Ağ Geçidi"
    )
