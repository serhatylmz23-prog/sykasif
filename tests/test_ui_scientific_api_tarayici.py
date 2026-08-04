import os

from playwright.sync_api import Page, expect


def test_bilimsel_ekran_api_ve_websocket_canli(page: Page):
    base_url = os.getenv(
        "SYK_UI_BASE_URL",
        "http://127.0.0.1:8013",
    )

    screen_url = os.getenv(
        "SYK_UI_TEST_URL",
        f"{base_url}/syk-ui-screen",
    )

    reset_response = page.request.patch(
        (
            f"{base_url}"
            "/api/syk-ui/scientific-modules/thermal"
        ),
        data={
            "live_value": 24.72,
            "confidence": 87.0,
            "status": "preview",
            "source": "digital_preview",
        },
    )

    assert reset_response.ok

    page.goto(screen_url, wait_until="networkidle")

    page.get_by_role(
        "button",
        name="Termal Analiz",
        exact=True,
    ).click()

    module_view = page.locator("#module-view")

    expect(module_view).to_be_visible()

    expect(
        module_view.locator(
            ".scientific-title strong"
        )
    ).to_have_text("TERMAL ANALİZ")

    expect(
        module_view.locator(
            "#scientific-source"
        )
    ).to_have_text("digital_preview")

    expect(
        module_view.locator(
            "#scientific-status"
        )
    ).to_have_text("preview")

    update_response = page.request.patch(
        (
            f"{base_url}"
            "/api/syk-ui/scientific-modules/thermal"
        ),
        data={
            "live_value": 29.45,
            "confidence": 97.2,
            "status": "verified",
            "source": "browser_test_adapter",
        },
    )

    assert update_response.ok

    expect(
        module_view.locator(
            "#scientific-live-value"
        )
    ).to_have_text("29.45 °C")

    expect(
        module_view.locator(
            "#scientific-confidence"
        )
    ).to_have_text("%97.2")

    expect(
        module_view.locator(
            "#scientific-source"
        )
    ).to_have_text("browser_test_adapter")

    expect(
        module_view.locator(
            "#scientific-status"
        )
    ).to_have_text("verified")