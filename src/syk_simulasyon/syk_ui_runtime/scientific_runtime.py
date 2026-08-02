from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any


@dataclass(frozen=True)
class ScientificMetric:
    id: str
    title: str
    value: float | int | str
    unit: str = ""
    note: str = ""


@dataclass(frozen=True)
class ScientificLayer:
    id: str
    title: str
    state: str
    enabled: bool = True


@dataclass(frozen=True)
class ScientificModuleDefinition:
    id: str
    title: str
    subtitle: str
    primary_unit: str
    metrics: tuple[ScientificMetric, ...]
    layers: tuple[ScientificLayer, ...]


@dataclass
class ScientificModuleState:
    module_id: str
    live_value: float | int | str
    confidence: float
    status: str = "preview"
    source: str = "digital_preview"
    sequence: int = 0
    updated_at: str = ""

    def touch(self) -> None:
        self.sequence += 1
        self.updated_at = datetime.now(UTC).isoformat()


def metric(
    metric_id: str,
    title: str,
    value: float | int | str,
    unit: str = "",
    note: str = "",
) -> ScientificMetric:
    return ScientificMetric(
        id=metric_id,
        title=title,
        value=value,
        unit=unit,
        note=note,
    )


def layer(
    layer_id: str,
    title: str,
    state: str = "active",
) -> ScientificLayer:
    return ScientificLayer(
        id=layer_id,
        title=title,
        state=state,
    )


