from __future__ import annotations

from .runtime_disa_aktarim import RuntimeDisaAktarim


class RuntimeHttpApi:
    """Runtime verisini HTTP yanıtı olarak sunar."""

    def __init__(self, disa_aktarim: RuntimeDisaAktarim) -> None:
        self._disa_aktarim = disa_aktarim

    def json(self) -> tuple[int, str]:
        return 200, self._disa_aktarim.json()

    def csv(self) -> tuple[int, str]:
        return 200, self._disa_aktarim.csv()

    def html(self) -> tuple[int, str]:
        return 200, self._disa_aktarim.html()

    def markdown(self) -> tuple[int, str]:
        return 200, self._disa_aktarim.markdown()

    def xml(self) -> tuple[int, str]:
        return 200, self._disa_aktarim.xml()

    def yaml(self) -> tuple[int, str]:
        return 200, self._disa_aktarim.yaml()