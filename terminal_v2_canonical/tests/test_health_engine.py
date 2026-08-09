from terminal_v2.runtime.health_engine import HealthEngine

def test_health():

    h=HealthEngine()

    assert "runtime" in h.health()
