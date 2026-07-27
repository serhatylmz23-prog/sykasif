from __future__ import annotations

import xml.etree.ElementTree as ET

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi


class RuntimeXmlSaglayicisi:
    """Runtime anlık görünümünü XML çıktısına dönüştürür."""

    def __init__(
        self,
        gorunum_saglayicisi: RuntimeAnlikGorunumSaglayicisi,
    ) -> None:
        self._gorunum_saglayicisi = gorunum_saglayicisi

    def xml_uret(self) -> str:
        gorunum = self._gorunum_saglayicisi.gorunum().sozluk()

        kok = ET.Element("runtime")

        for anahtar, deger in gorunum.items():
            dugum = ET.SubElement(kok, str(anahtar))
            dugum.text = "" if deger is None else str(deger)

        return ET.tostring(
            kok,
            encoding="unicode",
        )