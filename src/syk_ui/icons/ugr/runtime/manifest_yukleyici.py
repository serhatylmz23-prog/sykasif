"""UGR prototip ikon manifest yükleyicisi."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .modeller import IkonRuntimeKaydi


class IkonManifestHatasi(ValueError):
    """UGR ikon manifesti geçersiz."""


def manifest_oku(
    manifest_yolu: str | Path,
) -> dict[str, Any]:
    """UTF-8 veya UTF-8 BOM manifesti güvenli şekilde okur."""

    yol = Path(manifest_yolu)

    if not yol.exists():
        raise FileNotFoundError(yol)

    try:
        veri = json.loads(
            yol.read_text(
                encoding="utf-8-sig"
            )
        )
    except json.JSONDecodeError as exc:
        raise IkonManifestHatasi(
            f"Geçersiz ikon manifesti: {yol}"
        ) from exc

    if not isinstance(veri, dict):
        raise IkonManifestHatasi(
            "Manifest kökü nesne olmalıdır."
        )

    ikonlar = veri.get("icons")

    if not isinstance(ikonlar, list):
        raise IkonManifestHatasi(
            "Manifest 'icons' listesi taşımıyor."
        )

    return veri


def runtime_kayitlari_uret(
    manifest_yolu: str | Path,
) -> tuple[IkonRuntimeKaydi, ...]:
    """Prototip ikon manifestini runtime kayıtlarına dönüştürür."""

    veri = manifest_oku(
        manifest_yolu
    )

    kayitlar: list[IkonRuntimeKaydi] = []

    for sira, ikon in enumerate(
        veri["icons"],
        start=1,
    ):
        if not isinstance(ikon, dict):
            raise IkonManifestHatasi(
                f"{sira}. ikon kaydı nesne değil."
            )

        kimlik = str(
            ikon.get(
                "temporary_id",
                ikon.get(
                    "temporary_identifier",
                    "",
                ),
            )
        ).strip()

        kategori = str(
            ikon.get("category", "")
        ).strip()

        etiket = str(
            ikon.get(
                "label",
                ikon.get(
                    "filename",
                    kimlik,
                ),
            )
        ).strip()

        dosya_yolu = str(
            ikon.get(
                "path",
                ikon.get(
                    "relative_path",
                    "",
                ),
            )
        ).strip()

        if not kimlik:
            raise IkonManifestHatasi(
                f"{sira}. ikon kimliği boş."
            )

        kayitlar.append(
            IkonRuntimeKaydi(
                ikon_kimligi=kimlik,
                kategori=kategori,
                dosya_yolu=dosya_yolu,
                etiket=etiket,
                meta_veri={
                    "manifest_sirasi": sira,
                    "kalici_kimlik": ikon.get(
                        "permanent_id",
                        ikon.get(
                            "permanent_identifier",
                        None,
                        ),
                    ),
                    "sha256": ikon.get(
                        "sha256"
                    ),
                },
            )
        )

    return tuple(kayitlar)
