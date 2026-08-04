from __future__ import annotations

import json
from pathlib import Path

import pytest

from syk_core.runtime_hardware_validation import (
    DonanimDenetimAraci,
    DonanimDenetimAraciHatasi,
    DonanimDenetimSecenekleri,
    ag_noktasi_ayristir,
    donanim_denetim_main,
)


class SahteDenetleyici:
    def __init__(
        self,
        *,
        basarisiz: int = 0,
    ) -> None:
        self.basarisiz = basarisiz
        self.alinan_noktalar = ()

    def tum_baglantilari_denetle(
        self,
        *,
        ag_noktalari=(),
    ):
        self.alinan_noktalar = tuple(
            ag_noktalari
        )

        toplam = (
            3
            + len(self.alinan_noktalar)
        )

        return {
            "sistem": "Windows",
            "toplam_denetim_sayısı": toplam,
            "başarılı_denetim_sayısı": (
                toplam - self.basarisiz
            ),
            "başarısız_denetim_sayısı": (
                self.basarisiz
            ),
            "gerçek_sistem_denetimi": True,
            "sonuçlar": [],
        }


def test_ag_noktasi_ayristirilir() -> None:
    assert ag_noktasi_ayristir(
        "127.0.0.1:8013"
    ) == (
        "127.0.0.1",
        8013,
    )


def test_gecersiz_ag_noktasi_reddedilir() -> None:
    with pytest.raises(
        Exception,
    ):
        ag_noktasi_ayristir(
            "127.0.0.1"
        )


def test_gecersiz_port_reddedilir() -> None:
    with pytest.raises(
        Exception,
    ):
        ag_noktasi_ayristir(
            "127.0.0.1:70000"
        )


def test_arac_denetimi_calistirir(
    tmp_path: Path,
) -> None:
    denetleyici = SahteDenetleyici()

    arac = DonanimDenetimAraci(
        secenekler=(
            DonanimDenetimSecenekleri(
                cikti_dosyasi=str(
                    tmp_path
                    / "sonuc.json"
                ),
            )
        ),
        denetleyici=denetleyici,
    )

    sonuc = arac.calistir()

    assert sonuc[
        "toplam_denetim_sayısı"
    ] == 3

    assert sonuc[
        "gerçek_sistem_denetimi"
    ] is True


def test_ag_noktalari_denetleyiciye_aktarilir(
    tmp_path: Path,
) -> None:
    denetleyici = SahteDenetleyici()

    arac = DonanimDenetimAraci(
        secenekler=(
            DonanimDenetimSecenekleri(
                cikti_dosyasi=str(
                    tmp_path
                    / "sonuc.json"
                ),
                ag_noktalari=(
                    (
                        "127.0.0.1",
                        8013,
                    ),
                    (
                        "127.0.0.1",
                        8014,
                    ),
                ),
            )
        ),
        denetleyici=denetleyici,
    )

    arac.calistir()

    assert denetleyici.alinan_noktalar == (
        (
            "127.0.0.1",
            8013,
        ),
        (
            "127.0.0.1",
            8014,
        ),
    )


def test_json_cikti_dosyasi_yazilir(
    tmp_path: Path,
) -> None:
    hedef = tmp_path / "sonuc.json"

    arac = DonanimDenetimAraci(
        secenekler=(
            DonanimDenetimSecenekleri(
                cikti_dosyasi=str(
                    hedef
                ),
            )
        ),
        denetleyici=SahteDenetleyici(),
    )

    arac.calistir()

    veri = json.loads(
        hedef.read_text(
            encoding="utf-8"
        )
    )

    assert veri[
        "çalıştırma"
    ][
        "araç"
    ] == "syk_gercek_donanim_denetle"


def test_basarisiz_denetim_varsayilan_hata_vermez(
    tmp_path: Path,
) -> None:
    arac = DonanimDenetimAraci(
        secenekler=(
            DonanimDenetimSecenekleri(
                cikti_dosyasi=str(
                    tmp_path
                    / "sonuc.json"
                ),
            )
        ),
        denetleyici=(
            SahteDenetleyici(
                basarisiz=1
            )
        ),
    )

    sonuc = arac.calistir()

    assert sonuc[
        "başarısız_denetim_sayısı"
    ] == 1


def test_basarisizsa_hata_secenegi_calisir(
    tmp_path: Path,
) -> None:
    arac = DonanimDenetimAraci(
        secenekler=(
            DonanimDenetimSecenekleri(
                cikti_dosyasi=str(
                    tmp_path
                    / "sonuc.json"
                ),
                basarisiz_denetimde_hata=True,
            )
        ),
        denetleyici=(
            SahteDenetleyici(
                basarisiz=1
            )
        ),
    )

    with pytest.raises(
        DonanimDenetimAraciHatasi,
        match="başarısız kayıt",
    ):
        arac.calistir()


def test_main_tek_komutla_calisir(
    tmp_path: Path,
) -> None:
    hedef = tmp_path / "sonuc.json"

    cikis = donanim_denetim_main(
        [
            "--cikti",
            str(hedef),
            "--ag-noktasi",
            "127.0.0.1:8013",
        ],
        denetleyici=SahteDenetleyici(),
    )

    assert cikis == 0
    assert hedef.exists()


def test_secenekler_turkce_cikti_yolu_tasir(
    tmp_path: Path,
) -> None:
    secenekler = DonanimDenetimSecenekleri(
        cikti_dosyasi=str(
            tmp_path
            / "donanım_denetimi.json"
        )
    )

    assert secenekler.cikti_dosyasi.endswith(
        "donanım_denetimi.json"
    )
