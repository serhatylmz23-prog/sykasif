from terminal_v2.scaffold.core.parser import Manifest
from terminal_v2.scaffold.generator.generator import Generator

m=Manifest.load(
    "terminal_v2/scaffold/manifest/terminal.yml"
)

g=Generator()

for module in m.modules:

    g.emit(

        f"terminal_v2/generated/{module}.txt",

        f"MODULE={module}\n"

    )

print()

print("GENERATED =",g.report())

print()

print("GENERATOR_READY")
