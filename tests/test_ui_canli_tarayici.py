import os

from playwright.sync_api import Page, expect


def test_syk_ui_canli_tarayıcı_dogrulamasi(page: Page):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.goto(url, wait_until="networkidle")

    expect(page).to_have_title("SyKaşif")
    expect(page.locator("#brand-title")).to_have_text("SyKaşif")
    expect(page.locator("#active-module")).to_have_text("Ana Terminal")
    expect(page.locator("#module-list button")).to_have_count(27)
    expect(page.locator("#syframe")).to_be_visible()
    expect(page.locator("#syframe-title")).to_have_text(
        "Analiz Ediliyor"
    )

    page.locator("#sound-toggle").click()
    expect(page.locator("#sound-toggle")).to_have_text("Ses Açık")

    page.get_by_role("button", name="Haritalar").click()
    expect(page.locator("#active-module")).to_have_text("Haritalar")

    page.get_by_role("button", name="Sonar").click()
    expect(page.locator("#active-module")).to_have_text("Sonar")