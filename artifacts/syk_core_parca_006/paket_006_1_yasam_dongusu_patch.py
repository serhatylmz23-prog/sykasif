from __future__ import annotations

import ast
from pathlib import Path


path = Path(
    "src/syk_core/runtime_terminal/uygulama.py"
)

text = path.read_text(
    encoding="utf-8-sig"
)

if "from contextlib import asynccontextmanager" not in text:
    marker = "import json\n"

    if marker not in text:
        raise RuntimeError(
            "contextlib ekleme noktası bulunamadı."
        )

    text = text.replace(
        marker,
        (
            "import json\n"
            "from contextlib import asynccontextmanager\n"
        ),
        1,
    )

old_method = '''    def _yasam_dongusunu_kaydet(
        self,
    ) -> None:
        @self.uygulama.on_event(
            "startup"
        )
        async def baslangic() -> None:
            self.durum_kaydi_yaz()

        @self.uygulama.on_event(
            "shutdown"
        )
        async def kapanis() -> None:
            self.guvenli_durdur()
'''

new_method = '''    def _yasam_dongusunu_kaydet(
        self,
    ) -> None:
        onceki_yasam_dongusu = (
            self.uygulama.router.lifespan_context
        )

        @asynccontextmanager
        async def terminal_yasam_dongusu(
            uygulama: FastAPI,
        ):
            self.durum_kaydi_yaz()

            if onceki_yasam_dongusu is None:
                try:
                    yield
                finally:
                    self.guvenli_durdur()

                return

            async with onceki_yasam_dongusu(
                uygulama
            ):
                try:
                    yield
                finally:
                    self.guvenli_durdur()

        self.uygulama.router.lifespan_context = (
            terminal_yasam_dongusu
        )
'''

if old_method not in text:
    if (
        "async def terminal_yasam_dongusu("
        in text
    ):
        print(
            "TERMINAL_YASAM_DONGUSU_ZATEN_GUNCEL"
        )
        raise SystemExit(0)

    raise RuntimeError(
        "Eski yaşam döngüsü yöntemi bulunamadı."
    )

text = text.replace(
    old_method,
    new_method,
    1,
)

ast.parse(
    text,
    filename=str(path),
)

path.write_text(
    text,
    encoding="utf-8",
)

print(
    "TERMINAL_YASAM_DONGUSU_LIFESPAN_ILE_GUNCELLENDI"
)
