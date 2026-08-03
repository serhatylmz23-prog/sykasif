import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_goruntu_yukleme_paneli_rapor_linki_uretir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.route(
        "**/api/syk-ui/media-analysis",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "analysis_id": (
                        "ANL-BROWSER-001"
                    ),
                    "media_id": (
                        "MEDIA-BROWSER-001"
                    ),
                    "candidate_count": 3,
                    "dtse_created_count": 3,
                    "report_sha256": "a" * 64,
                    "download_url": (
                        "/api/syk-ui/"
                        "media-analysis/"
                        "ANL-BROWSER-001/"
                        "report"
                    ),
                    "manifest_url": (
                        "/api/syk-ui/"
                        "media-analysis/"
                        "ANL-BROWSER-001/"
                        "manifest"
                    ),
                }
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    panel = page.locator(
        "#syk-media-upload-panel"
    )

    expect(panel).to_be_visible()

    page.locator(
        "#syk-media-upload-toggle"
    ).click()

    file_input = page.locator(
        "#syk-media-upload-file"
    )

    file_input.set_input_files(
        {
            "name": "test.png",
            "mimeType": "image/png",
            "buffer": (
                b"\x89PNG\r\n\x1a\n"
                + b"test"
            ),
        }
    )

    page.locator(
        "#syk-media-upload-submit"
    ).click()

    result = page.locator(
        ".syk-media-analysis-result"
    )

    expect(result).to_be_visible()

    expect(result).to_contain_text(
        "3 aday"
    )

    expect(result).to_contain_text(
        "MEDIA-BROWSER-001"
    )

    expect(
        result.get_by_text(
            "PDF Raporu Aç"
        )
    ).to_be_visible()

    expect(
        result.get_by_text(
            "Manifest"
        )
    ).to_be_visible()