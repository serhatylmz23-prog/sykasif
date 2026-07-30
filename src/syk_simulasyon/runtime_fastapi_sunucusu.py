from __future__ import annotations

import asyncio
import os
import secrets

from fastapi import (
    FastAPI,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)

from .runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from .runtime_csv import RuntimeCsvSaglayicisi
from .runtime_disa_aktarim import RuntimeDisaAktarim
from .runtime_html import RuntimeHtmlSaglayicisi
from .runtime_hesap_deposu import RuntimeHesapDeposu
from .runtime_http_api import RuntimeHttpApi
from .runtime_izleme import RuntimeIzlemeSaglayicisi
from .runtime_json import RuntimeJsonSaglayicisi
from .runtime_markdown import RuntimeMarkdownSaglayicisi
from .runtime_olay_gunlugu import (
    RuntimeOlayGunluguButunlukHatasi,
)
from .runtime_oturum import (
    OTURUM_CEREZI_ADI,
    RuntimeOturumYoneticisi,
    parola_ozeti_uret,
)
from .runtime_servisi import RuntimeServisi
from .runtime_secure_export import (
    ExportRole,
    ExportSecurityProfile,
    SecureExportViewProvider,
)
from .runtime_durumu import RuntimeDurumu
from .runtime_terminal import RuntimeTerminal
from .runtime_websocket import RuntimeWebSocketYayincisi
from .runtime_xml import RuntimeXmlSaglayicisi
from .runtime_yaml import RuntimeYamlSaglayicisi


class RuntimeFastApiSunucusu:

    def __init__(
        self,
        disa_aktarim: RuntimeDisaAktarim,
        websocket_yayinci: RuntimeWebSocketYayincisi | None = None,
        runtime_durumu: RuntimeDurumu | None = None,
        runtime_servisi: RuntimeServisi | None = None,
        oturum_yoneticisi: RuntimeOturumYoneticisi | None = None,
        hesap_deposu: RuntimeHesapDeposu | None = None,
    ) -> None:

        self._api = RuntimeHttpApi(disa_aktarim)
        self._websocket = websocket_yayinci
        self._terminal = RuntimeTerminal(runtime_durumu)
        self._runtime_servisi = runtime_servisi
        self._oturum_yoneticisi = oturum_yoneticisi
        self._hesap_deposu = hesap_deposu

    def olustur(self) -> FastAPI:

        uygulama = FastAPI(
            title="SyKaşif Runtime API",
            version="1.1",
        )

        uygulama.state.runtime_hesap_deposu = (
            self._hesap_deposu
        )

        def oturum_gecerli_mi(
            istek: Request,
        ) -> bool:
            yonetici = self._oturum_yoneticisi

            if yonetici is None:
                return True

            return yonetici.oturum_dogrula(
                istek.cookies.get(
                    OTURUM_CEREZI_ADI
                )
            )

        def _guvenli_cerez_etkin_mi() -> bool:
            return (
                os.getenv(
                    "SYK_RUNTIME_GUVENLI_CEREZ",
                    "",
                ).strip().lower()
                in {
                    "1",
                    "true",
                    "evet",
                    "acik",
                    "a\u00e7\u0131k",
                }
            )

        def _giris_html(
            *,
            ilk_kurulum: bool,
        ) -> str:
            if ilk_kurulum:
                baslik = "SyKa\u015fif \u0130lk Kurulum"
                aciklama = (
                    "Kurucu hesab\u0131n\u0131 olu\u015fturun."
                )
                form_kimligi = "kurulum-formu"
                yol = "/runtime/ilk-kurulum"
                dugme = "Kurulumu tamamla"
                ek_alanlar = """
<label for="eposta">E-posta (iste\u011fe ba\u011fl\u0131)</label>
<input id="eposta" type="email" autocomplete="email">
<label for="telefon">Telefon (iste\u011fe ba\u011fl\u0131)</label>
<input id="telefon" autocomplete="tel">
<label for="parola_tekrar">Parola tekrar\u0131</label>
<input id="parola_tekrar" type="password"
       autocomplete="new-password" required>
"""
                parola_tamamlama = "new-password"
                veri_ekleri = """
                eposta:
                    document.getElementById("eposta").value,
                telefon:
                    document.getElementById("telefon").value,
                parola_tekrar:
                    document.getElementById("parola_tekrar").value,
"""
            else:
                baslik = "SyKa\u015fif Giri\u015f"
                aciklama = (
                    "G\u00fcvenli \u00e7al\u0131\u015fma "
                    "terminaline giri\u015f"
                )
                form_kimligi = "giris-formu"
                yol = "/runtime/oturum"
                dugme = "Giri\u015f yap"
                ek_alanlar = ""
                parola_tamamlama = "current-password"
                veri_ekleri = ""

            return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{baslik}</title>
