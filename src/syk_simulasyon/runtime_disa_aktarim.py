from __future__ import annotations

from .runtime_csv import RuntimeCsvSaglayicisi
from .runtime_html import RuntimeHtmlSaglayicisi
from .runtime_json import RuntimeJsonSaglayicisi
from .runtime_markdown import RuntimeMarkdownSaglayicisi
from .runtime_xml import RuntimeXmlSaglayicisi
from .runtime_yaml import RuntimeYamlSaglayicisi


class RuntimeDisaAktarim:
    """Runtime çıktılarını farklı formatlarda üretir."""

    def __init__(
        self,
        json: RuntimeJsonSaglayicisi,
        csv: RuntimeCsvSaglayicisi,
        html: RuntimeHtmlSaglayicisi,
        markdown: RuntimeMarkdownSaglayicisi,
        xml: RuntimeXmlSaglayicisi,
        yaml: RuntimeYamlSaglayicisi,
    ) -> None:
        self._json = json
        self._csv = csv
        self._html = html
        self._markdown = markdown
        self._xml = xml
        self._yaml = yaml

    def json(self) -> str:
        return self._json.json_uret()

    def csv(self) -> str:
        return self._csv.csv_uret()

    def html(self) -> str:
        return self._html.html_uret()

    def markdown(self) -> str:
        return self._markdown.markdown_uret()

    def xml(self) -> str:
        return self._xml.xml_uret()

    def yaml(self) -> str:
        return self._yaml.yaml_uret()