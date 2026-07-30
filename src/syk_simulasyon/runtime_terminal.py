from __future__ import annotations

from .runtime_terminal_model import SyOtagiDurumu


class RuntimeTerminal:
    """
    SyOtağı terminal görünüm sağlayıcısı.
    """

    def durum(self) -> SyOtagiDurumu:
        return SyOtagiDurumu(
            runtime_durumu="AKTİF",
            websocket_durumu="BAĞLI",
            sistem_durumu="HAZIR",
            baslangic="Belirlenmedi",
            hedef="Beklemede",
            rota="Hazırlanıyor",
        )

    def html(self) -> str:
        durum = self.durum()

        return f"""
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">

<title>SyOtağı</title>

<style>
body {{
    font-family: Arial, sans-serif;
    background: #111;
    color: #eee;
    padding: 30px;
}}

.panel {{
    max-width: 600px;
    margin: auto;
}}

.kart {{
    border: 1px solid #555;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
}}

.baslik {{
    text-align: center;
}}
</style>

</head>

<body>

<div class="panel">

<h1 class="baslik">
SYKAŞİF
</h1>

<h2 class="baslik">
SyOtağı
</h2>

<div class="kart">
<b>Runtime:</b>
{durum.runtime_durumu}
</div>

<div class="kart">
<b>WebSocket:</b>
{durum.websocket_durumu}
</div>

<div class="kart">
<b>Sistem:</b>
{durum.sistem_durumu}
</div>

<div class="kart">
<b>Başlangıç:</b>
{durum.baslangic}
</div>

<div class="kart">
<b>Rota:</b>
{durum.rota}
</div>

<div class="kart">
<b>Hedef:</b>
{durum.hedef}
</div>

</div>

</body>
</html>
"""

# SYK_CIFT_PANEL_TERMINAL_V1
_syk_onceki_runtime_terminal_html = RuntimeTerminal.html


def _syk_cift_panel_html(self, *args, **kwargs):
    mevcut_html = _syk_onceki_runtime_terminal_html(
        self,
        *args,
        **kwargs,
    )

    panel = """
<section id="syk-cift-panel" style="
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
    gap:16px;
    margin:18px 0;
    font-family:system-ui,-apple-system,'Segoe UI',sans-serif;
">
    <article style="
        border:1px solid #39424e;
        border-radius:12px;
        padding:18px;
        background:#111820;
    ">
        <h2>\u0130\u015fleyi\u015f Durumu</h2>
        <dl>
            <dt>Aktif Ad\u0131m</dt><dd>Beklemede</dd>
            <dt>Tamamlanan Ad\u0131m</dt><dd>0</dd>
            <dt>Toplam Ad\u0131m</dt><dd>0</dd>
            <dt>Genel \u0130lerleme</dt><dd>%0</dd>
        </dl>
    </article>

    <article style="
        border:1px solid #39424e;
        border-radius:12px;
        padding:18px;
        background:#111820;
    ">
        <h2>Sistem Haz\u0131rl\u0131k Durumu</h2>
        <dl>
            <dt>Terminal Aray\u00fcz\u00fc</dt><dd>%100</dd>
            <dt>Veri Ak\u0131\u015f\u0131</dt><dd>%0</dd>
            <dt>Kay\u0131t Zinciri</dt><dd>%0</dd>
            <dt>Test Durumu</dt><dd>%0</dd>
            <dt>D\u0131\u015fa Aktar\u0131m Haz\u0131rl\u0131\u011f\u0131</dt><dd>%0</dd>
            <dt>\u00dcretime Haz\u0131rl\u0131k</dt><dd>%0</dd>
        </dl>
    </article>
</section>

<span hidden>SYKA\u015e\u0130F</span>
"""

    if 'id="syk-cift-panel"' in mevcut_html:
        return mevcut_html

    kapanis = mevcut_html.lower().rfind("</body>")

    if kapanis >= 0:
        return (
            mevcut_html[:kapanis]
            + panel
            + mevcut_html[kapanis:]
        )

    return mevcut_html + panel


RuntimeTerminal.html = _syk_cift_panel_html
