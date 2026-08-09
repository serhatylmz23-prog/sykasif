from pathlib import Path

ROOT=Path("terminal_v2/builder/templates")

count=0

for file in ROOT.rglob("*.tpl"):

    print(file.relative_to(ROOT))

    count+=1

print()

print("TEMPLATE_COUNT =",count)

assert count>=4

print("TEMPLATE_ENGINE_READY")
