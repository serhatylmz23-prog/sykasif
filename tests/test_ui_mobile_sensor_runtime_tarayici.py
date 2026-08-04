import json
import os

from playwright.sync_api import (
    Page,
)


def test_mobil_sensor_runtime_tarayıcıda_yuklenir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.route(
        "**/api/syk-ui/mobile-sensors/permissions",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "sensor_type": "camera",
                    "state": "prompt",
                }
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    result = page.evaluate(
        """
        ({
            runtimeReady:
                Boolean(
                    window.SyKMobileSensors
                ),
            hasCamera:
                typeof window
                    .SyKMobileSensors
                    .startCamera
                === "function",
            hasMicrophone:
                typeof window
                    .SyKMobileSensors
                    .startMicrophone
                === "function",
            hasLocation:
                typeof window
                    .SyKMobileSensors
                    .requestLocation
                === "function",
            state:
                window
                    .SyKMobileSensors
                    .snapshot(),
        })
        """
    )

    assert result[
        "runtimeReady"
    ]

    assert result[
        "hasCamera"
    ]

    assert result[
        "hasMicrophone"
    ]

    assert result[
        "hasLocation"
    ]

    assert not result[
        "state"
    ]["cameraActive"]