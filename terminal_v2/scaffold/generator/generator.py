from pathlib import Path

class Generator:

    def __init__(self):

        self.files=[]

    def emit(self,target,content):

        target=Path(target)

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target.write_text(
            content,
            encoding="utf8"
        )

        self.files.append(target)

    def report(self):

        return len(self.files)
