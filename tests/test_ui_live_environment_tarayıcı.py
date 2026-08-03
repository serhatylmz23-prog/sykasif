import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_konum_canli_hava_ve_ay_uygulanir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.context.set_geolocation(
        {
            "latitude": 39.93,
            "longitude": 32.85,
        }
    )

    page.context.grant_permissions(
        ["geolocation"],
        origin=(
            "http://127.0.0.1:8013"
        ),
    )

    page.route(
        "**/api/syk-ui/environment/live?*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "weather": "clear",
                    "temperature_c": 28,
                    "wind_speed_kmh": 14,
                    "wind_direction_deg": 180,
                    "cloud_percent": 8,
                    "precipitation_percent": 0,
                    "timezone": (
                        "Europe/Istanbul"
                    ),
                    "local_time": (
                        "2026-08-03T22:00"
                    ),
                    "season": "summer",
                    "daylight_factor": 0.12,
                    "recommended_brightness": 0.48,
                    "sunrise": (
                        "2026-08-03T05:50"
                    ),
                    "sunset": (
                        "2026-08-03T20:00"
                    ),
                    "moon_phase": (
                        "waning_gibbous"
                    ),
                    "moon_illumination": 0.72,
                    "source": "open_meteo",
                }
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    expect(
        page.locator("body")
    ).to_have_attribute(
        "data-syk-location-mode",
        "device",
    )

    expect(
        page.locator("body")
    ).to_have_attribute(
        "data-syk-moon-phase",
        "waning_gibbous",
    )

    expect(
        page.locator("body")
    ).to_have_attribute(
        "data-syk-weather",
        "clear",
    )