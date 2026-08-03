import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_dtse_kanit_karti_canli_tarayıcı(
    page: Page,
):
    base_url = os.getenv(
        "SYK_UI_BASE_URL",
        "http://127.0.0.1:8013",
    )

    screen_url = os.getenv(
        "SYK_UI_TEST_URL",
        f"{base_url}/syk-ui-screen",
    )

    media_id = "BROWSER-EVIDENCE-001"

    page.route(
        (
            f"**/goruntu/kayitlar/"
            f"{media_id}/kanit-zinciri"
        ),
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=(
                """
                {
                  "media_id": "BROWSER-EVIDENCE-001",
                  "records": [
                    {
                      "record_sha256":
                      "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                    }
                  ],
                  "verification": {
                    "valid": true,
                    "record_count": 1
                  }
                }
                """
            ),
        ),
    )

    page.route(
        (
            f"**/goruntu/kayitlar/"
            f"{media_id}/kanit-manifesti"
        ),
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=(
                """
                {
                  "record_count": 1,
                  "manifest_sha256":
                  "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                  "field_validation_required": true,
                  "maximum_digital_confidence": 99.9
                }
                """
            ),
        ),
    )

    page.route(
        (
            f"**/goruntu/kayitlar/"
            f"{media_id}/kanit-dogrula"
        ),
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=(
                """
                {
                  "valid": true,
                  "record_count": 1,
                  "manifest_sha256":
                  "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                }
                """
            ),
        ),
    )

    page.goto(
        screen_url,
        wait_until="networkidle",
    )

    page.evaluate(
        """
        async () => {
            window.SyKDTSEEvidenceCard.reset();

            await window.SyKDTSEEvidenceCard.renderEvent({
                id: "event-browser-001",
                media_id: "BROWSER-EVIDENCE-001",
                source_kind: "image",
                frame_index: 14,
                timestamp_ms: 560,
                event_sha256:
                    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                signal: {
                    label: "Taş yüzey anomalisi",
                    kind: "anomaly",
                    confidence: 94.6
                },
                syframe: {
                    state: "rare_anomaly",
                    confidence: 94.6
                },
                visual_layer: {
                    box: {
                        x: 0.12,
                        y: 0.20,
                        width: 0.32,
                        height: 0.28
                    }
                }
            });
        }
        """
    )

    card = page.locator(
        ".dtse-evidence-card"
    )

    expect(card).to_be_visible()

    expect(card).to_have_attribute(
        "data-state",
        "rare_anomaly",
    )

    expect(card).to_have_attribute(
        "data-valid",
        "true",
    )

    expect(card).to_contain_text(
        "Taş yüzey anomalisi"
    )

    expect(card).to_contain_text(
        "Nadir Anomali"
    )

    expect(card).to_contain_text(
        "%94.6"
    )

    expect(card).to_contain_text(
        "SHA zinciri doğrulandı"
    )

    expect(
        card.locator(
            ".dtse-evidence-hashes code"
        )
    ).to_have_count(3)