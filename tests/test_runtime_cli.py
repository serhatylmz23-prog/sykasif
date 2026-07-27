from pathlib import Path

from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_cli import RuntimeCli
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_dosya_yazicisi import RuntimeDosyaYazicisi
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_markdown import RuntimeMarkdownSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


def _cli() -> RuntimeCli:
    servis = RuntimeServisi()

    gorunum = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    disa_aktarim = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(gorunum),
        RuntimeCsvSaglayicisi(gorunum),
        RuntimeHtmlSaglayicisi(gorunum),
        RuntimeMarkdownSaglayicisi(gorunum),
        RuntimeXmlSaglayicisi(gorunum),
        RuntimeYamlSaglayicisi(gorunum),
    )

    return RuntimeCli(RuntimeDosyaYazicisi(disa_aktarim))


def test_json_cli(tmp_path: Path):
    hedef = tmp_path / "runtime.json"

    sonuc = _cli().calistir([
        "--format", "json",
        "--output", str(hedef),
    ])

    assert sonuc == 0
    assert hedef.exists()


def test_html_cli(tmp_path: Path):
    hedef = tmp_path / "runtime.html"

    sonuc = _cli().calistir([
        "--format", "html",
        "--output", str(hedef),
    ])

    assert sonuc == 0
    assert hedef.exists()


def test_yaml_cli(tmp_path: Path):
    hedef = tmp_path / "runtime.yaml"

    sonuc = _cli().calistir([
        "--format", "yaml",
        "--output", str(hedef),
    ])

    assert sonuc == 0
    assert hedef.exists()