import time
import threading

class Scheduler:

    def __init__(self):

        self.jobs=[]

    def every(self,seconds,callback):

        self.jobs.append(
            (seconds,callback)
        )

    def run(self):

        def worker():

            while True:

                for sec,cb in self.jobs:

                    cb()

                    time.sleep(sec)

        threading.Thread(
            target=worker,
            daemon=True
        ).start()
