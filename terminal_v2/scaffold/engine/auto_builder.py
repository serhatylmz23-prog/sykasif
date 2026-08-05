from pathlib import Path

class AutoBuilder:

    def __init__(self):

        self.root=Path("terminal_v2")

        self.total=0

    def emit(self,path,text):

        p=self.root/path

        p.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        p.write_text(
            text,
            encoding="utf8"
        )

        self.total+=1

    def build_modules(self,manifest):

        for module in manifest.modules:

            self.emit(

                f"generated/{module}/__init__.py",

                ""

            )

            self.emit(

                f"generated/{module}/{module}.py",

                f"class {module.title().replace('_','')}:\n"
                f"    NAME='{module}'\n"

            )

    def report(self):

        return self.total
