from terminal_v2.core.service_registry import ServiceRegistry

def test_registry():

    r=ServiceRegistry()

    r.register("a",1)

    assert r.exists("a")

    assert r.get("a")==1
