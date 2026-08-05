class WidgetManager:

    def __init__(self):

        self.widgets={}

    def register(self,name,obj):

        self.widgets[name]=obj

    def all(self):

        return sorted(self.widgets)
