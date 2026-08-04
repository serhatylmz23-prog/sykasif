import json
import os

from playwright.sync_api import (
    Page,
    expect,
)


def test_dtse_odak_paneli_bilimsel_runtime_verisi_gosterir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    inventory = [
        {
            "definition": {
                "id": "thermal",
                "title": "Termal Analiz",
                "unit": "°C",
            },
            "state": {
                "module_id": "thermal",
                "live_value": 29.45,
                "confidence": 97.2,
                "status": "verified",
                "source": "browser_test_adapter",
                "sequence": 4,
                "updated_at": (
                    "2026-08-03T10:00:00+00:00"
                ),
            },
        },
        {
            "definition": {
                "id": "spectral",
                "title": "Spektral Analiz",
                "unit": "nm",
            },
            "state": {
                "module_id": "spectral",
                "live_value": 680,
                "confidence": 91.4,
                "status": "analyzing",
                "source": "browser_spectral_adapter",
                "sequence": 3,
                "updated_at": (
                    "2026-08-03T10:00:00+00:00"
                ),
            },
        },
    ]

    page.route(
        "**/api/syk-ui/scientific-modules",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(inventory),
        ),
    )

    for module_payload in inventory:
        module_id = (
            module_payload["state"]["module_id"]
        )

        page.route(
            (
                "**/api/syk-ui/"
                f"scientific-modules/{module_id}"
            ),
            lambda route, request, payload=module_payload:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(payload),
                ),
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

            stage.id =
                "dtse-scientific-runtime-stage";

            stage.setAttribute(
                "data-dtse-media-stage",
                ""
            );

            stage.style.position = "fixed";
            stage.style.left = "80px";
            stage.style.top = "80px";
            stage.style.width = "700px";
            stage.style.height = "420px";

            document.body.appendChild(stage);

            window.SyKDTSEEvidenceFocus.open({
                event: {
                    id: "scientific-focus-001",
                    media_id: "scientific-media-001",
                    source_kind: "image",
                    frame_index: 3,
                    timestamp_ms: 120,
                    signal: {
                        label:
                            "Termal ve spektral sapma",
                        kind: "anomaly",
                        confidence: 94.5
                    },
                    syframe: {
                        state: "rare_anomaly",
                        confidence: 94.5
                    },
                    analysis: {
                        requested_modules: [
                            "thermal",
                            "spectral"
                        ]
                    },
                    visual_layer: {
                        box: {
                            x: 0.20,
                            y: 0.20,
                            width: 0.30,
                            height: 0.30
                        }
                    }
                }
            });
        }
        """
    )

    page.locator(
        '[data-dtse-focus-tab="thermal"]'
    ).click()

    runtime_view = page.locator(
        (
            ".dtse-scientific-runtime-view"
            '[data-runtime-tab="thermal"]'
        )
    )

    expect(runtime_view).to_be_visible()

    expect(
        runtime_view.locator(
            ".dtse-scientific-live-card"
        )
    ).to_have_count(1)

    expect(runtime_view).to_contain_text(
        "Termal Analiz"
    )

    expect(runtime_view).to_contain_text(
        "29.45 °C"
    )

    expect(runtime_view).to_contain_text(
        "%97.2"
    )

    expect(runtime_view).to_contain_text(
        "Dijital Doğrulandı"
    )

    expect(runtime_view).to_contain_text(
        "browser_test_adapter"
    )

    page.locator(
        '[data-dtse-focus-tab="spectral"]'
    ).click()

    spectral_view = page.locator(
        (
            ".dtse-scientific-runtime-view"
            '[data-runtime-tab="spectral"]'
        )
    )

    expect(spectral_view).to_be_visible()

    expect(spectral_view).to_contain_text(
        "Spektral Analiz"
    )

    expect(spectral_view).to_contain_text(
        "680 nm"
    )

    expect(spectral_view).to_contain_text(
        "%91.4"
    )

    state = page.evaluate(
        """
        () => (
            window
                .SyKDTSEScientificRuntime
                .getState()
        )
        """
    )

    assert state["activeTab"] == "spectral"
    assert state["inventoryLoaded"]
    assert state["moduleCount"] == 1
    assert state["renderSequence"] >= 2