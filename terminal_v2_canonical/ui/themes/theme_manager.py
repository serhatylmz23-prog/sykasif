class ThemeManager:

    def __init__(self):

        self.theme="dark"

    def set(self,name):

        self.theme=name

    def current(self):

        return self.theme
