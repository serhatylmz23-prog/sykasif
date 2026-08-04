import json

import pytest

from syk_finans_otagi.baglanti_calisma_katmani import (
    SonGuvenilirYanitDeposu,
    YanitKaynagi,
)
from syk_finans_otagi.gercek_kaynak_sozlesmeleri import (
    BildirimOnemi,
    KapBildirimDogrulamaMotoru,
)
from syk_finans_otagi.kap_bildirim_bagdastiricisi import (
    KapBildirimBagdastiricisi,
    KapJsonCozumleyici,
)


ORNEK = {
    "items": [
        {
            "id": "KAP-001",
            "symbol": "ASELS",
            "title": "Yeni İş İlişkisi",
            "published_at": (
                "2026-08-03T18:30:00+03:00"
            ),
            "type": (
                "Özel Durum Açıklaması"
            ),
            "summary": (
                "Yeni sözleşme imzalandı."
            ),
            "url": (
                "https://kap.org.tr/"
                "tr/Bildirim/1001"
            ),
        },
        {
            "id": "KAP-002",
            "symbol": "ASELS",
            "title": (
                "Yönetim Kurulu Kararı"
            ),
            "published_at": (
                "2026-08-03T17:00:00+03:00"
            ),
            "type": (
                "Diğer Bildirim"
            ),
            "summary": (
                "Yönetim kurulu kararı."
            ),
            "url": (
                "https://kap.org.tr/"
                "tr/Bildirim/1002"
            ),
        },
    ]
}


def ham() -> bytes:
    return json.dumps(
        ORNEK,
        ensure_ascii=False,
    ).encode("utf-8")


def test_kap_json_ortak_bildirime_donusur():
    bildirimler = (
        KapJsonCozumleyici
        .coz(
            ham()
        )
    )

    assert len(
        bildirimler
    ) == 2

    assert (
        bildirimler[0].sembol
        == "ASELS"
    )

    assert (
        bildirimler[0].dogrulanmis
    )

    assert len(
        bildirimler[0]
        .bildirim_sha256
    ) == 64


def test_yeni_is_iliskisi_onemli_isaretlenir():
    bildirimler = (
        KapJsonCozumleyici
        .coz(
            ham()
        )
    )

    yeni_is = next(
        bildirim
        for bildirim
        in bildirimler
        if bildirim.bildirim_id
        == "KAP-001"
    )

    assert (
        yeni_is.onem
        == BildirimOnemi.ONEMLI
    )


def test_kap_muhru_dogrulanir():
    bildirim = (
        KapJsonCozumleyici
        .coz(
            ham()
        )[0]
    )

    assert (
        KapBildirimDogrulamaMotoru
        .dogrula(
            bildirim
        )
    )


def test_canli_bildirimler_depolanir():
    depo = SonGuvenilirYanitDeposu()

    kaynak = KapBildirimBagdastiricisi(
        adres=(
            "https://ornek.invalid/api"
        ),
        depo=depo,
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    )

    sonuc = (
        kaynak
        .bildirimleri_guvenli_getir(
            sembol="ASELS",
        )
    )

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.CANLI
    )

    assert not sonuc.cevrimdisi

    assert len(
        sonuc.bildirimler
    ) == 2


def test_baglanti_kesilince_son_guvenilir_bildirim_kullanilir():
    depo = SonGuvenilirYanitDeposu()

    canli = KapBildirimBagdastiricisi(
        adres=(
            "https://ornek.invalid/api"
        ),
        depo=depo,
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    )

    canli.bildirimleri_guvenli_getir(
        sembol="ASELS",
    )

    kesik = KapBildirimBagdastiricisi(
        adres=(
            "https://ornek.invalid/api"
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
        .bildirimleri_guvenli_getir(
            sembol="ASELS",
        )
    )

    assert sonuc.cevrimdisi

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi
        .SON_GUVENILIR
    )


def test_api_adresi_yoksa_acik_hata_uretilir(
    monkeypatch,
):
    monkeypatch.delenv(
        "SYFINANS_KAP_API_ADRESI",
        raising=False,
    )

    kaynak = (
        KapBildirimBagdastiricisi()
    )

    with pytest.raises(
        ConnectionError,
        match="son güvenilir",
    ):
        kaynak.bildirimleri_getir(
            sembol="ASELS"
        )


def test_bos_bildirim_listesi_reddedilir():
    with pytest.raises(
        ValueError,
        match="kullanılabilir",
    ):
        KapJsonCozumleyici.coz(
            {
                "items": []
            }
        )