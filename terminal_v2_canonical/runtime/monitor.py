from threading import Lock

class RuntimeMonitor:

    def __init__(self):

        self.lock=Lock()

        self.running=False

        self.tick=0

    def start(self):

        with self.lock:
            self.running=True

    def stop(self):

        with self.lock:
            self.running=False

    def heartbeat(self):

        with self.lock:
            self.tick+=1

    def snapshot(self):

        return{
            "running":self.running,
            "tick":self.tick
        }
