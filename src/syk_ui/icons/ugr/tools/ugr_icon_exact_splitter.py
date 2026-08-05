from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageChops


@dataclass(frozen=True, slots=True)
class SheetDefinition:
    order: int
    category: str
    filename: str
    prefix: str
    columns: int
    rows: int
    content_box: tuple[int, int, int, int]
    labels: tuple[str, ...]


ANA_SISTEM = (
    "harita",
    "katman",
    "gorev",
    "kanit",
    "analiz",
    "rapor",
    "yapay_zeka",
    "zaman",
    "ar",
    "2b",
    "3b",
    "4d",
    "tarama",
    "sinyal",
    "drone",
    "gps_rtk",
    "goruntu",
    "ses",
    "kimya",
    "botanik",
    "jeoloji",
    "manyetometre",
    "gravimetre",
    "spektral",
    "termal",
    "gpr",
    "sismik",
    "hidrojeoloji",
    "guvenlik",
    "ayarlar",
)

BILIMSEL_SENSORLER = (
    "drone",
    "sonar",
    "spektral",
    "termal",
    "manyetik",
    "ert",
    "gpr",
    "sismik",
    "su_analizi",
    "toprak_analizi",
    "botanik",
    "jeoloji",
    "lidar",
    "multispektral",
    "hiperspektral",
    "radyometrik",
    "gravimetre",
    "manyetometre",
    "elektromanyetik",
    "infrared",
    "ultraviyole",
    "x_isini_floresans",
    "kimyasal_sensor",
    "gaz_sensoru",
    "ph_olcer",
    "oksijen_sensoru",
    "nem_sensoru",
    "sicaklik_sensoru",
    "basinc_sensoru",
    "akis_sensoru",
    "tuzluluk_sensoru",
    "bulaniklik_sensoru",
    "sivi_kromatografi",
    "kutle_spektrometri",
    "dna_analizi",
    "mikroskop",
    "partikul_sayaci",
    "ruzgar_sensoru",
    "gunes_radyasyonu",
    "isik_sensoru",
)

CANLI_DURUMLAR = (
    "bekliyor",
    "calisiyor",
    "tariyor",
    "dogrulaniyor",
    "tamamlandi",
    "basarili",
    "uyari",
    "hata",
    "cevrimdisi",
    "yeni_veri",
    "yeni_kanit",
    "yeni_rapor",
    "senkronize",
    "yukleniyor",
    "indiriliyor",
    "guncelleniyor",
    "aktif",
    "pasif",
    "kilitli",
    "kilit_acik",
    "yedekleniyor",
    "yedeklendi",
    "paylasiliyor",
    "baglaniyor",
    "baglandi",
    "koparildi",
    "konum_tespit",
    "gps_sinyali",
    "sinyal_zayif",
    "sinyal_guclu",
    "pil_dolu",
    "pil_orta",
    "pil_dusuk",
    "isinma",
    "soguma",
    "zaman_damgasi",
    "takvim",
    "surec_plani",
    "ilerleme",
    "hedef",
    "kalibrasyon",
    "analiz_ediliyor",
    "onay_bekliyor",
    "arsivleniyor",
    "arsivlendi",
)

EKOSISTEM_MODULLERI = (
    "sykasif",
    "syfinansotagi",
    "marina",
    "balikcilik",
    "enerji",
    "lojistik",
    "kafe",
    "yayin",
    "guzellik",
    "benzinlik",
    "teknoloji",
    "egitim",
    "saglik",
    "tarim",
    "insaat",
    "turizm",
    "otelcilik",
    "guvenlik",
    "medya",
    "sinema",
    "otomotiv",
    "tersane",
    "madencilik",
    "kimya",
    "tekstil",
    "e_ticaret",
    "restoran",
    "gayrimenkul",
    "spor",
    "etkinlik",
    "su_yonetimi",
    "geri_donusum",
    "gunes_enerjisi",
    "ruzgar_enerjisi",
    "hidroelektrik",
    "enerji_depolama",
    "akilli_sehir",
    "uydu",
    "arge",
    "danismanlik",
    "deniz_tasimaciligi",
    "hava_tasimaciligi",
    "demiryolu",
    "depolama",
    "gumruk",
    "soguk_zincir",
    "sigorta",
    "hukuk",
    "insan_kaynaklari",
    "pazarlama",
)

