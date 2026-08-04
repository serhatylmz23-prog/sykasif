from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
from typing import Any
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.parse import urljoin
from urllib.request import (
    Request,
    build_opener,
    HTTPRedirectHandler,
)


RAPOR_JSON = Path(
    "artifacts/"
    "SYFINANS_TEFAS_RESMI_KAYNAK_INCELEME.json"
)

RAPOR_TXT = Path(
    "artifacts/"
    "SYFINANS_TEFAS_RESMI_KAYNAK_INCELEME.txt"
)

HAM_KLASOR = Path(
    "artifacts/"
    "tefas_resmi_yanitlar"
)

HAM_KLASOR.mkdir(
    parents=True,
    exist_ok=True,
)


ADRESLER = {
    "fon_analiz": (
        "https://www.tefas.gov.tr/"
        "FonAnaliz.aspx"
    ),
    "fon_karsilastirma": (
        "https://www.tefas.gov.tr/"
        "FonKarsilastirma.aspx"
    ),
}


class SayfaInceleyici(
    HTMLParser
):
    def __init__(self) -> None:
        super().__init__()

        self.formlar: list[
            dict[str, Any]
        ] = []

        self.betikler: list[str] = []
        self.baglantilar: list[str] = []
        self.girdiler: list[
            dict[str, str]
        ] = []

        self._aktif_form: (
            dict[str, Any] | None
        ) = None

    def handle_starttag(
        self,
        tag: str,
        attrs,
    ) -> None:
        ozellikler = {
            str(anahtar): (
                ""
                if deger is None
                else str(deger)
            )
            for anahtar, deger
            in attrs
        }

        if tag == "form":
            form = {
                "action": (
                    ozellikler.get(
                        "action",
                        "",
                    )
                ),
                "method": (
                    ozellikler.get(
                        "method",
                        "get",
                    ).lower()
                ),
                "id": ozellikler.get(
                    "id",
                    "",
                ),
                "name": ozellikler.get(
                    "name",
                    "",
                ),
                "girdiler": [],
            }

            self.formlar.append(
                form
            )

            self._aktif_form = form

        elif tag == "input":
            girdi = {
                "name": ozellikler.get(
                    "name",
                    "",
                ),
                "id": ozellikler.get(
                    "id",
                    "",
                ),
                "type": ozellikler.get(
                    "type",
                    "text",
                ),
                "value": ozellikler.get(
                    "value",
                    "",
                ),
            }

            self.girdiler.append(
                girdi
            )

            if (
                self._aktif_form
                is not None
            ):
                self._aktif_form[
                    "girdiler"
                ].append(
                    girdi
                )

        elif tag == "script":
            adres = ozellikler.get(
                "src",
                "",
            )

            if adres:
                self.betikler.append(
                    adres
                )

        elif tag == "a":
            adres = ozellikler.get(
                "href",
                "",
            )

            if adres:
                self.baglantilar.append(
                    adres
                )

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        if tag == "form":
            self._aktif_form = None


def _metin_var_mi(
    metin: str,
    *ifadeler: str,
) -> bool:
    kucuk = metin.casefold()

    return any(
        ifade.casefold()
        in kucuk
        for ifade in ifadeler
    )


def _olasi_veri_adresleri(
    *,
    temel_adres: str,
    html: str,
    inceleme: SayfaInceleyici,
) -> list[str]:
    adaylar: set[str] = set()

    for form in inceleme.formlar:
        action = str(
            form.get(
                "action",
                "",
            )
        ).strip()

        if action:
            adaylar.add(
                urljoin(
                    temel_adres,
                    action,
                )
            )

    for adres in (
        inceleme.betikler
        + inceleme.baglantilar
    ):
        tam_adres = urljoin(
            temel_adres,
            adres,
        )

        kucuk = tam_adres.casefold()

        if any(
            ifade in kucuk
            for ifade in (
                "api",
                "service",
                "ajax",
                "json",
                "fund",
                "fon",
                "data",
            )
        ):
            adaylar.add(
                tam_adres
            )

    desenler = (
        r'["\']([^"\']*'
        r'(?:api|service|ajax|json)'
        r'[^"\']*)["\']',
        r'url\s*:\s*["\']'
        r'([^"\']+)["\']',
    )

    for desen in desenler:
        for eslesme in re.findall(
            desen,
            html,
            flags=re.IGNORECASE,
        ):
            adaylar.add(
                urljoin(
                    temel_adres,
                    eslesme,
                )
            )

    return sorted(
        adaylar
    )


