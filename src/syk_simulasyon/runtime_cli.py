from __future__ import annotations

import argparse
from pathlib import Path

from .runtime_dosya_yazicisi import RuntimeDosyaYazicisi


class RuntimeCli:
    """Runtime dışa aktarma komut satırı arayüzü."""

    def __init__(self, yazici: RuntimeDosyaYazicisi) -> None:
        self._yazici = yazici

    def calistir(self, argv: list[str]) -> int:
        parser = argparse.ArgumentParser(prog="sykasif-runtime")
        parser.add_argument(
            "--format",
            choices=["json", "csv", "html", "markdown", "xml", "yaml"],
            required=True,
        )
        parser.add_argument(
            "--output",
            required=True,
        )

        args = parser.parse_args(argv)

        hedef = Path(args.output)

        match args.format:
            case "json":
                self._yazici.json_yaz(hedef)
            case "csv":
                self._yazici.csv_yaz(hedef)
            case "html":
                self._yazici.html_yaz(hedef)
            case "markdown":
                self._yazici.markdown_yaz(hedef)
            case "xml":
                self._yazici.xml_yaz(hedef)
            case "yaml":
                self._yazici.yaml_yaz(hedef)

        return 0