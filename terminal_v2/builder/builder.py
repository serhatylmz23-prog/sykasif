from pathlib import Path
import textwrap

ROOT = Path("terminal_v2")

FILES = {

"app/main.py": """
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from terminal_v2.core.api import router

app = FastAPI(
    title="SYK Terminal V2",
    version="2.0.0"
)

app.include_router(router)

app.mount(
    "/static",
    StaticFiles(directory="terminal_v2/static"),
    name="static"
)

@app.get("/")
def root():
    return {"runtime":"terminal_v2"}
""",

"runtime/runtime.py": """
class Runtime:

    def __init__(self):
        self.running=False

    def start(self):
        self.running=True

    def stop(self):
        self.running=False

runtime=Runtime()
""",

"core/logger.py": """
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger=logging.getLogger("terminal_v2")
""",

"static/css/runtime.css": """
html,body{
margin:0;
padding:0;
background:#080808;
color:white;
}
""",

"static/js/runtime.js": """
console.log("Terminal V2");
""",

"templates/index.html": """
<!doctype html>
<html>
<head>
<meta charset="utf8">
<link rel="stylesheet" href="/static/css/runtime.css">
</head>
<body>

<div id="app"></div>

<script src="/static/js/runtime.js"></script>

</body>
</html>
"""
}

for file,content in FILES.items():

    target=ROOT/file

    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target.write_text(
        textwrap.dedent(content).strip()+"\n",
        encoding="utf8"
    )

print(f"{len(FILES)} FILE GENERATED")
