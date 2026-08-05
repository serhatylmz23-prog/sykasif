class RuntimeKernel:

    def __init__(self):

        self.running=False
        self.version="2.0"

    def start(self):
        self.running=True

    def stop(self):
        self.running=False

    def status(self):

        return{
            "running":self.running,
            "version":self.version
        }
