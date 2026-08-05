from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

STEPS = [

    ("Manifest" , "scaffold/engine.py"),

    ("Resolver" , "scaffold/resolver.py"),

    ("Template" , "scaffold/template_engine.py"),

    ("Generator" , "scaffold/generator.py"),

    ("Validator" , "scaffold/validator.py")

]

print()

print("SYK BUILD ENGINE")

print()

for title,file in STEPS:

    target=ROOT/file

    if not target.exists():

        print(f"[SKIP] {title}")

        continue

    print(f"[RUN ] {title}")

    subprocess.run(

        [sys.executable,str(target)],

        check=True

    )

print()

print("BUILD_STAGE_OK")
