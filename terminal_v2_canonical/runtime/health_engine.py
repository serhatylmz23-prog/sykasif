from terminal_v2.runtime.monitor import RuntimeMonitor

class HealthEngine:

    def __init__(self):

        self.monitor=RuntimeMonitor()

    def health(self):

        s=self.monitor.snapshot()

        return{

            "runtime":"ONLINE" if s["running"] else "OFFLINE",

            "tick":s["tick"]

        }
