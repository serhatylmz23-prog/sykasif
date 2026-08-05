from __future__ import annotations

from copy import deepcopy
from typing import Any

from terminal_v2.core.runtime_state import runtime_state


MODUL_ADLARI = {
    "dashboard": "Ana Çalışma Alanı",
    "harita": "Harita",
    "kanit": "Kanıt",
    "analiz": "Analiz",
    "rapor": "Rapor",
    "gorev": "Görev",
    "sensorler": "Bilimsel Sensörler",
}

DURUM_METINLERI = {
    "BEKLIYOR": "Bekliyor",
    "CALISIYOR": "Çalışıyor",
    "TARIYOR": "Tarıyor",
    "DOGRULANIYOR": "Doğrulanıyor",
    "TAMAMLANDI": "Tamamlandı",
    "DURDU": "Durdu",
    "CEVRIMDISI": "Çevrimdışı",
    "HATA": "Hata",
}


async def modul_kartlari() -> dict[str, Any]:
    snapshot = await runtime_state.snapshot()
    durum = snapshot["durum"]
    aktif_modul = durum["aktif_modul"]
    kayitli_moduller = durum.get("moduller", {})

    kodlar = list(MODUL_ADLARI)

    for kod in kayitli_moduller:
        if kod not in kodlar:
            kodlar.append(kod)

    kartlar = []

    for kod in kodlar:
        modul = deepcopy(
            kayitli_moduller.get(
                kod,
                {"durum": "BEKLIYOR"},
            )
        )

        durum_kodu = str(
            modul.get("durum", "BEKLIYOR")
        ).upper()

        kartlar.append(
            {
                "kod": kod,
                "ad": MODUL_ADLARI.get(
                    kod,
                    kod.replace("_", " ").title(),
                ),
                "durum_kodu": durum_kodu,
                "durum_metni": DURUM_METINLERI.get(
                    durum_kodu,
                    durum_kodu,
                ),
                "aktif": kod == aktif_modul,
                "ikon_durumu": durum_kodu.lower(),
                "veri": modul,
            }
        )

    return {
        "sonuc": "BASARILI",
        "mesaj": "Canlı modül kartları hazır.",
        "revision": snapshot["revision"],
        "aktif_modul": aktif_modul,
        "kartlar": kartlar,
    }


async def modul_durumunu_degistir(
    *,
    modul_kodu: str,
    durum: str,
    kaynak: str,
) -> dict[str, Any]:
    kod = modul_kodu.strip().lower()
    durum_kodu = durum.strip().upper()

    if not kod:
        raise ValueError("Modül kodu boş olamaz.")

    if durum_kodu not in runtime_state.VALID_STATUSES:
        raise ValueError(
            f"Geçersiz modül durumu: {durum}"
        )

    await runtime_state.update(
        {
            "moduller": {
                kod: {
                    "durum": durum_kodu,
                }
            }
        },
        olay_turu="MODUL_DURUMU_DEGISTI",
        kaynak=kaynak,
    )

    return await modul_kartlari()
