import json

from syk_core.goruntu.goruntu_kanit_baglanti import (
    GoruntuKanitYoneticisi,
)
from syk_simulasyon.syk_ui_runtime.dtse_attention_engine import (
    AttentionSignal,
    DTSEAttentionEngine,
    NormalizedBox,
)
from syk_simulasyon.syk_ui_runtime.goruntu_dtse_kanit_zinciri import (
    GoruntuDTSEKanitZinciri,
)


def _event(
    *,
    frame_index: int = 0,
):
    engine = DTSEAttentionEngine()

    result = engine.ingest(
        media_id="FOTO-001",
        source_kind="image",
        frame_index=frame_index,
        timestamp_ms=frame_index * 40,
        frame_width=1000,
        frame_height=800,
        signals=[
            AttentionSignal(
                label=(
                    "Taş yüzeyinde "
                    "dikkat çeken doku"
                ),
                kind="texture",
                confidence=92.4,
                box=NormalizedBox(
                    x=0.1,
                    y=0.2,
                    width=0.3,
                    height=0.25,
                ),
            )
        ],
    )

    return result["events"][0]


def test_dtse_olayi_kanit_zincirine_baglanir(
    tmp_path,
):
    manager = GoruntuKanitYoneticisi()

    chain = GoruntuDTSEKanitZinciri(
        kanit_yoneticisi=manager,
        root=tmp_path / "chain",
    )

    result = chain.append_event(
        _event()
    )

    assert result["chain_valid"]
    assert len(result["record_sha256"]) == 64
    assert len(result["manifest_sha256"]) == 64

    evidence = manager.getir(
        "FOTO-001"
    )

    assert evidence is not None
    assert len(evidence.kanit_baglantilari) == 1
    assert len(evidence.materyal_adaylari) == 1

    verification = chain.verify(
        "FOTO-001"
    )

    assert verification["valid"]
    assert verification["record_count"] == 1


def test_ardisik_kayitlar_onceki_hashi_tasir(
    tmp_path,
):
    chain = GoruntuDTSEKanitZinciri(
        kanit_yoneticisi=(
            GoruntuKanitYoneticisi()
        ),
        root=tmp_path / "chain",
    )

    first = chain.append_event(
        _event(frame_index=0)
    )

    second = chain.append_event(
        _event(frame_index=20)
    )

    assert (
        second["previous_hash"]
        == first["record_sha256"]
    )

    verification = chain.verify(
        "FOTO-001"
    )

    assert verification["valid"]
    assert verification["record_count"] == 2


def test_kanit_kaydi_degisirse_zincir_bozulur(
    tmp_path,
):
    chain = GoruntuDTSEKanitZinciri(
        kanit_yoneticisi=(
            GoruntuKanitYoneticisi()
        ),
        root=tmp_path / "chain",
    )

    chain.append_event(
        _event()
    )

    path = chain.chain_path(
        "FOTO-001"
    )

    record = json.loads(
        path.read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    record["signal"]["label"] = (
        "Değiştirilmiş kayıt"
    )

    path.write_text(
        json.dumps(record) + "\n",
        encoding="utf-8",
    )

    verification = chain.verify(
        "FOTO-001"
    )

    assert not verification["valid"]

    assert verification["reason"] == (
        "record_sha256_mismatch"
    )