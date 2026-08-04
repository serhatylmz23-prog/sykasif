"""SyKaşif gerçek donanım denetleme komutu."""

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

    from syk_core.runtime_hardware_validation import (
        donanim_denetim_main,
    )

    return donanim_denetim_main()


if __name__ == "__main__":
    raise SystemExit(main())
