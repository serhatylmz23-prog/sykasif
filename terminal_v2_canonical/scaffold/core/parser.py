from pathlib import Path

class Manifest:

    def __init__(self):

        self.values={}
        self.modules=[]

    @classmethod
    def load(cls,path):

        obj=cls()

        for raw in Path(path).read_text(
            encoding="utf8"
        ).splitlines():

            line=raw.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if line=="modules:":
                continue

            if line.startswith("-"):

                obj.modules.append(
                    line[1:].strip()
                )

                continue

            if ":" not in line:
                continue

            k,v=line.split(":",1)

            obj.values[k.strip()]=v.strip()

        return obj

    def enabled(self,name):

        return self.values.get(name)=="true"

    def export(self):

        return{

            "settings":self.values,

            "modules":self.modules

        }
