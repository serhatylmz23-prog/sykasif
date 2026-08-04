from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from syk_core.runtime_hardware_validation import (
    AgNoktasiSonucu,
    DenetimDurumu,
    DenetimTuru,
    GercekSistemDenetleyicisi,
    KomutSonucu,
    SistemDenetimHatasi,
)


class ElleSaat:
    def __init__(self) -> None:
        self.simdi = datetime(
            2026,
            8,
            5,
            3,
            0,
            tzinfo=UTC,
        )

    def oku(self) -> datetime:
        sonuc = self.simdi

        self.simdi += timedelta(
            milliseconds=10
        )

        return sonuc


def komut_sonucu(
    veri,
    *,
    cikis_kodu: int = 0,
    hata: str = "",
) -> KomutSonucu:
    return KomutSonucu(
        komut=("powershell",),
        cikis_kodu=cikis_kodu,
        standart_cikti=(
            json.dumps(
                veri,
                ensure_ascii=False,
            )
            if veri is not None
            else ""
        ),
        hata_ciktisi=hata,
        sure_milisaniye=12.5,
    )


def test_usb_cihazlari_ayristirilir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu(
                [
                    {
                        "InstanceId": (
                            "USB\\VID_1234"
                        ),
                        "FriendlyName": (
                            "SYK Probe"
                        ),
                        "Manufacturer": (
                            "SyKaşif"
                        ),
                        "Status": "OK",
                    }
                ]
            )
        ),
    )

    sonuc = (
        denetleyici
        .usb_cihazlarini_denetle()
    )

    assert (
        sonuc.durum
        is DenetimDurumu.BASARILI
    )

    assert sonuc.kayitlar[0][
        "cihaz_adı"
    ] == "SYK Probe"


def test_usb_komut_hatasi_kaydedilir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu(
                None,
                cikis_kodu=1,
                hata="Get-PnpDevice başarısız.",
            )
        ),
    )

    sonuc = (
        denetleyici
        .usb_cihazlarini_denetle()
    )

    assert (
        sonuc.durum
        is DenetimDurumu.BASARISIZ
    )

    assert "Get-PnpDevice" in (
        sonuc.hata or ""
    )


def test_seri_baglanti_noktasi_ayristirilir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu(
                {
                    "DeviceID": "COM7",
                    "Name": (
                        "USB Serial Device"
                    ),
                    "Manufacturer": (
                        "SyKaşif"
                    ),
                    "PNPDeviceID": (
                        "USB\\VID_5678"
                    ),
                }
            )
        ),
    )

    sonuc = (
        denetleyici
        .seri_baglanti_noktalarini_denetle()
    )

    assert (
        sonuc.durum
        is DenetimDurumu.BASARILI
    )

    assert sonuc.kayitlar[0][
        "bağlantı_noktası"
    ] == "COM7"


def test_seri_nokta_yoksa_kismi_sonuc() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu([])
        ),
    )

    sonuc = (
        denetleyici
        .seri_baglanti_noktalarini_denetle()
    )

    assert (
        sonuc.durum
        is DenetimDurumu.KISMI
    )


def test_ag_arayuzu_ayristirilir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu(
                [
                    {
                        "Name": "Wi-Fi",
                        "Status": "Up",
                        "MacAddress": (
                            "AA-BB-CC-DD-EE-FF"
                        ),
                        "IPAddresses": [
                            "192.168.1.10"
                        ],
                        "Gateway": (
                            "192.168.1.1"
                        ),
                        "DnsServers": [
                            "1.1.1.1"
                        ],
                    }
                ]
            )
        ),
    )

    sonuc = (
        denetleyici
        .ag_arayuzlerini_denetle()
    )

    assert (
        sonuc.durum
        is DenetimDurumu.BASARILI
    )

    assert sonuc.kayitlar[0][
        "etkin"
    ] is True

    assert sonuc.kayitlar[0][
        "ağ_geçidi"
    ] == "192.168.1.1"


def test_kapali_ag_arayuzu_kismi_sonuctur() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu(
                {
                    "Name": "Ethernet",
                    "Status": "Disconnected",
                    "MacAddress": None,
                    "IPAddresses": [],
                    "Gateway": None,
                    "DnsServers": [],
                }
            )
        ),
    )

    sonuc = (
        denetleyici
        .ag_arayuzlerini_denetle()
    )

    assert (
        sonuc.durum
        is DenetimDurumu.KISMI
    )