def sayfa_getir(
    *,
    ad: str,
    adres: str,
) -> dict[str, Any]:
    istek = Request(
        adres,
        headers={
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/json;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": (
                "tr-TR,tr;q=0.9,"
                "en;q=0.7"
            ),
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/150.0 Safari/537.36"
            ),
        },
        method="GET",
    )

    baslangic = datetime.now(
        UTC
    )

    sonuc: dict[str, Any] = {
        "ad": ad,
        "istenen_adres": adres,
        "baslangic_zamani": (
            baslangic.isoformat()
        ),
    }

    try:
        opener = build_opener(
            HTTPRedirectHandler()
        )

        with opener.open(
            istek,
            timeout=20,
        ) as yanit:
            ham = yanit.read()

            durum_kodu = int(
                yanit.status
            )

            son_adres = yanit.geturl()

            basliklar = {
                anahtar: deger
                for anahtar, deger
                in yanit.headers.items()
            }

    except HTTPError as error:
        ham = error.read()

        durum_kodu = int(
            error.code
        )

        son_adres = error.geturl()

        basliklar = {
            anahtar: deger
            for anahtar, deger
            in error.headers.items()
        }

        sonuc["http_hatasi"] = str(
            error
        )

    except (
        URLError,
        TimeoutError,
        ssl.SSLError,
    ) as error:
        sonuc.update(
            {
                "durum": (
                    "baglanti_basarisiz"
                ),
                "hata_turu": (
                    type(error).__name__
                ),
                "hata": str(error),
                "bitis_zamani": (
                    datetime.now(
                        UTC
                    ).isoformat()
                ),
            }
        )

        return sonuc

    icerik_turu = basliklar.get(
        "Content-Type",
        "",
    )

    kodlama = "utf-8"

    eslesme = re.search(
        r"charset=([^;\s]+)",
        icerik_turu,
        flags=re.IGNORECASE,
    )

    if eslesme:
        kodlama = eslesme.group(
            1
        ).strip(
            "\"'"
        )

    try:
        metin = ham.decode(
            kodlama,
        )
    except (
        LookupError,
        UnicodeDecodeError,
    ):
        metin = ham.decode(
            "utf-8",
            errors="replace",
        )

    ham_yolu = (
        HAM_KLASOR
        / f"{ad}.html"
    )

    ham_yolu.write_bytes(
        ham
    )

    inceleme = SayfaInceleyici()

    try:
        inceleme.feed(
            metin
        )
    except Exception:
        pass

    erisim_reddi = _metin_var_mi(
        metin,
        "requested url was rejected",
        "access denied",
        "erişim engellendi",
        "support id",
        "forbidden",
    )

    javascript_gerekli = _metin_var_mi(
        metin,
        "enable javascript",
        "javascript is required",
        "javascript'i etkinleştirin",
    )

    olasi_adresler = (
        _olasi_veri_adresleri(
            temel_adres=son_adres,
            html=metin,
            inceleme=inceleme,
        )
    )

    bitis = datetime.now(
        UTC
    )

    sonuc.update(
        {
            "durum": (
                "yanit_alindi"
            ),
            "http_durum_kodu": (
                durum_kodu
            ),
            "son_adres": son_adres,
            "icerik_turu": (
                icerik_turu
            ),
            "yanit_boyutu": len(
                ham
            ),
            "yanit_sha256": sha256(
                ham
            ).hexdigest(),
            "erisim_reddi_algilandi": (
                erisim_reddi
            ),
            "javascript_gerekli": (
                javascript_gerekli
            ),
            "form_sayisi": len(
                inceleme.formlar
            ),
            "betik_sayisi": len(
                inceleme.betikler
            ),
            "baglanti_sayisi": len(
                inceleme.baglantilar
            ),
            "formlar": (
                inceleme.formlar
            ),
            "betikler": sorted(
                set(
                    urljoin(
                        son_adres,
                        adres_degeri,
                    )
                    for adres_degeri
                    in inceleme.betikler
                )
            ),
            "olasi_veri_adresleri": (
                olasi_adresler
            ),
            "ham_yanit_dosyasi": str(
                ham_yolu
            ),
            "bitis_zamani": (
                bitis.isoformat()
            ),
            "gecen_saniye": round(
                (
                    bitis
                    - baslangic
                ).total_seconds(),
                3,
            ),
        }
    )

    return sonuc


