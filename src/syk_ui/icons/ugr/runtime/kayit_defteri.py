"""UGR dinamik ikon kayıt defteri."""

from __future__ import annotations

from collections.abc import Iterable

from .durumlar import IkonCalismaDurumu
from .modeller import IkonRuntimeKaydi


class IkonBulunamadiError(KeyError):
    """İstenen ikon kayıt defterinde yok."""


class IkonZatenKayitliError(ValueError):
    """Aynı kimlikte ikon zaten kayıtlı."""


class IkonRuntimeKayitDefteri:
    """Dinamik ikonların bellekteki merkezi kayıt defteri."""

    def __init__(self) -> None:
        self._kayitlar: dict[str, IkonRuntimeKaydi] = {}

    def ekle(
        self,
        kayit: IkonRuntimeKaydi,
    ) -> None:
        """Yeni ikon kaydı ekler."""

        if kayit.ikon_kimligi in self._kayitlar:
            raise IkonZatenKayitliError(
                kayit.ikon_kimligi
            )

        self._kayitlar[kayit.ikon_kimligi] = kayit

    def getir(
        self,
        ikon_kimligi: str,
    ) -> IkonRuntimeKaydi:
        """Kimliğe göre ikon kaydını döndürür."""

        try:
            return self._kayitlar[ikon_kimligi]
        except KeyError as exc:
            raise IkonBulunamadiError(
                ikon_kimligi
            ) from exc

    def sil(
        self,
        ikon_kimligi: str,
    ) -> IkonRuntimeKaydi:
        """İkon kaydını siler."""

        try:
            return self._kayitlar.pop(
                ikon_kimligi
            )
        except KeyError as exc:
            raise IkonBulunamadiError(
                ikon_kimligi
            ) from exc

    def tumu(self) -> tuple[IkonRuntimeKaydi, ...]:
        """Bütün ikon kayıtlarını döndürür."""

        return tuple(self._kayitlar.values())

    def kategoriye_gore(
        self,
        kategori: str,
    ) -> tuple[IkonRuntimeKaydi, ...]:
        """Belirli kategorideki ikonları döndürür."""

        return tuple(
            kayit
            for kayit in self._kayitlar.values()
            if kayit.kategori == kategori
        )

    def duruma_gore(
        self,
        durum: IkonCalismaDurumu,
    ) -> tuple[IkonRuntimeKaydi, ...]:
        """Belirli çalışma durumundaki ikonları döndürür."""

        return tuple(
            kayit
            for kayit in self._kayitlar.values()
            if kayit.durum == durum
        )

    def toplu_ekle(
        self,
        kayitlar: Iterable[IkonRuntimeKaydi],
    ) -> None:
        """Birden fazla ikon kaydını ekler."""

        for kayit in kayitlar:
            self.ekle(kayit)

    def sayi(self) -> int:
        """Kayıt sayısını döndürür."""

        return len(self._kayitlar)

    def temizle(self) -> None:
        """Bütün kayıtları siler."""

        self._kayitlar.clear()
