from pathlib import Path

class FileWriter:

    def write(self,target,text):

        target=Path(target)

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target.write_text(
            text,
            encoding="utf8"
        )

        return target
