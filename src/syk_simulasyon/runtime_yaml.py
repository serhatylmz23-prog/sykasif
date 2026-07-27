from __future__ import annotations

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


class RuntimeYamlSaglayicisi:
    """Runtime anlık görünümünü YAML benzeri metne dönüştürür."""

    def __init__(
        self,
        gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi,
    ) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi

    def yaml_uret(self) -> str:
        gorunum = self._gorunum_saglayicisi.gorunum().sozluk()

        satirlar = []

        for anahtar, deger in gorunum.items():
            satirlar.append(f"{anahtar}: {deger}")

        return "\n".join(satirlar)