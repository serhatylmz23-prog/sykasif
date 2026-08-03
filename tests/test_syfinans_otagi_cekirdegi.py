from syk_finans_otagi import (
    SyFinansOtagiCekirdegi,
    VarlikTuru,
    VeriGuncelligi,
    YatirimKosulu,
)


def test_kademeli_alim_plani_olusturulur():
    cekirdek = SyFinansOtagiCekirdegi()

    plan = cekirdek.yatirim_plani_olustur(
        sembol="ASELS",
        toplam_butce=100_000,
        referans_fiyat=300,
        fiyatlar=[
            300,
            297,
            293,
            288,
        ],
        dagilim_oranlari=[
            25,
            25,
            25,
            25,
        ],
        yatirim_kosulu=(
            YatirimKosulu.KASIF_ONERISI
        ),
    )

    assert len(
        plan.kademeler
    ) == 4

    assert (
        plan.kademeler[0].fiyat
        == 300
    )

    assert (
        plan.kademeler[0].lot
        == 83
    )

    assert len(
        plan.plan_sha256
    ) == 64


def test_kullanici_kademeyi_gerceklesti_secer():
    cekirdek = SyFinansOtagiCekirdegi()

    plan = cekirdek.yatirim_plani_olustur(
        sembol="ASELS",
        toplam_butce=100_000,
        referans_fiyat=300,
        fiyatlar=[
            300,
            297,
            293,
            288,
        ],
        yatirim_kosulu=(
            YatirimKosulu.SERBEST
        ),
    )

    plan = cekirdek.kademe_durumu_degistir(
        plan.plan_id,
        1,
        gerceklesti=True,
    )

    assert (
        plan.kademeler[0]
        .gerceklesti
    )

    assert (
        plan.kademeler[0]
        .as_dict()["durum_sembolu"]
        == "✓"
    )

    assert plan.gerceklesen_lot > 0
    assert plan.ortalama_maliyet is not None


def test_ortalama_maliyet_gerceklesen_kademelere_gore_hesaplanir():
    cekirdek = SyFinansOtagiCekirdegi()

    plan = cekirdek.yatirim_plani_olustur(
        sembol="ASELS",
        toplam_butce=100_000,
        referans_fiyat=300,
        fiyatlar=[
            300,
            290,
        ],
        dagilim_oranlari=[
            50,
            50,
        ],
        yatirim_kosulu=(
            YatirimKosulu.KENDI_SECIMI
        ),
    )

    plan = cekirdek.kademe_durumu_degistir(
        plan.plan_id,
        1,
        gerceklesti=True,
        gerceklesen_fiyat=299,
    )

    plan = cekirdek.kademe_durumu_degistir(
        plan.plan_id,
        2,
        gerceklesti=True,
        gerceklesen_fiyat=289,
    )

    assert (
        289
        <= float(
            plan.ortalama_maliyet
        )
        <= 299
    )

    assert plan.gerceklesme_orani > 95
    assert plan.basari_orani > 0


def test_portfoy_dunu_ve_bugunu_icin_kayit_tutar():
    cekirdek = SyFinansOtagiCekirdegi()

    cekirdek.portfoye_ekle(
        sembol="ASELS",
        varlik_turu=VarlikTuru.HISSE,
        miktar=10,
        birim_fiyat=250,
        islem_tarihi=(
            "2025-01-10T10:00:00+03:00"
        ),
    )

    cekirdek.portfoye_ekle(
        sembol="ASELS",
        varlik_turu=VarlikTuru.HISSE,
        miktar=20,
        birim_fiyat=300,
        islem_tarihi=(
            "2026-01-10T10:00:00+03:00"
        ),
    )

    ozet = cekirdek.kasa_ozeti(
        "ASELS"
    )

    assert (
        ozet["portfoy"][
            "toplam_miktar"
        ]
        == 30
    )

    assert (
        ozet["portfoy"][
            "ortalama_maliyet"
        ]
        is not None
    )

    assert (
        ozet["portfoy"][
            "ilk_islem_tarihi"
        ]
        == "2025-01-10T10:00:00+03:00"
    )


def test_anlik_veri_bilgisi_kullaniciya_gosterilir():
    cekirdek = SyFinansOtagiCekirdegi()

    durum = VeriGuncelligi.anlik(
        kaynak="Deneme veri kaynağı"
    )

    sonuc = cekirdek.veri_durumu_kaydet(
        "ASELS",
        durum,
    )

    assert sonuc["durum"] == "anlik"
    assert "Anlık" in sonuc["aciklama"]


def test_cevrimdisi_veri_gecikmesi_gosterilir():
    durum = VeriGuncelligi.cevrimdisi(
        kaynak="Son yerel kayıt",
        son_guncelleme=(
            "2026-08-03T20:00:00+03:00"
        ),
        gecikme_saniyesi=60,
    )

    sonuc = durum.as_dict()

    assert not sonuc["internet_var"]
    assert "1.0 dakika" in sonuc["aciklama"]
    assert (
        "Bağlantı geldiğinde yenilenecek"
        in sonuc["aciklama"]
    )