DEFINITIONS: dict[str, ScientificModuleDefinition] = {
    "geology": ScientificModuleDefinition(
        id="geology",
        title="JEOLOJİ",
        subtitle="Katman, kayaç, fay ve mineral inceleme paneli",
        primary_unit="m",
        metrics=(
            metric("depth", "Katman Derinliği", 12.48, "m"),
            metric("rock", "Kayaç Sınıfı", "Kireçtaşı"),
            metric("fault", "Fay Yakınlığı", 184, "m"),
            metric("mineral", "Mineral İşareti", 3),
        ),
        layers=(
            layer("surface", "Yüzey"),
            layer("soil", "Toprak"),
            layer("rock", "Kayaç"),
            layer("mineral", "Mineral", "preview"),
        ),
    ),
    "frequency": ScientificModuleDefinition(
        id="frequency",
        title="FREKANS",
        subtitle="Rezonans, titreşim ve sinyal yoğunluğu paneli",
        primary_unit="Hz",
        metrics=(
            metric("main", "Ana Frekans", 847.20, "Hz"),
            metric("bandwidth", "Bant Genişliği", 41.8, "Hz"),
            metric("signal", "Sinyal Gücü", -32, "dB"),
            metric("noise", "Gürültü", -71, "dB"),
        ),
        layers=(
            layer("raw", "Ham Sinyal"),
            layer("filtered", "Filtreli"),
            layer("resonance", "Rezonans"),
            layer("reference", "Referans", "ready"),
        ),
    ),
    "lidar": ScientificModuleDefinition(
        id="lidar",
        title="LiDAR",
        subtitle="Üç boyutlu nokta bulutu ve yüzey tarama paneli",
        primary_unit="nokta",
        metrics=(
            metric("points", "Nokta Sayısı", "1.28M"),
            metric("area", "Tarama Alanı", 84, "m²"),
            metric("height", "Yükseklik Farkı", 3.42, "m"),
            metric("density", "Yoğunluk", 92, "%"),
        ),
        layers=(
            layer("cloud", "Nokta Bulutu"),
            layer("surface", "Yüzey"),
            layer("height", "Yükseklik"),
            layer("anomaly", "Anomali", "preview"),
        ),
    ),
    "astronomy": ScientificModuleDefinition(
        id="astronomy",
        title="ASTRONOMİ / ARKEOASTRONOMİ",
        subtitle="Gökyüzü doğrultusu ve tarihsel hizalanma paneli",
        primary_unit="°",
        metrics=(
            metric("azimuth", "Azimut", 127.40, "°"),
            metric("elevation", "Yükseklik", 34.18, "°"),
            metric("solar", "Güneş Açısı", 18.72, "°"),
            metric("alignment", "Hizalanma", 76, "%"),
        ),
        layers=(
            layer("sun", "Güneş"),
            layer("moon", "Ay"),
            layer("stars", "Yıldız", "reference"),
            layer("axis", "Yapı Ekseni"),
        ),
    ),
    "chemistry": ScientificModuleDefinition(
        id="chemistry",
        title="KİMYASAL ANALİZ",
        subtitle="Numune bileşimi ve element işareti paneli",
        primary_unit="ppm",
        metrics=(
            metric("element", "Ana İşaret", "Fe"),
            metric("density", "Yoğunluk", 24.8, "ppm"),
            metric("ph", "pH", 7.18),
            metric("sample", "Numune", "K-014"),
        ),
        layers=(
            layer("element", "Element"),
            layer("compound", "Bileşik", "preview"),
            layer("reference", "Referans"),
            layer("deviation", "Sapma"),
        ),
    ),
    "spectral": ScientificModuleDefinition(
        id="spectral",
        title="SPEKTRAL ANALİZ",
        subtitle="Dalga boyu, yansıma ve bant karşılaştırma paneli",
        primary_unit="nm",
        metrics=(
            metric("band", "Ana Bant", 742.6, "nm"),
            metric("reflection", "Yansıma", 63, "%"),
            metric("bands", "Bant Sayısı", 12),
            metric("deviation", "Sapma", 8.4, "%"),
        ),
        layers=(
            layer("visible", "Görünür"),
            layer("nir", "NIR"),
            layer("reflection", "Yansıma"),
            layer("reference", "Referans", "ready"),
        ),
    ),
    "thermal": ScientificModuleDefinition(
        id="thermal",
        title="TERMAL ANALİZ",
        subtitle="Sıcaklık dağılımı ve termal sapma paneli",
        primary_unit="°C",
        metrics=(
            metric("average", "Ortalama", 24.72, "°C"),
            metric("minimum", "Minimum", 19.84, "°C"),
            metric("maximum", "Maksimum", 31.16, "°C"),
            metric("deviation", "Sapma", 6.44, "°C"),
        ),
        layers=(
            layer("raw", "Ham Termal"),
            layer("cold", "Soğuk Bölge"),
            layer("hot", "Sıcak Bölge"),
            layer("deviation", "Sapma"),
        ),
    ),
    "magnetometer": ScientificModuleDefinition(
        id="magnetometer",
        title="MANYETOMETRE",
        subtitle="Manyetik alan yoğunluğu ve sapma paneli",
        primary_unit="nT",
        metrics=(
            metric("total", "Toplam Alan", 48720, "nT"),
            metric("deviation", "Sapma", 184, "nT"),
            metric("direction", "Yön", "Kuzeydoğu"),
            metric("anomaly", "Anomali", 2),
        ),
        layers=(
            layer("x", "X Ekseni"),
            layer("y", "Y Ekseni"),
            layer("z", "Z Ekseni"),
            layer("total", "Toplam Alan"),
        ),
    ),
    "gravimeter": ScientificModuleDefinition(
        id="gravimeter",
        title="GRAVİMETRE",
        subtitle="Yerçekimi farkı ve yoğunluk sapması paneli",
        primary_unit="mGal",
        metrics=(
            metric("local", "Yerel Fark", -2.84, "mGal"),
            metric("reference", "Referans", 0.0, "mGal"),
            metric("density", "Yoğunluk Farkı", 12, "%"),
            metric("anomaly", "Anomali", 1),
        ),
        layers=(
            layer("raw", "Ham Ölçüm"),
            layer("correction", "Düzeltme"),
            layer("density", "Yoğunluk", "preview"),
            layer("anomaly", "Anomali"),
        ),
    ),
    "ert": ScientificModuleDefinition(
        id="ert",
        title="ELEKTRİK DİRENÇ — ERT",
        subtitle="Özdirenç kesiti ve yeraltı katman paneli",
        primary_unit="Ωm",
        metrics=(
            metric("resistivity", "Özdirenç", 184.6, "Ωm"),
            metric("depth", "Kesit Derinliği", 18.0, "m"),
            metric("electrode", "Elektrot", 24),
            metric("deviation", "Sapma", 14, "%"),
        ),
        layers=(
            layer("surface", "Yüzey"),
            layer("low", "Düşük Direnç"),
            layer("high", "Yüksek Direnç"),
            layer("model", "Model", "preview"),
        ),
    ),
    "gpr": ScientificModuleDefinition(
        id="gpr",
        title="GPR — YER RADARI",
        subtitle="Radargram, yansıma ve tabaka süre paneli",
        primary_unit="ns",
        metrics=(
            metric("reflection", "Yansıma Süresi", 46.2, "ns"),
            metric("depth", "Tahmini Derinlik", 2.84, "m"),
            metric("line", "Hat Uzunluğu", 18.5, "m"),
            metric("targets", "Hedef Sayısı", 3),
        ),
        layers=(
            layer("raw", "Ham Radargram"),
            layer("gain", "Kazanç"),
            layer("reflection", "Yansıma"),
            layer("target", "Hedef", "preview"),
        ),
    ),
    "seismic": ScientificModuleDefinition(
        id="seismic",
        title="SİSMİK",
        subtitle="Dalga varış süresi ve tabaka hızı paneli",
        primary_unit="m/s",
        metrics=(
            metric("p_wave", "P Dalga Hızı", 1842, "m/s"),
            metric("s_wave", "S Dalga Hızı", 924, "m/s"),
            metric("arrival", "Varış Süresi", 18.4, "ms"),
            metric("line", "Hat Uzunluğu", 42, "m"),
        ),
        layers=(
            layer("raw", "Ham Kayıt"),
            layer("p", "P Dalgası"),
            layer("s", "S Dalgası"),
            layer("velocity", "Hız Modeli", "preview"),
        ),
    ),
    "hydro": ScientificModuleDefinition(
        id="hydro",
        title="HİDROJEOLOJİ",
        subtitle="Yeraltı suyu ve geçirgenlik değerlendirme paneli",
        primary_unit="m",
        metrics=(
            metric("level", "Su Seviyesi", 8.42, "m"),
            metric("permeability", "Geçirgenlik", "Orta"),
            metric("direction", "Akış Yönü", "Güneybatı"),
            metric("moisture", "Nem İşareti", 68, "%"),
        ),
        layers=(
            layer("surface", "Yüzey Suyu", "reference"),
            layer("moisture", "Nem"),
            layer("aquifer", "Akifer", "preview"),
            layer("flow", "Akış"),
        ),
    ),
    "botany": ScientificModuleDefinition(
        id="botany",
        title="BOTANİK",
        subtitle="Bitki örtüsü, tür yoğunluğu ve stres paneli",
        primary_unit="NDVI",
        metrics=(
            metric("ndvi", "Bitki İndeksi", 0.72),
            metric("species", "Tür Sayısı", 18),
            metric("stress", "Stres Alanı", 9, "%"),
            metric("moisture", "Nem", 61, "%"),
        ),
        layers=(
            layer("green", "Yeşil Örtü"),
            layer("stress", "Stres"),
            layer("density", "Yoğunluk"),
            layer("reference", "Referans", "ready"),
        ),
    ),
    "soil": ScientificModuleDefinition(
        id="soil",
        title="TOPRAK ANALİZİ",
        subtitle="Toprak sınıfı, nem, pH ve yoğunluk paneli",
        primary_unit="pH",
        metrics=(
            metric("ph", "pH", 7.18),
            metric("moisture", "Nem", 28, "%"),
            metric("density", "Yoğunluk", 1.42, "g/cm³"),
            metric("organic", "Organik Madde", 3.8, "%"),
        ),
        layers=(
            layer("surface", "Yüzey"),
            layer("moisture", "Nem"),
            layer("organic", "Organik"),
            layer("mineral", "Mineral", "preview"),
        ),
    ),
    "water": ScientificModuleDefinition(
        id="water",
        title="SU ANALİZİ",
        subtitle="Su kalitesi, iletkenlik ve bulanıklık paneli",
        primary_unit="µS/cm",
        metrics=(
            metric("conductivity", "İletkenlik", 412, "µS/cm"),
            metric("ph", "pH", 7.42),
            metric("turbidity", "Bulanıklık", 3.8, "NTU"),
            metric("temperature", "Sıcaklık", 18.6, "°C"),
        ),
        layers=(
            layer("physical", "Fiziksel"),
            layer("chemical", "Kimyasal"),
            layer("turbidity", "Bulanıklık"),
            layer("reference", "Referans", "ready"),
        ),
    ),
}


