import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_kasif_ikonlari_dinamik_uretilir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    manifest = {
        "manifest_sha256": "a" * 64,
        "icons": [
            {
                "icon_id": "map",
                "order": 1,
                "title": "Harita",
                "group": "exploration",
                "module_id": "map",
                "description": (
                    "Harita çalışma alanı."
                ),
                "asset": "map.webp",
                "asset_url": (
                    "/syk-ui/icons/kasif/"
                    "map.webp"
                ),
                "asset_exists": False,
                "fallback_symbol": "✦",
                "theme": "gold",
                "animation": "float",
                "enabled": True,
                "permission": (
                    "module.map.view"
                ),
                "keywords": [
                    "harita",
                ],
                "visual_rules": {},
            },
            {
                "icon_id": "kasif",
                "order": 100,
                "title": "Kaşif",
                "group": "assistant",
                "module_id": "kasif",
                "description": (
                    "Bilge ve gizemli asistan."
                ),
                "asset": "kasif.webp",
                "asset_url": (
                    "/syk-ui/icons/kasif/"
                    "kasif.webp"
                ),
                "asset_exists": False,
                "fallback_symbol": "✦",
                "theme": "gold",
                "animation": "glow",
                "enabled": True,
                "permission": (
                    "assistant.kasif.use"
                ),
                "keywords": [
                    "kaşif",
                ],
                "visual_rules": {
                    "face_visible": False,
                    "eyes_visible": False,
                    "headphones": False,
                    "hooded": True,
                    "mysterious": True,
                },
            },
        ],
    }

    page.route(
        "**/api/syk-ui/kasif-icons/"
        "manifest",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                manifest
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    page.evaluate(
        """
        () => {
            const host =
                document.createElement(
                    "div"
                );

            host.id =
                "kasif-test-grid";

            document.body.appendChild(
                host
            );

            window.SyKKasifIcons
                .renderGrid(
                    host,
                    {
                        interactive:
                            false,
                    }
                );
        }
        """
    )

    icons = page.locator(
        "#kasif-test-grid "
        ".syk-kasif-icon"
    )

    expect(icons).to_have_count(
        2
    )

    map_icon = page.locator(
        '[data-icon-id="map"]'
    )

    expect(map_icon).to_contain_text(
        "Harita"
    )

    kasif_icon = page.locator(
        '[data-icon-id="kasif"]'
    )

    expect(kasif_icon).to_contain_text(
        "Kaşif"
    )

    snapshot = page.evaluate(
        """
        window
            .SyKKasifIcons
            .snapshot()
        """
    )

    assert (
        snapshot["iconCount"]
        == 2
    )

    assert (
        snapshot["assistant"][
            "visual_rules"
        ]["headphones"]
        is False
    )