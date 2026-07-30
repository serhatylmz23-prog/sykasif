from pathlib import Path

import pytest

from syk_simulasyon.runtime_hesap_deposu import (
    HesapDeposuHatasi,
    RuntimeHesapDeposu,
)


class TestKoruyucusu:
    ON_EK = b"TEST-KORUMALI:"

    def koru(self, veri: bytes) -> bytes:
        return self.ON_EK + veri[::-1]

    def ac(self, veri: bytes) -> bytes:
        if not veri.startswith(self.ON_EK):
            raise ValueError(
                "Korumali veri gecersiz."
            )

        return veri[
            len(self.ON_EK):
        ][::-1]


def _depo(tmp_path: Path) -> RuntimeHesapDeposu:
    return RuntimeHesapDeposu(
        tmp_path / "guvenlik" / "hesaplar.db",
        koruyucu=TestKoruyucusu(),
    )


def test_hesap_deposu_proje_disinda_verilen_yolu_kullanir(
    tmp_path,
):
    depo = _depo(tmp_path)

    assert depo.yol == (
        tmp_path
        / "guvenlik"
        / "hesaplar.db"
    )
    assert depo.yol.exists()


def test_ilk_hesaptan_once_depo_bostur(tmp_path):
    depo = _depo(tmp_path)

    assert not depo.hesap_var_mi()


def test_kurucu_hesabi_olusturulur(tmp_path):
    depo = _depo(tmp_path)

    hesap = depo.hesap_olustur(
        kullanici_adi="kurucu",
        eposta="kurucu@example.test",
        telefon="+905551112233",
        parola="yalnizca-test-parolasi",
        rol="kurucu",
        hizli_giris_etkin=True,
        tur_sayisi=100_000,
    )

    assert hesap.kullanici_adi == "kurucu"
    assert hesap.rol == "kurucu"
    assert hesap.hizli_giris_etkin
    assert depo.hesap_var_mi()


@pytest.mark.parametrize(
    "kimlik",
    (
        "kurucu",
        "kurucu@example.test",
        "+905551112233",
    ),
)
def test_kullanici_adi_eposta_ve_telefonla_hesap_bulunur(
    tmp_path,
    kimlik,
):
    depo = _depo(tmp_path)

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        eposta="kurucu@example.test",
        telefon="+905551112233",
        parola="yalnizca-test-parolasi",
        tur_sayisi=100_000,
    )

    hesap = depo.kimlikle_hesap_bul(
        kimlik
    )

    assert hesap is not None
    assert hesap.kullanici_adi == "kurucu"


def test_dogru_parola_hesabi_dogrular(tmp_path):
    depo = _depo(tmp_path)

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola="yalnizca-test-parolasi",
        tur_sayisi=100_000,
    )

    hesap = depo.kimlik_dogrula(
        "kurucu",
        "yalnizca-test-parolasi",
    )

    assert hesap is not None


def test_yanlis_parola_reddedilir(tmp_path):
    depo = _depo(tmp_path)

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola="yalnizca-test-parolasi",
        tur_sayisi=100_000,
    )

    assert (
        depo.kimlik_dogrula(
            "kurucu",
            "yanlis-parola",
        )
        is None
    )


def test_duz_parola_veritabaninda_saklanmaz(tmp_path):
    depo = _depo(tmp_path)

    parola = "yalnizca-test-parolasi"

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola=parola,
        tur_sayisi=100_000,
    )

    ham = depo.yol.read_bytes()

    assert parola.encode("utf-8") not in ham


def test_ayni_kullanici_ikinci_kez_olusturulamaz(tmp_path):
    depo = _depo(tmp_path)

    depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola="birinci-parola",
        tur_sayisi=100_000,
    )

    with pytest.raises(HesapDeposuHatasi):
        depo.hesap_olustur(
            kullanici_adi="kurucu",
            parola="ikinci-parola",
            tur_sayisi=100_000,
        )


def test_hizli_giris_tercihi_degistirilir(tmp_path):
    depo = _depo(tmp_path)

    hesap = depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola="yalnizca-test-parolasi",
        tur_sayisi=100_000,
    )

    depo.hizli_giris_ayarla(
        hesap.hesap_kimligi,
        True,
    )

    guncel = depo.hesap_getir(
        hesap.hesap_kimligi
    )

    assert guncel is not None
    assert guncel.hizli_giris_etkin


def test_taninmis_cihaz_anahtari_korumali_saklanir(
    tmp_path,
):
    depo = _depo(tmp_path)

    hesap = depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola="yalnizca-test-parolasi",
        tur_sayisi=100_000,
    )

    anahtar = bytes(range(1, 33))

    cihaz = depo.cihaz_tanit(
        hesap_kimligi=hesap.hesap_kimligi,
        cihaz_kimligi="cihaz-1",
        cihaz_anahtari=anahtar,
    )

    ham = depo.yol.read_bytes()

    assert anahtar not in ham
    assert depo.cihaz_dogrula(
        hesap_kimligi=hesap.hesap_kimligi,
        cihaz_kimligi=cihaz.cihaz_kimligi,
        cihaz_anahtari=anahtar,
    )


def test_iptal_edilen_cihaz_hizli_giriste_kullanilamaz(
    tmp_path,
):
    depo = _depo(tmp_path)

    hesap = depo.hesap_olustur(
        kullanici_adi="kurucu",
        parola="yalnizca-test-parolasi",
        tur_sayisi=100_000,
    )

    anahtar = b"b" * 32

    cihaz = depo.cihaz_tanit(
        hesap_kimligi=hesap.hesap_kimligi,
        cihaz_kimligi="cihaz-2",
        cihaz_anahtari=anahtar,
    )

    depo.cihaz_iptal_et(
        cihaz.cihaz_kimligi
    )

    assert not depo.cihaz_dogrula(
        hesap_kimligi=hesap.hesap_kimligi,
        cihaz_kimligi=cihaz.cihaz_kimligi,
        cihaz_anahtari=anahtar,
    )
