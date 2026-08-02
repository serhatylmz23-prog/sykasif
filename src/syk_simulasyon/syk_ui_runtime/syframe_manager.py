from dataclasses import dataclass


@dataclass(frozen=True)
class SyFrameState:
    id: str
    title: str
    color: str


STATES = {
    "verified": SyFrameState(
        "verified",
        "Doğrulandı",
        "#6DFF41",
    ),
    "analyzing": SyFrameState(
        "analyzing",
        "Analiz Ediliyor",
        "#37DFFF",
    ),
    "review": SyFrameState(
        "review",
        "İncelenmeli",
        "#FFD640",
    ),
    "low_confidence": SyFrameState(
        "low_confidence",
        "Düşük Güven",
        "#FF9D1A",
    ),
    "inconsistent": SyFrameState(
        "inconsistent",
        "Tutarsız Veri",
        "#FF4D3F",
    ),
    "rare_anomaly": SyFrameState(
        "rare_anomaly",
        "Nadir Anomali",
        "#B86CFF",
    ),
    "reference": SyFrameState(
        "reference",
        "Referans Veri",
        "#F2F2F2",
    ),
}


class SyFrameManager:
    def __init__(self):
        self._state = "analyzing"
        self._mode = "focus"
        self._visible = True
        self._confidence = 0.0

    @property
    def state(self) -> SyFrameState:
        return STATES[self._state]

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def confidence(self) -> float:
        return self._confidence

    def update(
        self,
        *,
        state=None,
        mode=None,
        visible=None,
        confidence=None,
    ) -> SyFrameState:
        if state is not None:
            if state not in STATES:
                raise KeyError(
                    f"Unknown SyFrame state: {state}"
                )
            self._state = state

        if mode is not None:
            allowed = {
                "focus",
                "object",
                "region",
                "evidence",
                "anomaly",
            }
            if mode not in allowed:
                raise KeyError(
                    f"Unknown SyFrame mode: {mode}"
                )
            self._mode = mode

        if visible is not None:
            self._visible = bool(visible)

        if confidence is not None:
            self._confidence = max(
                0.0,
                min(99.9, float(confidence)),
            )

        return self.state

    def available_states(self) -> list[SyFrameState]:
        return list(STATES.values())
