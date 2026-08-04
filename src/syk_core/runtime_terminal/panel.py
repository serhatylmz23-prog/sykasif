"""SyKaşif Türkçe terminal paneli."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from syk_core.runtime_kernel import (
    RuntimeEvent,
    RuntimeEventBus,
)

from .ag_gecidi import TerminalAgGecidi
from .modeller import (
    CihazDurumu,
    KomutDurumu,
)
from .oturum_modelleri import (
    OturumDurumu,
)
from .panel_modelleri import (
    PanelAnlikGorunumu,
    PanelAyarlari,
    PanelDurumu,
)
from .terminal import CalismaTerminali
from .oturum_yoneticisi import (
    TerminalOturumYoneticisi,
)


class TerminalPaneli:
    """Terminal durumunu Türkçe ve anlaşılır biçimde gösterir."""

    def __init__(
        self,
        terminal: CalismaTerminali,
        oturum_yoneticisi: TerminalOturumYoneticisi,
        *,
        ag_gecidi: TerminalAgGecidi | None = None,
        ayarlar: PanelAyarlari | None = None,
        olay_hatti: RuntimeEventBus | None = None,
        saat: Callable[[], datetime] | None = None,
    ) -> None:
        self.terminal = terminal
        self.oturum_yoneticisi = (
            oturum_yoneticisi
        )
        self.ag_gecidi = ag_gecidi
        self.ayarlar = ayarlar or PanelAyarlari()
        self.olay_hatti = (
            olay_hatti
            or terminal.olay_hatti
        )
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self.durum = PanelDurumu.HAZIR

        self._olay_yayinla(
            konu="terminal.panel.hazir",
            icerik={
                "başlık": self.ayarlar.baslik,
            },
        )

    def anlik_gorunum_olustur(
        self,
    ) -> PanelAnlikGorunumu:
        terminal_ozeti = (
            self.terminal.durum_ozeti()
        )

        oturum_ozeti = (
            self.oturum_yoneticisi.durum_ozeti()
        )

        cihazlar = list(
            terminal_ozeti.get(
                "cihazlar",
                [],
            )
        )

        oturumlar = list(
            oturum_ozeti.get(
                "oturumlar",
                [],
            )
        )

        komutlar = list(
            terminal_ozeti.get(
                "komutlar",
                [],
            )
        )

        bildirimler = list(
            terminal_ozeti.get(
                "bildirimler",
                [],
            )
        )

        komutlar = komutlar[
            -self.ayarlar.en_fazla_komut_sayisi:
        ]

        bildirimler = bildirimler[
            -self.ayarlar.en_fazla_bildirim_sayisi:
        ]

        oturumlar = oturumlar[
            -self.ayarlar.en_fazla_oturum_sayisi:
        ]

        sistem: dict[str, Any] = {
            "terminal": "hazır",
            "oturum_yöneticisi": "hazır",
            "ağ_geçidi": (
                "hazır"
                if self.ag_gecidi is not None
                else "bağlı_değil"
            ),
            "dil": "Türkçe",
            "insan_onayı": "zorunlu",
            "dışarı_veri_çıkışı": (
                "varsayılan_olarak_kapalı"
            ),
        }

        if self.ag_gecidi is not None:
            sistem["ağ_geçidi_özeti"] = (
                self.ag_gecidi.durum_ozeti()
            )

        gorunum = PanelAnlikGorunumu(
            olusturulma_zamani=self._saat(),
            panel_durumu=self.durum,
            toplam_cihaz_sayisi=int(
                terminal_ozeti.get(
                    "toplam_cihaz_sayısı",
                    0,
                )
            ),
            bagli_cihaz_sayisi=int(
                terminal_ozeti.get(
                    "bağlı_cihaz_sayısı",
                    0,
                )
            ),
            cevrimdisi_cihaz_sayisi=int(
                terminal_ozeti.get(
                    "çevrimdışı_cihaz_sayısı",
                    0,
                )
            ),
            engelli_cihaz_sayisi=int(
                terminal_ozeti.get(
                    "engelli_cihaz_sayısı",
                    0,
                )
            ),
            etkin_oturum_sayisi=int(
                oturum_ozeti.get(
                    "bağlı_oturum_sayısı",
                    0,
                )
            ),
            kuyruktaki_komut_sayisi=int(
                terminal_ozeti.get(
                    "kuyruktaki_komut_sayısı",
                    0,
                )
            ),
            tamamlanan_komut_sayisi=int(
                terminal_ozeti.get(
                    "tamamlanan_komut_sayısı",
                    0,
                )
            ),
            reddedilen_komut_sayisi=int(
                terminal_ozeti.get(
                    "reddedilen_komut_sayısı",
                    0,
                )
            ),
            bildirim_sayisi=int(
                terminal_ozeti.get(
                    "bildirim_sayısı",
                    0,
                )
            ),
            cihazlar=cihazlar,
            oturumlar=oturumlar,
            komutlar=komutlar,
            bildirimler=bildirimler,
            sistem=sistem,
        )

        self._olay_yayinla(
            konu="terminal.panel.gorunum_olusturuldu",
            icerik={
                "toplam_cihaz_sayısı": (
                    gorunum.toplam_cihaz_sayisi
                ),
                "etkin_oturum_sayısı": (
                    gorunum.etkin_oturum_sayisi
                ),
            },
        )

        return gorunum

    def html_olustur(
        self,
    ) -> str:
        gorunum = self.anlik_gorunum_olustur()

        cihaz_satirlari = "".join(
            self._cihaz_satiri(cihaz)
            for cihaz in gorunum.cihazlar
        )

        if not cihaz_satirlari:
            cihaz_satirlari = (
                '<tr><td colspan="5" class="bos">'
                "Kayıtlı cihaz bulunmuyor."
                "</td></tr>"
            )

        oturum_satirlari = "".join(
            self._oturum_satiri(oturum)
            for oturum in gorunum.oturumlar
        )

        if not oturum_satirlari:
            oturum_satirlari = (
                '<tr><td colspan="4" class="bos">'
                "Etkin oturum bulunmuyor."
                "</td></tr>"
            )

        komut_satirlari = "".join(
            self._komut_satiri(komut)
            for komut in reversed(
                gorunum.komutlar
            )
        )

        if not komut_satirlari:
            komut_satirlari = (
                '<tr><td colspan="5" class="bos">'
                "Henüz komut bulunmuyor."
                "</td></tr>"
            )

        bildirim_kartlari = "".join(
            self._bildirim_karti(bildirim)
            for bildirim in reversed(
                gorunum.bildirimler
            )
        )

        if not bildirim_kartlari:
            bildirim_kartlari = (
                '<div class="bos-kart">'
                "Henüz bildirim bulunmuyor."
                "</div>"
            )

        yenileme_milisaniye = (
            self.ayarlar.yenileme_suresi_saniye
            * 1000
        )

        baslik = escape(
            self.ayarlar.baslik
        )

        alt_baslik = escape(
            self.ayarlar.alt_baslik
        )

        zaman = escape(
            gorunum.olusturulma_zamani
            .astimezone()
            .strftime("%d.%m.%Y %H:%M:%S")
        )

        return f"""<!doctype html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>{baslik}</title>
    <style>
        :root {{
            color-scheme: dark;
            --zemin: #101417;
            --zemin-iki: #171d21;
            --zemin-uc: #20282d;
            --cizgi: #334047;
            --yazi: #eef5f7;
            --soluk: #9eb0b8;
            --basarili: #6dd3a0;
            --uyari: #e8c46a;
            --hata: #ee7d7d;
            --bilgi: #7eb9df;
            --vurgu: #b9cbd2;
            --golge: rgba(0, 0, 0, 0.28);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(
                    circle at top,
                    #1d262c 0,
                    var(--zemin) 48%
                );
            color: var(--yazi);
            font-family:
                "Segoe UI",
                Arial,
                sans-serif;
        }}

        .sayfa {{
            width: min(1500px, 96vw);
            margin: 0 auto;
            padding: 22px 0 40px;
        }}

        .ust {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            padding: 20px 22px;
            border: 1px solid var(--cizgi);
            border-radius: 18px;
            background:
                linear-gradient(
                    135deg,
                    rgba(34, 44, 50, 0.96),
                    rgba(19, 25, 29, 0.96)
                );
            box-shadow: 0 18px 45px var(--golge);
        }}

        .baslik h1 {{
            margin: 0;
            font-size: clamp(24px, 3vw, 38px);
            font-weight: 650;
            letter-spacing: 0.02em;
        }}

        .baslik p {{
            margin: 7px 0 0;
            color: var(--soluk);
            font-size: 15px;
        }}

        .ust-durum {{
            display: flex;
            align-items: center;
            gap: 10px;
            white-space: nowrap;
        }}

        .durum-noktasi {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--basarili);
            box-shadow:
                0 0 0 5px rgba(109, 211, 160, 0.12),
                0 0 18px rgba(109, 211, 160, 0.5);
        }}

        .zaman {{
            color: var(--soluk);
            font-size: 13px;
            margin-top: 6px;
            text-align: right;
        }}

        .kartlar {{
            display: grid;
            grid-template-columns:
                repeat(6, minmax(140px, 1fr));
            gap: 14px;
            margin-top: 16px;
        }}

        .ozet-karti {{
            min-height: 112px;
            padding: 17px;
            border: 1px solid var(--cizgi);
            border-radius: 15px;
            background: rgba(24, 31, 35, 0.93);
            box-shadow: 0 12px 28px var(--golge);
        }}

        .ozet-karti .etiket {{
            color: var(--soluk);
            font-size: 13px;
            line-height: 1.35;
        }}

        .ozet-karti .deger {{
            margin-top: 9px;
            font-size: 32px;
            font-weight: 700;
        }}

        .bolum {{
            margin-top: 16px;
            padding: 18px;
            border: 1px solid var(--cizgi);
            border-radius: 16px;
            background: rgba(22, 29, 33, 0.95);
            box-shadow: 0 14px 34px var(--golge);
        }}

        .bolum-basligi {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 14px;
        }}

        .bolum-basligi h2 {{
            margin: 0;
            font-size: 19px;
            font-weight: 650;
        }}

        .bolum-basligi span {{
            color: var(--soluk);
            font-size: 12px;
        }}

        .iki-sutun {{
            display: grid;
            grid-template-columns: 1.25fr 0.75fr;
            gap: 16px;
        }}

        .tablo-kapsayici {{
            width: 100%;
            overflow-x: auto;
            border: 1px solid var(--cizgi);
            border-radius: 12px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 680px;
        }}

        th,
        td {{
            padding: 12px 13px;
            text-align: left;
            border-bottom: 1px solid var(--cizgi);
            font-size: 13px;
        }}

        th {{
            color: var(--soluk);
            background: var(--zemin-uc);
            font-weight: 600;
        }}

        tr:last-child td {{
            border-bottom: 0;
        }}

        .rozet {{
            display: inline-flex;
            align-items: center;
            min-height: 25px;
            padding: 4px 9px;
            border-radius: 999px;
            border: 1px solid var(--cizgi);
            background: var(--zemin-uc);
            font-size: 12px;
        }}

        .rozet.basarili {{
            color: var(--basarili);
            border-color: rgba(109, 211, 160, 0.4);
        }}

        .rozet.uyari {{
            color: var(--uyari);
            border-color: rgba(232, 196, 106, 0.4);
        }}

        .rozet.hata {{
            color: var(--hata);
            border-color: rgba(238, 125, 125, 0.4);
        }}

        .rozet.bilgi {{
            color: var(--bilgi);
            border-color: rgba(126, 185, 223, 0.4);
        }}

        .bildirimler {{
            display: grid;
            gap: 10px;
        }}

        .bildirim {{
            padding: 13px 14px;
            border: 1px solid var(--cizgi);
            border-radius: 12px;
            background: var(--zemin-iki);
        }}

        .bildirim-ust {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }}

        .bildirim-baslik {{
            font-weight: 650;
            font-size: 14px;
        }}

        .bildirim-aciklama {{
            margin-top: 7px;
            color: var(--soluk);
            font-size: 13px;
            line-height: 1.5;
        }}

        .bildirim-zaman {{
            margin-top: 8px;
            color: #71838c;
            font-size: 11px;
        }}

        .guvenlik {{
            display: grid;
            grid-template-columns:
                repeat(3, minmax(160px, 1fr));
            gap: 12px;
        }}

        .guvenlik-karti {{
            padding: 14px;
            border: 1px solid var(--cizgi);
            border-radius: 12px;
            background: var(--zemin-iki);
        }}

        .guvenlik-karti strong {{
            display: block;
            margin-bottom: 6px;
            font-size: 13px;
        }}

        .guvenlik-karti span {{
            color: var(--soluk);
            font-size: 12px;
            line-height: 1.45;
        }}

        .bos,
        .bos-kart {{
            color: var(--soluk);
            text-align: center;
            padding: 22px;
        }}

        .alt {{
            margin-top: 18px;
            color: #778991;
            font-size: 12px;
            text-align: center;
        }}

        @media (max-width: 1180px) {{
            .kartlar {{
                grid-template-columns:
                    repeat(3, minmax(140px, 1fr));
            }}

            .iki-sutun {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 700px) {{
            .sayfa {{
                width: min(95vw, 700px);
            }}

            .ust {{
                align-items: flex-start;
                flex-direction: column;
            }}

            .ust-durum {{
                align-items: flex-start;
            }}

            .zaman {{
                text-align: left;
            }}

            .kartlar {{
                grid-template-columns:
                    repeat(2, minmax(130px, 1fr));
            }}

            .guvenlik {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <main class="sayfa">
        <header class="ust">
            <div class="baslik">
                <h1>{baslik}</h1>
                <p>{alt_baslik}</p>
            </div>

            <div>
                <div class="ust-durum">
                    <span class="durum-noktasi"></span>
                    <strong>Çalışma sistemi hazır</strong>
                </div>
                <div class="zaman">
                    Son güncelleme: {zaman}
                </div>
            </div>
        </header>

        <section class="kartlar">
            <article class="ozet-karti">
                <div class="etiket">Toplam cihaz</div>
                <div class="deger">
                    {gorunum.toplam_cihaz_sayisi}
                </div>
            </article>

            <article class="ozet-karti">
                <div class="etiket">Bağlı cihaz</div>
                <div class="deger">
                    {gorunum.bagli_cihaz_sayisi}
                </div>
            </article>

            <article class="ozet-karti">
                <div class="etiket">Etkin oturum</div>
                <div class="deger">
                    {gorunum.etkin_oturum_sayisi}
                </div>
            </article>

            <article class="ozet-karti">
                <div class="etiket">Kuyruktaki komut</div>
                <div class="deger">
                    {gorunum.kuyruktaki_komut_sayisi}
                </div>
            </article>

            <article class="ozet-karti">
                <div class="etiket">Tamamlanan komut</div>
                <div class="deger">
                    {gorunum.tamamlanan_komut_sayisi}
                </div>
            </article>

            <article class="ozet-karti">
                <div class="etiket">Bildirim</div>
                <div class="deger">
                    {gorunum.bildirim_sayisi}
                </div>
            </article>
        </section>

        <section class="bolum">
            <div class="bolum-basligi">
                <h2>Yetkili cihazlar</h2>
                <span>
                    Samsung tablet, iPhone ve ana makine
                </span>
            </div>

            <div class="tablo-kapsayici">
                <table>
                    <thead>
                        <tr>
                            <th>Cihaz adı</th>
                            <th>Cihaz türü</th>
                            <th>Yetki seviyesi</th>
                            <th>Durum</th>
                            <th>Son bağlantı</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cihaz_satirlari}
                    </tbody>
                </table>
            </div>
        </section>

        <div class="iki-sutun">
            <section class="bolum">
                <div class="bolum-basligi">
                    <h2>Çalışma oturumları</h2>
                    <span>Canlı bağlantılar</span>
                </div>

                <div class="tablo-kapsayici">
                    <table>
                        <thead>
                            <tr>
                                <th>Cihaz</th>
                                <th>Durum</th>
                                <th>Son canlılık</th>
                                <th>Mesaj sayısı</th>
                            </tr>
                        </thead>
                        <tbody>
                            {oturum_satirlari}
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="bolum">
                <div class="bolum-basligi">
                    <h2>Güvenlik durumu</h2>
                    <span>Varsayılan koruma ilkeleri</span>
                </div>

                <div class="guvenlik">
                    <div class="guvenlik-karti">
                        <strong>İnsan onayı</strong>
                        <span>
                            Kritik işlemlerde zorunlu
                        </span>
                    </div>

                    <div class="guvenlik-karti">
                        <strong>Veri çıkışı</strong>
                        <span>
                            Varsayılan olarak kapalı
                        </span>
                    </div>

                    <div class="guvenlik-karti">
                        <strong>Yetkisiz cihaz</strong>
                        <span>
                            Bağlantı ve komut reddedilir
                        </span>
                    </div>
                </div>
            </section>
        </div>

        <section class="bolum">
            <div class="bolum-basligi">
                <h2>Komut geçmişi</h2>
                <span>
                    Son {self.ayarlar.en_fazla_komut_sayisi} kayıt
                </span>
            </div>

            <div class="tablo-kapsayici">
                <table>
                    <thead>
                        <tr>
                            <th>Komut türü</th>
                            <th>Kaynak cihaz</th>
                            <th>Hedef cihaz</th>
                            <th>Durum</th>
                            <th>Oluşturulma zamanı</th>
                        </tr>
                    </thead>
                    <tbody>
                        {komut_satirlari}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="bolum">
            <div class="bolum-basligi">
                <h2>Bildirimler</h2>
                <span>
                    Son {self.ayarlar.en_fazla_bildirim_sayisi} bildirim
                </span>
            </div>

            <div class="bildirimler">
                {bildirim_kartlari}
            </div>
        </section>

        <footer class="alt">
            SyKaşif · Türkçe terminal arayüzü ·
            Otomatik yenileme:
            {self.ayarlar.yenileme_suresi_saniye} saniye
        </footer>
    </main>

    <script>
        window.setTimeout(
            function () {{
                window.location.reload();
            }},
            {yenileme_milisaniye}
        );
    </script>
</body>
</html>
"""

    def uygulamaya_bagla(
        self,
        uygulama: FastAPI,
        *,
        panel_yolu: str = "/terminal",
        veri_yolu: str = "/terminal/veri",
    ) -> None:
        if not panel_yolu.startswith("/"):
            raise ValueError(
                "Panel yolu eğik çizgi ile başlamalıdır."
            )

        if not veri_yolu.startswith("/"):
            raise ValueError(
                "Veri yolu eğik çizgi ile başlamalıdır."
            )

        @uygulama.get(
            panel_yolu,
            response_class=HTMLResponse,
            tags=["Terminal Paneli"],
        )
        async def terminal_paneli() -> HTMLResponse:
            return HTMLResponse(
                content=self.html_olustur(),
                status_code=200,
            )

        @uygulama.get(
            veri_yolu,
            tags=["Terminal Paneli"],
        )
        async def terminal_paneli_verisi() -> dict[str, Any]:
            return {
                "başarılı": True,
                "panel": (
                    self.anlik_gorunum_olustur()
                    .sozluk()
                ),
                "ayarlar": self.ayarlar.sozluk(),
            }

        uygulama.state.terminal_paneli = self

        self._olay_yayinla(
            konu="terminal.panel.uygulamaya_baglandi",
            icerik={
                "panel_yolu": panel_yolu,
                "veri_yolu": veri_yolu,
            },
        )

    @staticmethod
    def _rozet_sinifi(
        durum: str,
    ) -> str:
        basarili_durumlar = {
            "bağlı",
            "hazır",
            "tamamlandı",
            "çalışıyor",
            "kayıtlı",
        }

        uyari_durumlar = {
            "bekliyor",
            "kuyrukta",
            "çevrimdışı",
            "oluşturuldu",
        }

        hata_durumlar = {
            "hata",
            "reddedildi",
            "engelli",
            "iptal_edildi",
        }

        if durum in basarili_durumlar:
            return "basarili"

        if durum in uyari_durumlar:
            return "uyari"

        if durum in hata_durumlar:
            return "hata"

        return "bilgi"

    def _cihaz_satiri(
        self,
        cihaz: dict[str, Any],
    ) -> str:
        ad = escape(
            str(cihaz.get("ad", "-"))
        )

        cihaz_turu = escape(
            str(cihaz.get("cihaz_türü", "-"))
        )

        yetki = escape(
            str(cihaz.get("yetki_seviyesi", "-"))
        )

        durum = str(
            cihaz.get("durum", "-")
        )

        durum_gorunen = escape(durum)

        son_baglanti = escape(
            self._zaman_goster(
                cihaz.get(
                    "son_bağlantı_zamanı"
                )
            )
        )

        sinif = self._rozet_sinifi(
            durum
        )

        return f"""
<tr>
    <td>{ad}</td>
    <td>{cihaz_turu}</td>
    <td>{yetki}</td>
    <td>
        <span class="rozet {sinif}">
            {durum_gorunen}
        </span>
    </td>
    <td>{son_baglanti}</td>
</tr>
"""

    def _oturum_satiri(
        self,
        oturum: dict[str, Any],
    ) -> str:
        cihaz = escape(
            str(
                oturum.get(
                    "cihaz_kimliği",
                    "-",
                )
            )
        )

        durum = str(
            oturum.get("durum", "-")
        )

        son_canlilik = escape(
            self._zaman_goster(
                oturum.get(
                    "son_canlılık_zamanı"
                )
            )
        )

        mesaj_sayisi = int(
            oturum.get(
                "gönderilen_mesaj_sayısı",
                0,
            )
        ) + int(
            oturum.get(
                "alınan_mesaj_sayısı",
                0,
            )
        )

        sinif = self._rozet_sinifi(
            durum
        )

        return f"""
<tr>
    <td>{cihaz}</td>
    <td>
        <span class="rozet {sinif}">
            {escape(durum)}
        </span>
    </td>
    <td>{son_canlilik}</td>
    <td>{mesaj_sayisi}</td>
</tr>
"""

    def _komut_satiri(
        self,
        komut: dict[str, Any],
    ) -> str:
        komut_turu = escape(
            str(
                komut.get(
                    "komut_türü",
                    "-",
                )
            )
        )

        kaynak = escape(
            str(
                komut.get(
                    "kaynak_cihaz_kimliği",
                    "-",
                )
            )
        )

        hedef = escape(
            str(
                komut.get(
                    "hedef_cihaz_kimliği",
                    "-",
                )
            )
        )

        durum = str(
            komut.get("durum", "-")
        )

        zaman = escape(
            self._zaman_goster(
                komut.get(
                    "oluşturulma_zamanı"
                )
            )
        )

        sinif = self._rozet_sinifi(
            durum
        )

        return f"""
<tr>
    <td>{komut_turu}</td>
    <td>{kaynak}</td>
    <td>{hedef}</td>
    <td>
        <span class="rozet {sinif}">
            {escape(durum)}
        </span>
    </td>
    <td>{zaman}</td>
</tr>
"""

    def _bildirim_karti(
        self,
        bildirim: dict[str, Any],
    ) -> str:
        tur = str(
            bildirim.get(
                "bildirim_türü",
                "bilgi",
            )
        )

        baslik = escape(
            str(
                bildirim.get(
                    "başlık",
                    "Bildirim",
                )
            )
        )

        aciklama = escape(
            str(
                bildirim.get(
                    "açıklama",
                    "",
                )
            )
        )

        zaman = escape(
            self._zaman_goster(
                bildirim.get(
                    "oluşturulma_zamanı"
                )
            )
        )

        sinif = self._rozet_sinifi(
            tur
        )

        return f"""
<article class="bildirim">
    <div class="bildirim-ust">
        <div class="bildirim-baslik">
            {baslik}
        </div>
        <span class="rozet {sinif}">
            {escape(tur)}
        </span>
    </div>
    <div class="bildirim-aciklama">
        {aciklama}
    </div>
    <div class="bildirim-zaman">
        {zaman}
    </div>
</article>
"""

    @staticmethod
    def _zaman_goster(
        deger: Any,
    ) -> str:
        if deger in {
            None,
            "",
        }:
            return "-"

        metin = str(deger)

        try:
            zaman = datetime.fromisoformat(
                metin
            )

            return zaman.astimezone().strftime(
                "%d.%m.%Y %H:%M:%S"
            )
        except ValueError:
            return metin

    def _olay_yayinla(
        self,
        *,
        konu: str,
        icerik: dict[str, Any],
    ) -> None:
        self.olay_hatti.publish(
            RuntimeEvent(
                topic=konu,
                source="terminal_paneli",
                payload=icerik,
            )
        )


def terminal_panelini_bagla(
    uygulama: FastAPI,
    terminal: CalismaTerminali,
    oturum_yoneticisi: TerminalOturumYoneticisi,
    *,
    ag_gecidi: TerminalAgGecidi | None = None,
    ayarlar: PanelAyarlari | None = None,
    panel_yolu: str = "/terminal",
    veri_yolu: str = "/terminal/veri",
) -> TerminalPaneli:
    panel = TerminalPaneli(
        terminal,
        oturum_yoneticisi,
        ag_gecidi=ag_gecidi,
        ayarlar=ayarlar,
    )

    panel.uygulamaya_bagla(
        uygulama,
        panel_yolu=panel_yolu,
        veri_yolu=veri_yolu,
    )

    return panel
