from pathlib import Path

ROOT = Path("terminal_v2")

BUILDERS = (
    "python",
    "html",
    "css",
    "js",
    "runtime",
    "api",
    "tests"
)

print()
print("="*45)
print("SYK BUILD ENGINE")
print("="*45)

count = 0

for name in BUILDERS:

    folder = ROOT / "builder" / "builders" / name

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    (folder/"__init__.py").touch(exist_ok=True)

    print(f"[OK] {folder}")

    count += 1

print()

print("BUILDER_COUNT =", count)

print("BUILD_ENGINE_READY")
