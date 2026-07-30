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