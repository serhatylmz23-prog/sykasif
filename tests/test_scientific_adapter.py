import pytest

from syk_simulasyon.syk_ui_runtime.scientific_adapter import (
    ScientificAdapterRegistry,
)
from syk_simulasyon.syk_ui_runtime.scientific_runtime import (
    ScientificRuntime,
)


def test_bilimsel_adapter_registry():
    runtime = ScientificRuntime()
    registry = ScientificAdapterRegistry(runtime)

    assert registry.exists("simulated")
    assert not registry.exists("unknown")

    inventory = registry.inventory()

    assert len(inventory) == 1
    assert inventory[0]["id"] == "simulated"
    assert len(
        inventory[0]["supported_modules"]
    ) == 16


def test_bilimsel_adapter_veri_aktarimi():
    runtime = ScientificRuntime()
    registry = ScientificAdapterRegistry(runtime)

    before = runtime.get("gpr")

    result = registry.ingest(
        "simulated",
        "gpr",
        {
            "live_value": 51.8,
            "confidence": 93.6,
            "status": "verified",
            "source": "gpr_test_device",
            "metadata": {
                "port": "COM7",
                "baud_rate": 115200,
            },
        },
    )

    assert result["state"]["live_value"] == 51.8
    assert result["state"]["confidence"] == 93.6
    assert result["state"]["status"] == "verified"
    assert result["state"]["source"] == "gpr_test_device"

    assert (
        result["state"]["sequence"]
        == before["state"]["sequence"] + 1
    )

    assert result["adapter"]["id"] == "simulated"
    assert (
        result["adapter"]["metadata"]["port"]
        == "COM7"
    )


def test_bilimsel_adapter_hatalari():
    runtime = ScientificRuntime()
    registry = ScientificAdapterRegistry(runtime)

    with pytest.raises(KeyError):
        registry.ingest(
            "unknown",
            "gpr",
            {"live_value": 1},
        )

    with pytest.raises(KeyError):
        registry.ingest(
            "simulated",
            "unknown",
            {"live_value": 1},
        )