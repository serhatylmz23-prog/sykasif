from terminal_v2.runtime.runtime_engine import RuntimeEngine

def test_runtime_engine():

    r=RuntimeEngine()

    r.boot()

    assert r.status()["running"]
