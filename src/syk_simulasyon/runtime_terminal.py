from __future__ import annotations
from html import escape

from .runtime_terminal_model import SyOtagiDurumu
from .runtime_durumu import RuntimeDurumu

class RuntimeTerminal:
    """
    SyOtağı terminal görünüm sağlayıcısı.

    Çift panel görünümü, aynı RuntimeDurumu nesnesinden alınan anlık
    işleyiş ve sistem hazırlık verilerini gösterir.
    """

    def __init__(
        self,
        runtime_durumu: RuntimeDurumu | None = None,
    ) -> None:
        self._runtime_durumu = (
            runtime_durumu
            if runtime_durumu is not None
            else RuntimeDurumu()
        )

    @property
    def runtime_durumu(self) -> RuntimeDurumu:
        return self._runtime_durumu

    def durum(self) -> SyOtagiDurumu:
        """
        Mevcut SyOtağı dış sözleşmesini geriye uyumlu biçimde korur.
        """

        return SyOtagiDurumu(
            runtime_durumu="AKTİF",
            websocket_durumu="BAĞLI",
            sistem_durumu="HAZIR",
            baslangic="Belirlenmedi",
            hedef="Beklemede",
            rota="Hazırlanıyor",
        )

    @staticmethod
    def _metin(deger: object | None, varsayilan: str) -> str:
        if deger is None:
            return varsayilan

        temiz = str(deger).strip()
        if not temiz:
            return varsayilan

        return escape(temiz, quote=True)

    @staticmethod
    def _yuzde(deger: object) -> str:
        try:
            sayisal = float(deger)
        except (TypeError, ValueError):
            sayisal = 0.0

        sayisal = min(max(sayisal, 0.0), 100.0)

        if sayisal.is_integer():
            return str(int(sayisal))

        return f"{sayisal:.2f}".rstrip("0").rstrip(".")

    def _cift_panel_html(self) -> str:
        isleyis = self._runtime_durumu.gorunum()
        hazirlik = self._runtime_durumu.sistem_hazirlik_ozeti()

        aktif_adim = self._metin(
            isleyis.get("aktif_modul"),
            "Beklemede",
        )
        durum_metni = self._metin(
            isleyis.get("durum"),
            "Belirlenmedi",
        )
        risk = self._metin(
            isleyis.get("risk"),
            "Yok",
        )
        son_hata = self._metin(
            isleyis.get("son_hata"),
            "Yok",
        )

        tamamlanan = int(isleyis.get("tamamlanan_adim", 0))
        toplam = int(isleyis.get("toplam_adim", 0))
        kalan = int(isleyis.get("kalan_adim", 0))
        ilerleme = self._yuzde(
            isleyis.get("ilerleme_yuzdesi", 0),
        )

        terminal_arayuzu = self._yuzde(
            hazirlik.get("terminal_arayuzu", 0),
        )
        veri_akisi = self._yuzde(
            hazirlik.get("veri_akisi", 0),
        )
        kayit_zinciri = self._yuzde(
            hazirlik.get("kayit_zinciri", 0),
        )
        test_durumu = self._yuzde(
            hazirlik.get("test_durumu", 0),
        )
        disa_aktarim = self._yuzde(
            hazirlik.get("disa_aktarim_hazirligi", 0),
        )
        genel_hazirlik = self._yuzde(
            hazirlik.get("genel_uretime_hazirlik", 0),
        )

        return f"""
<section id="syk-cift-panel" style="
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
    gap:16px;
    margin:18px auto;
    max-width:1000px;
    font-family:system-ui,-apple-system,'Segoe UI',sans-serif;
">
    <article style="
        border:1px solid #39424e;
        border-radius:12px;
        padding:18px;
        background:#111820;
    ">
        <h2>İşleyiş Durumu</h2>
        <dl>
            <dt>Aktif Adım</dt><dd>{aktif_adim}</dd>
            <dt>Çalışma Durumu</dt><dd>{durum_metni}</dd>
            <dt>Tamamlanan Adım</dt><dd>{tamamlanan}</dd>
            <dt>Toplam Adım</dt><dd>{toplam}</dd>
            <dt>Kalan Adım</dt><dd>{kalan}</dd>
            <dt>Genel İlerleme</dt><dd>%{ilerleme}</dd>
            <dt>Risk</dt><dd>{risk}</dd>
            <dt>Son Hata</dt><dd>{son_hata}</dd>
        </dl>
    </article>

    <article style="
        border:1px solid #39424e;
        border-radius:12px;
        padding:18px;
        background:#111820;
    ">
        <h2>Sistem Hazırlık Durumu</h2>
        <dl>
            <dt>Terminal Arayüzü</dt><dd>%{terminal_arayuzu}</dd>
            <dt>Veri Akışı</dt><dd>%{veri_akisi}</dd>
            <dt>Kayıt Zinciri</dt><dd>%{kayit_zinciri}</dd>
            <dt>Test Durumu</dt><dd>%{test_durumu}</dd>
            <dt>Dışa Aktarım Hazırlığı</dt><dd>%{disa_aktarim}</dd>
            <dt>Üretime Hazırlık</dt><dd>%{genel_hazirlik}</dd>
        </dl>
    </article>
</section>
"""

    def _canli_betik_html(self) -> str:
        return r"""
<script>
(() => {
    "use strict";

    const tanimDegeriniBul = (etiket) => {
        const basliklar = document.querySelectorAll(
            "#syk-cift-panel dt"
        );

        for (const baslik of basliklar) {
            if (baslik.textContent.trim() === etiket) {
                return baslik.nextElementSibling;
            }
        }

        return null;
    };

    const kartDegeriniBul = (etiket) => {
        const kartlar = document.querySelectorAll(".kart");

        for (const kart of kartlar) {
            const baslik = kart.querySelector("b");

            if (
                baslik &&
                baslik.textContent.trim() === etiket
            ) {
                const metinDugumleri = Array.from(
                    kart.childNodes
                ).filter(
                    (dugum) => dugum.nodeType === Node.TEXT_NODE
                );

                if (metinDugumleri.length > 0) {
                    const alan = document.createElement("span");
                    alan.textContent = kart.textContent
                        .replace(baslik.textContent, "")
                        .trim();

                    for (const dugum of metinDugumleri) {
                        dugum.remove();
                    }

                    kart.appendChild(document.createTextNode(" "));
                    kart.appendChild(alan);
                    return alan;
                }
            }
        }

        return null;
    };

    const alanlar = {
        aktifAdim: tanimDegeriniBul("Aktif Adım"),
        calismaDurumu: tanimDegeriniBul("Çalışma Durumu"),
        genelIlerleme: tanimDegeriniBul("Genel İlerleme"),
        websocketDurumu: kartDegeriniBul("WebSocket:"),
    };

    let soket = null;
    let yenilemeZamanlayicisi = null;
    let yenidenBaglanmaZamanlayicisi = null;

    const metinAta = (alan, deger, varsayilan) => {
        if (!alan) {
            return;
        }

        if (
            deger === null ||
            deger === undefined ||
            deger === ""
        ) {
            alan.textContent = varsayilan;
            return;
        }

        alan.textContent = String(deger);
    };

    const yuzdeMetni = (deger) => {
        const sayi = Number(deger);

        if (!Number.isFinite(sayi)) {
            return "%0";
        }

        const sinirli = Math.min(
            100,
            Math.max(0, sayi)
        );

        const yuvarlanmis = (
            Math.round(sinirli * 100) / 100
        );

        return `%${yuvarlanmis}`;
    };

    const gorunumuUygula = (gorunum) => {
        if (
            !gorunum ||
            typeof gorunum !== "object"
        ) {
            return;
        }

        metinAta(
            alanlar.aktifAdim,
            gorunum.aktif_modul,
            "Beklemede"
        );

        metinAta(
            alanlar.calismaDurumu,
            gorunum.durum,
            "Belirlenmedi"
        );

        if (alanlar.genelIlerleme) {
            alanlar.genelIlerleme.textContent = (
                yuzdeMetni(
                    gorunum.ilerleme_yuzdesi
                )
            );
        }
    };

    const yenilemeDurdur = () => {
        if (yenilemeZamanlayicisi !== null) {
            window.clearInterval(
                yenilemeZamanlayicisi
            );
            yenilemeZamanlayicisi = null;
        }
    };

    const yenidenBaglanmayiPlanla = () => {
        if (
            yenidenBaglanmaZamanlayicisi !== null
        ) {
            return;
        }

        yenidenBaglanmaZamanlayicisi = (
            window.setTimeout(
                () => {
                    yenidenBaglanmaZamanlayicisi = null;
                    baglan();
                },
                3000
            )
        );
    };

    const baglan = () => {
        const protokol = (
            window.location.protocol === "https:"
            ? "wss:"
            : "ws:"
        );

        const adres = (
            `${protokol}//${window.location.host}/ws/runtime`
        );

        metinAta(
            alanlar.websocketDurumu,
            "BAĞLANIYOR",
            "BAĞLANIYOR"
        );

        soket = new WebSocket(adres);

        soket.addEventListener("open", () => {
            metinAta(
                alanlar.websocketDurumu,
                "BAĞLI",
                "BAĞLI"
            );

            yenilemeDurdur();

            yenilemeZamanlayicisi = (
                window.setInterval(
                    () => {
                        if (
                            soket &&
                            soket.readyState === WebSocket.OPEN
                        ) {
                            soket.send("yenile");
                        }
                    },
                    2000
                )
            );
        });

        soket.addEventListener(
            "message",
            (olay) => {
                try {
                    const mesaj = JSON.parse(olay.data);
                    gorunumuUygula(mesaj.gorunum);
                } catch (hata) {
                    console.warn(
                        "SyKaşif canlı görünüm mesajı "
                        + "işlenemedi.",
                        hata
                    );
                }
            }
        );

        soket.addEventListener("close", () => {
            yenilemeDurdur();

            metinAta(
                alanlar.websocketDurumu,
                "BAĞLANTI KESİLDİ",
                "BAĞLANTI KESİLDİ"
            );

            yenidenBaglanmayiPlanla();
        });

        soket.addEventListener("error", () => {
            if (soket) {
                soket.close();
            }
        });
    };

    baglan();
})();
</script>
"""

    def html(self) -> str:
        durum = self.durum()
        panel = self._cift_panel_html()
        canli_betik = self._canli_betik_html()

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

#syk-cift-panel dt {{
    font-weight: 700;
    margin-top: 8px;
}}

#syk-cift-panel dd {{
    margin: 2px 0 8px;
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
{escape(str(durum.runtime_durumu), quote=True)}
</div>

<div class="kart">
<b>WebSocket:</b>
{escape(str(durum.websocket_durumu), quote=True)}
</div>

<div class="kart">
<b>Sistem:</b>
{escape(str(durum.sistem_durumu), quote=True)}
</div>

<div class="kart">
<b>Başlangıç:</b>
{escape(str(durum.baslangic), quote=True)}
</div>

<div class="kart">
<b>Rota:</b>
{escape(str(durum.rota), quote=True)}
</div>

<div class="kart">
<b>Hedef:</b>
{escape(str(durum.hedef), quote=True)}
</div>

</div>

{panel}

{canli_betik}

</body>
</html>
"""
