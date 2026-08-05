from terminal_v2.scaffold.core.parser import Manifest
from terminal_v2.scaffold.engine.auto_builder import AutoBuilder

m=Manifest.load(
    "terminal_v2/scaffold/manifest/terminal.yml"
)

b=AutoBuilder()

b.build_modules(m)

print()

print("MODULES =",len(m.modules))

print("FILES =",b.report())

print()

assert b.report()==len(m.modules)*2

print("AUTO_BUILDER_READY")
