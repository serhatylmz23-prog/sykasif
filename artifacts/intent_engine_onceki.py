from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True, slots=True)
class IntentResult:
    intent_id: str
    confidence: float
    normalized_text: str
    entities: dict[str, Any]
    requires_confirmation: bool
    user_message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "confidence": round(
                min(
                    99.9,
                    max(
                        0.0,
                        self.confidence,
                    ),
                ),
                3,
            ),
            "normalized_text": (
                self.normalized_text
            ),
            "entities": dict(
                self.entities
            ),
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "user_message": (
                self.user_message
            ),
            "analysis_scope": (
                "digital_language_routing"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


class IntentEngine:
    INTENTS = (
        {
            "id": "system_status",
            "patterns": (
                r"\bsistem durumu\b",
                r"\bdurum nedir\b",
                r"\bsistem nasıl\b",
                r"\bsağlık durumu\b",
            ),
            "message": (
                "Sistem durumu hazırlanıyor."
            ),
            "confirmation": False,
        },
        {
            "id": "open_module",
            "patterns": (
                r"\bmodülü aç\b",
                r"\bmodulü aç\b",
                r"\bmodülünü aç\b",
                r"\baç\b",
            ),
            "message": (
                "İstenen bölüm açılıyor."
            ),
            "confirmation": False,
        },
        {
            "id": "close_module",
            "patterns": (
                r"\bmodülü kapat\b",
                r"\bmodülünü kapat\b",
                r"\bkapat\b",
            ),
            "message": (
                "İstenen bölüm kapatılıyor."
            ),
            "confirmation": True,
        },
        {
            "id": "create_report",
            "patterns": (
                r"\brapor oluştur\b",
                r"\brapor hazırla\b",
                r"\bpdf oluştur\b",
                r"\bmühürlü rapor\b",
            ),
            "message": (
                "Mühürlü rapor hazırlığı "
                "başlatılıyor."
            ),
            "confirmation": True,
        },
        {
            "id": "analyze_image",
            "patterns": (
                r"\bgörüntüyü analiz et\b",
                r"\bfotoğrafı incele\b",
                r"\bvideoyu incele\b",
                r"\bgörseli incele\b",
            ),
            "message": (
                "Görüntü inceleme akışı "
                "başlatılıyor."
            ),
            "confirmation": False,
        },
        {
            "id": "theme_change",
            "patterns": (
                r"\btema\b",
                r"\baltın görünüm\b",
                r"\bgümüş görünüm\b",
                r"\bkoyu görünüm\b",
            ),
            "message": (
                "Tema tercihi uygulanıyor."
            ),
            "confirmation": False,
        },
        {
            "id": "finance_summary",
            "patterns": (
                r"\bfinans özeti\b",
                r"\bportföy durumu\b",
                r"\bsyfinansotağı\b",
                r"\bpiyasa özeti\b",
            ),
            "message": (
                "Finans özeti hazırlanıyor."
            ),
            "confirmation": False,
        },
        {
            "id": "help",
            "patterns": (
                r"\byardım\b",
                r"\bne yapabilirsin\b",
                r"\bkomutlar\b",
            ),
            "message": (
                "Kullanılabilir Jarmin "
                "komutları listeleniyor."
            ),
            "confirmation": False,
        },
    )

    MODULE_ALIASES = {
        "görüntü": "image",
        "fotoğraf": "image",
        "video": "video",
        "canlı kamera": "live_camera",
        "rapor": "report",
        "harita": "map",
        "finans": "finance",
        "syfinansotağı": "finance",
        "ayarlar": "settings",
        "jeoloji": "geology",
        "termal": "thermal",
        "lidar": "lidar",
        "gpr": "gpr",
        "sismik": "seismic",
        "astronomi": "astronomy",
    }

    THEME_ALIASES = {
        "altın": "gold",
        "gümüş": "silver",
        "koyu": "dark",
        "otomatik": "automatic",
    }

    def resolve(
        self,
        text: str,
    ) -> IntentResult:
        normalized = self.normalize(
            text
        )

        if not normalized:
            return IntentResult(
                intent_id="empty",
                confidence=0.0,
                normalized_text="",
                entities={},
                requires_confirmation=False,
                user_message=(
                    "Komut içeriği algılanamadı."
                ),
            )

        best_intent = None
        best_score = 0.0

        for definition in self.INTENTS:
            score = self._score(
                normalized,
                definition["patterns"],
            )

            if score > best_score:
                best_score = score
                best_intent = definition

        if best_intent is None:
            return IntentResult(
                intent_id="unknown",
                confidence=25.0,
                normalized_text=normalized,
                entities=self._entities(
                    normalized
                ),
                requires_confirmation=False,
                user_message=(
                    "Komut anlaşılamadı. Daha açık "
                    "bir ifade kullanın."
                ),
            )

        return IntentResult(
            intent_id=best_intent["id"],
            confidence=min(
                99.9,
                60.0 + best_score * 39.9,
            ),
            normalized_text=normalized,
            entities=self._entities(
                normalized
            ),
            requires_confirmation=bool(
                best_intent[
                    "confirmation"
                ]
            ),
            user_message=str(
                best_intent["message"]
            ),
        )

    @staticmethod
    def normalize(
        text: str,
    ) -> str:
        value = str(
            text or ""
        ).strip().lower()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    def _score(
        self,
        text: str,
        patterns: tuple[str, ...],
    ) -> float:
        matches = [
            pattern
            for pattern in patterns
            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        ]

        if not matches:
            return 0.0

        longest = max(
            len(pattern)
            for pattern in matches
        )

        return min(
            1.0,
            0.55
            + len(matches) * 0.12
            + longest / 200.0,
        )

    def _entities(
        self,
        text: str,
    ) -> dict[str, Any]:
        entities: dict[str, Any] = {}

        for alias, module_id in (
            self.MODULE_ALIASES.items()
        ):
            if alias in text:
                entities[
                    "module_id"
                ] = module_id
                break

        for alias, theme_id in (
            self.THEME_ALIASES.items()
        ):
            if alias in text:
                entities[
                    "theme_id"
                ] = theme_id
                break

        percentage = re.search(
            r"%?\s*(\d{1,3}(?:[.,]\d+)?)",
            text,
        )

        if percentage:
            entities["number"] = float(
                percentage.group(1).replace(
                    ",",
                    ".",
                )
            )

        return entities