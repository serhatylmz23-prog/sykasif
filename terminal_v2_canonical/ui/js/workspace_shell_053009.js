(() => {
    "use strict";

    const REGISTRY_URL =
        "/ui/data/terminal_menu_registry.json";

    const secimler =
        new Set();

    const yukluKaynaklar =
        new Map();

    let registry = null;
    let aktifModul = "harita";
    let yol = [];


    function trLower(value) {
        return String(value)
            .toLocaleLowerCase("tr-TR")
            .trim();
    }


    function ortakAta(a, b) {

        if (!a || !b) {
            return null;
        }

        const parents =
            new Set();

        let node = a;

        while (node) {
            parents.add(node);
            node = node.parentElement;
        }

        node = b;

        while (node) {

            if (parents.has(node)) {
                return node;
            }

            node = node.parentElement;
        }

        return null;
    }


    function kabukTemizle() {

        /*
         * SOL MENÜ:
         * data-ana-modul içeren gerçek yan kolon bulunur.
         */

        const eskiAnaButon =
            document.querySelector(
                "[data-ana-modul]"
            );

        const solKolon =
            eskiAnaButon
                ?.closest(
                    "aside, nav, .sidebar, .sol-menu, .yan-menu"
                )
            ?? null;

        /*
         * SAĞ DURUM KOLONU:
         */

        const durumReferans =
            document.getElementById(
                "acikPanelSayisi"
            );

        const sagKolon =
            durumReferans
                ?.closest(
                    "aside, .sidebar, .sag-panel, .durum-paneli"
                )
            ?? null;


        if (solKolon) {
            solKolon.classList.add(
                "syk009-kolon-gizli"
            );
        }

        if (
            sagKolon &&
            sagKolon !== solKolon
        ) {
            sagKolon.classList.add(
                "syk009-kolon-gizli"
            );
        }


        /*
         * Grid kolonlarını gerçekten kaldır.
         * Yalnız display:none yapmak boş sütun bırakmasın.
         */

        if (solKolon && sagKolon) {

            const shell =
                ortakAta(
                    solKolon,
                    sagKolon
                );

            if (shell) {

                const stil =
                    getComputedStyle(
                        shell
                    );

                if (
                    stil.display === "grid"
                ) {
                    shell.classList.add(
                        "syk009-shell-tek-kolon"
                    );
                }
            }
        }


        /*
         * Eski ayrı Kaşif düğmesi gereksiz.
         * Kaşif artık ana alt menüde.
         */

        document
            .querySelectorAll(
                ".kasif-mini"
            )
            .forEach(
                node =>
                    node.classList.add(
                        "syk009-eski-kasif-gizli"
                    )
            );


        /*
         * Eski global 2B/3B/AR butonları:
         * panel içine taşınacağı için gizlenir.
         */

        document
            .querySelectorAll(
                "[data-gorunum]"
            )
            .forEach(
                node =>
                    node.classList.add(
                        "syk009-global-gorunum-gizli"
                    )
            );
    }


    function altKabukOlustur() {

        if (
            !document.getElementById(
                "syk009AltKabuk"
            )
        ) {

            const kabuk =
                document.createElement(
                    "div"
                );

            kabuk.id =
                "syk009AltKabuk";

            kabuk.innerHTML = `
                <section
                    id="syk009Drawer"
                    class="syk009-drawer"
                    aria-label="Dinamik seçim menüsü"
                >
                    <div class="syk009-tutamac"></div>

                    <header class="syk009-drawer-header">

                        <button
                            id="syk009Geri"
                            class="syk009-geri"
                            type="button"
                        >
                            ‹
                        </button>

                        <div>
                            <span
                                id="syk009Seviye"
                                class="syk009-etiket"
                            >
                                ANA KATMANLAR
                            </span>

                            <strong
                                id="syk009Baslik"
                            >
                                Harita
                            </strong>
                        </div>

                        <button
                            id="syk009HepsiniSec"
                            class="syk009-hepsini-sec"
                            type="button"
                        >
                            Hepsini Seç
                        </button>

                    </header>

                    <div
                        id="syk009Secimler"
                        class="syk009-secimler"
                    ></div>
                </section>


                <section
                    id="syk009DurumCubugu"
                    class="syk009-durum-cubugu"
                >
                    <span>
                        <i class="syk009-nokta"></i>
                        <b id="syk009Baglanti">
                            Çevrim içi
                        </b>
                    </span>

                    <span id="syk009PanelDurumu">
                        Çalışma alanı hazır
                    </span>

                    <span id="syk009SecimDurumu">
                        0 seçim etkin
                    </span>

                    <span id="syk009SonIslem">
                        Son işlem: —
                    </span>
                </section>
            `;

            document.body.appendChild(
                kabuk
            );
        }


        /*
         * SPRINT_053_008C ile kanıtlanan alt menüyü
         * yeni motorun gerçek ana menüsü olarak kullanıyoruz.
         * Tekrar menü üretmiyoruz.
         */

        const altMenu =
            document.getElementById(
                "syk008cKanıt"
            );

        if (!altMenu) {
            throw new Error(
                "KANITLANMIS_ALT_MENU_BULUNAMADI"
            );
        }

        altMenu.classList.add(
            "syk009-ana-menu"
        );
    }


    function modulIdBul(ad) {

        const value =
            trLower(ad);

        const map = {
            "harita": "harita",
            "görev": "gorev",
            "gorev": "gorev",
            "analiz": "analiz",
            "kanıt": "kanit",
            "kanit": "kanit",
            "rapor": "rapor",
            "cihaz": "cihaz",
            "kaşif": "kasif",
            "kasif": "kasif"
        };

        return map[value] ?? value;
    }


    function modulBul(id) {

        return registry
            ?.ana_moduller
            ?.find(
                item =>
                    item.id === id
            )
            ?? null;
    }


    function mevcutListe() {

        const modul =
            modulBul(
                aktifModul
            );

        if (!modul) {
            return [];
        }

        /*
         * 0. seviye:
         * ana katman grupları
         */

        if (yol.length === 0) {

            return (
                modul.alt_basliklar
                ?? []
            ).map(
                grup => ({
                    ...grup,
                    tur:
                        "grup",
                    ikon:
                        grup.ikon ?? "▦"
                })
            );
        }


        /*
         * İlk grup.
         */

        const grup =
            (
                modul.alt_basliklar
                ?? []
            ).find(
                item =>
                    item.id === yol[0]
            );

        if (!grup) {
            return [];
        }

        let liste =
            grup.cocuklar
            ?? [];


        /*
         * Alt-alt katman desteği.
         */

        for (
            let index = 1;
            index < yol.length;
            index++
        ) {

            const dugum =
                liste.find(
                    item =>
                        item.id ===
                        yol[index]
                );

            if (!dugum) {
                return [];
            }

            liste =
                dugum.cocuklar
                ?? [];
        }

        return liste;
    }


    function mevcutBaslik() {

        const modul =
            modulBul(
                aktifModul
            );

        if (!modul) {
            return aktifModul;
        }

        if (yol.length === 0) {
            return modul.ad;
        }

        let liste =
            modul.alt_basliklar
            ?? [];

        let ad =
            modul.ad;

        for (
            const id of yol
        ) {

            const item =
                liste.find(
                    x =>
                        x.id === id
                );

            if (!item) {
                break;
            }

            ad =
                item.ad;

            liste =
                item.cocuklar
                ?? [];
        }

        return ad;
    }


    function keyOlustur(item) {

        return [
            aktifModul,
            ...yol,
            item.id
        ].join(":");
    }


    function seciliMi(item) {

        return secimler.has(
            keyOlustur(
                item
            )
        );
    }


    function oncelikDegeri(item) {

        return Number(
            item.oncelik
            ?? 0
        );
    }


    function agirKaynakYukle(item) {

        if (!item.agir) {
            return;
        }

        if (
            yukluKaynaklar.has(
                item.id
            )
        ) {
            return;
        }

        /*
         * Burada sonraki gerçek katman motoru
         * tile/video/model kaynağını bağlayacak.
         *
         * Şimdiden bellekte yalnız seçili ağır
         * öğelerin sözleşmesi tutuluyor.
         */

        yukluKaynaklar.set(
            item.id,
            {
                durum:
                    "yüklü",
                zaman:
                    Date.now()
            }
        );
    }


    function agirKaynakBosalt(item) {

        if (!item.agir) {
            return;
        }

        yukluKaynaklar.delete(
            item.id
        );
    }


    function secimDurumunuGuncelle() {

        const durum =
            document.getElementById(
                "syk009SecimDurumu"
            );

        if (durum) {
            durum.textContent =
                `${secimler.size} seçim etkin`;
        }
    }


    function sonIslem(text) {

        const alt =
            document.getElementById(
                "syk009SonIslem"
            );

        if (alt) {
            alt.textContent =
                `Son işlem: ${text}`;
        }


        /*
         * Eski sistemle de senkron.
         */

        const eski =
            document.getElementById(
                "sonIslem"
            );

        if (eski) {
            eski.textContent =
                text;
        }
    }


    function secimUygula(item) {

        const key =
            keyOlustur(
                item
            );

        const secili =
            secimler.has(
                key
            );


        if (secili) {

            secimler.delete(
                key
            );

            agirKaynakBosalt(
                item
            );

            sonIslem(
                `${item.ad} kapatıldı`
            );
        }
        else {

            /*
             * Taban haritası tek seçim.
             */

            if (
                item.tip === "taban"
            ) {

                mevcutListe()
                    .filter(
                        x =>
                            x.tip === "taban"
                    )
                    .forEach(
                        diger => {

                            const digerKey =
                                keyOlustur(
                                    diger
                                );

                            secimler.delete(
                                digerKey
                            );

                            agirKaynakBosalt(
                                diger
                            );
                        }
                    );
            }

            secimler.add(
                key
            );

            agirKaynakYukle(
                item
            );

            sonIslem(
                `${item.ad} etkinleştirildi`
            );
        }


        secimDurumunuGuncelle();
        drawerCiz();
    }


    function drawerCiz() {

        const drawer =
            document.getElementById(
                "syk009Drawer"
            );

        const listeAlan =
            document.getElementById(
                "syk009Secimler"
            );

        const baslik =
            document.getElementById(
                "syk009Baslik"
            );

        const seviye =
            document.getElementById(
                "syk009Seviye"
            );

        const geri =
            document.getElementById(
                "syk009Geri"
            );

        if (
            !drawer ||
            !listeAlan
        ) {
            return;
        }


        baslik.textContent =
            mevcutBaslik();


        seviye.textContent =
            yol.length === 0
                ? "ANA KATMANLAR"
                : yol.length === 1
                    ? "ALT KATMANLAR"
                    : "ALT KATMAN";


        geri.style.visibility =
            yol.length === 0
                ? "hidden"
                : "visible";


        const liste =
            mevcutListe();


        /*
         * SEÇİLİLER ÖNE.
         * Aynı seçim durumunda önem sırası.
         */

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
                        return (
                            bSec -
                            aSec
                        );
                    }

                    return (
                        oncelikDegeri(b) -
                        oncelikDegeri(a)
                    );
                }
            );


        listeAlan.innerHTML =
            "";


        sirali.forEach(
            item => {

                const cocukVar =
                    (
                        item.tur ===
                        "grup"
                    )
                    ||
                    (
                        Array.isArray(
                            item.cocuklar
                        )
                        &&
                        item.cocuklar.length > 0
                    );

                const buton =
                    document.createElement(
                        "button"
                    );

                buton.type =
                    "button";

                buton.className =
                    [
                        "syk009-secim",
                        seciliMi(item)
                            ? "secili"
                            : "secili-degil",
                        cocukVar
                            ? "cocuklu"
                            : ""
                    ]
                    .filter(Boolean)
                    .join(" ");


                buton.innerHTML = `
                    <span class="syk009-secim-ikon">
                        ${item.ikon ?? "○"}
                    </span>

                    <span>
                        ${item.ad}
                    </span>

                    ${
                        cocukVar
                            ? '<i>›</i>'
                            : ""
                    }
                `;


                buton.addEventListener(
                    "click",
                    () => {

                        if (cocukVar) {

                            yol.push(
                                item.id
                            );

                            drawerCiz();

                            sonIslem(
                                `${item.ad} açıldı`
                            );

                            return;
                        }

                        secimUygula(
                            item
                        );
                    }
                );


                listeAlan.appendChild(
                    buton
                );
            });


        /*
         * Hepsini Seç yalnız bu bağlamı etkiler.
         */

        const secilebilir =
            liste.filter(
                item =>
                    !(
                        item.tur ===
                        "grup"
                    )
                    &&
                    !(
                        Array.isArray(
                            item.cocuklar
                        )
                        &&
                        item.cocuklar.length > 0
                    )
            );


        const tumSecili =
            secilebilir.length > 0
            &&
            secilebilir.every(
                item =>
                    seciliMi(item)
            );


        const allButton =
            document.getElementById(
                "syk009HepsiniSec"
            );

        allButton.textContent =
            tumSecili
                ? "Tümünü Kapat"
                : "Hepsini Seç";

        allButton.dataset.tumuSecili =
            tumSecili
                ? "1"
                : "0";
    }


    function drawerAc() {

        const drawer =
            document.getElementById(
                "syk009Drawer"
            );

        drawer?.classList.add(
            "acik"
        );

        drawerCiz();
    }


    function drawerKapat() {

        document
            .getElementById(
                "syk009Drawer"
            )
            ?.classList.remove(
                "acik"
            );

        yol = [];
    }


    function anaMenuBagla() {

        const altMenu =
            document.getElementById(
                "syk008cKanıt"
            );

        const butonlar =
            altMenu.querySelectorAll(
                ".syk008cAna"
            );


        butonlar.forEach(
            buton => {

                buton.addEventListener(
                    "click",
                    () => {

                        const ad =
                            buton
                                .querySelector(
                                    "strong"
                                )
                                ?.textContent
                            ?? "";

                        const id =
                            modulIdBul(
                                ad
                            );


                        const ayni =
                            aktifModul === id;

                        const acik =
                            document
                                .getElementById(
                                    "syk009Drawer"
                                )
                                ?.classList
                                .contains(
                                    "acik"
                                );


                        aktifModul =
                            id;

                        yol = [];


                        butonlar.forEach(
                            item =>
                                item.classList
                                    .remove(
                                        "aktif"
                                    )
                        );

                        buton.classList.add(
                            "aktif"
                        );


                        /*
                         * Aynı butona tekrar bas:
                         * drawer kapanır.
                         */

                        if (
                            ayni &&
                            acik
                        ) {
                            drawerKapat();
                            return;
                        }


                        drawerAc();

                        sonIslem(
                            `${ad} menüsü açıldı`
                        );
                    }
                );
            }
        );
    }


    function geriBagla() {

        document
            .getElementById(
                "syk009Geri"
            )
            ?.addEventListener(
                "click",
                () => {

                    if (
                        yol.length > 0
                    ) {

                        yol.pop();
                        drawerCiz();

                    }
                    else {
                        drawerKapat();
                    }
                }
            );
    }


    function hepsiniSecBagla() {

        document
            .getElementById(
                "syk009HepsiniSec"
            )
            ?.addEventListener(
                "click",
                () => {

                    const liste =
                        mevcutListe();

                    const secilebilir =
                        liste.filter(
                            item =>
                                !(
                                    item.tur ===
                                    "grup"
                                )
                                &&
                                !(
                                    Array.isArray(
                                        item.cocuklar
                                    )
                                    &&
                                    item.cocuklar
                                        .length > 0
                                )
                        );


                    if (
                        secilebilir.length === 0
                    ) {
                        return;
                    }


                    const tumSecili =
                        secilebilir.every(
                            item =>
                                seciliMi(
                                    item
                                )
                        );


                    /*
                     * Taban haritalarında
                     * "Hepsini Seç" mantıksal olarak
                     * tek taban seçer.
                     */

                    const tabanlar =
                        secilebilir.filter(
                            item =>
                                item.tip ===
                                "taban"
                        );


                    if (
                        tabanlar.length > 0
                    ) {

                        tabanlar.forEach(
                            item => {

                                secimler.delete(
                                    keyOlustur(
                                        item
                                    )
                                );

                                agirKaynakBosalt(
                                    item
                                );
                            }
                        );


                        if (!tumSecili) {

                            const ilk =
                                tabanlar[0];

                            secimler.add(
                                keyOlustur(
                                    ilk
                                )
                            );
                        }
                    }


                    secilebilir
                        .filter(
                            item =>
                                item.tip !==
                                "taban"
                        )
                        .forEach(
                            item => {

                                const key =
                                    keyOlustur(
                                        item
                                    );

                                if (tumSecili) {

                                    secimler.delete(
                                        key
                                    );

                                    agirKaynakBosalt(
                                        item
                                    );
                                }
                                else {

                                    secimler.add(
                                        key
                                    );

                                    agirKaynakYukle(
                                        item
                                    );
                                }
                            }
                        );


                    secimDurumunuGuncelle();
                    drawerCiz();

                    sonIslem(
                        tumSecili
                            ? "Seçimler kapatıldı"
                            : "Bağlamdaki seçimler etkinleştirildi"
                    );
                }
            );
    }


    function panelAraclariniKur() {

        const paneller =
            [
                ...document.querySelectorAll(
                    ".calisma-paneli"
                )
            ];


        paneller.forEach(
            panel => {

                if (
                    panel.querySelector(
                        ".syk009-panel-araclari"
                    )
                ) {
                    return;
                }


                const arac =
                    document.createElement(
                        "div"
                    );

                arac.className =
                    "syk009-panel-araclari";


                const panelAdi =
                    panel.dataset.panel
                    ?? "";


                if (
                    panelAdi === "harita"
                ) {

                    ["2B","3B","AR"]
                        .forEach(
                            gorunum => {

                                const button =
                                    document.createElement(
                                        "button"
                                    );

                                button.type =
                                    "button";

                                button.textContent =
                                    gorunum;

                                button.addEventListener(
                                    "click",
                                    () => {

                                        arac
                                            .querySelectorAll(
                                                "[data-gorunum-009]"
                                            )
                                            .forEach(
                                                x =>
                                                    x.classList
                                                        .remove(
                                                            "aktif"
                                                        )
                                            );

                                        button.classList.add(
                                            "aktif"
                                        );

                                        panel.dataset.gorunum =
                                            gorunum;

                                        sonIslem(
                                            `Harita ${gorunum} görünümü`
                                        );
                                    }
                                );

                                button.dataset.gorunum009 =
                                    gorunum;

                                if (
                                    gorunum ===
                                    "2B"
                                ) {
                                    button.classList.add(
                                        "aktif"
                                    );
                                }

                                arac.appendChild(
                                    button
                                );
                            }
                        );
                }


                const full =
                    document.createElement(
                        "button"
                    );

                full.type =
                    "button";

                full.textContent =
                    "Tam ekran";

                full.className =
                    "syk009-fullscreen";


                full.addEventListener(
                    "click",
                    () => {

                        panel.classList.toggle(
                            "syk009-panel-fullscreen"
                        );

                        const acik =
                            panel.classList
                                .contains(
                                    "syk009-panel-fullscreen"
                                );

                        full.textContent =
                            acik
                                ? "Geri dön"
                                : "Tam ekran";

                        sonIslem(
                            acik
                                ? "Panel tam ekran"
                                : "Panel çalışma düzenine döndü"
                        );
                    }
                );


                arac.appendChild(
                    full
                );

                panel.appendChild(
                    arac
                );


                /*
                 * Çift tık ile hızlı tam ekran.
                 */

                panel.addEventListener(
                    "dblclick",
                    event => {

                        if (
                            event.target.closest(
                                "button"
                            )
                        ) {
                            return;
                        }

                        full.click();
                    }
                );
            }
        );
    }


    function durumCubugunuSenkronla() {

        const panelDurumu =
            document.getElementById(
                "syk009PanelDurumu"
            );

        const mevcutPanelSayisi =
            document.querySelectorAll(
                ".calisma-paneli:not(.gizli)"
            ).length;


        panelDurumu.textContent =
            `${mevcutPanelSayisi} çalışma paneli`;
    }


    async function baslat() {

        kabukTemizle();
        altKabukOlustur();


        const response =
            await fetch(
                REGISTRY_URL,
                {
                    cache:
                        "no-store"
                }
            );


        if (!response.ok) {
            throw new Error(
                "MENU_REGISTRY_YUKLENEMEDI"
            );
        }


        registry =
            await response.json();


        anaMenuBagla();
        geriBagla();
        hepsiniSecBagla();
        panelAraclariniKur();
        durumCubugunuSenkronla();


        document.documentElement.dataset
            .syk009Runtime =
            "ready";


        /*
         * Başlangıçta drawer kapalı.
         * Kullanıcı alttaki Harita'ya basınca açılacak.
         */

        drawerKapat();


        console.info(
            "SPRINT_053_009_RUNTIME_READY"
        );
    }


    document.addEventListener(
        "DOMContentLoaded",
        () => {

            baslat().catch(
                hata => {

                    console.error(
                        "SPRINT_053_009_RUNTIME_FAIL",
                        hata
                    );

                    document.documentElement
                        .dataset.syk009Runtime =
                        "error";
                }
            );
        }
    );

})();


