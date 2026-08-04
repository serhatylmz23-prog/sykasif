"""Gerçek donanım denetimi tek komutlu çalıştırma aracı."""

from __future__ import annotations

import argparse
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .sistem_denetimi import (
    GercekSistemDenetleyicisi,
)


class DonanimDenetimAraciHatasi(RuntimeError):
    """Tek komutlu donanım denetimi hatası."""


@dataclass(slots=True, frozen=True)
class DonanimDenetimSecenekleri:
    cikti_dosyasi: str
    ag_noktalari: tuple[
        tuple[str, int],
        ...
    ] = ()
    basarisiz_denetimde_hata: bool = False

    def __post_init__(self) -> None:
        if not self.cikti_dosyasi.strip():
            raise ValueError(
                "Çıktı dosyası boş olamaz."
            )

        for ana_makine, port in self.ag_noktalari:
            if not ana_makine.strip():
                raise ValueError(
                    "Ağ noktası ana makinesi boş olamaz."
                )

            if not 1 <= port <= 65535:
                raise ValueError(
                    "Ağ noktası portu geçersiz."
                )


def ag_noktasi_ayristir(
    deger: str,
) -> tuple[str, int]:
    if ":" not in deger:
        raise argparse.ArgumentTypeError(
            "Ağ noktası ANA_MAKINE:PORT biçiminde olmalıdır."
        )

    ana_makine, port_metni = deger.rsplit(
        ":",
        1,
    )

    ana_makine = ana_makine.strip()

    if not ana_makine:
        raise argparse.ArgumentTypeError(
            "Ağ noktası ana makinesi boş olamaz."
        )

    try:
        port = int(port_metni)
    except ValueError as hata:
        raise argparse.ArgumentTypeError(
            "Ağ noktası portu sayı olmalıdır."
        ) from hata

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(
            "Ağ noktası portu 1–65535 aralığında olmalıdır."
        )

    return ana_makine, port


class DonanimDenetimAraci:
    """Gerçek bilgisayardaki bağlantıları tek komutla denetler."""

    def __init__(
        self,
        *,
        secenekler: DonanimDenetimSecenekleri,
        denetleyici: GercekSistemDenetleyicisi | None = None,
    ) -> None:
        self.secenekler = secenekler

        self.denetleyici = (
            denetleyici
            or GercekSistemDenetleyicisi()
        )

    def calistir(
        self,
    ) -> dict[str, Any]:
        sonuc = (
            self.denetleyici
            .tum_baglantilari_denetle(
                ag_noktalari=(
                    self.secenekler
                    .ag_noktalari
                )
            )
        )

        sonuc["çalıştırma"] = {
            "araç": (
                "syk_gercek_donanim_denetle"
            ),
            "sistem": platform.system(),
            "çıktı_dosyası": (
                self.secenekler.cikti_dosyasi
            ),
            "başarısız_denetimde_hata": (
                self.secenekler
                .basarisiz_denetimde_hata
            ),
        }

        hedef = Path(
            self.secenekler.cikti_dosyasi
        )

        hedef.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        hedef.write_text(
            json.dumps(
                sonuc,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        if (
            self.secenekler
            .basarisiz_denetimde_hata
            and sonuc[
                "başarısız_denetim_sayısı"
            ] > 0
        ):
            raise DonanimDenetimAraciHatasi(
                "Gerçek sistem denetiminde başarısız kayıt bulundu."
            )

        return sonuc


def arguman_ayristirici(
) -> argparse.ArgumentParser:
    ayristirici = argparse.ArgumentParser(
        prog="syk-donanim-denetle",
        description=(
            "SyKaşif gerçek bilgisayar USB, "
            "ağ ve seri bağlantı denetimi"
        ),
    )

    ayristirici.add_argument(
        "--cikti",
        default=(
            "artifacts/"
            "syk_core_parca_010/"
            "gercek_sistem_denetimi.json"
        ),
    )

    ayristirici.add_argument(
        "--ag-noktasi",
        action="append",
        default=[],
        type=ag_noktasi_ayristir,
        metavar="ANA_MAKINE:PORT",
    )

    ayristirici.add_argument(
        "--basarisizsa-hata",
        action="store_true",
    )

    return ayristirici


def main(
    argv: Sequence[str] | None = None,
    *,
    denetleyici: GercekSistemDenetleyicisi | None = None,
) -> int:
    argumanlar = (
        arguman_ayristirici()
        .parse_args(argv)
    )

    arac = DonanimDenetimAraci(
        secenekler=(
            DonanimDenetimSecenekleri(
                cikti_dosyasi=(
                    argumanlar.cikti
                ),
                ag_noktalari=tuple(
                    argumanlar.ag_noktasi
                ),
                basarisiz_denetimde_hata=(
                    argumanlar
                    .basarisizsa_hata
                ),
            )
        ),
        denetleyici=denetleyici,
    )

    sonuc = arac.calistir()

    print(
        json.dumps(
            sonuc,
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "SYK_GERCEK_DONANIM_DENETIMI_TAMAMLANDI"
    )

    print(
        "TOPLAM_DENETIM="
        f"{sonuc['toplam_denetim_sayısı']}"
    )

    print(
        "BASARILI_DENETIM="
        f"{sonuc['başarılı_denetim_sayısı']}"
    )

    print(
        "BASARISIZ_DENETIM="
        f"{sonuc['başarısız_denetim_sayısı']}"
    )

    return 0
