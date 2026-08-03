from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Iterable

from .frame_models import FrameRecord


@dataclass(frozen=True, slots=True)
class CandidateBox:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        values = (
            self.x,
            self.y,
            self.width,
            self.height,
        )

        if not all(
            math.isfinite(value)
            for value in values
        ):
            raise ValueError(
                "Aday kutusu değerleri "
                "sonlu olmalıdır."
            )

        if (
            self.x < 0.0
            or self.y < 0.0
            or self.width <= 0.0
            or self.height <= 0.0
            or self.x + self.width > 1.0
            or self.y + self.height > 1.0
        ):
            raise ValueError(
                "Aday kutusu normalize görüntü "
                "sınırları içinde olmalıdır."
            )

    @property
    def area(self) -> float:
        return self.width * self.height

    def as_dict(self) -> dict[str, float]:
        return {
            "x": round(self.x, 6),
            "y": round(self.y, 6),
            "width": round(
                self.width,
                6,
            ),
            "height": round(
                self.height,
                6,
            ),
        }


@dataclass(frozen=True, slots=True)
class FrameCandidate:
    candidate_id: str
    frame_id: str
    kind: str
    label: str
    confidence: float
    uncertainty: float
    box: CandidateBox
    metrics: dict[str, float]
    methods: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "candidate_id": (
                self.candidate_id
            ),
            "frame_id": self.frame_id,
            "kind": self.kind,
            "label": self.label,
            "confidence": round(
                min(99.9, self.confidence),
                3,
            ),
            "uncertainty": round(
                min(
                    100.0,
                    max(
                        0.0,
                        self.uncertainty,
                    ),
                ),
                3,
            ),
            "box": self.box.as_dict(),
            "metrics": {
                key: round(value, 6)
                for key, value
                in self.metrics.items()
            },
            "methods": list(
                self.methods
            ),
            "status": "candidate",
            "analysis_scope": (
                "digital_visual_candidate"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


@dataclass(frozen=True, slots=True)
class CandidateAnalysis:
    frame_id: str
    width: int
    height: int
    channels: int
    candidates: tuple[
        FrameCandidate,
        ...,
    ]
    global_metrics: dict[str, float]

    def as_dict(self) -> dict:
        return {
            "schema": (
                "sykasif-frame-candidates/v1"
            ),
            "frame_id": self.frame_id,
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "candidate_count": len(
                self.candidates
            ),
            "candidates": [
                candidate.as_dict()
                for candidate
                in self.candidates
            ],
            "global_metrics": {
                key: round(value, 6)
                for key, value
                in self.global_metrics.items()
            },
            "analysis_scope": (
                "digital_visual_candidates"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


class FrameCandidateEngine:
    """
    Ham gri/RGB/RGBA karelerden açıklanabilir
    dikkat bölgesi adayları üretir.

    Bu motor nesnenin ne olduğunu kesin olarak
    sınıflandırmaz. Yalnız dikkat çeken görsel
    bölgeleri candidate olarak işaretler.
    """

    SUPPORTED_CHANNELS = {
        1,
        3,
        4,
    }

    def __init__(
        self,
        *,
        grid_columns: int = 8,
        grid_rows: int = 6,
        minimum_score: float = 0.32,
        maximum_candidates: int = 8,
    ) -> None:
        if grid_columns < 2:
            raise ValueError(
                "Izgara sütun sayısı en az 2 olmalıdır."
            )

        if grid_rows < 2:
            raise ValueError(
                "Izgara satır sayısı en az 2 olmalıdır."
            )

        if not 0.0 <= minimum_score <= 1.0:
            raise ValueError(
                "Minimum aday puanı 0 ile 1 "
                "arasında olmalıdır."
            )

        if maximum_candidates <= 0:
            raise ValueError(
                "Maksimum aday sayısı pozitif olmalıdır."
            )

        self.grid_columns = grid_columns
        self.grid_rows = grid_rows
        self.minimum_score = minimum_score
        self.maximum_candidates = (
            maximum_candidates
        )

    def analyze(
        self,
        *,
        record: FrameRecord,
        pixels: bytes,
        channels: int,
    ) -> CandidateAnalysis:
        self._validate_pixels(
            record=record,
            pixels=pixels,
            channels=channels,
        )

        luminance = self._to_luminance(
            pixels=pixels,
            channels=channels,
        )

        global_mean = statistics.fmean(
            luminance
        )

        global_std = self._std(
            luminance
        )

        cells = self._build_cells(
            luminance=luminance,
            width=record.frame_width,
            height=record.frame_height,
        )

        scored = []

        for cell in cells:
            metrics = self._cell_metrics(
                luminance=luminance,
                width=record.frame_width,
                height=record.frame_height,
                cell=cell,
                global_mean=global_mean,
                global_std=global_std,
            )

            score = self._score(
                metrics
            )

            if score < self.minimum_score:
                continue

            scored.append(
                (
                    score,
                    cell,
                    metrics,
                )
            )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        selected = self._suppress_overlap(
            scored
        )

        candidates = tuple(
            self._candidate(
                record=record,
                sequence=index,
                score=score,
                cell=cell,
                metrics=metrics,
            )
            for index, (
                score,
                cell,
                metrics,
            )
            in enumerate(
                selected,
                start=1,
            )
        )

        return CandidateAnalysis(
            frame_id=record.frame_id,
            width=record.frame_width,
            height=record.frame_height,
            channels=channels,
            candidates=candidates,
            global_metrics={
                "mean_luminance": (
                    global_mean
                ),
                "luminance_std": (
                    global_std
                ),
                "evaluated_cells": float(
                    len(cells)
                ),
                "selected_cells": float(
                    len(candidates)
                ),
            },
        )

    def _validate_pixels(
        self,
        *,
        record: FrameRecord,
        pixels: bytes,
        channels: int,
    ) -> None:
        if channels not in self.SUPPORTED_CHANNELS:
            raise ValueError(
                "Kanal sayısı 1, 3 veya 4 olmalıdır."
            )

        if not isinstance(
            pixels,
            bytes,
        ):
            raise TypeError(
                "Piksel verisi bytes olmalıdır."
            )

        expected = (
            record.frame_width
            * record.frame_height
            * channels
        )

        if len(pixels) != expected:
            raise ValueError(
                "Piksel uzunluğu kare boyutlarıyla "
                "uyuşmuyor. "
                f"Beklenen={expected}, "
                f"Gelen={len(pixels)}"
            )

    def _to_luminance(
        self,
        *,
        pixels: bytes,
        channels: int,
    ) -> list[float]:
        if channels == 1:
            return [
                value / 255.0
                for value in pixels
            ]

        output: list[float] = []

        for index in range(
            0,
            len(pixels),
            channels,
        ):
            red = pixels[index]
            green = pixels[index + 1]
            blue = pixels[index + 2]

            value = (
                red * 0.2126
                + green * 0.7152
                + blue * 0.0722
            ) / 255.0

            output.append(value)

        return output

    def _build_cells(
        self,
        *,
        luminance: list[float],
        width: int,
        height: int,
    ) -> list[tuple[int, int, int, int]]:
        del luminance

        cell_width = max(
            1,
            math.ceil(
                width / self.grid_columns
            ),
        )

        cell_height = max(
            1,
            math.ceil(
                height / self.grid_rows
            ),
        )

        cells = []

        for y in range(
            0,
            height,
            cell_height,
        ):
            for x in range(
                0,
                width,
                cell_width,
            ):
                cells.append(
                    (
                        x,
                        y,
                        min(
                            width,
                            x + cell_width,
                        ),
                        min(
                            height,
                            y + cell_height,
                        ),
                    )
                )

        return cells

    def _cell_metrics(
        self,
        *,
        luminance: list[float],
        width: int,
        height: int,
        cell: tuple[
            int,
            int,
            int,
            int,
        ],
        global_mean: float,
        global_std: float,
    ) -> dict[str, float]:
        x0, y0, x1, y1 = cell

        values = [
            luminance[
                y * width + x
            ]
            for y in range(y0, y1)
            for x in range(x0, x1)
        ]

        local_mean = statistics.fmean(
            values
        )

        local_std = self._std(
            values
        )

        contrast = abs(
            local_mean - global_mean
        )

        texture_delta = abs(
            local_std - global_std
        )

        edge_density = (
            self._edge_density(
                luminance=luminance,
                width=width,
                height=height,
                cell=cell,
            )
        )

        return {
            "local_mean": local_mean,
            "local_std": local_std,
            "contrast": contrast,
            "texture_delta": (
                texture_delta
            ),
            "edge_density": (
                edge_density
            ),
        }

    def _edge_density(
        self,
        *,
        luminance: list[float],
        width: int,
        height: int,
        cell: tuple[
            int,
            int,
            int,
            int,
        ],
    ) -> float:
        x0, y0, x1, y1 = cell
        edge_total = 0.0
        comparisons = 0

        for y in range(y0, y1):
            for x in range(x0, x1):
                current = luminance[
                    y * width + x
                ]

                if x + 1 < min(
                    width,
                    x1,
                ):
                    edge_total += abs(
                        current
                        - luminance[
                            y * width
                            + x
                            + 1
                        ]
                    )
                    comparisons += 1

                if y + 1 < min(
                    height,
                    y1,
                ):
                    edge_total += abs(
                        current
                        - luminance[
                            (y + 1)
                            * width
                            + x
                        ]
                    )
                    comparisons += 1

        if comparisons == 0:
            return 0.0

        return edge_total / comparisons

    def _score(
        self,
        metrics: dict[str, float],
    ) -> float:
        contrast = min(
            1.0,
            metrics["contrast"] * 2.4,
        )

        texture = min(
            1.0,
            metrics["texture_delta"] * 3.2,
        )

        edge = min(
            1.0,
            metrics["edge_density"] * 3.0,
        )

        return min(
            1.0,
            contrast * 0.45
            + texture * 0.25
            + edge * 0.30,
        )

    def _suppress_overlap(
        self,
        scored: Iterable[
            tuple[
                float,
                tuple[int, int, int, int],
                dict[str, float],
            ]
        ],
    ) -> list[
        tuple[
            float,
            tuple[int, int, int, int],
            dict[str, float],
        ]
    ]:
        selected = []

        for item in scored:
            if len(selected) >= (
                self.maximum_candidates
            ):
                break

            score, cell, metrics = item

            if any(
                self._intersection_ratio(
                    cell,
                    existing[1],
                ) >= 0.65
                for existing in selected
            ):
                continue

            selected.append(
                (
                    score,
                    cell,
                    metrics,
                )
            )

        return selected

    @staticmethod
    def _intersection_ratio(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> float:
        fx0, fy0, fx1, fy1 = first
        sx0, sy0, sx1, sy1 = second

        intersection_width = max(
            0,
            min(fx1, sx1)
            - max(fx0, sx0),
        )

        intersection_height = max(
            0,
            min(fy1, sy1)
            - max(fy0, sy0),
        )

        intersection = (
            intersection_width
            * intersection_height
        )

        if intersection == 0:
            return 0.0

        first_area = (
            (fx1 - fx0)
            * (fy1 - fy0)
        )

        second_area = (
            (sx1 - sx0)
            * (sy1 - sy0)
        )

        return intersection / min(
            first_area,
            second_area,
        )

    def _candidate(
        self,
        *,
        record: FrameRecord,
        sequence: int,
        score: float,
        cell: tuple[int, int, int, int],
        metrics: dict[str, float],
    ) -> FrameCandidate:
        x0, y0, x1, y1 = cell

        methods = []

        if metrics["contrast"] >= 0.12:
            methods.append(
                "luminance_contrast"
            )

        if (
            metrics["texture_delta"]
            >= 0.08
        ):
            methods.append(
                "texture_variation"
            )

        if (
            metrics["edge_density"]
            >= 0.08
        ):
            methods.append(
                "edge_density"
            )

        if not methods:
            methods.append(
                "combined_visual_score"
            )

        dominant = max(
            (
                (
                    "contrast",
                    metrics["contrast"],
                ),
                (
                    "texture",
                    metrics[
                        "texture_delta"
                    ],
                ),
                (
                    "edge",
                    metrics[
                        "edge_density"
                    ],
                ),
            ),
            key=lambda item: item[1],
        )[0]

        labels = {
            "contrast": (
                "Parlaklık / renk sapması adayı"
            ),
            "texture": (
                "Doku değişimi adayı"
            ),
            "edge": (
                "Kenar / geometrik düzen adayı"
            ),
        }

        confidence = min(
            99.9,
            55.0 + score * 44.9,
        )

        uncertainty = max(
            0.1,
            100.0 - confidence,
        )

        return FrameCandidate(
            candidate_id=(
                f"{record.frame_id}-C"
                f"{sequence:03d}"
            ),
            frame_id=record.frame_id,
            kind="visual_anomaly",
            label=labels[dominant],
            confidence=confidence,
            uncertainty=uncertainty,
            box=CandidateBox(
                x=x0 / record.frame_width,
                y=y0 / record.frame_height,
                width=(
                    (x1 - x0)
                    / record.frame_width
                ),
                height=(
                    (y1 - y0)
                    / record.frame_height
                ),
            ),
            metrics=metrics,
            methods=tuple(methods),
        )

    @staticmethod
    def _std(
        values: list[float],
    ) -> float:
        if len(values) < 2:
            return 0.0

        return statistics.pstdev(
            values
        )