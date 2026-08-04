from syk_simulasyon.syk_ui_runtime.mobile_offline_runtime import (
    MobileOfflineRuntime,
)


def test_cevrimdisi_kayit_kuyruga_alinir():
    runtime = MobileOfflineRuntime()

    result = runtime.enqueue(
        item_type="evidence",
        device_id="PHONE-006C-001",
        endpoint="/api/test/evidence",
        method="POST",
        payload={
            "record_sha256": "a" * 64,
        },
    )

    assert result["created"]
    assert not result["duplicate"]

    item = result["item"]

    assert item["status"] == "pending"

    assert len(
        item["payload_sha256"]
    ) == 64


def test_ayni_kayit_iki_kez_eklenmez():
    runtime = MobileOfflineRuntime()

    first = runtime.enqueue(
        item_type="report",
        device_id="TABLET-006C-001",
        endpoint="/api/test/report",
        method="POST",
        payload={
            "report_id": "RPT-001",
        },
    )

    second = runtime.enqueue(
        item_type="report",
        device_id="TABLET-006C-001",
        endpoint="/api/test/report",
        method="POST",
        payload={
            "report_id": "RPT-001",
        },
    )

    assert first["created"]
    assert second["duplicate"]


def test_kuyruk_kaydi_tamamlanir():
    runtime = MobileOfflineRuntime()

    created = runtime.enqueue(
        item_type="location",
        device_id="PHONE-006C-002",
        endpoint="/api/test/location",
        method="POST",
        payload={
            "latitude": 39.9,
            "longitude": 32.8,
        },
    )

    item_id = created[
        "item"
    ]["item_id"]

    processing = runtime.begin_processing(
        item_id
    )

    assert (
        processing["status"]
        == "processing"
    )

    completed = runtime.complete(
        item_id
    )

    assert (
        completed["status"]
        == "completed"
    )


def test_cihaz_eslestirme_ve_token():
    runtime = MobileOfflineRuntime(
        pairing_lifetime_seconds=300
    )

    pairing = runtime.create_pairing(
        requesting_device_id=(
            "TABLET-006C-PAIR"
        ),
        requesting_device_title=(
            "Saha Tableti"
        ),
    )

    assert (
        len(
            pairing["pairing_code"]
        )
        == 6
    )

    confirmed = runtime.confirm_pairing(
        pairing_code=(
            pairing["pairing_code"]
        ),
        paired_device_id=(
            "DESKTOP-006C-MAIN"
        ),
    )

    assert (
        confirmed["pairing"][
            "status"
        ]
        == "paired"
    )

    assert runtime.verify_pairing_token(
        pairing_id=(
            pairing["pairing_id"]
        ),
        pairing_token=(
            confirmed[
                "pairing_token"
            ]
        ),
    )


def test_onbellek_kaydi():
    runtime = MobileOfflineRuntime()

    created = runtime.cache_put(
        cache_key="location:latest",
        category="location",
        value={
            "latitude": 41.0,
            "longitude": 29.0,
        },
        lifetime_seconds=60,
    )

    assert (
        created["category"]
        == "location"
    )

    loaded = runtime.cache_get(
        "location:latest"
    )

    assert loaded is not None

    assert (
        loaded["value"][
            "latitude"
        ]
        == 41.0
    )


def test_runtime_sha_uretir():
    runtime = MobileOfflineRuntime()

    snapshot = runtime.snapshot()

    assert len(
        snapshot[
            "snapshot_sha256"
        ]
    ) == 64