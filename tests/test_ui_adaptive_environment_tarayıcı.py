import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_meteoroloji_ekrana_uygulanir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.route(
        "**/api/syk-ui/environment/current",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "weather": "rain",
                    "temperature_c": 13.0,
                    "wind_speed_kmh": 32.0,
                    "wind_direction_deg": 220.0,
                    "cloud_percent": 92.0,
                    "precipitation_percent": 80.0,
                    "timezone": "Europe/Istanbul",
                    "local_time": (
                        "2026-08-03T15:00:00+03:00"
                    ),
                    "hour": 15,
                    "minute": 0,
                    "season": "summer",
                    "daylight_factor": 0.84,
                    "recommended_brightness": 0.71,
                    "source": "browser_test",
                }
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    expect(
        page.locator(
            "#syk-dynamic-atmosphere"
        )
    ).to_be_attached()

    expect(
        page.locator("body")
    ).to_have_attribute(
        "data-syk-weather",
        "rain",
    )

    expect(
        page.locator("body")
    ).to_have_attribute(
        "data-syk-season",
        "summer",
    )

    brightness = page.evaluate(
        """
        getComputedStyle(
            document.documentElement
        ).getPropertyValue(
            "--syk-screen-brightness"
        ).trim()
        """
    )

    assert brightness
    assert float(brightness) > 0.3