from syk_simulasyon.olay_omurgasi import OlayTuru
from syk_simulasyon.runtime_durumu import RuntimeDurumTuru
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_servis_guvenli_baslangic_durumu_ile_acilir():
    servis = RuntimeServisi()

    gorunum = servis.gorunum()

    assert gorunum["durum"] == "başlatılıyor"
    assert gorunum["ilerleme_yuzdesi"] == 0.0
    assert gorunum["aktif_modul"] is None


def test_servis_tek_runtime_durumunu_korur():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP",
        ilerleme_yuzdesi=35.0,
    )

    gorunum = servis.gorunum()

    assert gorunum["durum"] == "çalışıyor"
    assert gorunum["aktif_modul"] == "DSP"
    assert gorunum["ilerleme_yuzdesi"] == 35.0


def test_servis_runtime_durumundan_olay_uretir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP",
        ilerleme_yuzdesi=60.0,
    )

    olay = servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0011",
    )

    assert olay.tur == OlayTuru.GOZLEM
    assert olay.ortak_veri["durum"] == "çalışıyor"
    assert olay.ortak_veri["aktif_modul"] == "DSP"
    assert olay.ortak_veri["ilerleme_yuzdesi"] == 60.0
def test_uretilen_olay_gecmise_eklenir():
    servis = RuntimeServisi()

    olay = servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0012",
    )

    assert servis.olay_gecmisi() == (olay,)
    assert servis.son_olay() is olay


def test_olay_gecmisi_disaridan_degistirilemez():
    servis = RuntimeServisi()

    servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0012",
    )

    gecmis = servis.olay_gecmisi()

    assert isinstance(gecmis, tuple)


def test_olay_gecmisi_en_faz_yuz_kayit_tutar():
    servis = RuntimeServisi()

    for sira in range(105):
        servis.olay_uret(
            arastirma_kimligi="SPR002",
            deney_numarasi=f"DSP0012-{sira}",
        )

    gecmis = servis.olay_gecmisi()

    assert len(gecmis) == 100
    assert gecmis[0].deney_numarasi == "DSP0012-5"
    assert gecmis[-1].deney_numarasi == "DSP0012-104"


def test_olay_gecmisi_temizlenebilir():
    servis = RuntimeServisi()

    servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0012",
    )

    servis.olay_gecmisini_temizle()

    assert servis.olay_gecmisi() == ()
    assert servis.son_olay() is None
def test_servis_urettigi_olayi_abonelere_yayinlar():
    servis = RuntimeServisi()
    alinan = []

    servis.bildirim_merkezi.abone_ekle(alinan.append)

    olay = servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0015",
    )

    assert alinan == [olay]
def test_abone_hatasi_olay_uretimini_engellemez():
    servis = RuntimeServisi()

    def hatali_abone(_olay):
        raise RuntimeError("abone hatası")

    servis.bildirim_merkezi.abone_ekle(hatali_abone)

    olay = servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0015",
    )

    assert servis.son_olay() is olay