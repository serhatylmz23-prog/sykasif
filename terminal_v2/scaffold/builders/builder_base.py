from pathlib import Path

class BuilderBase:

    def __init__(self,root):

        self.root=Path(root)

        self.created=[]

    def mkdir(self,path):

        p=self.root/path

        p.mkdir(
            parents=True,
            exist_ok=True
        )

        self.created.append(str(p))

        return p

    def write(self,path,content):

        p=self.root/path

        p.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        p.write_text(
            content,
            encoding="utf8"
        )

        self.created.append(str(p))

        return p

    def exists(self,path):

        return (self.root/path).exists()

    def summary(self):

        return{

            "count":len(self.created),

            "items":self.created

        }
