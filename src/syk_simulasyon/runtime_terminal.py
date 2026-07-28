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
</head>

<body>

<h1>SYKAŞİF - SyOtağı</h1>

<p>Runtime: {durum.runtime_durumu}</p>
<p>WebSocket: {durum.websocket_durumu}</p>
<p>Sistem: {durum.sistem_durumu}</p>

<hr>

<p>Başlangıç: {durum.baslangic}</p>
<p>Hedef: {durum.hedef}</p>
<p>Rota: {durum.rota}</p>

</body>
</html>
"""