from __future__ import annotations

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


class RuntimeMarkdownSaglayicisi:
    """Runtime anlık görünümünü Markdown çıktısına dönüştürür."""

    def __init__(
        self,
        gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi,
    ) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi

    def markdown_uret(self) -> str:
        gorunum = self._gorunum_saglayicisi.gorunum().sozluk()

        satirlar = [
            "# SyKaşif Runtime",
            "",
            "| Alan | Değer |",
            "|------|-------|",
        ]

        for anahtar, deger in gorunum.items():
            satirlar.append(f"| {anahtar} | {deger} |")

        return "\n".join(satirlar)