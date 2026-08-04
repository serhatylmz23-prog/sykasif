import os

import pytest
from playwright.sync_api import Page, expect


MODULE_BUTTONS = [
    ("Jeoloji", "JEOLOJİ"),
    ("Frekans", "FREKANS"),
    ("LiDAR", "LiDAR"),
    ("Astronomi", "ASTRONOMİ / ARKEOASTRONOMİ"),
    ("Kimyasal Analiz", "KİMYASAL ANALİZ"),
    ("Spektral Analiz", "SPEKTRAL ANALİZ"),
    ("Termal Analiz", "TERMAL ANALİZ"),
    ("Manyetometre", "MANYETOMETRE"),
    ("Gravimetre", "GRAVİMETRE"),
    ("Elektrik Direnç", "ELEKTRİK DİRENÇ — ERT"),
    ("GPR", "GPR — YER RADARI"),
    ("Sismik", "SİSMİK"),
    ("Hidrojeoloji", "HİDROJEOLOJİ"),
    ("Botanik", "BOTANİK"),
    ("Toprak", "TOPRAK ANALİZİ"),
    ("Su", "SU ANALİZİ"),
]


@pytest.mark.parametrize(
    ("button_name", "screen_title"),
    MODULE_BUTTONS,
)
def test_bilimsel_modul_canli_tarayıcı(
    page: Page,
    button_name: str,
    screen_title: str,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.goto(url, wait_until="networkidle")

    page.get_by_role(
        "button",
        name=button_name,
        exact=True,
    ).click()

    module_view = page.locator("#module-view")

    expect(module_view).to_be_visible()

    expect(
        module_view.locator(
            ".scientific-title strong"
        )
    ).to_have_text(screen_title)

    expect(
        module_view.locator(".scientific-scan")
    ).to_be_visible()

    expect(
        module_view.locator(".scientific-metric")
    ).to_have_count(4)

    expect(
        module_view.get_by_text(
            "Bu ekran gerçek saha sonucu değildir.",
            exact=False,
        )
    ).to_be_visible()