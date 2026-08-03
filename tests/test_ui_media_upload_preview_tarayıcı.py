import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_isaretli_goruntu_ana_panelde_gosterilir(
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
                        "ANL-PREVIEW-001"
                    ),
                    "media_id": (
                        "MEDIA-PREVIEW-001"
                    ),
                    "candidate_count": 2,
                    "dtse_created_count": 2,
                    "report_sha256": "a" * 64,
                    "preview_sha256": "b" * 64,
                    "preview_url": (
                        "/api/syk-ui/"
                        "media-analysis/"
                        "ANL-PREVIEW-001/"
                        "preview"
                    ),
                    "download_url": (
                        "/api/syk-ui/"
                        "media-analysis/"
                        "ANL-PREVIEW-001/"
                        "report"
                    ),
                    "manifest_url": (
                        "/api/syk-ui/"
                        "media-analysis/"
                        "ANL-PREVIEW-001/"
                        "manifest"
                    ),
                }
            ),
        ),
    )

    page.route(
        "**/media-analysis/ANL-PREVIEW-001/preview",
        lambda route: route.fulfill(
            status=200,
            content_type="image/png",
            body=(
                b"\x89PNG\r\n\x1a\n"
                + b"preview"
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    page.locator(
        "#syk-media-upload-toggle"
    ).click()

    page.locator(
        "#syk-media-upload-file"
    ).set_input_files(
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

    preview = result.locator(
        ".syk-media-annotated-preview img"
    )

    expect(preview).to_be_visible()

    expect(
        result.get_by_text(
            "İşaretli Görsel"
        )
    ).to_be_visible()

    expect(result).to_contain_text(
        "2 aday"
    )