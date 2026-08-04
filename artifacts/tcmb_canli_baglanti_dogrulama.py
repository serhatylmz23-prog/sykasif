from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
import sys
import traceback

from syk_finans_otagi.tcmb_doviz_bagdastiricisi import (
    TcmbDovizBagdastiricisi,
)


rapor_yolu = Path(
    "artifacts/"
    "SYFINANS_TCMB_CANLI_BAGLANTI_RAPORU.json"
)

metin_rapor_yolu = Path(
    "artifacts/"
    "SYFINANS_TCMB_CANLI_BAGLANTI_RAPORU.txt"
)

bagdastirici = TcmbDovizBagdastiricisi(
    zaman_asimi_saniyesi=15.0,
)

baslangic = datetime.now(
    UTC
)

try:
    sonuc = (
        bagdastirici
        .tum_kurlari_getir()
    )

    usd = sonuc.sembol_getir(
        "USDTRY"
    )

    eur = sonuc.sembol_getir(
        "EURTRY"
    )

    usd_piyasa = (
        bagdastirici
        .piyasa_verisi_getir(
            sembol="USDTRY"
        )
    )

    eur_piyasa = (
        bagdastirici
        .piyasa_verisi_getir(
            sembol="EURTRY"
        )
    )

    assert usd.alis_fiyati > 0
    assert usd.satis_fiyati > 0
    assert eur.alis_fiyati > 0
    assert eur.satis_fiyati > 0

    assert (
        usd.satis_fiyati
        >= usd.alis_fiyati
    )

    assert (
        eur.satis_fiyati
        >= eur.alis_fiyati
    )

    assert len(
        sonuc.yanit_sha256
    ) == 64

    assert len(
        usd_piyasa
        .veri
        .veri_sha256
    ) == 64

    assert len(
        eur_piyasa
        .veri
        .veri_sha256
    ) == 64

    bitis = datetime.now(
        UTC
    )

    rapor = {
        "durum": "basarili",
        "kaynak": sonuc.kaynak,
        "veri_tarihi": (
            sonuc.veri_tarihi
        ),
        "baglanti_adresi": (
            bagdastirici.adres
        ),
        "kayit_sayisi": len(
            sonuc.kayitlar
        ),
        "baslangic_zamani": (
            baslangic.isoformat()
        ),
        "bitis_zamani": (
            bitis.isoformat()
        ),
        "gecen_saniye": round(
            (
                bitis - baslangic
            ).total_seconds(),
            3,
        ),
        "veri_uyarisi": (
            "TCMB gösterge kuru; "
            "doğrudan işlem fiyatı değildir."
        ),
        "usdtry": {
            "alis": str(
                usd.alis_fiyati
            ),
            "satis": str(
                usd.satis_fiyati
            ),
            "orta": str(
                usd.orta_fiyat
            ),
            "veri_durumu": (
                usd_piyasa
                .veri
                .veri_durumu
                .value
            ),
            "gecikme_saniyesi": (
                usd_piyasa
                .veri
                .gecikme_saniyesi
            ),
            "veri_sha256": (
                usd_piyasa
                .veri
                .veri_sha256
            ),
        },
        "eurtry": {
            "alis": str(
                eur.alis_fiyati
            ),
            "satis": str(
                eur.satis_fiyati
            ),
            "orta": str(
                eur.orta_fiyat
            ),
            "veri_durumu": (
                eur_piyasa
                .veri
                .veri_durumu
                .value
            ),
            "gecikme_saniyesi": (
                eur_piyasa
                .veri
                .gecikme_saniyesi
            ),
            "veri_sha256": (
                eur_piyasa
                .veri
                .veri_sha256
            ),
        },
        "yanit_sha256": (
            sonuc.yanit_sha256
        ),
    }

    rapor_yolu.write_text(
        json.dumps(
            rapor,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    metin_rapor_yolu.write_text(
        "\n".join(
            [
                (
                    "SYFİNANSOTAĞI "
                    "TCMB CANLI BAĞLANTI RAPORU"
                ),
                "",
                "DURUM: BAŞARILI",
                (
                    "KAYNAK: "
                    f"{sonuc.kaynak}"
                ),
                (
                    "VERİ TARİHİ: "
                    f"{sonuc.veri_tarihi}"
                ),
                (
                    "KAYIT SAYISI: "
                    f"{len(sonuc.kayitlar)}"
                ),
                "",
                "USD/TRY",
                (
                    "Alış: "
                    f"{usd.alis_fiyati}"
                ),
                (
                    "Satış: "
                    f"{usd.satis_fiyati}"
                ),
                (
                    "Orta: "
                    f"{usd.orta_fiyat}"
                ),
                "",
                "EUR/TRY",
                (
                    "Alış: "
                    f"{eur.alis_fiyati}"
                ),
                (
                    "Satış: "
                    f"{eur.satis_fiyati}"
                ),
                (
                    "Orta: "
                    f"{eur.orta_fiyat}"
                ),
                "",
                (
                    "UYARI: TCMB gösterge "
                    "kurları doğrudan işlem "
                    "fiyatı değildir."
                ),
                "",
                (
                    "YANIT SHA-256: "
                    f"{sonuc.yanit_sha256}"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "TCMB_CANLI_BAGLANTI_OK"
    )

    print(
        "VERI_TARIHI",
        sonuc.veri_tarihi,
    )

    print(
        "KAYIT_SAYISI",
        len(
            sonuc.kayitlar
        ),
    )

    print(
        "USDTRY",
        "ALIS",
        usd.alis_fiyati,
        "SATIS",
        usd.satis_fiyati,
    )

    print(
        "EURTRY",
        "ALIS",
        eur.alis_fiyati,
        "SATIS",
        eur.satis_fiyati,
    )

    print(
        "RAPOR",
        rapor_yolu,
    )

except Exception as error:
    hata = {
        "durum": "basarisiz",
        "kaynak": "TCMB",
        "baglanti_adresi": (
            bagdastirici.adres
        ),
        "zaman": datetime.now(
            UTC
        ).isoformat(),
        "hata_turu": (
            type(error).__name__
        ),
        "hata": str(error),
        "yigin": traceback.format_exc(),
    }

    rapor_yolu.write_text(
        json.dumps(
            hata,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "TCMB_CANLI_BAGLANTI_BASARISIZ"
    )

    print(
        "HATA_TURU",
        type(error).__name__,
    )

    print(
        "HATA",
        error,
    )

    print(
        "RAPOR",
        rapor_yolu,
    )

    sys.exit(1)
