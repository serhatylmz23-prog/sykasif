(() => {
    "use strict";

    let odakKartId = null;
    let kontrolTimer = null;

    const q = (selector, root=document) =>
        root.querySelector(selector);

    const qa = (selector, root=document) =>
        [...root.querySelectorAll(selector)];

    function temizMetin(value) {
        return String(value || "")
            .replace(/\s+/g, " ")
            .trim();
    }

    // ========================================================
    // 1. ÜST BAR SADELEŞTİR
    // ========================================================

    function ustBarSadelestir() {

        const komuta =
            q("#syk010Komuta");

        if (!komuta) {
            return;
        }

        /*
         * SyKaşif Terminal V2 -> SyKaşif
         */

        const marka =
            q(".syk010-marka strong", komuta);

        if (marka) {
            marka.textContent =
                "SyKaşif";
        }

        /*
         * Alt açıklama da çalışma yüzeyinde
         * gereksiz alan / metin oluşturmasın.
         */

        const altYazi =
            q(".syk010-marka small", komuta);

        if (altYazi) {
            altYazi.remove();
        }

        /*
         * Ayrı Kaşif düğmesi kaldırılıyor.
         * Kaşif ana alt menüden açılacak.
         */

        q("#syk010Kasif")?.remove();

        /*
         * Canlı durum yalnız ışık.
         * Yazı yok.
         */

        const canli =
            q("#syk010CanliDurum");

        if (canli) {
            canli.setAttribute(
                "title",
                "Canlı sistem"
            );

            canli.setAttribute(
                "aria-label",
                "Canlı sistem"
            );
        }
    }

    // ========================================================
    // 2. HARİTA KART DEĞİL, ÇALIŞMA YÜZEYİ
    // ========================================================

    function haritaYuzeyiTemizle() {

        const harita =
            q(
                '.calisma-paneli[data-panel="harita"]'
            );

        if (!harita) {
            return;
        }

        harita.classList.add(
            "syk011-ana-yuzey"
        );

        /*
         * Eski panel başlığı:
         * ÇALIŞMA ALANI / Canlı Harita / X
         * çalışma yüzeyinden kaldırılır.
         */

        qa(
            ":scope > header, :scope > .panel-header, :scope > .calisma-panel-baslik",
            harita
        ).forEach(
            node =>
                node.classList.add(
                    "syk011-panel-baslik-gizli"
                )
        );

        /*
         * Bilinen kapat X butonu da ana harita üzerinde gereksiz.
         */

        qa(
            ":scope > button, :scope > .panel-kapat",
            harita
        ).forEach(
            button => {

                const txt =
                    temizMetin(
                        button.textContent
                    );

                if (
                    txt === "×" ||
                    txt === "x" ||
                    txt === "X"
                ) {
                    button.classList.add(
                        "syk011-panel-baslik-gizli"
                    );
                }
            }
        );
    }

    // ========================================================
    // 3. GERÇEKTEN SEÇİLİ KATMANLARI BUL
    //
    // FALLBACK ROTA / İZ YOK.
    // SEÇİM YOKSA SAĞ ALAN DA YOK.
    // ========================================================

    function seciliKatmanlariBul() {

        const sonuc = [];
        const gorulen = new Set();

        /*
         * Yeni drawer seçimleri.
         */

        qa(".syk009-secim.secili")
            .forEach(
                node => {

                    const metinNode =
                        node.querySelector(
                            "span:nth-of-type(2)"
                        );

                    const ad =
                        temizMetin(
                            metinNode?.textContent
                            || node.textContent
                        )
                        .replace("›", "")
                        .trim();

                    if (
                        !ad ||
                        gorulen.has(ad)
                    ) {
                        return;
                    }

                    gorulen.add(ad);

                    sonuc.push({
                        id:
                            node.dataset.katmanId
                            || ad
                                .toLocaleLowerCase(
                                    "tr-TR"
                                )
                                .replace(
                                    /[^a-z0-9çğıöşü]+/gi,
                                    "-"
                                ),

                        ad,

                        oncelik:
                            Number(
                                node.dataset.oncelik
                                || 0
                            )
                    });
                }
            );


        /*
         * İleride gerçek analiz motorunun doğrudan
         * oluşturacağı katman/görüntü hücreleri de
         * aynı matrise otomatik girebilir.
         */

        qa("[data-syk-gorsel-katman]")
            .forEach(
                node => {

                    const ad =
                        temizMetin(
                            node.dataset.sykKatmanAdi
                            || node.getAttribute(
                                "aria-label"
                            )
                            || node.textContent
                        );

                    if (
                        !ad ||
                        gorulen.has(ad)
                    ) {
                        return;
                    }

                    gorulen.add(ad);

                    sonuc.push({
                        id:
                            node.dataset.sykGorselKatman,

                        ad,

                        oncelik:
                            Number(
                                node.dataset.oncelik
                                || 0
                            )
                    });
                }
            );


        return sonuc.sort(
            (a,b) =>
                b.oncelik -
                a.oncelik
        );
    }

    // ========================================================
    // 4. SAĞ TARAF = SINIRSIZ DİNAMİK MATRİS
    // ========================================================

    function sagMatrisCiz() {

        const workspace =
            q("#syk010Workspace");

        const sag =
            q("#syk010SagBolum");

        const grid =
            q("#syk010SideGrid");

        if (
            !workspace ||
            !sag ||
            !grid
        ) {
            return;
        }

        const katmanlar =
            seciliKatmanlariBul();


        /*
         * Seçim yok:
         * sağ alan tamamen kapanır,
         * harita bütün çalışma yüzeyini kullanır.
         */

        if (
            katmanlar.length === 0
        ) {

            odakKartId =
                null;

            grid.innerHTML =
                "";

            sag.classList.add(
                "syk011-sag-gizli"
            );

            workspace.classList.remove(
                "syk011-sag-aktif"
            );

            workspace.classList.add(
                "syk011-sadece-harita"
            );

            return;
        }


        sag.classList.remove(
            "syk011-sag-gizli"
        );

        workspace.classList.remove(
            "syk011-sadece-harita"
        );

        workspace.classList.add(
            "syk011-sag-aktif"
        );


        /*
         * Aktif odak kaldırılmış bir katmansa
         * otomatik olarak matrise dön.
         */

        if (
            odakKartId &&
            !katmanlar.some(
                item =>
                    item.id ===
                    odakKartId
            )
        ) {
            odakKartId =
                null;
        }


        grid.innerHTML =
            "";

        grid.dataset.adet =
            String(
                katmanlar.length
            );


        katmanlar.forEach(
            (katman,index) => {

                const kart =
                    document.createElement(
                        "button"
                    );

                kart.type =
                    "button";

                kart.className =
                    "syk011-matris-karti";

                kart.dataset.kartId =
                    katman.id;

                kart.dataset.sira =
                    String(
                        index + 1
                    );

                /*
                 * Şimdilik gerçek içerik motoru bağlanana
                 * kadar yalnız çalışma yüzeyi oluşturuyoruz.
                 * Sonraki katman motorları canvas/video/map/
                 * thermal/chart vb. içeriği bu body'ye basacak.
                 */

                kart.innerHTML = `
                    <div class="syk011-kart-icerik">

                        <span class="syk011-kart-numara">
                            ${index + 1}
                        </span>

                        <div class="syk011-kart-alt">
                            <strong>
                                ${katman.ad}
                            </strong>
                        </div>

                    </div>
                `;

                kart.addEventListener(
                    "click",
                    () => {

                        if (
                            odakKartId ===
                            katman.id
                        ) {
                            odakKartId =
                                null;
                        }
                        else {
                            odakKartId =
                                katman.id;
                        }

                        odakDurumunuUygula();
                    }
                );

                grid.appendChild(
                    kart
                );
            }
        );

        odakDurumunuUygula();
    }

    function odakDurumunuUygula() {

        const grid =
            q("#syk010SideGrid");

        if (!grid) {
            return;
        }

        const kartlar =
            qa(
                ".syk011-matris-karti",
                grid
            );

        if (!odakKartId) {

            grid.classList.remove(
                "syk011-tek-odak"
            );

            kartlar.forEach(
                kart =>
                    kart.classList.remove(
                        "syk011-odak",
                        "syk011-odak-disi"
                    )
            );

            return;
        }


        grid.classList.add(
            "syk011-tek-odak"
        );

        kartlar.forEach(
            kart => {

                const aktif =
                    kart.dataset.kartId ===
                    odakKartId;

                kart.classList.toggle(
                    "syk011-odak",
                    aktif
                );

                kart.classList.toggle(
                    "syk011-odak-disi",
                    !aktif
                );
            }
        );
    }

    // ========================================================
    // 5. 2B / 3B / AR / TAM EKRAN
    //
    // YÜZEYE DOKUN -> GÖRÜN
    // 6 SN -> KAYBOL
    // ========================================================

    function haritaKontrolMotoruKur() {

        const harita =
            q(
                '.calisma-paneli[data-panel="harita"]'
            );

        if (!harita) {
            return;
        }

        const araclar =
            q(
                ".syk009-panel-araclari",
                harita
            );

        if (!araclar) {
            return;
        }

        const goster = () => {

            harita.classList.add(
                "syk011-kontroller-acik"
            );

            if (
                kontrolTimer
            ) {
                clearTimeout(
                    kontrolTimer
                );
            }

            kontrolTimer =
                setTimeout(
                    () => {
                        harita.classList.remove(
                            "syk011-kontroller-acik"
                        );
                    },
                    6000
                );
        };


        harita.addEventListener(
            "pointerdown",
            event => {

                if (
                    event.target.closest(
                        ".syk009-panel-araclari"
                    )
                ) {
                    return;
                }

                goster();
            }
        );


        araclar.addEventListener(
            "pointerdown",
            goster
        );
    }

    // ========================================================
    // 6. DRAWER DEĞİŞİNCE MATRİSİ OTOMATİK GÜNCELLE
    // ========================================================

    function secimIzleyiciKur() {

        const drawer =
            q("#syk009Drawer");

        if (!drawer) {
            return;
        }

        let timer = null;

        const observer =
            new MutationObserver(
                () => {

                    if (timer) {
                        clearTimeout(
                            timer
                        );
                    }

                    timer =
                        setTimeout(
                            sagMatrisCiz,
                            40
                        );
                }
            );

        observer.observe(
            drawer,
            {
                subtree:
                    true,

                childList:
                    true,

                attributes:
                    true,

                attributeFilter:
                    ["class"]
            }
        );
    }

    // ========================================================
    // 7. ESKİ 053010 SABİT KARTLARI İPTAL
    // ========================================================

    function eskiSagKartlariTemizle() {

        q("#syk010SideGrid")
            ?.replaceChildren();
    }

    // ========================================================
    // BAŞLAT
    // ========================================================

    function baslat() {

        ustBarSadelestir();

        haritaYuzeyiTemizle();

        eskiSagKartlariTemizle();

        haritaKontrolMotoruKur();

        secimIzleyiciKur();

        sagMatrisCiz();


        document.documentElement
            .dataset.syk011Runtime =
            "ready";


        console.info(
            "SPRINT_053_011_RUNTIME_READY"
        );
    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            () => {
                setTimeout(
                    baslat,
                    500
                );
            }
        );
    }
    else {

        setTimeout(
            baslat,
            500
        );
    }

})();
