from __future__ import annotations

import os

from playwright.sync_api import Page, expect


def test_sonar_session_visual_panel(
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

    session = {
        "session_id": "sonar-ui-test",
        "device_id": "garmin-sonar-mock-001",
        "research_id": "research-001",
        "workspace_id": "workspace-001",
        "name": "Keban Kıyı Sonar Oturumu",
        "state": "active",
        "shallow_coast_profile": True,
        "maximum_priority_depth_m": 2.0,
        "started_at": "",
        "stopped_at": None,
        "created_at": "",
        "updated_at": "",
        "frame_count": 4,
        "frame_record_ids": [
            "record-1",
            "record-2",
            "record-3",
            "record-4",
        ],
        "timeline": [
            {
                "sequence": 1,
                "frame_id": "frame-1",
                "timestamp": "",
                "depth_m": 0.55,
                "water_temperature_c": 19.4,
                "target_count": 0,
                "fish_target_count": 0,
                "bottom_classification": "vegetated",
                "latitude": 38.712301,
                "longitude": 38.452101,
            },
            {
                "sequence": 2,
                "frame_id": "frame-2",
                "timestamp": "",
                "depth_m": 0.92,
                "water_temperature_c": 19.5,
                "target_count": 1,
                "fish_target_count": 1,
                "bottom_classification": "medium",
                "latitude": 38.712302,
                "longitude": 38.452102,
            },
            {
                "sequence": 3,
                "frame_id": "frame-3",
                "timestamp": "",
                "depth_m": 1.24,
                "water_temperature_c": 19.6,
                "target_count": 0,
                "fish_target_count": 0,
                "bottom_classification": "medium",
                "latitude": 38.712303,
                "longitude": 38.452103,
            },
            {
                "sequence": 4,
                "frame_id": "frame-4",
                "timestamp": "",
                "depth_m": 1.48,
                "water_temperature_c": 19.6,
                "target_count": 1,
                "fish_target_count": 1,
                "bottom_classification": "medium",
                "latitude": 38.712304,
                "longitude": 38.452104,
            },
        ],
        "gps_track": [
            {},
            {},
            {},
            {},
        ],
        "evidence_candidate_ids": [
            "candidate-1",
            "candidate-2",
            "candidate-3",
            "candidate-4",
        ],
        "map_layer_state": {
            "layer_key": "garmin-sonar-live",
            "visible": True,
            "frame_count": 4,
            "fish_target_count": 2,
            "last_depth_m": 1.48,
            "last_position": {
                "latitude": 38.712304,
                "longitude": 38.452104,
            },
            "profile": "shallow-coast-0-2m",
            "within_priority_depth": True,
        },
        "summary": {
            "target_count": 2,
            "fish_target_count": 2,
            "minimum_depth_m": 0.55,
            "maximum_depth_m": 1.48,
            "average_depth_m": 1.048,
            "bottom_classification": {
                "vegetated": 1,
                "medium": 3,
            },
        },
        "last_error": None,
    }

    page.evaluate(
        """
        (session) => {
            window.SyKSonarSessionPanel.render(
                session
            );
        }
        """,
        session,
    )

    panel = page.locator(
        "#syk-sonar-session-panel"
    )

    expect(panel).to_be_visible()

    expect(
        panel.locator(
            "#syk-sonar-session-name"
        )
    ).to_have_text(
        "Keban Kıyı Sonar Oturumu"
    )

    expect(
        panel.locator(
            "#syk-sonar-session-state"
        )
    ).to_have_text(
        "Çalışıyor"
    )

    expect(
        panel.locator(
            "#syk-sonar-depth"
        )
    ).to_have_text(
        "1.48 m"
    )

    expect(
        panel.locator(
            "#syk-sonar-temperature"
        )
    ).to_have_text(
        "19.6 °C"
    )

    expect(
        panel.locator(
            "#syk-sonar-fish-count"
        )
    ).to_have_text(
        "2"
    )

    expect(
        panel.locator(
            ".syk-sonar-fish-target"
        )
    ).to_have_count(2)

    expect(
        panel.locator(
            ".syk-sonar-timeline-bar"
        )
    ).to_have_count(4)

    expect(
        panel.locator(
            "#syk-sonar-frame-count"
        )
    ).to_have_text(
        "4"
    )

    expect(
        panel.locator(
            "#syk-sonar-map-layer"
        )
    ).to_have_text(
        "Canlı"
    )

    expect(
        panel.get_by_text(
            "0–2 m kıyı profili",
            exact=True,
        )
    ).to_be_visible()