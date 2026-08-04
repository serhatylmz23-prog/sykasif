from pathlib import Path

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


ROOT = (
    Path(__file__).resolve().parents[1]
)

RUNTIME = (
    ROOT
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
)

STATIC = RUNTIME / "static"


def test_spr_006_kaynak_dosyalari_var():
    required = [
        RUNTIME
        / "mobile_device_runtime.py",

        RUNTIME
        / "mobile_device_routes.py",

        RUNTIME
        / "mobile_sensor_runtime.py",

        RUNTIME
        / "mobile_sensor_routes.py",

        RUNTIME
        / "mobile_offline_runtime.py",

        RUNTIME
        / "mobile_offline_routes.py",

        RUNTIME
        / "mobile_control_runtime.py",

        RUNTIME
        / "mobile_control_routes.py",

        STATIC
        / "js"
        / "mobile_device_runtime.js",

        STATIC
        / "js"
        / "mobile_sensor_runtime.js",

        STATIC
        / "js"
        / "mobile_offline_runtime.js",

        STATIC
        / "js"
        / "mobile_control_panel.js",

        STATIC
        / "css"
        / "mobile_device_runtime.css",

        STATIC
        / "css"
        / "mobile_sensor_runtime.css",

        STATIC
        / "css"
        / "mobile_offline_runtime.css",

        STATIC
        / "css"
        / "mobile_control_panel.css",
    ]

    missing = [
        str(path)
        for path in required
        if not path.is_file()
    ]

    assert not missing, (
        "Eksik SPR-006 dosyaları: "
        + ", ".join(missing)
    )


def test_spr_006_dosyalari_bos_degildir():
    required = [
        RUNTIME
        / "mobile_device_runtime.py",

        RUNTIME
        / "mobile_sensor_runtime.py",

        RUNTIME
        / "mobile_offline_runtime.py",

        RUNTIME
        / "mobile_control_runtime.py",

        STATIC
        / "js"
        / "mobile_device_runtime.js",

        STATIC
        / "js"
        / "mobile_sensor_runtime.js",

        STATIC
        / "js"
        / "mobile_offline_runtime.js",

        STATIC
        / "js"
        / "mobile_control_panel.js",
    ]

    empty = [
        str(path)
        for path in required
        if path.stat().st_size == 0
    ]

    assert not empty, (
        "Boş SPR-006 dosyaları: "
        + ", ".join(empty)
    )


def test_spr_006_api_ucları_acik():
    client = TestClient(app)

    endpoints = [
        "/api/syk-ui/mobile-runtime",
        "/api/syk-ui/mobile-sensors",
        "/api/syk-ui/mobile-offline",
        "/api/syk-ui/mobile-control",
    ]

    failures = []

    for endpoint in endpoints:
        response = client.get(
            endpoint
        )

        if response.status_code != 200:
            failures.append(
                (
                    endpoint,
                    response.status_code,
                )
            )

    assert not failures, failures


def test_spr_006_dijital_kapsam_uyarisi():
    client = TestClient(app)

    sensor = client.get(
        "/api/syk-ui/mobile-sensors"
    ).json()

    assert (
        sensor[
            "native_sensor_bridge_ready"
        ]
        is False
    )

    mobile = client.get(
        "/api/syk-ui/mobile-runtime"
    ).json()

    assert (
        mobile[
            "native_android_bridge_ready"
        ]
        is False
    )