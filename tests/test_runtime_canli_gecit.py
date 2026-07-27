from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_canli_gecit import RuntimeCanliGecit
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi


def _gecit() -> RuntimeCanliGecit:
    servis = RuntimeServisi()

    return RuntimeCanliGecit(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )


def test_abone_eklenebilir():
    gecit = _gecit()

    def abone(_gorunum: dict[str, object]) -> None:
        pass

    gecit.abone_ekle(abone)

    assert gecit.abone_sayisi == 1


def test_gorunum_aboneye_yayinlanir():
    gecit = _gecit()
    alinan: list[dict[str, object]] = []

    gecit.abone_ekle(alinan.append)

    gorunum = gecit.yayinla()

    assert alinan == [gorunum]
    assert gorunum["durum"] == "başlatılıyor"


def test_abone_hatasi_diger_aboneleri_durdurmaz():
    gecit = _gecit()
    alinan: list[dict[str, object]] = []

    def hatali_abone(_gorunum: dict[str, object]) -> None:
        raise RuntimeError("abone hatası")

    gecit.abone_ekle(hatali_abone)
    gecit.abone_ekle(alinan.append)

    gorunum = gecit.yayinla()

    assert alinan == [gorunum]


def test_abone_silinebilir():
    gecit = _gecit()

    def abone(_gorunum: dict[str, object]) -> None:
        pass

    gecit.abone_ekle(abone)
    gecit.abone_sil(abone)

    assert gecit.abone_sayisi == 0