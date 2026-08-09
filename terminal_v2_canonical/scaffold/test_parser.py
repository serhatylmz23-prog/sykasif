from scaffold.core.parser import Manifest

m=Manifest.load(
    "terminal_v2/scaffold/manifest/terminal.yml"
)

print()

print("SETTINGS =",len(m.values))

print("MODULES =",len(m.modules))

print()

for i in m.modules:

    print(i)

print()

print("ENGINE_PARSER_READY")
