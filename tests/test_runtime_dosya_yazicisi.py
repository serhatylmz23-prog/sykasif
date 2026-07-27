from pathlib import Path

from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
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


def _yazici() -> RuntimeDosyaYazicisi:
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

    return RuntimeDosyaYazicisi(disa_aktarim)


def test_json_dosyaya_yazilir(tmp_path: Path):
    hedef = tmp_path / "runtime.json"

    sonuc = _yazici().json_yaz(hedef)

    assert sonuc == hedef
    assert hedef.exists()
    assert "durum" in hedef.read_text(encoding="utf-8")


def test_html_dosyaya_yazilir(tmp_path: Path):
    hedef = tmp_path / "rapor" / "runtime.html"

    sonuc = _yazici().html_yaz(hedef)

    assert sonuc == hedef
    assert hedef.exists()
    assert "<table>" in hedef.read_text(encoding="utf-8")


def test_tum_formatlar_dosyaya_yazilir(tmp_path: Path):
    yazici = _yazici()

    hedefler = (
        yazici.json_yaz(tmp_path / "runtime.json"),
        yazici.csv_yaz(tmp_path / "runtime.csv"),
        yazici.html_yaz(tmp_path / "runtime.html"),
        yazici.markdown_yaz(tmp_path / "runtime.md"),
        yazici.xml_yaz(tmp_path / "runtime.xml"),
        yazici.yaml_yaz(tmp_path / "runtime.yaml"),
    )

    assert all(hedef.exists() for hedef in hedefler)