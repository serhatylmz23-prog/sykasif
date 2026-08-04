import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_telefon_yerlesimi_tarayıcıda_uygulanir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.set_viewport_size(
        {
            "width": 390,
            "height": 844,
        }
    )

    page.add_init_script(
        """
        Object.defineProperty(
            navigator,
            "maxTouchPoints",
            {
                configurable: true,
                value: 5,
            }
        );
        """
    )

    page.route(
        "**/api/syk-ui/mobile-runtime/devices",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "device": {
                        "device_id": (
                            "PHONE-BROWSER-006A"
                        ),
                        "device_type": "phone",
                        "active": True,
                        "trusted": False,
                        "capabilities": {
                            "touch": True,
                            "camera": True,
                            "microphone": True,
                            "location": True,
                            "notification": True,
                            "vibration": True,
                            "fullscreen": True,
                            "wake_lock": True,
                            "online": True,
                            "input_mode": "touch",
                        },
                    },
                    "layout": {
                        "profile_id": (
                            "phone-portrait-compact"
                        ),
                        "device_type": "phone",
                        "orientation": "portrait",
                        "density": "compact",
                        "navigation_mode": (
                            "bottom_navigation"
                        ),
                        "panel_mode": "single_panel",
                        "columns": 1,
                        "compact_header": True,
                        "touch_target_px": 48,
                        "fullscreen_recommended": True,
                    },
                }
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    body = page.locator("body")

    expect(body).to_have_attribute(
        "data-syk-device-type",
        "phone",
    )

    expect(body).to_have_attribute(
        "data-syk-orientation",
        "portrait",
    )

    expect(body).to_have_attribute(
        "data-syk-panel-mode",
        "single_panel",
    )

    columns = page.evaluate(
        """
        getComputedStyle(
            document.documentElement
        ).getPropertyValue(
            "--syk-layout-columns"
        ).trim()
        """
    )

    assert columns == "1"

    target = page.evaluate(
        """
        getComputedStyle(
            document.documentElement
        ).getPropertyValue(
            "--syk-touch-target"
        ).trim()
        """
    )

    assert target == "48px"

    snapshot = page.evaluate(
        """
        window.SyKMobileRuntime.snapshot()
        """
    )

    assert (
        snapshot["profile"][
            "device_type"
        ]
        == "phone"
    )