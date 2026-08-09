from terminal_v2.scaffold.builders.builder_base import BuilderBase

b=BuilderBase("terminal_v2")

b.mkdir("generated")

b.write(
    "generated/test.txt",
    "SYK"
)

r=b.summary()

assert r["count"]==2

print()

print("FILES =",r["count"])

print()

print("ENGINE_CORE_READY")