sonuclar = [
    sayfa_getir(
        ad=ad,
        adres=adres,
    )
    for ad, adres
    in ADRESLER.items()
]

yanit_alinan = [
    sonuc
    for sonuc in sonuclar
    if sonuc.get(
        "durum"
    ) == "yanit_alindi"
]

erisim_acik = [
    sonuc
    for sonuc in yanit_alinan
    if (
        200
        <= int(
            sonuc.get(
                "http_durum_kodu",
                0,
            )
        )
        < 300
        and not sonuc.get(
            "erisim_reddi_algilandi",
            False,
        )
    )
]

aday_adresler = sorted(
    {
        adres
        for sonuc in sonuclar
        for adres in sonuc.get(
            "olasi_veri_adresleri",
            [],
        )
    }
)

rapor = {
    "schema": (
        "syfinans-tefas-resmi-"
        "kaynak-inceleme/v1"
    ),
    "inceleme_zamani": (
        datetime.now(
            UTC
        ).isoformat()
    ),
    "kaynak": (
        "Takasbank TEFAS resmî sitesi"
    ),
    "sonuclar": sonuclar,
    "yanit_alinan_sayfa_sayisi": len(
        yanit_alinan
    ),
    "dogrudan_erisim_acik_sayfa_sayisi": (
        len(
            erisim_acik
        )
    ),
    "olasi_veri_adresleri": (
        aday_adresler
    ),
    "sonuc": (
        "resmi_sayfa_incelendi"
        if yanit_alinan
        else "resmi_sayfaya_erisim_saglanamadi"
    ),
    "karar": (
        "Belgelendirilmiş ve izinli veri adresi "
        "doğrulanmadan üretim bağlantısı "
        "etkinleştirilmeyecektir."
    ),
}

RAPOR_JSON.write_text(
    json.dumps(
        rapor,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

satirlar = [
    "SYFİNANSOTAĞI TEFAS RESMÎ KAYNAK İNCELEMESİ",
    "",
]

for sonuc in sonuclar:
    satirlar.extend(
        [
            f"SAYFA: {sonuc['ad']}",
            (
                "DURUM: "
                f"{sonuc.get('durum')}"
            ),
            (
                "HTTP: "
                f"{sonuc.get('http_durum_kodu', '-')}"
            ),
            (
                "SON ADRES: "
                f"{sonuc.get('son_adres', '-')}"
            ),
            (
                "İÇERİK TÜRÜ: "
                f"{sonuc.get('icerik_turu', '-')}"
            ),
            (
                "ERİŞİM REDDİ: "
                f"{sonuc.get('erisim_reddi_algilandi', '-')}"
            ),
            (
                "JAVASCRIPT GEREKLİ: "
                f"{sonuc.get('javascript_gerekli', '-')}"
            ),
            (
                "FORM SAYISI: "
                f"{sonuc.get('form_sayisi', 0)}"
            ),
            (
                "OLASI VERİ ADRESİ: "
                f"{len(sonuc.get('olasi_veri_adresleri', []))}"
            ),
            (
                "SHA-256: "
                f"{sonuc.get('yanit_sha256', '-')}"
            ),
            "",
        ]
    )

satirlar.extend(
    [
        "GENEL SONUÇ",
        f"Yanıt alınan sayfa: {len(yanit_alinan)}",
        (
            "Doğrudan erişilebilir sayfa: "
            f"{len(erisim_acik)}"
        ),
        (
            "Olası veri adresi: "
            f"{len(aday_adresler)}"
        ),
        "",
        (
            "KARAR: Belgelendirilmiş ve izinli "
            "veri adresi doğrulanmadan üretim "
            "bağlantısı etkinleştirilmeyecektir."
        ),
    ]
)

RAPOR_TXT.write_text(
    "\n".join(
        satirlar
    )
    + "\n",
    encoding="utf-8",
)

print(
    "TEFAS_RESMI_KAYNAK_INCELEMESI_OK"
)

print(
    "YANIT_ALINAN_SAYFA",
    len(
        yanit_alinan
    ),
)

print(
    "DOGRUDAN_ERISIM_ACIK_SAYFA",
    len(
        erisim_acik
    ),
)

print(
    "OLASI_VERI_ADRESI",
    len(
        aday_adresler
    ),
)

print(
    "RAPOR",
    RAPOR_JSON,
)
