from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from typing import Any


ALLOWED_THEMES = {
    "gold",
    "silver",
    "blue",
    "green",
    "red",
    "dark",
}

ALLOWED_ANIMATIONS = {
    "none",
    "pulse",
    "rotate",
    "scan",
    "wave",
    "glow",
    "float",
}


@dataclass(frozen=True, slots=True)
class KasifIcon:
    icon_id: str
    order: int
    title: str
    group: str
    module_id: str
    description: str
    asset: str
    fallback_symbol: str
    theme: str
    animation: str
    enabled: bool
    permission: str
    keywords: tuple[str, ...]
    visual_rules: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        if not self.icon_id:
            raise ValueError(
                "İkon kimliği boş olamaz."
            )

        if not self.title:
            raise ValueError(
                "İkon başlığı boş olamaz."
            )

        if not self.group:
            raise ValueError(
                "İkon grubu boş olamaz."
            )

        if not self.module_id:
            raise ValueError(
                "Modül kimliği boş olamaz."
            )

        if self.order < 0:
            raise ValueError(
                "İkon sırası negatif olamaz."
            )

        if self.theme not in ALLOWED_THEMES:
            raise ValueError(
                f"Geçersiz ikon teması: "
                f"{self.theme}"
            )

        if (
            self.animation
            not in ALLOWED_ANIMATIONS
        ):
            raise ValueError(
                f"Geçersiz ikon animasyonu: "
                f"{self.animation}"
            )

    def as_dict(
        self,
        *,
        asset_base_url: str,
        asset_exists: bool,
    ) -> dict[str, Any]:
        return {
            "icon_id": self.icon_id,
            "order": self.order,
            "title": self.title,
            "group": self.group,
            "module_id": self.module_id,
            "description": self.description,
            "asset": self.asset,
            "asset_url": (
                f"{asset_base_url}/"
                f"{self.asset}"
            ),
            "asset_exists": asset_exists,
            "fallback_symbol": (
                self.fallback_symbol
            ),
            "theme": self.theme,
            "animation": self.animation,
            "enabled": self.enabled,
            "permission": self.permission,
            "keywords": list(
                self.keywords
            ),
            "visual_rules": dict(
                self.visual_rules
            ),
        }


