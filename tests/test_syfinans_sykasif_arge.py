from decimal import Decimal

from syk_finans_otagi.sykasif_arge import (
    ArgeDurumu,
    ArgeOneriTuru,
    ArgeVarligi,
    ArgeVarlikTuru,
    FiyatKaydi,
    SyFinansUcKatmanSozlesmesi,
    SyKasifArgeMotoru,
    TedarikciKaydi,
)


def tedarikciler():
    return (
        TedarikciKaydi(
            tedarikci_id="TR-001",
            ad="Türkiye Tedarikçisi A",
            ulke="Türkiye",
            guven_puani=90,
            garanti_puani=85,
            teslimat_puani=80,
            servis_puani=88,
            fiyat_puani=75,
            dogrulanmis_kaynak_sayisi=5,
        ),
        TedarikciKaydi(
            tedarikci_id="TR-002",
            ad="Türkiye Tedarikçisi B",
            ulke="Türkiye",
            guven_puani=75,
            garanti_puani=70,
            teslimat_puani=85,
            servis_puani=72,
            fiyat_puani=90,
            dogrulanmis_kaynak_sayisi=3,
        ),
    )


def varliklar():
    return (
        ArgeVarligi(
            varlik_id="BOBIN-001",
            ad="Geçici saha bobini",
            tur=ArgeVarlikTuru.PARCA,
            kategori="Algılama",
            mevcut_surumu="V2",
            edinme_tarihi="2026-01-10",
            edinme_maliyeti=5000,
            garanti_bitis_tarihi=(
                "2027-01-10"
            ),
            son_bakim_tarihi=(
                "2026-06-01"
            ),
            sonraki_bakim_tarihi=(
                "2026-09-01"
            ),
            performans_puani=42,
            guvenilirlik_puani=48,
            kritik_onem_puani=95,
            uyumluluk_puani=55,
            enerji_verimliligi_puani=60,
            durum=ArgeDurumu.KRITIK,
            fiyat_gecmisi=(
                FiyatKaydi(
                    tarih="2026-01-01",
                    fiyat=5000,
                    para_birimi="TRY",
                    kaynak="Tedarikçi A",
                ),
                FiyatKaydi(
                    tarih="2026-08-01",
                    fiyat=4500,
                    para_birimi="TRY",
                    kaynak="Tedarikçi B",
                ),
            ),
        ),
        ArgeVarligi(
            varlik_id="TABLET-001",
            ad="Saha terminali",
            tur=ArgeVarlikTuru.PARCA,
            kategori="Terminal",
            mevcut_surumu="Tab A 2019",
            edinme_tarihi="2020-01-10",
            edinme_maliyeti=3000,
            garanti_bitis_tarihi=(
                "2022-01-10"
            ),
            son_bakim_tarihi=None,
            sonraki_bakim_tarihi=None,
            performans_puani=65,
            guvenilirlik_puani=70,
            kritik_onem_puani=70,
            uyumluluk_puani=72,
            enerji_verimliligi_puani=58,
            durum=(
                ArgeDurumu.YENILEME_ADAYI
            ),
        ),
    )


def test_ucuncu_katman_ekran_sozlesmesinde_yer_alir():
    sozlesme = (
        SyFinansUcKatmanSozlesmesi
        .ekran_sozlesmesi()
    )

    assert [
        katman["katman_id"]
        for katman
        in sozlesme["katmanlar"]
    ] == [
        "piyasa_evreni",
        "kullanici_kasasi",
        "sykasif_arge",
    ]

    assert (
        sozlesme[
            "finans_fazlasi_argeye_aktarilabilir"
        ]
    )


def test_en_zayif_parca_bulunur():
    sonuc = SyKasifArgeMotoru.degerlendir(
        varliklar=varliklar(),
        tedarikciler=tedarikciler(),
        toplam_arge_butcesi=20_000,
    )

    assert (
        sonuc.en_zayif_varlik_id
        == "BOBIN-001"
    )


def test_kritik_parca_icin_yenileme_onerisi_uretilir():
    sonuc = SyKasifArgeMotoru.degerlendir(
        varliklar=varliklar(),
        tedarikciler=tedarikciler(),
        toplam_arge_butcesi=20_000,
    )

    bobin = next(
        oneri
        for oneri in sonuc.oneriler
        if oneri.varlik_id == "BOBIN-001"
    )

    assert (
        bobin.oneri_turu
        == ArgeOneriTuru.YENILE
    )

    assert (
        bobin.tedarikci_adaylari[0]
        .genel_puan
        >= bobin.tedarikci_adaylari[1]
        .genel_puan
    )


def test_fiyat_gecmisi_degisimi_hesaplanir():
    bobin = varliklar()[0]

    assert (
        bobin.fiyat_degisim_orani
        == -10.0
    )


def test_finans_butce_fazlasi_argeye_eklenir():
    sonuc = SyKasifArgeMotoru.degerlendir(
        varliklar=varliklar(),
        tedarikciler=tedarikciler(),
        toplam_arge_butcesi=20_000,
        finans_butce_fazlasi=15_000,
        asgari_nakit_guvenligi=5_000,
    )

    assert (
        sonuc.kullanilabilir_butce
        == Decimal("30000.00")
    )

    assert any(
        oneri.oneri_turu
        == ArgeOneriTuru.BUTCE_AYIR
        for oneri in sonuc.oneriler
    )


def test_tedarikci_guven_garanti_servis_ve_fiyatla_siralanir():
    sirali = sorted(
        tedarikciler(),
        key=lambda tedarikci: (
            tedarikci.genel_puan
        ),
        reverse=True,
    )

    assert (
        sirali[0].tedarikci_id
        == "TR-001"
    )


def test_nihai_karar_kullaniciya_birakilir():
    sonuc = SyKasifArgeMotoru.degerlendir(
        varliklar=varliklar(),
        tedarikciler=tedarikciler(),
        toplam_arge_butcesi=20_000,
    )

    assert (
        sonuc.as_dict()[
            "karar_yetkisi"
        ]
        == "Nihai karar kullanıcıya aittir."
    )


def test_arge_degerlendirmesi_sha256_uretir():
    sonuc = SyKasifArgeMotoru.degerlendir(
        varliklar=varliklar(),
        tedarikciler=tedarikciler(),
        toplam_arge_butcesi=20_000,
    )

    assert len(
        sonuc.degerlendirme_sha256
    ) == 64