def test_acik_ag_noktasi_dogrulanir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        yuva_denetleyici=(
            lambda ana_makine, port, _: (
                AgNoktasiSonucu(
                    ana_makine=ana_makine,
                    baglanti_noktasi=port,
                    erisilebilir=True,
                    gecikme_milisaniye=2.4,
                )
            )
        ),
    )

    sonuc = denetleyici.ag_noktasini_denetle(
        ana_makine="127.0.0.1",
        baglanti_noktasi=8013,
    )

    assert (
        sonuc.durum
        is DenetimDurumu.BASARILI
    )

    assert sonuc.kayitlar[0][
        "erişilebilir"
    ] is True


def test_kapali_ag_noktasi_basarisizdir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        yuva_denetleyici=(
            lambda ana_makine, port, _: (
                AgNoktasiSonucu(
                    ana_makine=ana_makine,
                    baglanti_noktasi=port,
                    erisilebilir=False,
                    hata="Bağlantı reddedildi.",
                )
            )
        ),
    )

    sonuc = denetleyici.ag_noktasini_denetle(
        ana_makine="127.0.0.1",
        baglanti_noktasi=65530,
    )

    assert (
        sonuc.durum
        is DenetimDurumu.BASARISIZ
    )


def test_windows_disinda_desteklenmiyor() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Linux",
    )

    usb = (
        denetleyici
        .usb_cihazlarini_denetle()
    )

    assert (
        usb.durum
        is DenetimDurumu.DESTEKLENMIYOR
    )


def test_gecersiz_json_reddedilir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            KomutSonucu(
                komut=("powershell",),
                cikis_kodu=0,
                standart_cikti="JSON-DEGIL",
                hata_ciktisi="",
                sure_milisaniye=1.0,
            )
        ),
    )

    with pytest.raises(
        SistemDenetimHatasi,
        match="geçerli JSON",
    ):
        denetleyici.usb_cihazlarini_denetle()


def test_tum_baglantilar_birlikte_denetlenir() -> None:
    saat = ElleSaat()

    cevaplar = [
        komut_sonucu(
            {
                "InstanceId": (
                    "USB\\VID_1234"
                ),
                "FriendlyName": (
                    "SYK Probe"
                ),
                "Status": "OK",
            }
        ),
        komut_sonucu(
            {
                "DeviceID": "COM7",
                "Name": "USB Serial",
            }
        ),
        komut_sonucu(
            {
                "Name": "Wi-Fi",
                "Status": "Up",
                "IPAddresses": [
                    "192.168.1.10"
                ],
            }
        ),
    ]

    def calistir(_):
        return cevaplar.pop(0)

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=calistir,
        yuva_denetleyici=(
            lambda ana_makine, port, _: (
                AgNoktasiSonucu(
                    ana_makine=ana_makine,
                    baglanti_noktasi=port,
                    erisilebilir=True,
                )
            )
        ),
    )

    sonuc = (
        denetleyici
        .tum_baglantilari_denetle(
            ag_noktalari=[
                (
                    "127.0.0.1",
                    8013,
                )
            ]
        )
    )

    assert sonuc[
        "toplam_denetim_sayısı"
    ] == 4

    assert sonuc[
        "başarısız_denetim_sayısı"
    ] == 0


def test_denetim_kaydi_json_yazilir(
    tmp_path: Path,
) -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu([])
        ),
    )

    denetleyici.usb_cihazlarini_denetle()

    hedef = denetleyici.sonuc_kaydi_yaz(
        tmp_path / "denetim.json"
    )

    veri = json.loads(
        hedef.read_text(
            encoding="utf-8"
        )
    )

    assert veri["sistem"] == "Windows"
    assert len(veri["denetimler"]) == 1


def test_durum_ozeti_turkcedir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu([])
        ),
    )

    denetleyici.usb_cihazlarini_denetle()

    ozet = denetleyici.durum_ozeti()

    assert ozet["windows"] is True

    assert (
        ozet[
            "gerçek_bağlantı_denetimi"
        ]
        == "çalıştırıldı"
    )


def test_denetime_turu_kaydedilir() -> None:
    saat = ElleSaat()

    denetleyici = GercekSistemDenetleyicisi(
        saat=saat.oku,
        sistem_adi="Windows",
        komut_calistirici=lambda _: (
            komut_sonucu([])
        ),
    )

    sonuc = (
        denetleyici
        .usb_cihazlarini_denetle()
    )

    assert (
        sonuc.denetim_turu
        is DenetimTuru.USB
    )
