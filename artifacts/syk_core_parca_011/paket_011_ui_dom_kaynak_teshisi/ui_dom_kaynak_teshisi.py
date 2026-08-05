from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from playwright.sync_api import sync_playwright


BILIMSEL_MODULLER = (
    "Jeoloji",
    "Astronomi",
    "Arkeoastronomi",
    "Kimyasal Analiz",
    "Spektral Analiz",
    "Termal Analiz",
    "Manyetometre",
    "Gravimetre",
    "Elektrik Direnç",
    "ERT",
    "GPR",
    "Sismik",
    "Hidrojeoloji",
    "Botanik",
    "Toprak Analizi",
    "Su Analizi",
)

TIKLANABILIR_SECICI = ",".join(
    (
        "button",
        "a",
        "[role='button']",
        "[onclick]",
        "[tabindex]",
        "input[type='button']",
        "input[type='submit']",
        "summary",
        "[data-action]",
        "[data-module]",
        "[data-testid]",
        ".button",
        ".btn",
        ".module",
        ".module-card",
        ".menu-item",
        ".nav-item",
        ".tile",
        ".card",
    )
)


def temiz_metin(
    deger: str | None,
) -> str:
    if not deger:
        return ""

    return " ".join(
        deger.split()
    )


def guvenli_attribute(
    locator: Any,
    ad: str,
) -> str | None:
    try:
        return locator.get_attribute(
            ad
        )
    except Exception:
        return None


