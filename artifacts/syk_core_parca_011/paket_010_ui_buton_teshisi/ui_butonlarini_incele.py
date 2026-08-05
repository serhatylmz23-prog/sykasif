from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from playwright.sync_api import sync_playwright


DEFAULT_URL = (
    "http://127.0.0.1:8013/"
    "syk-ui-screen"
)


def metni_temizle(
    deger: str | None,
) -> str:
    if deger is None:
        return ""

    return " ".join(
        deger.split()
    )


def element_bilgisi(
    locator: Any,
    indeks: int,
) -> dict[str, Any]:
    try:
        metin = metni_temizle(
            locator.inner_text(
                timeout=2000
            )
        )
    except Exception:
        metin = ""

    try:
        gorunur = locator.is_visible(
            timeout=2000
        )
    except Exception:
        gorunur = False

    try:
        etkin = locator.is_enabled(
            timeout=2000
        )
    except Exception:
        etkin = False

    try:
        kutu = locator.bounding_box(
            timeout=2000
        )
    except Exception:
        kutu = None

    return {
        "indeks": indeks,
        "tag": locator.evaluate(
            "(element) => element.tagName"
        ),
        "metin": metin,
        "aria_label": (
            locator.get_attribute(
                "aria-label"
            )
        ),
        "role": (
            locator.get_attribute(
                "role"
            )
        ),
        "id": (
            locator.get_attribute(
                "id"
            )
        ),
        "name": (
            locator.get_attribute(
                "name"
            )
        ),
        "type": (
            locator.get_attribute(
                "type"
            )
        ),
        "class": (
            locator.get_attribute(
                "class"
            )
        ),
        "title": (
            locator.get_attribute(
                "title"
            )
        ),
        "data_module": (
            locator.get_attribute(
                "data-module"
            )
        ),
        "data_action": (
            locator.get_attribute(
                "data-action"
            )
        ),
        "gorunur": gorunur,
        "etkin": etkin,
        "kutu": kutu,
    }


