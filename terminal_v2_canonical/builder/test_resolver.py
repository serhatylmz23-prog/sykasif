from terminal_v2.builder.core.resolver import Resolver

r=Resolver()

r.add("manifest")

r.add("builder","manifest")

r.add("python","builder")

r.add("html","builder")

r.add("css","builder")

r.add("js","builder")

r.add("runtime","python","html","css","js")

r.add("tests","runtime")

print()

print("="*40)

print("BUILD ORDER")

print("="*40)

for i,x in enumerate(r.resolve(),1):

    print(f"{i:02d}. {x}")

print()

print("DEPENDENCY_READY")
