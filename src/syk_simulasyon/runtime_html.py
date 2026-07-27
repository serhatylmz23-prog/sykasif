from __future__ import annotations

from html import escape

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


class RuntimeHtmlSaglayicisi:
    """Runtime anlık görünümünü HTML çıktısına dönüştürür."""

    def __init__(
        self,
        gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi,
    ) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi

    def html_uret(self) -> str:
        gorunum = self._gorunum_saglayicisi.gorunum().sozluk()

        satirlar = [
            "<table>",
            "  <tbody>",
        ]

        for anahtar, deger in gorunum.items():
            satirlar.append(
                f"    <tr><th>{escape(str(anahtar))}</th><td>{escape(str(deger))}</td></tr>"
            )

        satirlar.extend(
            [
                "  </tbody>",
                "</table>",
            ]
        )

        return "\n".join(satirlar)