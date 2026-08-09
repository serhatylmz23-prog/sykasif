document.addEventListener("DOMContentLoaded", async () => {
    "use strict";

    console.info("SPRINT_053_008A_DOM_READY");

    document.documentElement.dataset.drawerRuntime = "ready";

    const sykRuntimeDrawer =
        document.getElementById("sykDrawer");

    const sykRuntimeAltCubuk =
        document.getElementById("sykAltIkonCubugu");

    if (!sykRuntimeDrawer) {
        throw new Error("DRAWER_DOM_BULUNAMADI");
    }

    if (!sykRuntimeAltCubuk) {
        throw new Error("ALT_IKON_CUBUGU_BULUNAMADI");
    }

    requestAnimationFrame(() => {
        const ikonSayisi =
            document.querySelectorAll(
                "#sykAltIkonCubugu .syk-ana-ikon"
            ).length;

        document.documentElement.dataset.drawerIconCount =
            String(ikonSayisi);

        console.info(
            "SPRINT_053_008B_DRAWER_RUNTIME",
            {
                drawerRuntime:
                    document.documentElement.dataset.drawerRuntime,
                drawerIconCount:
                    document.documentElement.dataset.drawerIconCount
            }
        );

        if (ikonSayisi < 1) {
            console.error("ALT_IKON_CUBUGU_BOS");
        }
    });

    try {
{
    "use strict";

    console.info("SPRINT_053_008_VIDEO_DRAWER_ACTIVE");

    const registryUrl =
        "/ui/data/terminal_menu_registry.json";

    const drawer =
        document.getElementById("sykDrawerPanel");

    const altIkonCubugu =
        document.getElementById("sykAltIkonCubugu");

    const drawerSecimler =
        document.getElementById("sykDrawerSecimler");

    const drawerBaslik =
        document.getElementById("sykDrawerBaslik");

    const drawerEtiket =
        document.getElementById("sykDrawerUstEtiket");

    const geriButon =
        document.getElementById("sykDrawerGeri");

    const hepsiniSec =
        document.getElementById("sykHepsiniSec");

    const aktifModulBaslik =
        document.getElementById("aktifModulBaslik");

    const sonIslem =
        document.getElementById("sonIslem");

    const seciliKatmanSayisi =
        document.getElementById("seciliKatmanSayisi");

    const acikPanelSayisi =
        document.getElementById("acikPanelSayisi");

    const saat =
        document.getElementById("saat");

    const haritaYuzeyi =
        document.querySelector(".harita-yuzeyi");

    const kasifMini =
        document.getElementById("kasifMini");


    let registry = null;

    let aktifModulId = "harita";

    /*
      yol:
      []                  -> ana alt başlıklar
      ["saha"]            -> saha çocukları
      ["saha","..."]      -> gelecekte alt-alt katman
    */
    let yol = [];

    const secimler = new Set();
    const yukluKaynaklar = new Map();


    function modulBul(id) {
        return registry.ana_moduller.find(
            x => x.id === id
        );
    }


    function secimKey(modulId, path, id) {
        return [
            modulId,
            ...path,
            id
        ].join(":");
    }


    function oncelikSinifi(oncelik) {

        if ((oncelik ?? 0) >= 90) {
            return "oncelik-yuksek";
        }

        if ((oncelik ?? 0) >= 70) {
            return "oncelik-orta";
        }

        return "oncelik-dusuk";
    }


    function lazyLoad(item) {

        if (!item.agir) {
            return;
        }

        if (yukluKaynaklar.has(item.id)) {
            return;
        }

        yukluKaynaklar.set(
            item.id,
            {
                yuklendi:
                    Date.now()
            }
        );

        console.info(
            `[SyKaşif] LAZY LOAD -> ${item.id}`
        );
    }


    function unload(item) {

        if (!item.agir) {
            return;
        }

        if (!yukluKaynaklar.has(item.id)) {
            return;
        }

        yukluKaynaklar.delete(
            item.id
        );

        console.info(
            `[SyKaşif] UNLOAD -> ${item.id}`
        );
    }


    function drawerAc() {
        drawer.classList.add("acik");
    }


    function drawerKapat() {
        drawer.classList.remove("acik");
        yol = [];
    }


    function mevcutModul() {
        return modulBul(
            aktifModulId
        );
    }


    function mevcutListe() {

        const modul =
            mevcutModul();

        if (yol.length === 0) {

            return modul.alt_basliklar.map(
                alt => ({
                    id:
                        alt.id,

                    ad:
                        alt.ad,

                    ikon:
                        "▦",

                    oncelik:
                        alt.oncelik ?? 0,

                    secilebilir:
                        alt.secilebilir !== false,

                    cocuklar:
                        alt.cocuklar ?? [],

                    tur:
                        "alt_baslik"
                })
            );
        }

        const altId =
            yol[0];

        const alt =
            modul.alt_basliklar.find(
                x => x.id === altId
            );

        if (!alt) {
            return [];
        }

        /*
          Registry ileride çocukların kendi çocuklarını
          içerebildiğinde aynı motor devam eder.
        */

        if (yol.length === 1) {
            return alt.cocuklar ?? [];
        }

        let liste =
            alt.cocuklar ?? [];

        for (
            let index = 1;
            index < yol.length;
            index++
        ) {

            const dugum =
                liste.find(
                    x =>
                        x.id ===
                        yol[index]
                );

            liste =
                dugum?.cocuklar ?? [];
        }

        return liste;
    }


    function mevcutBaslik() {

        const modul =
            mevcutModul();

        if (yol.length === 0) {
            return modul.ad;
        }

        let liste =
            modul.alt_basliklar;

        let ad =
            modul.ad;

        for (
            let i = 0;
            i < yol.length;
            i++
        ) {

            const id =
                yol[i];

            const dugum =
                liste.find(
                    x => x.id === id
                );

            if (!dugum) {
                break;
            }

            ad =
                dugum.ad;

            liste =
                dugum.cocuklar ?? [];
        }

        return ad;
    }


    function seciliMi(item) {

        const key =
            secimKey(
                aktifModulId,
                yol,
                item.id
            );

        return secimler.has(
            key
        );
    }


    function toplamSecimSayisi() {

        seciliKatmanSayisi.textContent =
            `${secimler.size} seçim etkin`;
    }


    function tumuSeciliMi(liste) {

        const secilebilir =
            liste.filter(
                item =>
                    !item.cocuklar ||
                    item.cocuklar.length === 0
            );

        if (
            secilebilir.length === 0
        ) {
            return false;
        }

        return secilebilir.every(
            item =>
                seciliMi(item)
        );
    }


    function hepsiniSecDurumu(liste) {

        const tam =
            tumuSeciliMi(
                liste
            );

        hepsiniSec.classList.toggle(
            "tumu-secili",
            tam
        );

        hepsiniSec.textContent =
            tam
                ? "Tümünü Kapat"
                : "Hepsini Seç";
    }


    function secimUygula(item) {

        const key =
            secimKey(
                aktifModulId,
                yol,
                item.id
            );

        const secili =
            secimler.has(
                key
            );

        if (secili) {

            secimler.delete(
                key
            );

            unload(
                item
            );

            sonIslem.textContent =
                `${item.ad} kapatıldı`;
        }
        else {

            /*
              Taban haritasında aynı anda tek taban.
            */

            if (item.tip === "taban") {

                const liste =
                    mevcutListe();

                liste
                    .filter(
                        x =>
                            x.tip ===
                            "taban"
                    )
                    .forEach(
                        diger => {

                            const digerKey =
                                secimKey(
                                    aktifModulId,
                                    yol,
                                    diger.id
                                );

                            if (
                                digerKey !==
                                key
                            ) {
                                secimler.delete(
                                    digerKey
                                );

                                unload(
                                    diger
                                );
                            }
                        }
                    );
            }

            secimler.add(
                key
            );

            lazyLoad(
                item
            );

            if (
                item.tip === "taban" &&
                haritaYuzeyi
            ) {
                haritaYuzeyi.dataset.taban =
                    item.id;
            }

            sonIslem.textContent =
                `${item.ad} açıldı`;
        }

        toplamSecimSayisi();
        ekranCiz();
    }


    function dugumTiklandi(item) {

        const cocukVar =
            Array.isArray(
                item.cocuklar
            ) &&
            item.cocuklar.length > 0;

        if (
            item.tur === "alt_baslik" ||
            cocukVar
        ) {

            yol.push(
                item.id
            );

            ekranCiz();

            return;
        }

        secimUygula(
            item
        );
    }


    function ekranCiz() {

        const liste =
            mevcutListe();

        drawerBaslik.textContent =
            mevcutBaslik();

        drawerEtiket.textContent =
            yol.length === 0
                ? "ANA KATMANLAR"
                : (
                    yol.length === 1
                        ? "ALT KATMANLAR"
                        : "ALT KATMAN"
                );

        geriButon.classList.toggle(
            "gizli",
            yol.length === 0
        );

        drawer.dataset.seviye =
            String(
                yol.length
            );

        drawerSecimler.innerHTML =
            "";

        const sirali =
            [...liste]
            .sort(
                (a,b) => {

                    const aSec =
                        seciliMi(a)
                            ? 1
                            : 0;

                    const bSec =
                        seciliMi(b)
                            ? 1
                            : 0;

                    if (
                        aSec !== bSec
                    ) {
                        return bSec - aSec;
                    }

                    return (
                        (b.oncelik ?? 0) -
                        (a.oncelik ?? 0)
                    );
                }
            );

        sirali.forEach(
            item => {

                const buton =
                    document.createElement(
                        "button"
                    );

                buton.type =
                    "button";

                const secili =
                    seciliMi(
                        item
                    );

                const cocukVar =
                    item.tur === "alt_baslik" ||
                    (
                        Array.isArray(
                            item.cocuklar
                        ) &&
                        item.cocuklar.length > 0
                    );

                buton.className =
                    [
                        "syk-secim",

                        item.tur ===
                        "alt_baslik"
                            ? "alt-baslik"
                            : "",

                        secili
                            ? "secili"
                            : "secili-degil",

                        secili
                            ? oncelikSinifi(
                                item.oncelik
                            )
                            : ""
                    ]
                    .filter(Boolean)
                    .join(" ");

                buton.innerHTML = `
                    <span class="ikon">
                        ${item.ikon ?? "○"}
                    </span>

                    <span class="metin">
                        ${item.ad}
                    </span>

                    ${
                        cocukVar
                            ? '<span class="cocuk-isareti">›</span>'
                            : ""
                    }
                `;

                buton.addEventListener(
                    "click",
                    () =>
                        dugumTiklandi(
                            item
                        )
                );

                drawerSecimler.appendChild(
                    buton
                );
            }
        );

        hepsiniSecDurumu(
            liste
        );
    }


    function anaIkonlariCiz() {

        altIkonCubugu.innerHTML =
            "";

        const moduller =
            [...registry.ana_moduller]
            .sort(
                (a,b) =>
                    (b.oncelik ?? 0) -
                    (a.oncelik ?? 0)
            );

        moduller.forEach(
            modul => {

                const buton =
                    document.createElement(
                        "button"
                    );

                buton.type =
                    "button";

                buton.className =
                    "syk-ana-ikon";

                buton.dataset.modul =
                    modul.id;

                if (
                    modul.id ===
                    aktifModulId
                ) {
                    buton.classList.add(
                        "aktif"
                    );
                }

                buton.innerHTML = `
                    <span class="ikon">
                        ${modul.ikon ?? "○"}
                    </span>

                    <span class="ad">
                        ${modul.ad}
                    </span>
                `;

                buton.addEventListener(
                    "click",
                    () => {

                        const ayni =
                            aktifModulId ===
                            modul.id;

                        const acik =
                            drawer.classList
                                .contains(
                                    "acik"
                                );

                        aktifModulId =
                            modul.id;

                        yol = [];

                        aktifModulBaslik.textContent =
                            modul.ad;

                        document
                            .querySelectorAll(
                                ".syk-ana-ikon"
                            )
                            .forEach(
                                x =>
                                    x.classList
                                        .toggle(
                                            "aktif",
                                            x.dataset
                                                .modul ===
                                            modul.id
                                        )
                            );

                        if (
                            ayni &&
                            acik
                        ) {
                            drawerKapat();

                            return;
                        }

                        drawerAc();
                        ekranCiz();

                        sonIslem.textContent =
                            `${modul.ad} menüsü açıldı`;
                    }
                );

                altIkonCubugu.appendChild(
                    buton
                );
            }
        );
    }


    geriButon.addEventListener(
        "click",
        () => {

            if (
                yol.length === 0
            ) {
                drawerKapat();

                return;
            }

            yol.pop();

            ekranCiz();
        }
    );


    hepsiniSec.addEventListener(
        "click",
        () => {

            const liste =
                mevcutListe();

            const secilebilir =
                liste.filter(
                    item =>
                        !item.cocuklar ||
                        item.cocuklar.length === 0
                );

            const tumSecili =
                secilebilir.length > 0 &&
                secilebilir.every(
                    item =>
                        seciliMi(
                            item
                        )
                );

            secilebilir.forEach(
                item => {

                    const key =
                        secimKey(
                            aktifModulId,
                            yol,
                            item.id
                        );

                    if (tumSecili) {

                        secimler.delete(
                            key
                        );

                        unload(
                            item
                        );
                    }
                    else {

                        /*
                          Aynı gruptaki taban haritalarında
                          Hepsini Seç yalnız ilk tabanı seçer.
                        */

                        if (
                            item.tip ===
                            "taban"
                        ) {
                            return;
                        }

                        secimler.add(
                            key
                        );

                        lazyLoad(
                            item
                        );
                    }
                }
            );

            if (
                !tumSecili
            ) {

                const taban =
                    secilebilir.find(
                        item =>
                            item.tip ===
                            "taban"
                    );

                if (taban) {

                    const key =
                        secimKey(
                            aktifModulId,
                            yol,
                            taban.id
                        );

                    secimler.add(
                        key
                    );

                    haritaYuzeyi.dataset.taban =
                        taban.id;
                }
            }

            toplamSecimSayisi();
            ekranCiz();

            sonIslem.textContent =
                tumSecili
                    ? "Seçimler kapatıldı"
                    : "Tüm seçimler etkinleştirildi";
        }
    );


    function varsayilanSecimleriKur() {

        registry.ana_moduller
            .forEach(
                modul => {

                    modul.alt_basliklar
                        .forEach(
                            alt => {

                                (alt.cocuklar ?? [])
                                    .forEach(
                                        item => {

                                            if (
                                                !item.varsayilan
                                            ) {
                                                return;
                                            }

                                            secimler.add(
                                                secimKey(
                                                    modul.id,
                                                    [alt.id],
                                                    item.id
                                                )
                                            );
                                        }
                                    );
                            }
                        );
                }
            );

        toplamSecimSayisi();
    }


    function kasifCompactKur() {

        if (!kasifMini) {
            return;
        }

        kasifMini.addEventListener(
            "click",
            () => {

                const panel =
                    document.querySelector(
                        '[data-panel="kasif"]'
                    );

                if (!panel) {
                    return;
                }

                panel.classList.toggle(
                    "gizli"
                );

                sonIslem.textContent =
                    panel.classList
                        .contains(
                            "gizli"
                        )
                        ? "Kaşif küçültüldü"
                        : "Kaşif açıldı";

                panelSayisiGuncelle();
            }
        );
    }


    function panelSayisiGuncelle() {

        const sayi =
            document.querySelectorAll(
                ".calisma-paneli:not(.gizli)"
            ).length;

        acikPanelSayisi.textContent =
            `${sayi} panel açık`;
    }


    function saatGuncelle() {

        saat.textContent =
            new Intl.DateTimeFormat(
                "tr-TR",
                {
                    hour:
                        "2-digit",

                    minute:
                        "2-digit",

                    second:
                        "2-digit"
                }
            ).format(
                new Date()
            );
    }


    async function baslat() {

        const response =
            await fetch(
                registryUrl,
                {
                    cache:
                        "no-store"
                }
            );

        if (!response.ok) {
            throw new Error(
                "Terminal menü kayıt defteri yüklenemedi."
            );
        }

        registry =
            await response.json();

        const varsayilan =
            registry.ana_moduller.find(
                x => x.varsayilan
            )
            ??
            registry.ana_moduller[0];

        aktifModulId =
            varsayilan.id;

        aktifModulBaslik.textContent =
            varsayilan.ad;

        varsayilanSecimleriKur();
        anaIkonlariCiz();
        ekranCiz();
        kasifCompactKur();
        panelSayisiGuncelle();

        /*
          Başlangıçta drawer kapalı.
          Kullanıcı alt Harita ikonuna basınca
          videodaki gibi yukarı açılır.
        */

        drawerKapat();

        console.info(
            "[SyKaşif] Video referanslı bottom drawer hazır."
        );
    }


    saatGuncelle();

    setInterval(
        saatGuncelle,
        1000
    );


    baslat().catch(
        hata => {

            console.error(
                hata
            );

            sonIslem.textContent =
                "Dinamik menü başlatılamadı";
        }
    );


    window.SyKasifTerminal = {
        secimler,
        yukluKaynaklar,
        drawerAc,
        drawerKapat
    };


    }
    catch (hata) {
        console.error(
            "SPRINT_053_008A_RUNTIME_ERROR",
            hata
        );

        const sonIslem =
            document.getElementById("sonIslem");

        if (sonIslem) {
            sonIslem.textContent =
                "Dinamik alt menü başlatılamadı";
        }

        document.documentElement.dataset
            .drawerRuntime = "error";
    }
});


