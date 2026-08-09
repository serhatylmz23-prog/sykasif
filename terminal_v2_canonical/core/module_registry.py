from pathlib import Path
import importlib

class ModuleRegistry:

    def __init__(self):
        self.modules={}

    def discover(self,root="terminal_v2/modules"):

        root=Path(root)

        for file in root.rglob("*.py"):

            if file.name=="__init__.py":
                continue

            name=file.stem

            self.modules[name]=str(file)

    def load(self):

        loaded=[]

        for name,path in self.modules.items():

            module=path.replace("\\",".").replace("/",".")
            module=module[:-3]

            try:
                importlib.import_module(module)
                loaded.append(name)
            except Exception:
                pass

        return loaded