/* ==========================================================
   SPRINT_053_009A_RUNTIME
   ========================================================== */

function syk009aTamGenislikKur() {

    const sol =
        document.querySelector(
            ".syk009-kolon-gizli"
        );

    const mainCandidates =
        [
            document.querySelector("main"),
            document.querySelector(".calisma-alani"),
            document.querySelector(".ana-calisma-alani"),
            document.querySelector(".workspace-main"),
            document.querySelector(".terminal-content")
        ]
        .filter(Boolean);

    mainCandidates.forEach(
        alan => {

            alan.classList.add(
                "syk009a-tam-genislik"
            );

            alan.style.width =
                "100%";

            alan.style.maxWidth =
                "none";

            alan.style.marginLeft =
                "0";

            alan.style.marginRight =
                "0";
        }
    );


    /*
     * Sol kolon + ana alan aynı parent içindeyse
     * parent gridini tek kolona düşür.
     */

    if (sol) {

        const parent =
            sol.parentElement;

        if (parent) {

            parent.classList.add(
                "syk009-shell-tek-kolon"
            );

            parent.style.gridTemplateColumns =
                "minmax(0,1fr)";
        }
    }


    /*
     * Harita / Katman panel düzeni.
     */

    const harita =
        document.querySelector(
            '.calisma-paneli[data-panel="harita"]'
        );

    const katman =
        document.querySelector(
            '.calisma-paneli[data-panel="katman"]'
        );

    if (harita) {
        harita.classList.remove(
            "syk009-panel-gizli"
        );
    }


    /*
     * Etkin katman paneli başlangıçta boşsa kaldır.
     */

    if (katman) {

        const metin =
            (katman.textContent || "")
                .replace(/\s+/g," ")
                .trim();

        const secimChip =
            katman.querySelector(
                ".secili-katman, .katman-chip, [data-katman-id]"
            );

        if (
            !secimChip &&
            (
                metin === "" ||
                metin.includes("Etkin Katmanlar")
            )
        ) {
            katman.classList.add(
                "syk009-bos-panel"
            );
        }
    }


    /*
     * Panel parent'ı iki sütun bırakmasın.
     */

    if (harita?.parentElement) {

        const parent =
            harita.parentElement;

        parent.style.display =
            "grid";

        parent.style.gridTemplateColumns =
            katman &&
            !katman.classList.contains(
                "syk009-bos-panel"
            )
                ? "minmax(0,2fr) minmax(260px,.7fr)"
                : "minmax(0,1fr)";

        parent.style.width =
            "100%";

        parent.style.maxWidth =
            "none";
    }


    document.documentElement.dataset
        .syk009aRuntime =
        "ready";

    console.info(
        "SPRINT_053_009A_RUNTIME_READY"
    );
}


/*
 * Eski runtime DOM'u bitirdikten sonra tekrar uygula.
 */

if (
    document.readyState ===
    "loading"
) {
    document.addEventListener(
        "DOMContentLoaded",
        () => {
            requestAnimationFrame(
                syk009aTamGenislikKur
            );
        }
    );
}
else {
    requestAnimationFrame(
        syk009aTamGenislikKur
    );
}

setTimeout(
    syk009aTamGenislikKur,
    250
);

setTimeout(
    syk009aTamGenislikKur,
    750
);

