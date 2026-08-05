from collections import defaultdict

class EventBus:

    def __init__(self):
        self.events=defaultdict(list)

    def on(self,event,callback):
        self.events[event].append(callback)

    def emit(self,event,*args,**kwargs):
        for cb in list(self.events[event]):
            cb(*args,**kwargs)
