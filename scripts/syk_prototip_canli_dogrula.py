"""SyKaşif birleşik prototip canlı doğrulama komutu."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    kok = Path(__file__).resolve().parents[1]
    kaynak = kok / "src"

    if str(kaynak) not in sys.path:
        sys.path.insert(
            0,
            str(kaynak),
        )

    from syk_core.runtime_prototype import (
        PrototipBaslatmaSecenekleri,
        PrototipBaslaticisi,
        PrototipCanliDogrulayici,
        guvenlik_ayarlari_ortamdan,
        prototip_ayarlari_olustur,
    )

    guvenlik = guvenlik_ayarlari_ortamdan(
        os.environ
    )

    ayarlar = prototip_ayarlari_olustur(
        guvenlik=guvenlik,
        secenekler=(
            PrototipBaslatmaSecenekleri(
                ana_makine="127.0.0.1",
                baglanti_noktasi=0,
                durum_dosyasi=(
                    "artifacts/"
                    "syk_core_parca_009/"
                    "canli_prototip_durumu.json"
                ),
            )
        ),
    )

    dogrulayici = PrototipCanliDogrulayici(
        PrototipBaslaticisi(
            ayarlar=ayarlar
        )
    )

    sonuc = dogrulayici.dogrula()

    print(
        json.dumps(
            sonuc,
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "SYKASIF_BIRLESIK_PROTOTIP_CANLI_DOGRULANDI"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