<style>
body {{
    font-family: system-ui, sans-serif;
    background: #111827;
    color: #f9fafb;
    min-height: 100vh;
    display: grid;
    place-items: center;
    margin: 0;
}}
main {{
    width: min(440px, calc(100% - 32px));
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 16px;
    padding: 28px;
    box-sizing: border-box;
}}
h1 {{ margin-top: 0; }}
label {{
    display: block;
    margin: 16px 0 6px;
}}
input {{
    box-sizing: border-box;
    width: 100%;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #4b5563;
}}
button {{
    width: 100%;
    margin-top: 20px;
    padding: 12px;
    border: 0;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
}}
#mesaj {{
    min-height: 24px;
    color: #fca5a5;
}}
</style>
</head>
<body>
<main>
<h1>{baslik}</h1>
<p>{aciklama}</p>
<form id="{form_kimligi}">
<label for="kullanici_adi">Kullan\u0131c\u0131 ad\u0131</label>
<input id="kullanici_adi" autocomplete="username" required>
{ek_alanlar}
<label for="parola">Parola veya PIN</label>
<input id="parola" type="password"
       autocomplete="{parola_tamamlama}" required>
<button type="submit">{dugme}</button>
<p id="mesaj" role="alert"></p>
</form>
</main>
<script>
document.getElementById("{form_kimligi}").addEventListener(
    "submit",
    async (olay) => {{
        olay.preventDefault();

        const yanit = await fetch("{yol}", {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{
                kullanici_adi:
                    document.getElementById("kullanici_adi").value,
                parola:
                    document.getElementById("parola").value,
{veri_ekleri}
            }})
        }});

        if (yanit.ok) {{
            window.location.assign("/terminal");
            return;
        }}

        let mesaj = "Kimlik bilgileri do\u011frulanamad\u0131.";

        try {{
            const veri = await yanit.json();
            mesaj = veri.mesaj || mesaj;
        }}
        catch (_hata) {{
        }}

        document.getElementById("mesaj").textContent = mesaj;
    }}
);
</script>
</body>
</html>"""

        @uygulama.get("/giris")
        def giris_ekrani(
            istek: Request,
        ) -> Response:
            if oturum_gecerli_mi(istek):
                return RedirectResponse(
                    url="/terminal",
                    status_code=303,
                )

            depo = self._hesap_deposu
            ilk_kurulum = (
                depo is not None
                and not depo.hesap_var_mi()
            )

            return HTMLResponse(
                content=_giris_html(
                    ilk_kurulum=ilk_kurulum,
                ),
                status_code=200,
            )

        @uygulama.post("/runtime/ilk-kurulum")
        async def ilk_kurulum(
            istek: Request,
        ) -> JSONResponse:
            depo = self._hesap_deposu
            yonetici = self._oturum_yoneticisi

            if depo is None or yonetici is None:
                return JSONResponse(
                    status_code=503,
                    content={
                        "durum": "kurulum_kullan\u0131lam\u0131yor",
                        "mesaj": "Kurulum altyap\u0131s\u0131 haz\u0131r de\u011fil.",
                    },
                )

            if depo.hesap_var_mi():
                return JSONResponse(
                    status_code=409,
                    content={
                        "durum": "kurulum_tamamlanm\u0131\u015f",
                        "mesaj": "Kurucu hesab\u0131 zaten olu\u015fturulmu\u015f.",
                    },
                )

            try:
                veri = await istek.json()
                kullanici_adi = str(
                    veri.get("kullanici_adi", "")
                ).strip()
                eposta = str(
                    veri.get("eposta", "")
                ).strip() or None
                telefon = str(
                    veri.get("telefon", "")
                ).strip() or None
                parola = str(
                    veri.get("parola", "")
                )
                parola_tekrar = str(
                    veri.get("parola_tekrar", "")
                )
            except (
                AttributeError,
                TypeError,
                ValueError,
            ):
                return JSONResponse(
                    status_code=400,
                    content={
                        "durum": "ge\u00e7ersiz_istek",
                        "mesaj": "Kurulum bilgileri ge\u00e7ersiz.",
                    },
                )

            if not kullanici_adi:
                return JSONResponse(
                    status_code=400,
                    content={
                        "durum": "kullan\u0131c\u0131_ad\u0131_gerekli",
                        "mesaj": "Kullan\u0131c\u0131 ad\u0131 gereklidir.",
                    },
                )

            if len(parola) < 4:
                return JSONResponse(
                    status_code=400,
                    content={
                        "durum": "parola_k\u0131sa",
                        "mesaj": "Parola veya PIN en az 4 karakter olmal\u0131d\u0131r.",
                    },
                )

            if parola != parola_tekrar:
                return JSONResponse(
                    status_code=400,
                    content={
                        "durum": "parolalar_e\u015fle\u015fmiyor",
                        "mesaj": "Parolalar e\u015fle\u015fmiyor.",
                    },
                )

            try:
                hesap = depo.hesap_olustur(
                    kullanici_adi=kullanici_adi,
                    eposta=eposta,
                    telefon=telefon,
                    parola=parola,
                    rol="kurucu",
                )
            except (
                ValueError,
                RuntimeError,
            ):
                return JSONResponse(
                    status_code=409,
                    content={
                        "durum": "hesap_olu\u015fturulamad\u0131",
                        "mesaj": "Kurucu hesab\u0131 olu\u015fturulamad\u0131.",
                    },
                )

            yanit = JSONResponse(
                status_code=201,
                content={
                    "durum": "kurulum_tamamland\u0131",
                    "hesap_kimligi": hesap.hesap_kimligi,
                },
            )

            yanit.set_cookie(
                key=OTURUM_CEREZI_ADI,
                value=yonetici.oturum_uret(
                    kullanici_adi=hesap.kullanici_adi,
                    hesap_kimligi=hesap.hesap_kimligi,
                    rol=hesap.rol,
                ),
                max_age=yonetici.oturum_suresi_saniye,
                httponly=True,
                secure=_guvenli_cerez_etkin_mi(),
                samesite="strict",
                path="/",
            )

            return yanit

        @uygulama.post("/runtime/oturum")
        async def oturum_ac(
            istek: Request,
        ) -> JSONResponse:
            yonetici = self._oturum_yoneticisi

            if yonetici is None:
                return JSONResponse(
                    status_code=503,
                    content={
                        "durum": "giri\u015f_yap\u0131land\u0131r\u0131lmad\u0131",
                        "mesaj": "Giri\u015f altyap\u0131s\u0131 haz\u0131r de\u011fil.",
                    },
                )

            try:
                veri = await istek.json()
                kimlik = str(
                    veri.get(
                        "kimlik",
                        veri.get("kullanici_adi", ""),
                    )
                ).strip()
                parola = str(
                    veri.get("parola", "")
                )
            except (
                AttributeError,
                TypeError,
                ValueError,
            ):
                return JSONResponse(
                    status_code=400,
                    content={
                        "durum": "ge\u00e7ersiz_istek",
                        "mesaj": "Giri\u015f bilgileri ge\u00e7ersiz.",
                    },
                )

            depo = self._hesap_deposu
            hesap = None

            if depo is not None:
                if not depo.hesap_var_mi():
                    return JSONResponse(
                        status_code=409,
                        content={
                            "durum": "ilk_kurulum_gerekli",
                            "mesaj": "\u00d6nce ilk kurulumu tamamlay\u0131n.",
                        },
                    )

                hesap = depo.kimlik_dogrula(
                    kimlik,
                    parola,
                )

                dogrulandi = hesap is not None
            else:
                dogrulandi = yonetici.kimlik_dogrula(
                    kimlik,
                    parola,
                )

            if not dogrulandi:
                return JSONResponse(
                    status_code=401,
                    content={
                        "durum": "kimlik_do\u011frulanamad\u0131",
                        "mesaj": "Kullan\u0131c\u0131 kimli\u011fi veya parola ge\u00e7ersiz.",
                    },
                )

            if hesap is not None:
                belirtec = yonetici.oturum_uret(
                    kullanici_adi=hesap.kullanici_adi,
                    hesap_kimligi=hesap.hesap_kimligi,
                    rol=hesap.rol,
                )
            else:
                belirtec = yonetici.oturum_uret()

            yanit = JSONResponse(
                status_code=200,
                content={
                    "durum": "oturum_a\u00e7\u0131ld\u0131"
                },
            )

            yanit.set_cookie(
                key=OTURUM_CEREZI_ADI,
                value=belirtec,
                max_age=yonetici.oturum_suresi_saniye,
                httponly=True,
                secure=_guvenli_cerez_etkin_mi(),
                samesite="strict",
                path="/",
            )

            return yanit

        @uygulama.post("/cikis")
        def oturum_kapat() -> JSONResponse:
            yanit = JSONResponse(
                status_code=200,
                content={
                    "durum": "oturum_kapatıldı"
                },
            )

            yanit.delete_cookie(
                key=OTURUM_CEREZI_ADI,
                path="/",
                httponly=True,
                samesite="strict",
            )

            return yanit

        @uygulama.get("/runtime/health")
        def runtime_sagligi() -> JSONResponse:
            servis = self._runtime_servisi
            tanilama_etkin = os.getenv(
                "SYK_RUNTIME_TANILAMA",
                "",
            ).strip().lower() in {
                "1",
                "true",
                "evet",
                "acik",
                "açık",
            }

            if servis is None:
                return JSONResponse(
                    status_code=200,
                    content={
                        "durum": "çalışıyor",
                        "hazir": True,
                        "kalici_gunluk": {
                            "etkin": False,
                            "butunluk": "kullanılmıyor",
                            "yol": None,
                            "kayit_sayisi": 0,
                        },
                    },
                )

            gunluk = servis.olay_gunlugu

            if gunluk is None:
                return JSONResponse(
                    status_code=200,
                    content={
                        "durum": "çalışıyor",
                        "hazir": True,
                        "kalici_gunluk": {
                            "etkin": False,
                            "butunluk": "kullanılmıyor",
                            "yol": None,
                            "kayit_sayisi": len(
                                servis.olay_gecmisi()
                            ),
                        },
                    },
                )

            try:
                olaylar = gunluk.olaylari_oku()
                gunluk.butunlugu_dogrula()
            except RuntimeOlayGunluguButunlukHatasi as hata:
                gunluk_bilgisi = {
                    "etkin": True,
                    "butunluk": "bozuk",
                    "kayit_sayisi": None,
                }

                yanit = {
                    "durum": "hatalı",
                    "hazir": False,
                    "kalici_gunluk": gunluk_bilgisi,
                }

                if tanilama_etkin:
                    gunluk_bilgisi["yol"] = str(
                        gunluk.yol
                    )
                    yanit["hata"] = str(hata)

                return JSONResponse(
                    status_code=503,
                    content=yanit,
                )

            gunluk_bilgisi = {
                "etkin": True,
                "butunluk": "sağlam",
                "kayit_sayisi": len(olaylar),
            }

            if tanilama_etkin:
                gunluk_bilgisi["yol"] = str(
                    gunluk.yol
                )

            return JSONResponse(
                status_code=200,
                content={
                    "durum": "çalışıyor",
                    "hazir": True,
                    "kalici_gunluk": gunluk_bilgisi,
                },
            )

        @uygulama.get("/terminal")
        def terminal(
            istek: Request,
        ) -> Response:
            if not oturum_gecerli_mi(istek):
                return RedirectResponse(
                    url="/giris",
                    status_code=303,
                )

            return Response(
                content=self._terminal.html(),
                media_type="text/html; charset=utf-8",
            )

        @uygulama.get("/runtime/json")
        def runtime_json() -> Response:

            durum, govde = self._api.json()

            return Response(
                content=govde,
                status_code=durum,
                media_type="application/json",
            )

        @uygulama.get("/runtime/html")
        def runtime_html() -> Response:

            durum, govde = self._api.html()

            return Response(
                content=govde,
                status_code=durum,
                media_type="text/html",
            )

        @uygulama.get("/runtime/csv")
        def runtime_csv() -> Response:

            durum, govde = self._api.csv()

            return Response(
                content=govde,
                status_code=durum,
                media_type="text/csv",
            )

        @uygulama.get("/runtime/markdown")
        def runtime_markdown() -> Response:

            durum, govde = self._api.markdown()

            return Response(
                content=govde,
                status_code=durum,
                media_type="text/markdown",
            )

        @uygulama.get("/runtime/xml")
        def runtime_xml() -> Response:

            durum, govde = self._api.xml()

            return Response(
                content=govde,
                status_code=durum,
                media_type="application/xml",
            )

        @uygulama.get("/runtime/yaml")
        def runtime_yaml() -> Response:

            durum, govde = self._api.yaml()

            return Response(
                content=govde,
                status_code=durum,
                media_type="application/yaml",
            )

        @uygulama.websocket("/ws/runtime")
        async def runtime_websocket(
            websocket: WebSocket,
        ) -> None:
            yonetici = self._oturum_yoneticisi

            if (
                yonetici is not None
                and not yonetici.oturum_dogrula(
                    websocket.cookies.get(
                        OTURUM_CEREZI_ADI
                    )
                )
            ):
                await websocket.close(
                    code=4401
                )
                return


            await websocket.accept()

            if self._websocket is None:
                await websocket.send_json(
                    {
                        "durum": "kullanılamıyor",
                        "mesaj": (
                            "WebSocket yayıncısı yapılandırılmadı."
                        ),
                    }
                )
                await websocket.close(code=1011)
                return

            olay_kuyrugu: asyncio.Queue[None] = asyncio.Queue()
            olay_dongusu = asyncio.get_running_loop()

            def runtime_olayi_geldi(_olay: object) -> None:
                olay_dongusu.call_soon_threadsafe(
                    olay_kuyrugu.put_nowait,
                    None,
                )

            bildirim_merkezi = (
                self._runtime_servisi.bildirim_merkezi
                if self._runtime_servisi is not None
                else None
            )

            if bildirim_merkezi is not None:
                bildirim_merkezi.abone_ekle(
                    runtime_olayi_geldi
                )

            olay_yayin_gorevi: asyncio.Task[None] | None = None

            async def olaylari_yayinla() -> None:
                while True:
                    await olay_kuyrugu.get()

                    try:
                        await websocket.send_json(
                            self._websocket.guncelleme_mesaji()
                        )
                    except (
                        WebSocketDisconnect,
                        RuntimeError,
                    ):
                        return

            try:
                await websocket.send_json(
                    self._websocket.baglanti_mesaji()
                )

                if bildirim_merkezi is not None:
                    olay_yayin_gorevi = asyncio.create_task(
                        olaylari_yayinla()
                    )

                while True:
                    komut = await websocket.receive_text()

                    if komut.lower() in {
                        "güncelle",
                        "guncelle",
                        "yenile",
                    }:
                        await websocket.send_json(
                            self._websocket.guncelleme_mesaji()
                        )
                    else:
                        await websocket.send_json(
                            self._websocket.bilinmeyen_komut(
                                komut
                            )
                        )

            except WebSocketDisconnect:
                pass
            finally:
                if bildirim_merkezi is not None:
                    bildirim_merkezi.abone_sil(
                        runtime_olayi_geldi
                    )

                if olay_yayin_gorevi is not None:
                    if not olay_yayin_gorevi.done():
                        olay_yayin_gorevi.cancel()

                    await asyncio.gather(
                        olay_yayin_gorevi,
                        return_exceptions=True,
                    )

        return uygulama


def uygulama_olustur(
    *,
    hesap_deposu_etkin: bool = True,
) -> FastAPI:

    olay_gunlugu_yolu = os.getenv(
        "SYK_RUNTIME_OLAY_GUNLUGU"
    )

    servis = RuntimeServisi(
        olay_gunlugu_yolu or None
    )

    gorunum = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    guvenli_gorunum = SecureExportViewProvider(
        gorunum,
        ExportSecurityProfile.from_environment(
            role=ExportRole.PUBLIC,
        ),
    )

    disa_aktarim = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(guvenli_gorunum),
        RuntimeCsvSaglayicisi(guvenli_gorunum),
        RuntimeHtmlSaglayicisi(guvenli_gorunum),
        RuntimeMarkdownSaglayicisi(guvenli_gorunum),
        RuntimeXmlSaglayicisi(guvenli_gorunum),
        RuntimeYamlSaglayicisi(guvenli_gorunum),
    )

    websocket_yayinci = RuntimeWebSocketYayincisi(
        gorunum,
        servis.durum.sistem_hazirlik_ozeti,
    )

    oturum_yoneticisi = (
        RuntimeOturumYoneticisi.ortamdan_olustur()
    )

    hesap_deposu = (
        RuntimeHesapDeposu()
        if os.name == "nt" and hesap_deposu_etkin
        else None
    )

    if oturum_yoneticisi is None and hesap_deposu is not None:
        gecici_parola = secrets.token_urlsafe(32)
        oturum_yoneticisi = RuntimeOturumYoneticisi(
            kullanici_adi="__hesap_deposu__",
            parola_ozeti=parola_ozeti_uret(
                gecici_parola,
            ),
            oturum_anahtari=secrets.token_bytes(32),
        )

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket_yayinci,
        servis.durum,
        runtime_servisi=servis,
        oturum_yoneticisi=oturum_yoneticisi,
        hesap_deposu=hesap_deposu,
    ).olustur()

    uygulama.state.runtime_servisi = servis
    uygulama.state.runtime_olay_gunlugu_yolu = (
        olay_gunlugu_yolu
    )

    return uygulama


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        uygulama_olustur(),
        host="0.0.0.0",
        port=8000,
    )
