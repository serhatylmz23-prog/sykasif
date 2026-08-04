import json
from decimal import Decimal

import pytest

from syk_finans_otagi.baglanti_calisma_katmani import (
    SonGuvenilirYanitDeposu,
    YanitKaynagi,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from syk_finans_otagi.tefas_fon_bagdastiricisi import (
    TefasFonBagdastiricisi,
    TefasJsonCozumleyici,
)


ORNEK = {
    "data": [
        {
            "fund_code": "FON-A",
            "fund_name": "Örnek Hisse Fonu",
            "price": "2.456789",
            "total_value": "125000000",
            "investor_count": 4500,
            "date": (
                "2026-08-04T18:00:00+03:00"
            ),
            "portfolio_distribution": {
                "Hisse": 70,
                "Tahvil": 20,
                "Nakit": 10,
            },
        },
        {
            "fund_code": "FON-B",
            "fund_name": "Örnek Altın Fonu",
            "price": "5.250000",
            "total_value": "80000000",
            "investor_count": 3200,
            "date": (
                "2026-08-04T18:00:00+03:00"
            ),
            "portfolio_distribution": {
                "Altın": 90,
                "Nakit": 10,
            },
        },
    ]
}


def ham() -> bytes:
    return json.dumps(
        ORNEK,
        ensure_ascii=False,
    ).encode("utf-8")


def test_fon_json_ortak_kayda_donusur():
    fonlar = (
        TefasJsonCozumleyici
        .coz(
            ham()
        )
    )

    assert len(
        fonlar
    ) == 2

    assert (
        fonlar[0].fon_kodu
        == "FON-A"
    )

    assert (
        fonlar[0].birim_fiyat
        == Decimal("2.456789")
    )

    assert (
        fonlar[0].yatirimci_sayisi
        == 4500
    )


def test_portfoy_dagilimi_korunur():
    fon = (
        TefasJsonCozumleyici
        .coz(
            ham()
        )[0]
    )

    assert (
        fon.portfoy_dagilimi[
            "Hisse"
        ]
        == 70
    )

    assert sum(
        fon.portfoy_dagilimi
        .values()
    ) == 100


def test_canli_fon_verisi_depolanir():
    depo = SonGuvenilirYanitDeposu()

    kaynak = TefasFonBagdastiricisi(
        adres=(
            "https://ornek.invalid/fon"
        ),
        depo=depo,
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    )

    sonuc = (
        kaynak
        .fonlari_guvenli_getir()
    )

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.CANLI
    )

    assert not sonuc.cevrimdisi

    assert len(
        sonuc.fonlar
    ) == 2


def test_baglanti_kesilince_son_guvenilir_fonlar_kullanilir():
    depo = SonGuvenilirYanitDeposu()

    canli = TefasFonBagdastiricisi(
        adres=(
            "https://ornek.invalid/fon"
        ),
        depo=depo,
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    )

    canli.fonlari_guvenli_getir(
        fon_kodu="FON-A"
    )

    kesik = TefasFonBagdastiricisi(
        adres=(
            "https://ornek.invalid/fon"
        ),
        depo=depo,
        tasiyici=lambda *args: (
            (_ for _ in ())
            .throw(
                TimeoutError(
                    "Bağlantı yok"
                )
            )
        ),
    )

    sonuc = (
        kesik
        .fonlari_guvenli_getir(
            fon_kodu="FON-A"
        )
    )

    assert sonuc.cevrimdisi

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi
        .SON_GUVENILIR
    )


def test_fon_ortak_piyasa_verisine_donusur():
    kaynak = TefasFonBagdastiricisi(
        adres=(
            "https://ornek.invalid/fon"
        ),
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="FON-A"
    )

    assert (
        sonuc.veri.varlik_turu
        == VarlikTuru.FON
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.GECIKMELI
    )

    assert (
        sonuc.veri.fiyat
        == Decimal("2.456789")
    )

    assert len(
        sonuc.veri.veri_sha256
    ) == 64


def test_api_adresi_yoksa_acik_hata_uretilir(
    monkeypatch,
):
    monkeypatch.delenv(
        "SYFINANS_TEFAS_API_ADRESI",
        raising=False,
    )

    kaynak = TefasFonBagdastiricisi()

    with pytest.raises(
        ConnectionError,
        match="son güvenilir",
    ):
        kaynak.fonlari_guvenli_getir()


def test_bos_fon_listesi_reddedilir():
    with pytest.raises(
        ValueError,
        match="kullanılabilir",
    ):
        TefasJsonCozumleyici.coz(
            {
                "data": []
            }
        )


def test_fon_bulunamazsa_acik_hata_uretilir():
    sonuc = TefasFonBagdastiricisi(
        adres=(
            "https://ornek.invalid/fon"
        ),
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    ).fonlari_guvenli_getir()

    with pytest.raises(
        KeyError,
        match="bulunamadı",
    ):
        sonuc.fon_getir(
            "FON-X"
        )