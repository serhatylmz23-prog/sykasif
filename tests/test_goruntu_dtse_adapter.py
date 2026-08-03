from syk_core.goruntu.goruntu_uzmani_modeli import (
    GoruntuKaydi,
    GoruntuUzmani,
)

from syk_simulasyon.syk_ui_runtime.dtse_attention_engine import (
    DTSEAttentionEngine,
)
from syk_simulasyon.syk_ui_runtime.goruntu_dtse_adapter import (
    GoruntuDTSEAdapter,
)


def test_supheli_bolge_otomatik_dtseye_aktarilir():
    uzman = GoruntuUzmani()
    dtse = DTSEAttentionEngine()

    adapter = GoruntuDTSEAdapter(
        uzman=uzman,
        dtse=dtse,
    )

    uzman.goruntu_kaydet(
        GoruntuKaydi(
            veri_kimligi="FOTO-001",
            veri_turu="Fotoğraf",
            kaynak="kullanıcı verisi",
            kare_genisligi=1000,
            kare_yuksekligi=800,
        )
    )

    uzman.supheli_bolge_isaretle(
        "FOTO-001",
        100,
        160,
        300,
        240,
        "Taş yüzey dokusunda anomali",
        93.4,
    )

    result = adapter.son_sonuc

    assert result is not None
    assert result["created_count"] == 1

    event = result["events"][0]

    assert event["media_id"] == "FOTO-001"
    assert event["source_kind"] == "image"
    assert event["signal"]["kind"] == "texture"
    assert event["signal"]["confidence"] == 93.4

    assert event["visual_layer"]["box"] == {
        "x": 0.1,
        "y": 0.2,
        "width": 0.3,
        "height": 0.3,
    }


def test_video_kare_bilgisi_dtseye_aktarilir():
    uzman = GoruntuUzmani()
    dtse = DTSEAttentionEngine()

    adapter = GoruntuDTSEAdapter(
        uzman=uzman,
        dtse=dtse,
    )

    uzman.goruntu_kaydet(
        GoruntuKaydi(
            veri_kimligi="VID-001",
            veri_turu="Video",
            kaynak="saha kaydı",
            kare_genisligi=1920,
            kare_yuksekligi=1080,
            kare_numarasi=140,
            zaman_ms=5600,
        )
    )

    uzman.supheli_bolge_isaretle(
        "VID-001",
        500,
        300,
        400,
        300,
        "Sembol benzeri işaret",
        88.0,
    )

    event = (
        adapter
        .son_sonuc["events"][0]
    )

    assert event["source_kind"] == "video"
    assert event["frame_index"] == 140
    assert event["timestamp_ms"] == 5600
    assert event["signal"]["kind"] == "symbol"


def test_kare_olcusu_yoksa_dtse_olayi_uretilmez():
    uzman = GoruntuUzmani()
    dtse = DTSEAttentionEngine()

    adapter = GoruntuDTSEAdapter(
        uzman=uzman,
        dtse=dtse,
    )

    uzman.goruntu_kaydet(
        GoruntuKaydi(
            "IMG-001",
            "Fotoğraf",
            "dış kaynak",
        )
    )

    uzman.supheli_bolge_isaretle(
        "IMG-001",
        10,
        20,
        100,
        80,
        "Nesne benzeri alan",
    )

    assert adapter.son_sonuc is None

    assert (
        "kare genişliği"
        in adapter.son_hata["reason"]
    )