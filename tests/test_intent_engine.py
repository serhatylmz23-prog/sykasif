from syk_jarmin.runtime.intent_engine import (
    IntentEngine,
)


def test_turkce_komut_cozulur():
    engine = IntentEngine()

    result = engine.resolve(
        "Gümüş temaya geç"
    )

    assert (
        result.intent_id
        == "theme_change"
    )

    assert (
        result.entities[
            "theme_id"
        ]
        == "silver"
    )


def test_bilinmeyen_komut():
    result = IntentEngine().resolve(
        "anlamsız rastgele ifade"
    )

    assert (
        result.intent_id
        == "unknown"
    )

    assert (
        result.confidence
        < 60.0
    )