def element_kaydi(
    locator: Any,
    indeks: int,
) -> dict[str, Any]:
    try:
        metin = temiz_metin(
            locator.inner_text(
                timeout=1000
            )
        )
    except Exception:
        metin = ""

    try:
        tag = locator.evaluate(
            "(element) => element.tagName.toLowerCase()"
        )
    except Exception:
        tag = ""

    try:
        gorunur = locator.is_visible(
            timeout=1000
        )
    except Exception:
        gorunur = False

    try:
        etkin = locator.is_enabled(
            timeout=1000
        )
    except Exception:
        etkin = False

    try:
        html = locator.evaluate(
            "(element) => element.outerHTML"
        )
    except Exception:
        html = ""

    return {
        "indeks": indeks,
        "tag": tag,
        "metin": metin,
        "id": guvenli_attribute(
            locator,
            "id",
        ),
        "class": guvenli_attribute(
            locator,
            "class",
        ),
        "role": guvenli_attribute(
            locator,
            "role",
        ),
        "aria_label": guvenli_attribute(
            locator,
            "aria-label",
        ),
        "href": guvenli_attribute(
            locator,
            "href",
        ),
        "onclick": guvenli_attribute(
            locator,
            "onclick",
        ),
        "tabindex": guvenli_attribute(
            locator,
            "tabindex",
        ),
        "data_action": guvenli_attribute(
            locator,
            "data-action",
        ),
        "data_module": guvenli_attribute(
            locator,
            "data-module",
        ),
        "data_testid": guvenli_attribute(
            locator,
            "data-testid",
        ),
        "gorunur": gorunur,
        "etkin": etkin,
        "outer_html": html[:2000],
    }


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--url",
        required=True,
    )

    parser.add_argument(
        "--json",
        required=True,
    )

    parser.add_argument(
        "--text",
        required=True,
    )

    parser.add_argument(
        "--html",
        required=True,
    )

    parser.add_argument(
        "--screenshot",
        required=True,
    )

    args = parser.parse_args(
        argv
    )

    json_path = Path(
        args.json
    )

    text_path = Path(
        args.text
    )

    html_path = Path(
        args.html
    )

    screenshot_path = Path(
        args.screenshot
    )

    for path in (
        json_path,
        text_path,
        html_path,
        screenshot_path,
    ):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            viewport={
                "width": 1600,
                "height": 1200,
            },
            locale="tr-TR",
        )

        page = context.new_page()

        console_mesajlari: list[
            dict[str, str]
        ] = []

        page_hatalari: list[str] = []

        basarisiz_istekler: list[
            dict[str, Any]
        ] = []

        yanitlar: list[
            dict[str, Any]
        ] = []

        page.on(
            "console",
            lambda mesaj:
                console_mesajlari.append(
                    {
                        "tur": mesaj.type,
                        "metin": mesaj.text,
                    }
                ),
        )

        page.on(
            "pageerror",
            lambda hata:
                page_hatalari.append(
                    str(hata)
                ),
        )

        page.on(
            "requestfailed",
            lambda request:
                basarisiz_istekler.append(
                    {
                        "url": request.url,
                        "method": request.method,
                        "failure": request.failure,
                    }
                ),
        )

        page.on(
            "response",
            lambda response:
                yanitlar.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "content_type": (
                            response.headers.get(
                                "content-type",
                                "",
                            )
                        ),
                    }
                ),
        )

        ana_yanit = page.goto(
            args.url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(
            5000
        )

        html = page.content()

        html_path.write_text(
            html,
            encoding="utf-8",
        )

        page.screenshot(
            path=str(
                screenshot_path
            ),
            full_page=True,
        )

        tum_element_sayisi = page.locator(
            "*"
        ).count()

        body_metni = temiz_metin(
            page.locator(
                "body"
            ).inner_text(
                timeout=5000
            )
        )

        tiklanabilir_locator = page.locator(
            TIKLANABILIR_SECICI
        )

        tiklanabilirler = [
            element_kaydi(
                tiklanabilir_locator.nth(
                    indeks
                ),
                indeks,
            )
            for indeks in range(
                tiklanabilir_locator.count()
            )
        ]

        metin_eslesmeleri: dict[
            str,
            list[dict[str, Any]]
        ] = {}

        for modul in BILIMSEL_MODULLER:
            locator = page.get_by_text(
                modul,
                exact=True,
            )

            kayitlar = []

            for indeks in range(
                locator.count()
            ):
                kayitlar.append(
                    element_kaydi(
                        locator.nth(
                            indeks
                        ),
                        indeks,
                    )
                )

            metin_eslesmeleri[
                modul
            ] = kayitlar

        script_kaynaklari = page.locator(
            "script[src]"
        )

        scriptler = [
            guvenli_attribute(
                script_kaynaklari.nth(
                    indeks
                ),
                "src",
            )
            for indeks in range(
                script_kaynaklari.count()
            )
        ]

        stil_kaynaklari = page.locator(
            "link[rel='stylesheet']"
        )

        stiller = [
            guvenli_attribute(
                stil_kaynaklari.nth(
                    indeks
                ),
                "href",
            )
            for indeks in range(
                stil_kaynaklari.count()
            )
        ]

        iframe_kayitlari = [
            {
                "url": frame.url,
                "name": frame.name,
            }
            for frame in page.frames
        ]

        sonuc = {
            "istenen_url": args.url,
            "son_url": page.url,
            "http_durum": (
                ana_yanit.status
                if ana_yanit
                else None
            ),
            "sayfa_basligi": page.title(),
            "html_uzunlugu": len(html),
            "body_metin_uzunlugu": len(
                body_metni
            ),
            "body_metin_ilk_3000": (
                body_metni[:3000]
            ),
            "tum_element_sayisi": (
                tum_element_sayisi
            ),
            "button_sayisi": (
                page.locator(
                    "button"
                ).count()
            ),
            "link_sayisi": (
                page.locator(
                    "a"
                ).count()
            ),
            "role_button_sayisi": (
                page.locator(
                    "[role='button']"
                ).count()
            ),
            "onclick_sayisi": (
                page.locator(
                    "[onclick]"
                ).count()
            ),
            "tiklanabilir_aday_sayisi": (
                len(
                    tiklanabilirler
                )
            ),
            "tiklanabilir_adaylar": (
                tiklanabilirler
            ),
            "bilimsel_metin_eslesmeleri": (
                metin_eslesmeleri
            ),
            "scriptler": scriptler,
            "stiller": stiller,
            "frameler": iframe_kayitlari,
            "console_mesajlari": (
                console_mesajlari
            ),
            "page_hatalari": page_hatalari,
            "basarisiz_istekler": (
                basarisiz_istekler
            ),
            "http_yanitlari": yanitlar,
        }

        browser.close()

    json_path.write_text(
        json.dumps(
            sonuc,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    satirlar = [
        "SPR-011 PAKET-011",
        "UI DOM VE KAYNAK TESHISI",
        "",
        f"ISTENEN_URL={sonuc['istenen_url']}",
        f"SON_URL={sonuc['son_url']}",
        f"HTTP_DURUM={sonuc['http_durum']}",
        (
            "SAYFA_BASLIGI="
            f"{sonuc['sayfa_basligi']}"
        ),
        (
            "HTML_UZUNLUGU="
            f"{sonuc['html_uzunlugu']}"
        ),
        (
            "BODY_METIN_UZUNLUGU="
            f"{sonuc['body_metin_uzunlugu']}"
        ),
        (
            "TUM_ELEMENT_SAYISI="
            f"{sonuc['tum_element_sayisi']}"
        ),
        (
            "BUTTON_SAYISI="
            f"{sonuc['button_sayisi']}"
        ),
        (
            "LINK_SAYISI="
            f"{sonuc['link_sayisi']}"
        ),
        (
            "ROLE_BUTTON_SAYISI="
            f"{sonuc['role_button_sayisi']}"
        ),
        (
            "ONCLICK_SAYISI="
            f"{sonuc['onclick_sayisi']}"
        ),
        (
            "TIKLANABILIR_ADAY_SAYISI="
            f"{sonuc['tiklanabilir_aday_sayisi']}"
        ),
        (
            "SCRIPT_SAYISI="
            f"{len(sonuc['scriptler'])}"
        ),
        (
            "STIL_SAYISI="
            f"{len(sonuc['stiller'])}"
        ),
        (
            "FRAME_SAYISI="
            f"{len(sonuc['frameler'])}"
        ),
        (
            "PAGE_HATA_SAYISI="
            f"{len(sonuc['page_hatalari'])}"
        ),
        (
            "BASARISIZ_ISTEK_SAYISI="
            f"{len(sonuc['basarisiz_istekler'])}"
        ),
        "",
        "=== BODY METNI ===",
        sonuc["body_metin_ilk_3000"],
        "",
        "=== TIKLANABILIR ADAYLAR ===",
    ]

    for kayit in tiklanabilirler:
        satirlar.append(
            " | ".join(
                (
                    f"INDEX={kayit['indeks']}",
                    f"TAG={kayit['tag']!r}",
                    f"METIN={kayit['metin']!r}",
                    f"ROLE={kayit['role']!r}",
                    (
                        "ARIA_LABEL="
                        f"{kayit['aria_label']!r}"
                    ),
                    f"ID={kayit['id']!r}",
                    f"CLASS={kayit['class']!r}",
                    f"HREF={kayit['href']!r}",
                    (
                        "DATA_ACTION="
                        f"{kayit['data_action']!r}"
                    ),
                    (
                        "DATA_MODULE="
                        f"{kayit['data_module']!r}"
                    ),
                    f"GORUNUR={kayit['gorunur']}",
                    f"ETKIN={kayit['etkin']}",
                )
            )
        )

    satirlar.extend(
        [
            "",
            "=== BILIMSEL METIN ESLESMELERI ===",
            json.dumps(
                metin_eslesmeleri,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== SCRIPTLER ===",
            json.dumps(
                scriptler,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== STILLER ===",
            json.dumps(
                stiller,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== FRAMELER ===",
            json.dumps(
                iframe_kayitlari,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== CONSOLE MESAJLARI ===",
            json.dumps(
                console_mesajlari,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== PAGE HATALARI ===",
            json.dumps(
                page_hatalari,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== BASARISIZ ISTEKLER ===",
            json.dumps(
                basarisiz_istekler,
                ensure_ascii=False,
                indent=2,
            ),
        ]
    )

    text_path.write_text(
        "\n".join(
            satirlar
        )
        + "\n",
        encoding="utf-8",
    )

    jeoloji_sayisi = len(
        metin_eslesmeleri.get(
            "Jeoloji",
            [],
        )
    )

    bilimsel_toplam = sum(
        len(kayitlar)
        for kayitlar
        in metin_eslesmeleri.values()
    )

    print(
        "UI_DOM_KAYNAK_TESHISI_TAMAMLANDI"
    )
    print(
        f"HTTP_DURUM={sonuc['http_durum']}"
    )
    print(
        f"SON_URL={sonuc['son_url']}"
    )
    print(
        f"HTML_UZUNLUGU={sonuc['html_uzunlugu']}"
    )
    print(
        f"BODY_METIN_UZUNLUGU={sonuc['body_metin_uzunlugu']}"
    )
    print(
        f"TUM_ELEMENT_SAYISI={tum_element_sayisi}"
    )
    print(
        f"BUTTON_SAYISI={sonuc['button_sayisi']}"
    )
    print(
        f"LINK_SAYISI={sonuc['link_sayisi']}"
    )
    print(
        "TIKLANABILIR_ADAY_SAYISI="
        + str(
            len(
                tiklanabilirler
            )
        )
    )
    print(
        f"JEOLOJI_METIN_ESLESME_SAYISI={jeoloji_sayisi}"
    )
    print(
        f"BILIMSEL_METIN_TOPLAMI={bilimsel_toplam}"
    )
    print(
        f"SCRIPT_SAYISI={len(scriptler)}"
    )
    print(
        f"PAGE_HATA_SAYISI={len(page_hatalari)}"
    )
    print(
        "BASARISIZ_ISTEK_SAYISI="
        + str(
            len(
                basarisiz_istekler
            )
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
