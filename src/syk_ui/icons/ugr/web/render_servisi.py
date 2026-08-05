"""UGR dinamik ikon web render servisi."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape
from pathlib import Path
from typing import Any

from syk_ui.icons.ugr.runtime.modeller import (
    IkonRuntimeKaydi,
)
from syk_ui.icons.ugr.runtime.servis import (
    UgrDinamikIkonServisi,
)
from syk_ui.icons.ugr.runtime.stil_kurallari import (
    durum_stili,
)

from .render_modeli import (
    IkonWebRenderKaydi,
    IkonWebStili,
)


class UgrIkonWebRenderServisi:
    """Runtime kayıtlarını web bileşenlerine dönüştürür."""

    def __init__(
        self,
        ikon_servisi: UgrDinamikIkonServisi,
        *,
        statik_kok: str = "/static/icons/ugr/",
    ) -> None:
        self.ikon_servisi = ikon_servisi
        self.statik_kok = statik_kok.rstrip(
            "/"
        )

    def _web_dosya_yolu(
        self,
        kayit: IkonRuntimeKaydi,
    ) -> str:
        """Yerel prototip yolunu web yoluna dönüştürür."""

        yol = Path(
            kayit.dosya_yolu
        )

        parcalar = list(yol.parts)

        if "prototype_icons" in parcalar:
            baslangic = (
                parcalar.index(
                    "prototype_icons"
                )
            )

            kalan = parcalar[
                baslangic:
            ]

            return (
                self.statik_kok
                + "/"
                + "/".join(kalan)
            )

        return kayit.dosya_yolu.replace(
            "\\",
            "/",
        )

    def render_kaydi(
        self,
        ikon_kimligi: str,
    ) -> IkonWebRenderKaydi:
        """Tek ikon için render modeli üretir."""

        kayit = (
            self.ikon_servisi
            .kayit_defteri
            .getir(ikon_kimligi)
        )

        stil = durum_stili(
            kayit.durum
        )

        return IkonWebRenderKaydi(
            ikon_kimligi=(
                kayit.ikon_kimligi
            ),
            kategori=kayit.kategori,
            etiket=kayit.etiket,
            dosya_yolu=(
                self._web_dosya_yolu(
                    kayit
                )
            ),
            durum=kayit.durum.value,
            gorunum_modu=(
                kayit.gorunum_modu.value
            ),
            aktif=kayit.aktif,
            bagli_nesne_kimligi=(
                kayit.bagli_nesne_kimligi
            ),
            stil=IkonWebStili(
                durum=kayit.durum.value,
                animasyon=(
                    stil.animasyon.value
                ),
                renk_rolu=(
                    stil.renk_rolu.value
                ),
                animasyon_suresi_ms=(
                    stil.animasyon_suresi_ms
                ),
                tekrarli=stil.tekrarli,
                parlaklik=stil.parlaklik,
                saydamlik=stil.saydamlik,
                olcek=stil.olcek,
            ),
        )

    def html_uret(
        self,
        ikon_kimligi: str,
    ) -> str:
        """Tek ikon için HTML üretir."""

        return self.render_kaydi(
            ikon_kimligi
        ).html()

    def json_uret(
        self,
        ikon_kimligi: str,
    ) -> dict[str, Any]:
        """Tek ikon için JSON sözlüğü üretir."""

        return self.render_kaydi(
            ikon_kimligi
        ).json_verisi()

    def kategori_html_uret(
        self,
        kategori: str,
    ) -> str:
        """Kategori içindeki ikonları grid olarak üretir."""

        kayitlar = (
            self.ikon_servisi
            .kayit_defteri
            .kategoriye_gore(kategori)
        )

        return self.grid_html_uret(
            kayitlar,
            baslik=kategori,
        )

    def grid_html_uret(
        self,
        kayitlar: Iterable[
            IkonRuntimeKaydi
        ],
        *,
        baslik: str = "UGR İkonları",
    ) -> str:
        """İkon kayıtlarından bir panel üretir."""

        renderlar = [
            self.render_kaydi(
                kayit.ikon_kimligi
            )
            for kayit in kayitlar
        ]

        ikon_html = "\n".join(
            render.html()
            for render in renderlar
        )

        guvenli_baslik = escape(
            baslik,
            quote=True,
        )

        return (
            '<section '
            'class="syk-ugr-icon-library" '
            'data-syk-ugr-library>'
            '<header '
            'class="syk-ugr-library-header">'
            f'<h2>{guvenli_baslik}</h2>'
            '<span '
            'class="syk-ugr-library-count">'
            f'{len(renderlar)} ikon'
            '</span>'
            '</header>'
            '<div '
            'class="syk-ugr-icon-grid">'
            f'{ikon_html}'
            '</div>'
            '</section>'
        )
