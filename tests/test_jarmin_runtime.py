from syk_jarmin.runtime.runtime import (
    JarminRuntime,
    jarmin_runtime,
    kasif_runtime,
)


def test_jarmin_runtime_import_edilir():
    runtime = JarminRuntime()

    assert (
        runtime.assistant_name
        == "Kaşif"
    )

    assert (
        runtime.state
        == "ready"
    )


def test_kasif_komut_isler():
    runtime = JarminRuntime()

    result = runtime.execute(
        "Kamera görüntüsünü analiz et."
    )

    assert (
        result.intent
        == "camera"
    )

    assert (
        result.status
        == "completed"
    )

    assert len(
        result.result_sha256
    ) == 64


def test_runtime_aliaslari():
    assert (
        jarmin_runtime
        is kasif_runtime
    )


def test_runtime_snapshot_sha():
    runtime = JarminRuntime()

    snapshot = runtime.snapshot()

    assert (
        snapshot["assistant_name"]
        == "Kaşif"
    )

    assert len(
        snapshot["snapshot_sha256"]
    ) == 64