import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_telefon_kontrol_paneli_tarayıcıda_calısır(
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

        window.Notification = class {
            static permission = "granted";

            static async requestPermission() {
                return "granted";
            }

            constructor() {}
        };
        """
    )

    page.route(
        "**/api/syk-ui/mobile-control/devices",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "state": {
                        "device_id": (
                            "PHONE-BROWSER-006D"
                        ),
                        "device_type": "phone",
                        "camera_state": "idle",
                        "microphone_state": "idle",
                        "location_state": "idle",
                        "notification_permission": (
                            "granted"
                        ),
                        "connection_state": (
                            "online"
                        ),
                        "pairing_state": (
                            "unpaired"
                        ),
                        "offline_queue_count": 0,
                        "fullscreen": False,
                        "wake_lock": False,
                        "last_error": None,
                    },
                    "state_sha256": "a" * 64,
                }
            ),
        ),
    )

    page.route(
        "**/api/syk-ui/mobile-control/devices/*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "state": {
                        "device_id": (
                            "PHONE-BROWSER-006D"
                        ),
                        "device_type": "phone",
                        "camera_state": "idle",
                        "microphone_state": "idle",
                        "location_state": "idle",
                        "notification_permission": (
                            "granted"
                        ),
                        "connection_state": (
                            "online"
                        ),
                        "pairing_state": (
                            "unpaired"
                        ),
                        "offline_queue_count": 0,
                        "fullscreen": False,
                        "wake_lock": False,
                        "last_error": None,
                    },
                    "state_sha256": "a" * 64,
                }
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    panel = page.locator(
        "#syk-mobile-control-panel"
    )

    expect(panel).to_be_visible()

    toggle = page.locator(
        "#syk-mobile-control-toggle"
    )

    toggle.click()

    expect(toggle).to_have_attribute(
        "aria-expanded",
        "true",
    )

    expect(
        page.get_by_role(
            "button",
            name="Kamera",
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "button",
            name="Mikrofon",
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "button",
            name="GPS",
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "button",
            name="Bildirim İzni",
        )
    ).to_be_visible()

    expect(
        page.get_by_role(
            "button",
            name="Cihaz Eşleştir",
        )
    ).to_be_visible()

    snapshot = page.evaluate(
        """
        window
            .SyKMobileControl
            .snapshot()
        """
    )

    assert (
        snapshot["deviceType"]
        in {
            "phone",
            "browser",
        }
    )

    assert (
        snapshot[
            "notificationPermission"
        ]
        == "granted"
    )