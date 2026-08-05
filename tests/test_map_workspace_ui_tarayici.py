from __future__ import annotations

import os

from playwright.sync_api import Page, expect


def test_map_workspace_visual_runtime(
    page: Page,
) -> None:
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    workspace = {
        "workspace_id": "ui-map-test",
        "research_id": "research-test",
        "name": "Keban Kıyı Alanı",
        "status": "active",
        "ar_enabled": True,
        "center": {
            "latitude": 38.7123,
            "longitude": 38.4521,
        },
        "zoom": 18,
        "pins": [
            {
                "pin_id": "pin-1",
                "name": "Kıyı Tarama Noktası",
                "latitude": 38.7124,
                "longitude": 38.4522,
            }
        ],
        "layers": [
            {
                "layer_id": "base-1",
                "key": "base-map",
                "name": "Temel Harita",
                "layer_type": "base",
                "visible": True,
                "opacity": 1.0,
                "ar_enabled": False,
                "source": "syk-map-runtime",
            },
            {
                "layer_id": "sonar-1",
                "key": "garmin-sonar",
                "name": "Garmin Sonar",
                "layer_type": "sonar",
                "visible": True,
                "opacity": 0.82,
                "ar_enabled": True,
                "source": "external-device-adapter",
            },
        ],
        "measurements": [
            {
                "measurement_id": "measurement-1",
                "measurement_type": "distance",
                "value": 14.8,
                "unit": "m",
                "start": {
                    "latitude": 38.7123,
                    "longitude": 38.4521,
                },
                "end": {
                    "latitude": 38.7124,
                    "longitude": 38.4522,
                },
            }
        ],
        "created_at": "",
        "updated_at": "",
    }

    page.evaluate(
        """
        (workspace) => {
            window.SyKMapWorkspaceView.render(
                workspace
            );
        }
        """,
        workspace,
    )

    panel = page.locator(
        "#syk-map-workspace-panel"
    )

    expect(panel).to_be_visible()

    expect(
        panel.locator(
            "#syk-map-workspace-title"
        )
    ).to_have_text(
        "Keban Kıyı Alanı"
    )

    expect(
        panel.locator(
            "#syk-map-ar-state"
        )
    ).to_have_text(
        "AR Açık"
    )

    expect(
        panel.locator(
            "#syk-map-sonar-sweep"
        )
    ).to_be_visible()

    expect(
        panel.locator(
            ".syk-map-pin"
        )
    ).to_have_count(1)

    expect(
        panel.locator(
            ".syk-map-measurement-line"
        )
    ).to_have_count(1)

    expect(
        panel.get_by_text(
            "0–2 m kıyı tarama bölgesi",
            exact=True,
        )
    ).to_be_visible()