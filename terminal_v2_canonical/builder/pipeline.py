from pathlib import Path

from terminal_v2.scaffold.core.parser import Manifest
from terminal_v2.builder.dependency_resolver import DependencyResolver

class BuilderPipeline:

    def __init__(self, manifest):

        self.manifest = manifest

        self.queue = DependencyResolver(
            manifest
        ).build()

    def run(self):

        print()
        print("="*40)
        print("BUILDER PIPELINE")
        print("="*40)

        for step in self.queue:

            print(f"RUN -> {step}")

        print()
        print("STEP_COUNT =", len(self.queue))
        print("PIPELINE_READY")


m = Manifest.load(
    "terminal_v2/scaffold/manifest/terminal.yml"
)

BuilderPipeline(m).run()
