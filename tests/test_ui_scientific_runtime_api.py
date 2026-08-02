from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_bilimsel_runtime_api_uclari():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    inventory = client.get(
        "/api/syk-ui/scientific-modules"
    )

    assert inventory.status_code == 200
    assert len(inventory.json()) == 16

    geology = client.get(
        "/api/syk-ui/scientific-modules/geology"
    )

    assert geology.status_code == 200

    payload = geology.json()

    assert payload["definition"]["id"] == "geology"
    assert payload["definition"]["title"] == "JEOLOJİ"
    assert len(payload["definition"]["metrics"]) == 4
    assert payload["state"]["source"] == "digital_preview"

    missing = client.get(
        "/api/syk-ui/scientific-modules/unknown"
    )

    assert missing.status_code == 404