HARITA_NESNELERI = (
    "arastirma_noktasi",
    "fotograf",
    "video",
    "ses",
    "olcum",
    "rota",
    "iz",
    "kamp",
    "kazi",
    "numune",
    "risk",
    "tehlike_alani",
    "guvenli_alan",
    "ilgi_alani",
    "hedef",
    "bakis_noktasi",
    "panorama",
    "2b_harita",
    "3b_harita",
    "katman",
    "yol",
    "patika",
    "kopru",
    "gecit",
    "sinir",
    "alan",
    "kareleme",
    "koordinat",
    "yukseklik",
    "derinlik",
    "su_kaynagi",
    "magara",
    "kaya_olusumu",
    "magara_girisi",
    "orman",
    "tarim_alani",
    "yerlesim",
    "yapi",
    "anit",
    "heykel",
    "mezar",
    "yazit",
    "sikke",
    "taki",
    "seramik",
    "metal_obje",
    "cam_obje",
    "organik_ornek",
    "fosil",
    "belirsiz_nesne",
)


SHEETS = (
    SheetDefinition(
        order=1,
        category="ana_sistem",
        filename="01_ana_sistem.png",
        prefix="sys",
        columns=6,
        rows=5,
        content_box=(20, 0, 1516, 1024),
        labels=ANA_SISTEM,
    ),
    SheetDefinition(
        order=2,
        category="bilimsel_sensorler",
        filename="02_bilimsel_sensorler.png",
        prefix="sci",
        columns=8,
        rows=5,
        content_box=(20, 54, 1516, 1008),
        labels=BILIMSEL_SENSORLER,
    ),
    SheetDefinition(
        order=3,
        category="canli_durumlar",
        filename="03_canli_durumlar.png",
        prefix="sta",
        columns=9,
        rows=5,
        content_box=(20, 55, 1516, 1002),
        labels=CANLI_DURUMLAR,
    ),
    SheetDefinition(
        order=4,
        category="ekosistem_modulleri",
        filename="04_ekosistem_modulleri.png",
        prefix="eco",
        columns=10,
        rows=5,
        content_box=(20, 54, 1516, 1000),
        labels=EKOSISTEM_MODULLERI,
    ),
    SheetDefinition(
        order=5,
        category="harita_nesneleri",
        filename="05_harita_nesneleri.png",
        prefix="map",
        columns=10,
        rows=5,
        content_box=(20, 48, 1516, 910),
        labels=HARITA_NESNELERI,
    ),
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for block in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest().upper()


def validate_definition(
    definition: SheetDefinition,
) -> None:
    expected = (
        definition.columns
        * definition.rows
    )

    actual = len(definition.labels)

    if actual != expected:
        raise RuntimeError(
            f"{definition.category}: "
            f"label count {actual}, "
            f"expected {expected}"
        )


def remove_dark_background(
    image: Image.Image,
    threshold: int = 18,
) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()

    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, alpha = (
                pixels[x, y]
            )

            brightness = max(
                red,
                green,
                blue,
            )

            if brightness <= threshold:
                pixels[x, y] = (
                    red,
                    green,
                    blue,
                    0,
                )
                continue

            fade_limit = threshold + 18

            if brightness < fade_limit:
                new_alpha = round(
                    255
                    * (
                        brightness - threshold
                    )
                    / max(
                        fade_limit - threshold,
                        1,
                    )
                )

                pixels[x, y] = (
                    red,
                    green,
                    blue,
                    min(
                        alpha,
                        new_alpha,
                    ),
                )

    return rgba


def trim_transparent(
    image: Image.Image,
    margin: int = 10,
) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    box = alpha.getbbox()

    if box is None:
        return rgba

    left, top, right, bottom = box

    left = max(
        0,
        left - margin,
    )

    top = max(
        0,
        top - margin,
    )

    right = min(
        rgba.width,
        right + margin,
    )

    bottom = min(
        rgba.height,
        bottom + margin,
    )

    return rgba.crop(
        (
            left,
            top,
            right,
            bottom,
        )
    )


def fit_canvas(
    image: Image.Image,
    size: int = 512,
    padding: int = 18,
) -> Image.Image:
    rgba = image.convert("RGBA")

    available = size - padding * 2

    scale = min(
        available / max(
            rgba.width,
            1,
        ),
        available / max(
            rgba.height,
            1,
        ),
    )

    target_width = max(
        1,
        round(
            rgba.width * scale
        ),
    )

    target_height = max(
        1,
        round(
            rgba.height * scale
        ),
    )

    resized = rgba.resize(
        (
            target_width,
            target_height,
        ),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGBA",
        (
            size,
            size,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    x = (
        size - target_width
    ) // 2

    y = (
        size - target_height
    ) // 2

    canvas.alpha_composite(
        resized,
        (
            x,
            y,
        ),
    )

    return canvas


def alpha_statistics(
    image: Image.Image,
) -> dict[str, Any]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    histogram = alpha.histogram()

    total = (
        rgba.width
        * rgba.height
    )

    transparent = histogram[0]
    opaque = histogram[255]
    semi = (
        total
        - transparent
        - opaque
    )

    return {
        "transparent_pixels": (
            transparent
        ),
        "semi_transparent_pixels": (
            semi
        ),
        "opaque_pixels": opaque,
        "transparent_ratio": round(
            transparent / total,
            8,
        ),
        "semi_transparent_ratio": round(
            semi / total,
            8,
        ),
        "opaque_ratio": round(
            opaque / total,
            8,
        ),
    }


def split_sheet(
    source_root: Path,
    output_root: Path,
    definition: SheetDefinition,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
]:
    validate_definition(
        definition
    )

    source_path = (
        source_root
        / definition.filename
    )

    if not source_path.exists():
        raise FileNotFoundError(
            source_path
        )

    with Image.open(source_path) as opened:
        source = opened.convert("RGBA")

    if source.size != (
        1536,
        1024,
    ):
        raise RuntimeError(
            f"{source_path}: "
            f"unexpected size "
            f"{source.size}"
        )

    left, top, right, bottom = (
        definition.content_box
    )

    content = source.crop(
        (
            left,
            top,
            right,
            bottom,
        )
    )

    category_root = (
        output_root
        / definition.category
    )

    if category_root.exists():
        shutil.rmtree(
            category_root
        )

    category_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    records: list[
        dict[str, Any]
    ] = []

    icon_index = 0

    for row in range(
        definition.rows
    ):
        cell_top = round(
            row
            * content.height
            / definition.rows
        )

        cell_bottom = round(
            (row + 1)
            * content.height
            / definition.rows
        )

        for column in range(
            definition.columns
        ):
            cell_left = round(
                column
                * content.width
                / definition.columns
            )

            cell_right = round(
                (column + 1)
                * content.width
                / definition.columns
            )

            cell = content.crop(
                (
                    cell_left,
                    cell_top,
                    cell_right,
                    cell_bottom,
                )
            )

            label = (
                definition.labels[
                    icon_index
                ]
            )

            temporary_id = (
                f"{definition.prefix}-"
                f"{icon_index + 1:03d}"
            )

            filename = (
                f"{icon_index + 1:03d}_"
                f"{label}.png"
            )

            transparent = (
                remove_dark_background(
                    cell
                )
            )

            trimmed = trim_transparent(
                transparent,
                margin=8,
            )

            canvas = fit_canvas(
                trimmed,
                size=512,
                padding=16,
            )

            target_path = (
                category_root
                / filename
            )

            canvas.save(
                target_path,
                format="PNG",
                optimize=True,
            )

            records.append(
                {
                    "temporary_id": (
                        temporary_id
                    ),
                    "permanent_id": None,
                    "permanent_id_status": (
                        "prototype_sonrasina_ertelendi"
                    ),
                    "category": (
                        definition.category
                    ),
                    "category_order": (
                        definition.order
                    ),
                    "index": (
                        icon_index + 1
                    ),
                    "row": row + 1,
                    "column": column + 1,
                    "label": label,
                    "filename": filename,
                    "path": (
                        target_path.as_posix()
                    ),
                    "source_cell_box": [
                        left + cell_left,
                        top + cell_top,
                        left + cell_right,
                        top + cell_bottom,
                    ],
                    "output_width": (
                        canvas.width
                    ),
                    "output_height": (
                        canvas.height
                    ),
                    "output_mode": (
                        canvas.mode
                    ),
                    "alpha": (
                        alpha_statistics(
                            canvas
                        )
                    ),
                    "sha256": (
                        sha256_file(
                            target_path
                        )
                    ),
                    "asset_status": (
                        "prototype_png"
                    ),
                    "runtime_state": (
                        "static"
                    ),
                    "animation_status": (
                        "bekliyor"
                    ),
                }
            )

            icon_index += 1

    sheet_record = {
        "order": definition.order,
        "category": (
            definition.category
        ),
        "source_filename": (
            definition.filename
        ),
        "source_path": (
            source_path.as_posix()
        ),
        "source_width": (
            source.width
        ),
        "source_height": (
            source.height
        ),
        "source_sha256": (
            sha256_file(
                source_path
            )
        ),
        "content_box": list(
            definition.content_box
        ),
        "columns": (
            definition.columns
        ),
        "rows": (
            definition.rows
        ),
        "icon_count": len(
            records
        ),
        "grid_status": (
            "gorsel_olarak_dogrulandi"
        ),
    }

    return (
        sheet_record,
        records,
    )


def build(
    source_root: Path,
    output_root: Path,
    icon_manifest_path: Path,
    sheet_manifest_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    icon_manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    sheet_records: list[
        dict[str, Any]
    ] = []

    icon_records: list[
        dict[str, Any]
    ] = []

    for definition in SHEETS:
        sheet_record, records = (
            split_sheet(
                source_root,
                output_root,
                definition,
            )
        )

        sheet_records.append(
            sheet_record
        )

        icon_records.extend(
            records
        )

    category_counts = {
        definition.category: sum(
            1
            for record in icon_records
            if record["category"]
            == definition.category
        )
        for definition in SHEETS
    }

    sheet_manifest = {
        "schema": (
            "sykasif.ugr.exact-grid.v1"
        ),
        "library": (
            "SyKaşif UGR Icon Library"
        ),
        "version": (
            "prototype-0.2"
        ),
        "created_at": utc_now(),
        "sheet_count": len(
            sheet_records
        ),
        "sheets": sheet_records,
    }

    icon_manifest = {
        "schema": (
            "sykasif.ugr.prototype-icons.v1"
        ),
        "library": (
            "SyKaşif UGR Icon Library"
        ),
        "version": (
            "prototype-0.2"
        ),
        "created_at": utc_now(),
        "icon_count": len(
            icon_records
        ),
        "category_counts": (
            category_counts
        ),
        "permanent_identifier_policy": (
            "prototype_sonrasina_ertelendi"
        ),
        "vector_status": (
            "yok"
        ),
        "svg_status": (
            "yok"
        ),
        "runtime_animation_status": (
            "bekliyor"
        ),
        "icons": icon_records,
    }

    sheet_manifest_path.write_text(
        json.dumps(
            sheet_manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    icon_manifest_path.write_text(
        json.dumps(
            icon_manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "UGR TEKİL İKON AYRIŞTIRMA RAPORU",
        "",
        f"OLUSTURULMA_ZAMANI={utc_now()}",
        (
            "TOPLAM_KAYNAK_SAYFA="
            f"{len(sheet_records)}"
        ),
        (
            "TOPLAM_TEKIL_IKON="
            f"{len(icon_records)}"
        ),
        (
            "KALICI_IKON_KIMLIGI="
            "PROTOTIP_SONRASINA_ERTELENDI"
        ),
        "CIKTI_BOYUTU=512x512",
        "CIKTI_TURU=PNG_RGBA",
        "ARKA_PLAN=SEFFAF_PROTOTIP",
        "VEKTOR_DURUMU=YOK",
        "SVG_DURUMU=YOK",
        "DINAMIK_DURUM_MAKINESI=BEKLIYOR",
        "",
        "KATEGORI_SONUCLARI:",
    ]

    for category, count in (
        category_counts.items()
    ):
        report_lines.append(
            f"{category.upper()}={count}"
        )

    report_lines.extend(
        [
            "",
            "GRIDLER:",
        ]
    )

    for sheet in sheet_records:
        report_lines.append(
            (
                f"{sheet['category']}="
                f"{sheet['columns']}x"
                f"{sheet['rows']}="
                f"{sheet['icon_count']}"
            )
        )

    report_path.write_text(
        "\n".join(
            report_lines
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "sheet_count": len(
            sheet_records
        ),
        "icon_count": len(
            icon_records
        ),
        "category_counts": (
            category_counts
        ),
        "icon_manifest": (
            icon_manifest_path.as_posix()
        ),
        "sheet_manifest": (
            sheet_manifest_path.as_posix()
        ),
        "report": (
            report_path.as_posix()
        ),
    }


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source-root",
        required=True,
    )

    parser.add_argument(
        "--output-root",
        required=True,
    )

    parser.add_argument(
        "--icon-manifest",
        required=True,
    )

    parser.add_argument(
        "--sheet-manifest",
        required=True,
    )

    parser.add_argument(
        "--report",
        required=True,
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    arguments = (
        create_parser()
        .parse_args(argv)
    )

    result = build(
        source_root=Path(
            arguments.source_root
        ),
        output_root=Path(
            arguments.output_root
        ),
        icon_manifest_path=Path(
            arguments.icon_manifest
        ),
        sheet_manifest_path=Path(
            arguments.sheet_manifest
        ),
        report_path=Path(
            arguments.report
        ),
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "UGR_EXACT_ICON_SPLIT_COMPLETED"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
