from terminal_v2.runtime.monitor import RuntimeMonitor

def test_monitor():

    m=RuntimeMonitor()

    m.start()

    m.heartbeat()

    assert m.snapshot()["tick"]==1
