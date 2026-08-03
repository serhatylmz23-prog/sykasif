import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_kanit_karti_bolgeye_odaklanir_ve_sekmeleri_acar(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    page.evaluate(
        """
        () => {
            const stage =
                document.createElement("div");

            stage.id = "dtse-focus-test-stage";

            stage.setAttribute(
                "data-dtse-media-stage",
                ""
            );

            stage.style.position = "fixed";
            stage.style.left = "120px";
            stage.style.top = "100px";
            stage.style.width = "700px";
            stage.style.height = "420px";
            stage.style.background =
                "rgb(8, 28, 35)";

            document.body.appendChild(stage);

            const payload = {
                event: {
                    id: "focus-event-001",
                    media_id: "focus-media-001",
                    source_kind: "image",
                    frame_index: 8,
                    timestamp_ms: 320,
                    signal: {
                        label:
                            "Taş yüzey anomalisi",
                        kind: "anomaly",
                        confidence: 94.6
                    },
                    syframe: {
                        state: "rare_anomaly",
                        confidence: 94.6
                    },
                    analysis: {
                        requested_modules: [
                            "dtse",
                            "thermal",
                            "spectral",
                            "measurement"
                        ]
                    },
                    visual_layer: {
                        box: {
                            x: 0.20,
                            y: 0.18,
                            width: 0.30,
                            height: 0.32
                        }
                    }
                },
                evidence: {
                    verification: {
                        valid: true
                    }
                }
            };

            window.SyKDTSEEvidenceFocus.open(
                payload
            );
        }
        """
    )

    stage = page.locator(
        "#dtse-focus-test-stage"
    )

    expect(stage).to_have_class(
        "dtse-evidence-stage-focused"
    )

    expect(stage).to_have_attribute(
        "data-dtse-focus-event-id",
        "focus-event-001",
    )

    expect(
        stage.locator(
            ".dtse-evidence-focus-frame"
        )
    ).to_be_visible()

    panel = page.locator(
        "#dtse-evidence-focus-panel"
    )

    expect(panel).to_be_visible()

    expect(panel).to_contain_text(
        "Taş yüzey anomalisi"
    )

    expect(
        panel.locator(
            "[data-dtse-focus-tab]"
        )
    ).to_have_count(4)

    page.locator(
        '[data-dtse-focus-tab="thermal"]'
    ).click()

    expect(
        page.locator(
            '[data-tab-content="thermal"]'
        )
    ).to_be_visible()

    expect(panel).to_contain_text(
        "Termal İncelemesi"
    )

    expect(panel).to_contain_text(
        "Isı farkı"
    )

    page.locator(
        "#dtse-evidence-focus-close"
    ).click()

    expect(panel).to_be_hidden()

    expect(stage).not_to_have_class(
        "dtse-evidence-stage-focused"
    )