from __future__ import annotations

import ast
from pathlib import Path


def test_desktop_package_entry_exists():
    path = Path(
        "terminal_v2/desktop/__main__.py"
    )

    assert path.is_file()

    text = path.read_text(
        encoding="utf-8-sig",
    )

    assert (
        "from terminal_v2.desktop.app import main"
        in text
    )
    assert 'if __name__ == "__main__":' in text
    assert "main()" in text


def test_desktop_package_entry_compiles():
    path = Path(
        "terminal_v2/desktop/__main__.py"
    )

    ast.parse(
        path.read_text(
            encoding="utf-8-sig",
        )
    )


def test_windows_launcher_exists():
    path = Path(
        "terminal_v2/WINDOWS_MASAUSTU_BASLAT.ps1"
    )

    assert path.is_file()

    text = path.read_text(
        encoding="utf-8-sig",
    )

    assert ".venv\\Scripts\\python.exe" in text
    assert "$env:PYTHONPATH = $repo" in text
    assert (
        "$env:SYK_TERMINAL_BASE_URL = $SunucuAdresi"
        in text
    )
    assert "-m terminal_v2.desktop" in text


def test_windows_launcher_is_turkish():
    text = Path(
        "terminal_v2/WINDOWS_MASAUSTU_BASLAT.ps1"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "SYKASIF WINDOWS MASAUSTU BASLATIYOR" in text
    assert "SUNUCU" in text
    assert (
        "WINDOWS_MASAUSTU_UYGULAMASI_BASLATILAMADI"
        in text
    )
