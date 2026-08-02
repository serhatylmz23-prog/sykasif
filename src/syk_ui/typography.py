from dataclasses import dataclass


@dataclass(frozen=True)
class Font:
    id: str
    family: str
    weight: int = 400


FONTS = {
    "sykasif": Font("sykasif", "SyKasif"),
    "syotagi": Font("syotagi", "SyOtagi"),
    "body": Font("body", "Inter"),
    "mono": Font("mono", "JetBrains Mono"),
}


class TypographyManager:
    def available(self) -> list[Font]:
        return list(FONTS.values())

    def get(self, font_id: str) -> Font:
        if font_id not in FONTS:
            raise KeyError(f"Unknown font: {font_id}")

        return FONTS[font_id]
