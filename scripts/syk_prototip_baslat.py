"""SyKaşif birleşik prototip başlatma komutu."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    kok = Path(__file__).resolve().parents[1]
    kaynak = kok / "src"

    if str(kaynak) not in sys.path:
        sys.path.insert(
            0,
            str(kaynak),
        )

    from syk_core.runtime_prototype.baslatici import (
        main as prototip_main,
    )

    return prototip_main()


if __name__ == "__main__":
    raise SystemExit(main())
