from pathlib import Path

ROOT = Path("terminal_v2")

cfg = {}
modules = []

for raw in (ROOT / "scaffold" / "manifest" / "terminal.yml").read_text(
    encoding="utf8"
).splitlines():

    line = raw.strip()

    if not line or line.startswith("#"):
        continue

    if line == "modules:":
        continue

    if line.startswith("-"):
        modules.append(line[1:].strip())
        continue

    if ":" not in line:
        continue

    k, v = line.split(":", 1)

    cfg[k.strip()] = v.strip()

cfg["modules"] = modules

print(cfg)
print()
print(f"MODULE_COUNT={len(modules)}")
print("SCAFFOLD_READY")
