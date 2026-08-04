from syk_jarmin.runtime.event_bridge import (
    JarminEventBridge,
)


def test_dtse_olayi_jarmin_bildirimi_uretir():
    bridge = JarminEventBridge()

    event = bridge.publish(
        event_type="dtse_attention",
        source="dtse",
        message=(
            "Dikkat bölgesi algılandı."
        ),
        payload={
            "confidence": 88.4,
        },
    )

    assert (
        event.event_type
        == "dtse_attention"
    )

    assert event.notification

    assert len(
        event.event_sha256
    ) == 64


def test_olay_kapasitesi_korunur():
    bridge = JarminEventBridge(
        maximum_events=2
    )

    for index in range(3):
        bridge.publish(
            event_type=(
                "environment_changed"
            ),
            source="environment",
            message=f"Ortam {index}",
        )

    assert len(
        bridge.list()
    ) == 2