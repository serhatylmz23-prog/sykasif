from datetime import UTC, datetime, timedelta
from decimal import Decimal

from syk_finans_otagi.finans_uyari_ogrenme import (
    AlarmKurali,
    AlarmTekrarEngelleyici,
    AlarmTuru,
    AlarmYonelimi,
    FinansArastirmaArgeMotoru,
    KararBasariMotoru,
    KaynakGuvenOgrenmeMotoru,
    OneriSonucu,
    SyFinansAlarmMotoru,
)


ZAMAN = datetime(
    2026,
    8,
    4,
    10,
    0,
    tzinfo=UTC,
)


def test_fiyat_alarm_esigi_gecilince_olay_uretilir():
    motor = SyFinansAlarmMotoru()

    kural = AlarmKurali(
        alarm_id="ASELS-450",
        alarm_turu=AlarmTuru.FIYAT,
        sembol="ASELS",
        hedef_deger=Decimal("450"),
        yonelim=AlarmYonelimi.YUKARI,
    )

    olay = motor.fiyat_alarm_degerlendir(
        kural=kural,
        guncel_fiyat="451",
        zaman=ZAMAN.isoformat(),
    )

    assert olay is not None
    assert olay.sembol == "ASELS"
    assert len(
        olay.kanit_sha256
    ) == 64


def test_ayni_alarm_bekleme_suresinde_tekrarlanmaz():
    engelleyici = AlarmTekrarEngelleyici()

    motor = SyFinansAlarmMotoru(
        tekrar_engelleyici=engelleyici
    )

    kural = AlarmKurali(
        alarm_id="ASELS-300",
        alarm_turu=AlarmTuru.KADEME,
        sembol="ASELS",
        hedef_deger=Decimal("300"),
        yonelim=AlarmYonelimi.ASAGI,
        tekrar_bekleme_saniyesi=300,
    )

    ilk = motor.fiyat_alarm_degerlendir(
        kural=kural,
        guncel_fiyat=299,
        zaman=ZAMAN.isoformat(),
    )

    ikinci = motor.fiyat_alarm_degerlendir(
        kural=kural,
        guncel_fiyat=298,
        zaman=(
            ZAMAN
            + timedelta(seconds=60)
        ).isoformat(),
    )

    assert ilk is not None
    assert ikinci is None


def test_kritik_kap_bildirimi_alarm_uretir():
    motor = SyFinansAlarmMotoru()

    olay = motor.kap_alarm_degerlendir(
        bildirim_id="KAP-001",
        sembol="ASELS",
        baslik="Önemli sözleşme bildirimi",
        onem="kritik",
        bildirim_sha256="a" * 64,
        zaman=ZAMAN.isoformat(),
    )

    assert olay is not None
    assert (
        olay.alarm_turu
        == AlarmTuru.KAP
    )


def test_kaynak_kesintisi_alarm_uretir():
    motor = SyFinansAlarmMotoru()

    olay = (
        motor
        .kaynak_kesinti_alarm_degerlendir(
            saglayici_id="bist-a",
            durum="erisilemiyor",
            son_hata="Zaman aşımı",
            zaman=ZAMAN.isoformat(),
        )
    )

    assert olay is not None
    assert (
        olay.alarm_turu
        == AlarmTuru.KAYNAK_KESINTISI
    )


def test_karar_basari_kaydi_acilir_ve_kapanir():
    motor = KararBasariMotoru()

    acik = motor.karar_ac(
        karar_id="KARAR-001",
        sembol="ASELS",
        karar_turu="alim",
        baslangic_fiyati=300,
        hedef_fiyat=330,
        kanit_puani=88,
        guven_puani=84,
        zaman=ZAMAN.isoformat(),
    )

    kapanmis = motor.karar_kapat(
        kayit=acik,
        sonuc_fiyati=330,
        basari_esigi_yuzde=5,
        zaman=(
            ZAMAN
            + timedelta(days=30)
        ).isoformat(),
    )

    assert (
        kapanmis.sonuc
        == OneriSonucu.BASARILI
    )

    assert (
        kapanmis.getiri_orani
        == 10.0
    )


def test_gecmis_karar_basari_orani_hesaplanir():
    motor = KararBasariMotoru()

    kayitlar = []

    for sira, sonuc_fiyati in enumerate(
        (
            330,
            315,
            280,
        ),
        start=1,
    ):
        acik = motor.karar_ac(
            karar_id=f"KARAR-{sira}",
            sembol="ASELS",
            karar_turu="alim",
            baslangic_fiyati=300,
            hedef_fiyat=330,
            kanit_puani=80,
            guven_puani=80,
        )

        kayitlar.append(
            motor.karar_kapat(
                kayit=acik,
                sonuc_fiyati=sonuc_fiyati,
                basari_esigi_yuzde=5,
            )
        )

    ozet = motor.basari_ozeti(
        kayitlar
    )

    assert (
        ozet["kapanan_karar"]
        == 3
    )

    assert len(
        ozet["ozet_sha256"]
    ) == 64


def test_kaynak_guven_puani_sonuclara_gore_guncellenir():
    motor = (
        KaynakGuvenOgrenmeMotoru()
    )

    sonuc = motor.guncelle(
        saglayici_id="bist-a",
        toplam_istek=100,
        basarili_istek=98,
        hatali_istek=2,
        tutarli_veri=95,
        tutarsiz_veri=5,
        onceki_guven_puani=85,
    )

    assert (
        sonuc.yeni_guven_puani
        > 85
    )

    assert len(
        sonuc.kayit_sha256
    ) == 64


def test_zayif_kaynak_icin_arastirma_onerisi_uretilir():
    motor = FinansArastirmaArgeMotoru()

    oneriler = motor.oneriler_uret(
        kaynak_durumlari=[
            {
                "saglayici_id": "tefas",
                "durum": "erisilemiyor",
                "basari_orani": 45.0,
            }
        ]
    )

    assert len(
        oneriler
    ) == 1

    assert (
        oneriler[0].kategori
        == "veri_kaynagi"
    )

    assert (
        oneriler[0]
        .kullanici_onayi_gerekli
    )


def test_dusuk_karar_basarisi_arge_onerisi_uretir():
    motor = FinansArastirmaArgeMotoru()

    oneriler = motor.oneriler_uret(
        karar_basari_ozeti={
            "kapanan_karar": 10,
            "basari_orani": 45.0,
        }
    )

    assert any(
        oneri.kategori
        == "karar_modeli"
        for oneri in oneriler
    )


def test_portfoy_yogunlasmasi_risk_onerisi_uretir():
    motor = FinansArastirmaArgeMotoru()

    oneriler = motor.oneriler_uret(
        portfoy_ozeti={
            "en_yuksek_varlik_orani": 55.0,
        }
    )

    assert any(
        oneri.kategori
        == "portfoy_riski"
        for oneri in oneriler
    )