from __future__ import annotations

from pathlib import Path

from .runtime_disa_aktarim import RuntimeDisaAktarim


class RuntimeDosyaYazicisi:
    """Runtime çıktılarını dosyaya yazar."""

    def __init__(self, disa_aktarim: RuntimeDisaAktarim) -> None:
        self._disa_aktarim = disa_aktarim

    def yaz(self, hedef: Path, icerik: str) -> Path:
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(icerik, encoding="utf-8")
        return hedef

    def json_yaz(self, hedef: Path) -> Path:
        return self.yaz(hedef, self._disa_aktarim.json())

    def csv_yaz(self, hedef: Path) -> Path:
        return self.yaz(hedef, self._disa_aktarim.csv())

    def html_yaz(self, hedef: Path) -> Path:
        return self.yaz(hedef, self._disa_aktarim.html())

    def markdown_yaz(self, hedef: Path) -> Path:
        return self.yaz(hedef, self._disa_aktarim.markdown())

    def xml_yaz(self, hedef: Path) -> Path:
        return self.yaz(hedef, self._disa_aktarim.xml())

    def yaml_yaz(self, hedef: Path) -> Path:
        return self.yaz(hedef, self._disa_aktarim.yaml())