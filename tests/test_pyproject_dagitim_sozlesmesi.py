from __future__ import annotations

from pathlib import Path
import tomllib


PROJE_KOKU = Path(__file__).resolve().parents[1]
PYPROJECT = PROJE_KOKU / "pyproject.toml"


def pyproject_verisi() -> dict[str, object]:
    with PYPROJECT.open("rb") as dosya:
        return tomllib.load(dosya)


def test_build_backend_setuptools_olarak_sabit() -> None:
    veri = pyproject_verisi()
    build_system = veri["build-system"]

    assert build_system["build-backend"] == (
        "setuptools.build_meta"
    )
    assert "setuptools>=68" in build_system["requires"]


def test_paket_kesfi_yalniz_src_dizinine_bagli() -> None:
    veri = pyproject_verisi()
    setuptools = veri["tool"]["setuptools"]

    assert setuptools["package-dir"] == {"": "src"}

    paket_kesfi = setuptools["packages"]["find"]

    assert paket_kesfi["where"] == ["src"]
    assert paket_kesfi["include"] == [
        "syk_simulasyon*",
        "syk_core*",
    ]
    assert paket_kesfi["exclude"] == ["tests*"]


def test_src_altinda_tek_urun_paketi_var() -> None:
    src = PROJE_KOKU / "src"

    paketler = sorted(
        yol.parent.relative_to(src).as_posix()
        for yol in src.rglob("__init__.py")
        if "__pycache__" not in yol.parts
    )

    assert paketler == [
        "syk_core",
        "syk_core/ecosystem",
        "syk_core/entegrasyon",
        "syk_core/integration",
        "syk_core/learning",
        "syk_core/live_analysis",
        "syk_core/live_persistence",
        "syk_core/ovm",
        "syk_core/runtime_device_link",
        "syk_core/runtime_field_link",
        "syk_core/runtime_kernel",
        "syk_core/runtime_prototype",
        "syk_core/runtime_terminal",
        "syk_finans_otagi",
        "syk_jarmin",
        "syk_simulasyon",
    ]


def test_build_ve_dist_git_disinda() -> None:
    gitignore = (
        PROJE_KOKU / ".gitignore"
    ).read_text(encoding="utf-8").splitlines()

    kurallar = {
        satir.strip()
        for satir in gitignore
        if satir.strip()
    }

    assert "build/" in kurallar
    assert "dist/" in kurallar
    assert "*.egg-info/" in kurallar


def test_paket_disinda_python_kaynagi_yok() -> None:
    src = PROJE_KOKU / "src"

    izinli_urunler = {
        "syk_simulasyon",
        "syk_core",
        "syk_jarmin",
        "syk_finans_otagi",
        "syk_core/ecosystem",
        "syk_core/integration",
        "syk_core/learning",
        "syk_core/live_analysis",
        "syk_core/live_persistence",
        "syk_core/ovm",
    }

    paket_disindakiler = [
        yol.relative_to(src).as_posix()
        for yol in src.rglob("*.py")
        if not (
            set(yol.relative_to(src).parts)
            & izinli_urunler
        )
    ]

    assert paket_disindakiler == []
