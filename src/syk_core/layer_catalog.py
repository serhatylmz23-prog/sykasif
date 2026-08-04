"""SYK Atlas katman tanım kataloğu."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .enums import LayerCategory, ResearchCategory
from .layer import LayerRecord


@dataclass(slots=True, frozen=True)
class LayerDefinition:
    """Sistemde kullanılabilen bir katmanın katalog tanımı."""

    code: str
    name: str
    category: LayerCategory
    default_priority: int
    default_opacity: float
    compatible_research_categories: frozenset[ResearchCategory]
    requires_online_source: bool = False
    requires_device_data: bool = False
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized_code = self.code.strip().lower()

        if not normalized_code:
            raise ValueError("Katman katalog kodu boş olamaz.")

        if not normalized_code.replace("_", "").isalnum():
            raise ValueError(
                "Katman katalog kodu yalnız harf, rakam ve alt çizgi içerebilir."
            )

        if not self.name.strip():
            raise ValueError("Katman katalog adı boş olamaz.")

        if not 0 <= self.default_priority <= 100:
            raise ValueError(
                "Katman katalog önceliği 0 ile 100 arasında olmalıdır."
            )

        if not 0.0 <= self.default_opacity <= 1.0:
            raise ValueError(
                "Katman katalog opaklığı 0.0 ile 1.0 arasında olmalıdır."
            )

        object.__setattr__(self, "code", normalized_code)
        object.__setattr__(self, "name", self.name.strip())

    def supports(
        self,
        category: ResearchCategory,
    ) -> bool:
        """Araştırma türünün katmanla uyumlu olup olmadığını döndürür."""

        return category in self.compatible_research_categories

    def create_record(
        self,
        *,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LayerRecord:
        """Katalog tanımından çalışma katmanı üretir."""

        record_metadata = dict(self.metadata)
        record_metadata["catalog_code"] = self.code

        if metadata:
            record_metadata.update(metadata)

        return LayerRecord(
            name=self.name,
            category=self.category,
            opacity=self.default_opacity,
            priority=self.default_priority,
            source=source,
            metadata=record_metadata,
        )


class LayerCatalog:
    """Katman tanımlarını kod ve kategori üzerinden yönetir."""

    def __init__(
        self,
        definitions: Iterable[LayerDefinition] | None = None,
    ) -> None:
        self._definitions: dict[str, LayerDefinition] = {}

        for definition in definitions or ():
            self.register(definition)

    def register(
        self,
        definition: LayerDefinition,
        *,
        replace: bool = False,
    ) -> None:
        """Katalog tanımı ekler."""

        if definition.code in self._definitions and not replace:
            raise ValueError(
                f"Katman katalog kodu zaten kayıtlı: {definition.code}"
            )

        self._definitions[definition.code] = definition

    def get(self, code: str) -> LayerDefinition:
        """Kodla katman tanımı döndürür."""

        normalized = code.strip().lower()

        try:
            return self._definitions[normalized]
        except KeyError as exc:
            raise KeyError(
                f"Katman katalog tanımı bulunamadı: {normalized}"
            ) from exc

    def find_by_category(
        self,
        category: LayerCategory,
    ) -> tuple[LayerDefinition, ...]:
        """Kategoriye göre katman tanımlarını döndürür."""

        matches = [
            definition
            for definition in self._definitions.values()
            if definition.category == category
        ]

        matches.sort(
            key=lambda item: (
                -item.default_priority,
                item.code,
            )
        )

        return tuple(matches)

    def compatible_with(
        self,
        category: ResearchCategory,
    ) -> tuple[LayerDefinition, ...]:
        """Araştırma türüyle uyumlu tanımları döndürür."""

        matches = [
            definition
            for definition in self._definitions.values()
            if definition.supports(category)
        ]

        matches.sort(
            key=lambda item: (
                -item.default_priority,
                item.code,
            )
        )

        return tuple(matches)

    def all(self) -> tuple[LayerDefinition, ...]:
        """Katalogdaki tüm tanımları döndürür."""

        return tuple(
            sorted(
                self._definitions.values(),
                key=lambda item: item.code,
            )
        )

    def __len__(self) -> int:
        return len(self._definitions)

    @classmethod
    def create_default(cls) -> "LayerCatalog":
        """SyKaşif varsayılan katman kataloğunu oluşturur."""

        all_research = frozenset(
            {
                ResearchCategory.GENERAL,
                ResearchCategory.ARCHAEOLOGY,
                ResearchCategory.HISTORY,
                ResearchCategory.GEOLOGY,
                ResearchCategory.HYDROGEOLOGY,
                ResearchCategory.BOTANY,
                ResearchCategory.SOIL,
                ResearchCategory.WATER,
                ResearchCategory.ASTRONOMY,
                ResearchCategory.ARCHAEOSTRONOMY,
                ResearchCategory.ENVIRONMENT,
                ResearchCategory.MULTIDISCIPLINARY,
            }
        )

        archaeology = frozenset(
            {
                ResearchCategory.ARCHAEOLOGY,
                ResearchCategory.HISTORY,
                ResearchCategory.ARCHAEOSTRONOMY,
                ResearchCategory.MULTIDISCIPLINARY,
            }
        )

        geology = frozenset(
            {
                ResearchCategory.GEOLOGY,
                ResearchCategory.HYDROGEOLOGY,
                ResearchCategory.SOIL,
                ResearchCategory.WATER,
                ResearchCategory.ENVIRONMENT,
                ResearchCategory.ARCHAEOLOGY,
                ResearchCategory.MULTIDISCIPLINARY,
            }
        )

        water = frozenset(
            {
                ResearchCategory.WATER,
                ResearchCategory.HYDROGEOLOGY,
                ResearchCategory.ENVIRONMENT,
                ResearchCategory.BOTANY,
                ResearchCategory.SOIL,
                ResearchCategory.MULTIDISCIPLINARY,
            }
        )

        astronomy = frozenset(
            {
                ResearchCategory.ASTRONOMY,
                ResearchCategory.ARCHAEOSTRONOMY,
                ResearchCategory.ARCHAEOLOGY,
                ResearchCategory.HISTORY,
                ResearchCategory.MULTIDISCIPLINARY,
            }
        )

        definitions = (
            LayerDefinition(
                code="base_map",
                name="Temel Harita",
                category=LayerCategory.BASE_MAP,
                default_priority=100,
                default_opacity=1.0,
                compatible_research_categories=all_research,
                description="Ana coğrafi referans haritası.",
            ),
            LayerDefinition(
                code="satellite",
                name="Uydu Görüntüsü",
                category=LayerCategory.SATELLITE,
                default_priority=95,
                default_opacity=0.90,
                compatible_research_categories=all_research,
                requires_online_source=True,
            ),
            LayerDefinition(
                code="topography",
                name="Topografya",
                category=LayerCategory.TOPOGRAPHY,
                default_priority=92,
                default_opacity=0.72,
                compatible_research_categories=all_research,
            ),
            LayerDefinition(
                code="geology",
                name="Jeolojik Formasyonlar",
                category=LayerCategory.GEOLOGY,
                default_priority=90,
                default_opacity=0.68,
                compatible_research_categories=geology,
            ),
            LayerDefinition(
                code="hydrology",
                name="Yüzey Suları",
                category=LayerCategory.HYDROLOGY,
                default_priority=88,
                default_opacity=0.62,
                compatible_research_categories=water,
            ),
            LayerDefinition(
                code="hydrogeology",
                name="Hidrojeolojik Formasyonlar",
                category=LayerCategory.HYDROGEOLOGY,
                default_priority=91,
                default_opacity=0.66,
                compatible_research_categories=water | geology,
            ),
            LayerDefinition(
                code="vegetation",
                name="Bitki Örtüsü",
                category=LayerCategory.VEGETATION,
                default_priority=74,
                default_opacity=0.55,
                compatible_research_categories=frozenset(
                    {
                        ResearchCategory.BOTANY,
                        ResearchCategory.SOIL,
                        ResearchCategory.WATER,
                        ResearchCategory.ENVIRONMENT,
                        ResearchCategory.ARCHAEOLOGY,
                        ResearchCategory.MULTIDISCIPLINARY,
                    }
                ),
            ),
            LayerDefinition(
                code="roads",
                name="Yol ve Ulaşım",
                category=LayerCategory.ROADS,
                default_priority=60,
                default_opacity=0.50,
                compatible_research_categories=all_research,
            ),
            LayerDefinition(
                code="artificial_structures",
                name="Yapay Yapılar",
                category=LayerCategory.ARTIFICIAL_STRUCTURES,
                default_priority=72,
                default_opacity=0.60,
                compatible_research_categories=all_research,
            ),
            LayerDefinition(
                code="archaeology",
                name="Arkeolojik Alanlar",
                category=LayerCategory.ARCHAEOLOGY,
                default_priority=96,
                default_opacity=0.78,
                compatible_research_categories=archaeology,
            ),
            LayerDefinition(
                code="history",
                name="Tarih Katmanı",
                category=LayerCategory.HISTORY,
                default_priority=94,
                default_opacity=0.64,
                compatible_research_categories=archaeology,
            ),
            LayerDefinition(
                code="temporal",
                name="Zamansal Katman",
                category=LayerCategory.TEMPORAL,
                default_priority=93,
                default_opacity=0.62,
                compatible_research_categories=archaeology | astronomy,
            ),
            LayerDefinition(
                code="lidar",
                name="Lidar Nokta Bulutu",
                category=LayerCategory.LIDAR,
                default_priority=89,
                default_opacity=0.82,
                compatible_research_categories=all_research,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="drone",
                name="Drone Görüntüleri",
                category=LayerCategory.DRONE,
                default_priority=86,
                default_opacity=0.84,
                compatible_research_categories=all_research,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="gps",
                name="GPS Kayıtları",
                category=LayerCategory.GPS,
                default_priority=98,
                default_opacity=1.0,
                compatible_research_categories=all_research,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="rtk",
                name="RTK Düzeltme Katmanı",
                category=LayerCategory.RTK,
                default_priority=99,
                default_opacity=1.0,
                compatible_research_categories=all_research,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="magnetic",
                name="Manyetik Analiz",
                category=LayerCategory.MAGNETIC,
                default_priority=84,
                default_opacity=0.70,
                compatible_research_categories=geology | archaeology,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="gravity",
                name="Gravite Analizi",
                category=LayerCategory.GRAVITY,
                default_priority=78,
                default_opacity=0.68,
                compatible_research_categories=geology,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="spectral",
                name="Spektral Analiz",
                category=LayerCategory.SPECTRAL,
                default_priority=83,
                default_opacity=0.72,
                compatible_research_categories=all_research,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="thermal",
                name="Termal Analiz",
                category=LayerCategory.THERMAL,
                default_priority=80,
                default_opacity=0.70,
                compatible_research_categories=all_research,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="ert",
                name="Elektrik Direnç Katmanı",
                category=LayerCategory.ERT,
                default_priority=85,
                default_opacity=0.76,
                compatible_research_categories=geology | archaeology,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="gpr",
                name="GPR Katmanı",
                category=LayerCategory.GPR,
                default_priority=85,
                default_opacity=0.76,
                compatible_research_categories=geology | archaeology,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="seismic",
                name="Sismik Analiz",
                category=LayerCategory.SEISMIC,
                default_priority=82,
                default_opacity=0.72,
                compatible_research_categories=geology,
                requires_device_data=True,
            ),
            LayerDefinition(
                code="soil",
                name="Toprak Analizi",
                category=LayerCategory.SOIL,
                default_priority=79,
                default_opacity=0.66,
                compatible_research_categories=frozenset(
                    {
                        ResearchCategory.SOIL,
                        ResearchCategory.BOTANY,
                        ResearchCategory.WATER,
                        ResearchCategory.ENVIRONMENT,
                        ResearchCategory.ARCHAEOLOGY,
                        ResearchCategory.MULTIDISCIPLINARY,
                    }
                ),
            ),
            LayerDefinition(
                code="water",
                name="Su Analizi",
                category=LayerCategory.WATER,
                default_priority=81,
                default_opacity=0.68,
                compatible_research_categories=water,
            ),
            LayerDefinition(
                code="botanical",
                name="Botanik Analizi",
                category=LayerCategory.BOTANICAL,
                default_priority=77,
                default_opacity=0.62,
                compatible_research_categories=frozenset(
                    {
                        ResearchCategory.BOTANY,
                        ResearchCategory.ENVIRONMENT,
                        ResearchCategory.ARCHAEOLOGY,
                        ResearchCategory.MULTIDISCIPLINARY,
                    }
                ),
            ),
            LayerDefinition(
                code="evidence",
                name="Kanıt Katmanı",
                category=LayerCategory.EVIDENCE,
                default_priority=100,
                default_opacity=1.0,
                compatible_research_categories=all_research,
            ),
            LayerDefinition(
                code="expert",
                name="Uzman Görüşleri",
                category=LayerCategory.EXPERT,
                default_priority=70,
                default_opacity=1.0,
                compatible_research_categories=all_research,
            ),
            LayerDefinition(
                code="report",
                name="Rapor Bağlantıları",
                category=LayerCategory.REPORT,
                default_priority=68,
                default_opacity=1.0,
                compatible_research_categories=all_research,
            ),
            LayerDefinition(
                code="astronomy",
                name="Astronomi Katmanı",
                category=LayerCategory.CUSTOM,
                default_priority=87,
                default_opacity=0.70,
                compatible_research_categories=astronomy,
                metadata={
                    "custom_type": "astronomy",
                },
            ),
        )

        return cls(definitions)

