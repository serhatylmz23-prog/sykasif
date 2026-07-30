from __future__ import annotations

from pathlib import Path
import tomllib


def _pyproject() -> dict:
    yol = Path(__file__).parents[1] / "pyproject.toml"

    with yol.open("rb") as dosya:
        return tomllib.load(dosya)


def test_runtime_bagimliliklari_tanimlidir():
    proje = _pyproject()["project"]
    bagimliliklar = proje["dependencies"]

    assert any(
        deger.startswith("fastapi>=")
        for deger in bagimliliklar
    )
    assert any(
        deger.startswith("uvicorn>=")
        for deger in bagimliliklar
    )
    assert any(
        deger.startswith("websockets>=")
        for deger in bagimliliklar
    )


def test_tarayıcı_test_bagimliliklari_ayri_gruptadir():
    proje = _pyproject()["project"]
    test_bagimliliklari = (
        proje["optional-dependencies"]["test"]
    )

    beklenenler = (
        "httpx",
        "pytest",
        "playwright",
        "pytest-playwright",
    )

    for paket in beklenenler:
        assert any(
            deger.startswith(f"{paket}>=")
            for deger in test_bagimliliklari
        )


def test_python_alt_surumu_korunur():
    proje = _pyproject()["project"]

    assert proje["requires-python"] == ">=3.11"
