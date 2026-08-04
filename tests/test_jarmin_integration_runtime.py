from pathlib import Path

from syk_jarmin.runtime.event_bridge import (
    JarminEventBridge,
)
from syk_jarmin.runtime.integration_runtime import (
    JarminIntegrationRuntime,
)
from syk_jarmin.runtime.persistent_settings import (
    PersistentJarminSettings,
)
from syk_jarmin.runtime.runtime import (
    JarminRuntime,
)


def test_ayarlar_runtimea_uygulanir(
    tmp_path: Path,
):
    settings = (
        PersistentJarminSettings(
            tmp_path
            / "settings.json"
        )
    )

    integration = (
        JarminIntegrationRuntime(
            runtime=JarminRuntime(),
            settings=settings,
            event_bridge=(
                JarminEventBridge()
            ),
        )
    )

    result = (
        integration.update_settings(
            voice_enabled=False,
            notification_enabled=False,
            voice_profile_id=(
                "jarmin_field"
            ),
        )
    )

    assistant = result[
        "runtime"
    ]["assistant"]

    assert not assistant[
        "voice_enabled"
    ]

    assert not assistant[
        "notification_enabled"
    ]

    assert (
        result["runtime"]["voice"][
            "profile_id"
        ]
        == "jarmin_field"
    )


def test_rapor_olayi_entegre_edilir(
    tmp_path: Path,
):
    integration = (
        JarminIntegrationRuntime(
            runtime=JarminRuntime(),
            settings=(
                PersistentJarminSettings(
                    tmp_path
                    / "settings.json"
                )
            ),
            event_bridge=(
                JarminEventBridge()
            ),
        )
    )

    result = integration.ingest_event(
        event_type="report_created",
        source="sealed_report",
        message=(
            "Mühürlü rapor hazır."
        ),
        payload={
            "report_sha256": "a" * 64,
        },
    )

    assert (
        result["event_type"]
        == "report_created"
    )

    assert result[
        "notification"
    ]