class KasifIconRegistry:
    def __init__(
        self,
        manifest_path: str | Path | None = None,
        *,
        asset_base_url: str = (
            "/syk-ui/icons/kasif"
        ),
    ) -> None:
        default_path = (
            Path(__file__)
            .resolve()
            .parent
            / "static"
            / "icons"
            / "kasif"
            / "icons.json"
        )

        self.manifest_path = (
            Path(manifest_path)
            if manifest_path
            else default_path
        )

        self.asset_directory = (
            self.manifest_path.parent
        )

        self.asset_base_url = (
            asset_base_url.rstrip("/")
        )

        self._icons: dict[
            str,
            KasifIcon,
        ] = {}

        self._metadata: dict[
            str,
            Any,
        ] = {}

        self._lock = RLock()

        self.reload()

    def reload(self) -> dict[str, Any]:
        try:
            payload = json.loads(
                self.manifest_path.read_text(
                    encoding="utf-8"
                )
            )

        except FileNotFoundError as error:
            raise RuntimeError(
                "Kaşif ikon manifesti "
                "bulunamadı."
            ) from error

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Kaşif ikon manifesti "
                "geçerli JSON değil."
            ) from error

        raw_icons = payload.get(
            "icons"
        )

        if not isinstance(
            raw_icons,
            list,
        ):
            raise RuntimeError(
                "İkon listesi bulunamadı."
            )

        loaded: dict[
            str,
            KasifIcon,
        ] = {}

        for raw in raw_icons:
            icon = KasifIcon(
                icon_id=str(
                    raw["icon_id"]
                ).strip(),
                order=int(
                    raw.get(
                        "order",
                        0,
                    )
                ),
                title=str(
                    raw["title"]
                ).strip(),
                group=str(
                    raw["group"]
                ).strip(),
                module_id=str(
                    raw["module_id"]
                ).strip(),
                description=str(
                    raw.get(
                        "description",
                        "",
                    )
                ).strip(),
                asset=str(
                    raw.get(
                        "asset",
                        "",
                    )
                ).strip(),
                fallback_symbol=str(
                    raw.get(
                        "fallback_symbol",
                        "✦",
                    )
                ),
                theme=str(
                    raw.get(
                        "theme",
                        "gold",
                    )
                ).strip().lower(),
                animation=str(
                    raw.get(
                        "animation",
                        "none",
                    )
                ).strip().lower(),
                enabled=bool(
                    raw.get(
                        "enabled",
                        True,
                    )
                ),
                permission=str(
                    raw.get(
                        "permission",
                        "",
                    )
                ).strip(),
                keywords=tuple(
                    str(value).strip()
                    for value
                    in raw.get(
                        "keywords",
                        [],
                    )
                    if str(value).strip()
                ),
                visual_rules=dict(
                    raw.get(
                        "visual_rules",
                        {},
                    )
                ),
            )

            icon.validate()

            if icon.icon_id in loaded:
                raise RuntimeError(
                    "Tekrarlanan ikon kimliği: "
                    f"{icon.icon_id}"
                )

            loaded[
                icon.icon_id
            ] = icon

        with self._lock:
            self._icons = loaded

            self._metadata = {
                key: value
                for key, value
                in payload.items()
                if key != "icons"
            }

        return self.snapshot()

    def get(
        self,
        icon_id: str,
    ) -> dict[str, Any]:
        normalized = (
            icon_id.strip().lower()
        )

        with self._lock:
            try:
                icon = self._icons[
                    normalized
                ]

            except KeyError as error:
                raise KeyError(
                    "Kaşif ikonu bulunamadı: "
                    f"{normalized}"
                ) from error

        return self._serialize(icon)

    def list(
        self,
        *,
        group: str | None = None,
        enabled_only: bool = True,
        theme: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            icons = list(
                self._icons.values()
            )

        if enabled_only:
            icons = [
                icon
                for icon in icons
                if icon.enabled
            ]

        if group is not None:
            normalized_group = (
                group.strip().lower()
            )

            icons = [
                icon
                for icon in icons
                if (
                    icon.group.lower()
                    == normalized_group
                )
            ]

        if theme is not None:
            normalized_theme = (
                theme.strip().lower()
            )

            if (
                normalized_theme
                not in ALLOWED_THEMES
            ):
                raise ValueError(
                    "Geçersiz ikon teması."
                )

            icons = [
                icon
                for icon in icons
                if (
                    icon.theme
                    == normalized_theme
                )
            ]

        icons.sort(
            key=lambda icon: (
                icon.order,
                icon.title.casefold(),
            )
        )

        return [
            self._serialize(icon)
            for icon in icons
        ]

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        normalized = (
            query.strip().casefold()
        )

        if not normalized:
            return []

        if limit <= 0:
            raise ValueError(
                "Arama sınırı pozitif "
                "olmalıdır."
            )

        scored: list[
            tuple[int, KasifIcon]
        ] = []

        with self._lock:
            icons = list(
                self._icons.values()
            )

        for icon in icons:
            searchable = [
                icon.icon_id,
                icon.title,
                icon.group,
                icon.module_id,
                icon.description,
                *icon.keywords,
            ]

            score = 0

            for value in searchable:
                candidate = (
                    value.casefold()
                )

                if candidate == normalized:
                    score += 100

                elif candidate.startswith(
                    normalized
                ):
                    score += 50

                elif normalized in candidate:
                    score += 20

            if score > 0:
                scored.append(
                    (
                        score,
                        icon,
                    )
                )

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].order,
            )
        )

        return [
            self._serialize(icon)
            for _, icon
            in scored[:limit]
        ]

    def groups(
        self,
    ) -> list[dict[str, Any]]:
        with self._lock:
            icons = list(
                self._icons.values()
            )

        grouped: dict[
            str,
            list[KasifIcon],
        ] = {}

        for icon in icons:
            grouped.setdefault(
                icon.group,
                [],
            ).append(icon)

        result = []

        for group_id, values in sorted(
            grouped.items()
        ):
            result.append(
                {
                    "group_id": group_id,
                    "icon_count": len(
                        values
                    ),
                    "enabled_count": sum(
                        1
                        for icon in values
                        if icon.enabled
                    ),
                }
            )

        return result

    def assistant_profile(
        self,
    ) -> dict[str, Any]:
        assistant = dict(
            self._metadata.get(
                "assistant",
                {},
            )
        )

        assistant_icon = self.get(
            "kasif"
        )

        return {
            **assistant,
            "icon": assistant_icon,
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:
        icons = self.list(
            enabled_only=False
        )

        unsigned = {
            **self._metadata,
            "icon_count": len(icons),
            "enabled_count": sum(
                1
                for icon in icons
                if icon["enabled"]
            ),
            "asset_count": sum(
                1
                for icon in icons
                if icon[
                    "asset_exists"
                ]
            ),
            "icons": icons,
        }

        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return {
            **unsigned,
            "manifest_sha256": sha256(
                canonical
            ).hexdigest(),
        }

    def _serialize(
        self,
        icon: KasifIcon,
    ) -> dict[str, Any]:
        asset_exists = bool(
            icon.asset
            and (
                self.asset_directory
                / icon.asset
            ).is_file()
        )

        return icon.as_dict(
            asset_base_url=(
                self.asset_base_url
            ),
            asset_exists=asset_exists,
        )


kasif_icon_registry = (
    KasifIconRegistry()
)