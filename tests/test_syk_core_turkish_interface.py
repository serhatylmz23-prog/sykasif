from __future__ import annotations

import json

from syk_core.ovm import (
    EntityKind,
    OvmEntity,
    RuntimeState,
    VisualStatus,
)


def test_interface_json_preserves_turkish_characters() -> None:
    entity = OvmEntity(
        kind=EntityKind.AI_ANALYSIS,
        title="Yüzey Zekâsı Değerlendirmesi",
        description=(
            "Çatlak, oyuk, kanal ve mineral damarı "
            "birlikte değerlendiriliyor."
        ),
        runtime_state=RuntimeState.ANALYZING,
        visual_status=VisualStatus.ANALYZING,
        metadata={
            "açıklama": "Görüntü işleme sürüyor.",
            "ölçüm": "Yüksek doğruluk",
            "sonuç": "İnceleme devam ediyor.",
        },
    )

    payload = entity.to_runtime_dict()

    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )

    assert "Yüzey Zekâsı" in text
    assert "değerlendiriliyor" in text
    assert "çalışma_durumu" in text
    assert "\\u00e7" not in text
    assert "\\u011f" not in text
    assert "\\u0131" not in text
