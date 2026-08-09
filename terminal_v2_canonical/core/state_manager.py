from .models import RuntimeState

class StateManager:

    def __init__(self):
        self.state=RuntimeState()

    def get(self):
        return self.state

    def update(self,**kwargs):
        for k,v in kwargs.items():
            if hasattr(self.state,k):
                setattr(self.state,k,v)