def benzerlik_kayitlari(
    butonlar: list[dict[str, Any]],
    aranan: str,
) -> list[dict[str, Any]]:
    aranan_kucuk = aranan.casefold()

    sonuclar = []

    for buton in butonlar:
        alanlar = {
            "metin": buton.get(
                "metin"
            )
            or "",
            "aria_label": buton.get(
                "aria_label"
            )
            or "",
            "title": buton.get(
                "title"
            )
            or "",
            "id": buton.get(
                "id"
            )
            or "",
            "class": buton.get(
                "class"
            )
            or "",
            "data_module": buton.get(
                "data_module"
            )
            or "",
            "data_action": buton.get(
                "data_action"
            )
            or "",
        }

        eslesen_alanlar = [
            alan
            for alan, deger
            in alanlar.items()
            if aranan_kucuk
            in deger.casefold()
        ]

        if eslesen_alanlar:
            sonuclar.append(
                {
                    **buton,
                    "eslesen_alanlar": (
                        eslesen_alanlar
                    ),
                }
            )

    return sonuclar


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
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

    screenshot_path = Path(
        args.screenshot
    )

    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 1000,
            }
        )

        page = context.new_page()

        console_messages: list[
            dict[str, str]
        ] = []

        page_errors: list[
            str
        ] = []

        failed_requests: list[
            dict[str, Any]
        ] = []

        page.on(
            "console",
            lambda mesaj:
                console_messages.append(
                    {
                        "tur": mesaj.type,
                        "metin": (
                            mesaj.text
                        ),
                    }
                ),
        )

        page.on(
            "pageerror",
            lambda hata:
                page_errors.append(
                    str(
                        hata
                    )
                ),
        )

        page.on(
            "requestfailed",
            lambda request:
                failed_requests.append(
                    {
                        "url": request.url,
                        "method": (
                            request.method
                        ),
                        "failure": (
                            request.failure
                        ),
                    }
                ),
        )

        response = page.goto(
            args.url,
            wait_until="networkidle",
            timeout=60000,
        )

        page.wait_for_timeout(
            3000
        )

        screenshot_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        page.screenshot(
            path=str(
                screenshot_path
            ),
            full_page=True,
        )

        button_locator = page.locator(
            "button"
        )

        button_count = (
            button_locator.count()
        )

        buttons = [
            element_bilgisi(
                button_locator.nth(
                    indeks
                ),
                indeks,
            )
            for indeks
            in range(
                button_count
            )
        ]

        role_buttons = (
            page.get_by_role(
                "button"
            )
        )

        role_button_count = (
            role_buttons.count()
        )

        links = []

        link_locator = page.locator(
            "a"
        )

        for indeks in range(
            link_locator.count()
        ):
            link = link_locator.nth(
                indeks
            )

            try:
                links.append(
                    {
                        "indeks": indeks,
                        "metin": (
                            metni_temizle(
                                link.inner_text(
                                    timeout=1000
                                )
                            )
                        ),
                        "href": (
                            link.get_attribute(
                                "href"
                            )
                        ),
                        "aria_label": (
                            link.get_attribute(
                                "aria-label"
                            )
                        ),
                        "role": (
                            link.get_attribute(
                                "role"
                            )
                        ),
                        "gorunur": (
                            link.is_visible(
                                timeout=1000
                            )
                        ),
                    }
                )
            except Exception:
                continue

        headings = []

        heading_locator = page.locator(
            "h1, h2, h3, h4, h5, h6"
        )

        for indeks in range(
            heading_locator.count()
        ):
            heading = heading_locator.nth(
                indeks
            )

            try:
                headings.append(
                    {
                        "indeks": indeks,
                        "tag": (
                            heading.evaluate(
                                "(element) => "
                                "element.tagName"
                            )
                        ),
                        "metin": (
                            metni_temizle(
                                heading.inner_text(
                                    timeout=1000
                                )
                            )
                        ),
                        "gorunur": (
                            heading.is_visible(
                                timeout=1000
                            )
                        ),
                    }
                )
            except Exception:
                continue

        iframes = [
            {
                "url": frame.url,
                "name": frame.name,
            }
            for frame in page.frames
        ]

        jeoloji_eslesmeleri = (
            benzerlik_kayitlari(
                buttons,
                "Jeoloji",
            )
        )

        bilimsel_eslesmeleri = (
            benzerlik_kayitlari(
                buttons,
                "Bilim",
            )
        )

        sonuc = {
            "url": args.url,
            "son_url": page.url,
            "http_durum": (
                response.status
                if response
                else None
            ),
            "sayfa_basligi": (
                page.title()
            ),
            "button_element_sayisi": (
                button_count
            ),
            "role_button_sayisi": (
                role_button_count
            ),
            "link_sayisi": len(
                links
            ),
            "heading_sayisi": len(
                headings
            ),
            "frame_sayisi": len(
                iframes
            ),
            "butonlar": buttons,
            "linkler": links,
            "basliklar": headings,
            "frame_listesi": iframes,
            "jeoloji_eslesmeleri": (
                jeoloji_eslesmeleri
            ),
            "bilimsel_eslesmeleri": (
                bilimsel_eslesmeleri
            ),
            "console_mesajlari": (
                console_messages
            ),
            "page_hatalari": (
                page_errors
            ),
            "basarisiz_istekler": (
                failed_requests
            ),
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
        "SPR-011 PAKET-010",
        "UI BUTON TEShis RAPORU",
        "",
        f"URL={sonuc['url']}",
        f"SON_URL={sonuc['son_url']}",
        (
            "HTTP_DURUM="
            f"{sonuc['http_durum']}"
        ),
        (
            "SAYFA_BASLIGI="
            f"{sonuc['sayfa_basligi']}"
        ),
        (
            "BUTTON_ELEMENT_SAYISI="
            f"{sonuc['button_element_sayisi']}"
        ),
        (
            "ROLE_BUTTON_SAYISI="
            f"{sonuc['role_button_sayisi']}"
        ),
        (
            "JEoloji_ESLESME_SAYISI="
            f"{len(jeoloji_eslesmeleri)}"
        ),
        (
            "BILIMSEL_ESLESME_SAYISI="
            f"{len(bilimsel_eslesmeleri)}"
        ),
        (
            "CONSOLE_MESAJ_SAYISI="
            f"{len(console_messages)}"
        ),
        (
            "PAGE_HATA_SAYISI="
            f"{len(page_errors)}"
        ),
        (
            "BASARISIZ_ISTEK_SAYISI="
            f"{len(failed_requests)}"
        ),
        "",
        "=== BUTONLAR ===",
    ]

    for buton in buttons:
        satirlar.append(
            " | ".join(
                [
                    (
                        f"INDEX="
                        f"{buton['indeks']}"
                    ),
                    (
                        f"METIN="
                        f"{buton['metin']!r}"
                    ),
                    (
                        "ARIA_LABEL="
                        f"{buton['aria_label']!r}"
                    ),
                    (
                        f"ROLE="
                        f"{buton['role']!r}"
                    ),
                    (
                        f"ID="
                        f"{buton['id']!r}"
                    ),
                    (
                        f"CLASS="
                        f"{buton['class']!r}"
                    ),
                    (
                        f"TITLE="
                        f"{buton['title']!r}"
                    ),
                    (
                        "DATA_MODULE="
                        f"{buton['data_module']!r}"
                    ),
                    (
                        "DATA_ACTION="
                        f"{buton['data_action']!r}"
                    ),
                    (
                        f"GORUNUR="
                        f"{buton['gorunur']}"
                    ),
                    (
                        f"ETKIN="
                        f"{buton['etkin']}"
                    ),
                ]
            )
        )

    satirlar.extend(
        [
            "",
            "=== JEOLOJI ESLESMELERI ===",
            json.dumps(
                jeoloji_eslesmeleri,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== BASLIKLAR ===",
        ]
    )

    for baslik in headings:
        satirlar.append(
            (
                f"TAG={baslik['tag']} "
                f"METIN={baslik['metin']!r} "
                f"GORUNUR={baslik['gorunur']}"
            )
        )

    satirlar.extend(
        [
            "",
            "=== FRAME LISTESI ===",
            json.dumps(
                iframes,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== CONSOLE MESAJLARI ===",
            json.dumps(
                console_messages,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== PAGE HATALARI ===",
            json.dumps(
                page_errors,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "=== BASARISIZ ISTEKLER ===",
            json.dumps(
                failed_requests,
                ensure_ascii=False,
                indent=2,
            ),
            "",
        ]
    )

    text_path.write_text(
        "\n".join(
            satirlar
        ),
        encoding="utf-8",
    )

    print(
        "UI_BUTON_TESHISI_TAMAMLANDI"
    )
    print(
        "HTTP_DURUM="
        + str(
            sonuc[
                "http_durum"
            ]
        )
    )
    print(
        "SON_URL="
        + sonuc[
            "son_url"
        ]
    )
    print(
        "BUTTON_ELEMENT_SAYISI="
        + str(
            button_count
        )
    )
    print(
        "ROLE_BUTTON_SAYISI="
        + str(
            role_button_count
        )
    )
    print(
        "JEOLOJI_ESLESME_SAYISI="
        + str(
            len(
                jeoloji_eslesmeleri
            )
        )
    )
    print(
        "PAGE_HATA_SAYISI="
        + str(
            len(
                page_errors
            )
        )
    )
    print(
        "BASARISIZ_ISTEK_SAYISI="
        + str(
            len(
                failed_requests
            )
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
