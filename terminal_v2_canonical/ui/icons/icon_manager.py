class IconManager:

    def __init__(self):

        self.icons={}

    def register(self,name,path):

        self.icons[name]=path

    def get(self,name):

        return self.icons.get(name)
