import os

from playwright.sync_api import Page, expect


def test_balik_rehberi_ve_syframe_canli(page: Page):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.goto(url, wait_until="networkidle")

    page.get_by_role("button", name="Sonar").click()

    expect(
        page.get_by_text(
            "TATLI SU BALIK REHBERİ",
            exact=True,
        )
    ).to_be_visible()

    expect(page.locator(".fish-card")).to_have_count(12)

    expect(
        page.get_by_text(
            "ALABALIK",
            exact=True,
        )
    ).to_be_visible()

    page.get_by_role("button", name="SyFrame").click()

    expect(
        page.get_by_text(
            "SyFrame™",
            exact=True,
        )
    ).to_be_visible()

    expect(page.locator(".syframe-evidence")).to_have_count(6)

    expect(
        page.get_by_text(
            "HEYKEL",
            exact=True,
        )
    ).to_be_visible()