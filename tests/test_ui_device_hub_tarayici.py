import os

from playwright.sync_api import Page, expect


DEVICE_ID = "tcp:test-device"


def _aktif_test_oturumlarini_durdur(
    page: Page,
    base_url: str,
) -> None:
    response = page.request.get(
        f"{base_url}/api/syk-ui/device-sessions"
    )

    assert response.ok

    for session in response.json():
        if (
            session.get("device_id") == DEVICE_ID
            and session.get("state") == "recording"
        ):
            stopped = page.request.post(
                (
                    f"{base_url}/api/syk-ui/"
                    f"device-sessions/{session['id']}/stop"
                )
            )

            assert stopped.ok


def test_device_hub_canli_tarayıcı(page: Page):
    base_url = os.getenv(
        "SYK_UI_BASE_URL",
        "http://127.0.0.1:8013",
    )

    screen_url = os.getenv(
        "SYK_UI_TEST_URL",
        f"{base_url}/syk-ui-screen",
    )

    register = page.request.post(
        f"{base_url}/api/syk-ui/device-hub/register",
        data={
            "device_id": DEVICE_ID,
            "title": "SYK TEST DEVICE",
            "transport": "tcp",
            "address": "127.0.0.1:9100",
            "module_id": "gpr",
            "metadata": {},
        },
    )

    assert register.status in {200, 422}

    _aktif_test_oturumlarini_durdur(
        page,
        base_url,
    )

    connection = page.request.patch(
        (
            f"{base_url}/api/syk-ui/device-hub/"
            f"{DEVICE_ID}/connection"
        ),
        data={
            "connected": True,
        },
    )

    assert connection.ok

    page.goto(
        screen_url,
        wait_until="networkidle",
    )

    page.get_by_role(
        "button",
        name="Ölçüm",
        exact=True,
    ).click()

    module_view = page.locator("#module-view")

    expect(module_view).to_be_visible()

    expect(
        module_view.get_by_text(
            "SYK DEVICE HUB",
            exact=True,
        )
    ).to_be_visible()

    card = module_view.locator(
        (
            "article.device-card"
            f'[data-device-id="{DEVICE_ID}"]'
        )
    )

    expect(card).to_be_visible()

    expect(
        card.get_by_text(
            "SYK TEST DEVICE",
            exact=True,
        )
    ).to_be_visible()

    expect(
        card.get_by_text(
            "BAĞLI",
            exact=True,
        )
    ).to_be_visible()

    record_button = card.locator(
        '[data-device-action="record"]'
    )

    expect(record_button).to_be_enabled()

    record_button.click()

    expect(record_button).to_have_text(
        "Kayıt Aktif"
    )

    expect(card).to_have_attribute(
        "data-recording",
        "true",
    )

    sessions = page.request.get(
        f"{base_url}/api/syk-ui/device-sessions"
    )

    assert sessions.ok

    active = [
        session
        for session in sessions.json()
        if (
            session.get("device_id") == DEVICE_ID
            and session.get("state") == "recording"
        )
    ]

    assert len(active) == 1

    stopped = page.request.post(
        (
            f"{base_url}/api/syk-ui/"
            f"device-sessions/{active[0]['id']}/stop"
        )
    )

    assert stopped.ok
    assert stopped.json()["state"] == "stopped"