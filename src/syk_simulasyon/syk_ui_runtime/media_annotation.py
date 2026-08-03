from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


@dataclass(frozen=True, slots=True)
class AnnotationResult:
    output_path: str
    output_sha256: str
    width: int
    height: int
    candidate_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "output_path": self.output_path,
            "output_sha256": (
                self.output_sha256
            ),
            "width": self.width,
            "height": self.height,
            "candidate_count": (
                self.candidate_count
            ),
        }


class MediaAnnotationEngine:
    def render(
        self,
        *,
        source_content: bytes,
        candidates: list[dict[str, Any]],
        output_path: str | Path,
    ) -> AnnotationResult:
        if not source_content:
            raise ValueError(
                "İşaretlenecek görüntü boş olamaz."
            )

        output = Path(output_path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with Image.open(
            BytesIO(source_content)
        ) as source:
            image = source.convert("RGB")

        draw = ImageDraw.Draw(
            image,
            "RGBA",
        )

        font = ImageFont.load_default()

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            box = candidate.get(
                "box",
                {},
            )

            x = self._normalized(
                box.get("x", 0.0)
            )

            y = self._normalized(
                box.get("y", 0.0)
            )

            width = self._normalized(
                box.get("width", 0.0)
            )

            height = self._normalized(
                box.get("height", 0.0)
            )

            if width <= 0.0 or height <= 0.0:
                continue

            left = round(
                x * image.width
            )

            top = round(
                y * image.height
            )

            right = round(
                min(
                    1.0,
                    x + width,
                )
                * image.width
            )

            bottom = round(
                min(
                    1.0,
                    y + height,
                )
                * image.height
            )

            confidence = float(
                candidate.get(
                    "confidence",
                    0.0,
                )
            )

            label = str(
                candidate.get(
                    "title",
                    candidate.get(
                        "label",
                        "Dikkat bölgesi",
                    ),
                )
            )

            line_width = max(
                2,
                round(
                    min(
                        image.width,
                        image.height,
                    )
                    / 220
                ),
            )

            draw.rectangle(
                (
                    left,
                    top,
                    right,
                    bottom,
                ),
                outline=(
                    55,
                    223,
                    255,
                    255,
                ),
                width=line_width,
            )

            corner_length = max(
                8,
                round(
                    min(
                        right - left,
                        bottom - top,
                    )
                    * 0.18
                ),
            )

            self._draw_corners(
                draw=draw,
                left=left,
                top=top,
                right=right,
                bottom=bottom,
                length=corner_length,
                width=line_width + 1,
            )

            badge = (
                f"{index:02d}  "
                f"%{confidence:.1f}"
            )

            text_box = draw.textbbox(
                (0, 0),
                badge,
                font=font,
            )

            badge_width = (
                text_box[2]
                - text_box[0]
                + 12
            )

            badge_height = (
                text_box[3]
                - text_box[1]
                + 8
            )

            badge_top = max(
                0,
                top - badge_height,
            )

            draw.rounded_rectangle(
                (
                    left,
                    badge_top,
                    left + badge_width,
                    badge_top + badge_height,
                ),
                radius=4,
                fill=(
                    2,
                    29,
                    36,
                    225,
                ),
                outline=(
                    55,
                    223,
                    255,
                    255,
                ),
                width=1,
            )

            draw.text(
                (
                    left + 6,
                    badge_top + 4,
                ),
                badge,
                font=font,
                fill=(
                    225,
                    252,
                    255,
                    255,
                ),
            )

            if image.width >= 500:
                description = (
                    label[:52]
                )

                draw.text(
                    (
                        left + 4,
                        min(
                            image.height - 12,
                            bottom + 4,
                        ),
                    ),
                    description,
                    font=font,
                    fill=(
                        210,
                        247,
                        252,
                        255,
                    ),
                    stroke_width=2,
                    stroke_fill=(
                        2,
                        20,
                        26,
                        220,
                    ),
                )

        image.save(
            output,
            format="PNG",
            optimize=True,
        )

        payload = output.read_bytes()

        return AnnotationResult(
            output_path=str(output),
            output_sha256=sha256(
                payload
            ).hexdigest(),
            width=image.width,
            height=image.height,
            candidate_count=len(
                candidates
            ),
        )

    @staticmethod
    def _normalized(
        value: Any,
    ) -> float:
        number = float(value)

        return min(
            1.0,
            max(
                0.0,
                number,
            ),
        )

    @staticmethod
    def _draw_corners(
        *,
        draw: ImageDraw.ImageDraw,
        left: int,
        top: int,
        right: int,
        bottom: int,
        length: int,
        width: int,
    ) -> None:
        color = (
            214,
            248,
            255,
            255,
        )

        segments = (
            (
                (left, top + length),
                (left, top),
                (left + length, top),
            ),
            (
                (right - length, top),
                (right, top),
                (right, top + length),
            ),
            (
                (left, bottom - length),
                (left, bottom),
                (left + length, bottom),
            ),
            (
                (right - length, bottom),
                (right, bottom),
                (right, bottom - length),
            ),
        )

        for segment in segments:
            draw.line(
                segment,
                fill=color,
                width=width,
                joint="curve",
            )