DEFAULT_CONFIDENCE = {
    "geology": 82.0,
    "frequency": 88.0,
    "lidar": 91.0,
    "astronomy": 76.0,
    "chemistry": 79.0,
    "spectral": 84.0,
    "thermal": 87.0,
    "magnetometer": 89.0,
    "gravimeter": 74.0,
    "ert": 85.0,
    "gpr": 83.0,
    "seismic": 81.0,
    "hydro": 77.0,
    "botany": 86.0,
    "soil": 88.0,
    "water": 90.0,
}


class ScientificRuntime:
    def __init__(self) -> None:
        self._lock = RLock()
        self._states: dict[str, ScientificModuleState] = {}

        for module_id, definition in DEFINITIONS.items():
            first_metric = definition.metrics[0]

            state = ScientificModuleState(
                module_id=module_id,
                live_value=first_metric.value,
                confidence=DEFAULT_CONFIDENCE[module_id],
            )
            state.touch()
            self._states[module_id] = state

    def module_ids(self) -> list[str]:
        return list(DEFINITIONS)

    def exists(self, module_id: str) -> bool:
        return module_id in DEFINITIONS

    def get(self, module_id: str) -> dict[str, Any]:
        if module_id not in DEFINITIONS:
            raise KeyError(module_id)

        with self._lock:
            definition = DEFINITIONS[module_id]
            state = self._states[module_id]

            return {
                "definition": asdict(definition),
                "state": asdict(state),
                "warning": (
                    "Bu ekran gerçek saha sonucu değildir. "
                    "Donanım veya doğrulanmış veri bağlandığında "
                    "değerler canlı ölçümle güncellenecektir."
                ),
            }

    def inventory(self) -> list[dict[str, Any]]:
        return [
            self.get(module_id)
            for module_id in self.module_ids()
        ]

    def update(
        self,
        module_id: str,
        *,
        live_value: float | int | str | None = None,
        confidence: float | None = None,
        status: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        if module_id not in DEFINITIONS:
            raise KeyError(module_id)

        with self._lock:
            state = self._states[module_id]

            if live_value is not None:
                state.live_value = live_value

            if confidence is not None:
                state.confidence = max(
                    0.0,
                    min(99.9, float(confidence)),
                )

            if status is not None:
                state.status = status

            if source is not None:
                state.source = source

            state.touch()

            return self.get(module_id)