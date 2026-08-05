from pathlib import Path

from terminal_v2.scaffold.core.parser import Manifest

class DependencyResolver:

    def __init__(self, manifest):

        self.manifest = manifest

        self.queue = []

    def build(self):

        if self.manifest.enabled("runtime"):
            self.queue.append("runtime")

        if self.manifest.enabled("layout"):
            self.queue.append("html")

        if self.manifest.enabled("theme"):
            self.queue.append("css")

        if self.manifest.enabled("icons"):
            self.queue.append("css")

        if self.manifest.enabled("widgets"):
            self.queue.append("js")

        if self.manifest.enabled("api"):
            self.queue.append("api")

        if self.manifest.enabled("tests"):
            self.queue.append("tests")

        self.queue.append("compile")

        if self.manifest.enabled("pytest"):
            self.queue.append("pytest")

        self.queue.append("package")

        return self.queue


m = Manifest.load(
    "terminal_v2/scaffold/manifest/terminal.yml"
)

resolver = DependencyResolver(m)

queue = resolver.build()

print()
print("="*40)
print("DEPENDENCY QUEUE")
print("="*40)

for i, step in enumerate(queue, 1):

    print(f"{i:02d} -> {step}")

print()
print("QUEUE_SIZE =", len(queue))
print("DEPENDENCY_RESOLVER_READY")
