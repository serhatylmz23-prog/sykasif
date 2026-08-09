from __future__ import annotations

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from terminal_v2.app.main import app
from terminal_v2.shared.module_catalog import (
    modul_bilgisi_getir,
)


client = TestClient(app)


MODULLER = (
    "dashboard",
    "harita",
    "kanit",
    "analiz",
    "gorev",
    "rapor",
    "sensorler",
)


BOSLUK_CIFTLERI = (
    ("", ""),
    (" ", ""),
    ("", " "),
    (" ", " "),
    ("  ", ""),
    ("", "  "),
    ("\t", ""),
    ("", "\t"),
    ("\t", "\t"),
    (" \t", "\t "),
)


def donusumler(kod: str):
    return (
        kod,
        kod.upper(),
        kod.capitalize(),
        kod.swapcase(),
        kod.lower(),
        kod.casefold(),
        "".join(
            karakter.upper()
            if index % 2 == 0
            else karakter.lower()
            for index, karakter in enumerate(kod)
        ),
        "".join(
            karakter.lower()
            if index % 2 == 0
            else karakter.upper()
            for index, karakter in enumerate(kod)
        ),
    )


def katalog_senaryolari():
    senaryolar = []

    for modul_kodu in MODULLER:
        for sol, sag in BOSLUK_CIFTLERI:
            for donusmus in donusumler(
                modul_kodu
            ):
                girdi = (
                    sol
                    + donusmus
                    + sag
                )

                senaryolar.append(
                    pytest.param(
                        modul_kodu,
                        girdi,
                        id=(
                            f"katalog-"
                            f"{modul_kodu}-"
                            f"{len(senaryolar):03d}"
                        ),
                    )
                )

    return tuple(senaryolar)


def api_senaryolari():
    senaryolar = []

    for modul_kodu in MODULLER:
        varyantlar = (
            modul_kodu,
            modul_kodu.upper(),
            modul_kodu.capitalize(),
            modul_kodu.swapcase(),
            modul_kodu.lower(),
            modul_kodu.casefold(),
            "".join(
                karakter.upper()
                if index % 2 == 0
                else karakter.lower()
                for index, karakter
                in enumerate(modul_kodu)
            ),
            "".join(
                karakter.lower()
                if index % 2 == 0
                else karakter.upper()
                for index, karakter
                in enumerate(modul_kodu)
            ),
            f" {modul_kodu}",
            f"{modul_kodu} ",
            f"  {modul_kodu}",
            f"{modul_kodu}  ",
            f" {modul_kodu} ",
            f"\t{modul_kodu}",
            f"{modul_kodu}\t",
            f"\t{modul_kodu}\t",
            f" {modul_kodu.upper()} ",
            f"  {modul_kodu.upper()}  ",
            f"\t{modul_kodu.capitalize()}",
            f"{modul_kodu.capitalize()}\t",
        )

        for girdi in varyantlar:
            senaryolar.append(
                pytest.param(
                    modul_kodu,
                    girdi,
                    id=(
                        f"api-"
                        f"{modul_kodu}-"
                        f"{len(senaryolar):03d}"
                    ),
                )
            )

    return tuple(senaryolar)


KATALOG_SENARYOLARI = (
    katalog_senaryolari()
)

API_SENARYOLARI = (
    api_senaryolari()
)


def test_generated_matrix_exceeds_700_cases():
    assert len(
        KATALOG_SENARYOLARI
    ) == 560

    assert len(
        API_SENARYOLARI
    ) == 140

    assert (
        len(KATALOG_SENARYOLARI)
        + len(API_SENARYOLARI)
    ) == 700


@pytest.mark.parametrize(
    ("beklenen_kod", "girdi"),
    KATALOG_SENARYOLARI,
)
def test_shared_catalog_normalizes_codes(
    beklenen_kod,
    girdi,
):
    modul = modul_bilgisi_getir(
        girdi
    )

    assert modul["kod"] == beklenen_kod
    assert isinstance(
        modul["ad"],
        str,
    )
    assert modul["ad"].strip()
    assert isinstance(
        modul["baslik"],
        str,
    )
    assert modul["baslik"].strip()
    assert isinstance(
        modul["aciklama"],
        str,
    )
    assert modul["aciklama"].strip()
    assert isinstance(
        modul["islemler"],
        list,
    )
    assert modul["islemler"]


@pytest.mark.parametrize(
    ("beklenen_kod", "girdi"),
    API_SENARYOLARI,
)
def test_module_detail_api_normalizes_codes(
    beklenen_kod,
    girdi,
):
    response = client.get(
        "/api/v2/modul-katalogu/"
        + quote(
            girdi,
            safe="",
        )
    )

    assert response.status_code == 200

    modul = response.json()

    assert modul["kod"] == beklenen_kod
    assert modul["ad"]
    assert modul["baslik"]
    assert modul["aciklama"]
    assert isinstance(
        modul["islemler"],
        list,
    )
    assert modul["islemler"]
