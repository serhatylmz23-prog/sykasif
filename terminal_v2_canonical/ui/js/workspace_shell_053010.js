(() => {
    "use strict";

    let kontrolTimer = null;
    let odakKartId = null;

    function metinTemizle(value) {
        return String(value || "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function tamMetinElemaniAra(text) {
        const hedef = text.toLocaleLowerCase("tr-TR");

        return [...document.querySelectorAll("body *")]
            .find(el => {
                if (el.children.length > 0) {
                    return false;
                }

                return metinTemizle(el.textContent)
                    .toLocaleLowerCase("tr-TR") === hedef;
            }) || null;
    }

    function kucukBilgiBloguGizle(text) {
        const node = tamMetinElemaniAra(text);

        if (!node) {
            return;
        }

        let parent = node.parentElement;

        for (let i = 0; i < 4 && parent; i++) {
            const rect = parent.getBoundingClientRect();

            if (
                rect.height > 0 &&
                rect.height < 140
            ) {
                parent.classList.add(
                    "syk010-eski-bilgi-gizli"
                );
                return;
            }

            parent = parent.parentElement;
        }

        node.classList.add(
            "syk010-eski-bilgi-gizli"
        );
    }

    // ========================================================
    // ÜST KOMUTA ALANI
    // ========================================================

    function ustKomutaKatmaniKur() {
        if (document.getElementById("syk010Komuta")) {
            return;
        }

        const header =
            document.querySelector("header")
            || document.body;

        const komuta =
            document.createElement("div");

        komuta.id = "syk010Komuta";

        komuta.innerHTML = `
            <div class="syk010-komuta-sol">

                <div class="syk010-marka">
                    <span class="syk010-aktif-sembol">
                        ◉
                    </span>

                    <div>
                        <strong>
                            SyKaşif Terminal V2
                        </strong>

                        <small>
                            Canlı çalışma sistemi
                        </small>
                    </div>
                </div>

                <button
                    type="button"
                    id="syk010Kasif"
                    class="syk010-komuta-buton"
                    title="Kaşif"
                >
                    ◌ Kaşif
                </button>

                <button
                    type="button"
                    id="syk010Ses"
                    class="syk010-komuta-buton syk010-ses"
                    title="Ses"
                >
                    ◍
                </button>

            </div>

            <div class="syk010-komuta-sag">

                <button
                    type="button"
                    id="syk010CanliDurum"
                    class="syk010-canli-durum aktif"
                    title="Canlı sistem"
                    aria-label="Canlı sistem"
                ></button>

            </div>
        `;

        header.appendChild(komuta);

        document
            .getElementById("syk010Kasif")
            ?.addEventListener("click", () => {
                const kasifPanel =
                    document.querySelector(
                        '[data-panel="kasif"]'
                    );

                if (!kasifPanel) {
                    return;
                }

                kasifPanel.classList.toggle("gizli");
            });

        document
            .getElementById("syk010Ses")
            ?.addEventListener("click", event => {
                event.currentTarget.classList.toggle(
                    "aktif"
                );
            });
    }

    // ========================================================
    // GEREKSİZ ÜST BİLGİ BLOKLARINI KALDIR
    // ========================================================

    function eskiBilgiAlanlariniTemizle() {
        [
            "SİSTEM",
            "AKTİF MODÜL",
            "ÇALIŞMA ALANI"
        ].forEach(
            kucukBilgiBloguGizle
        );

        document
            .querySelectorAll(".kasif-mini")
            .forEach(
                el => el.classList.add(
                    "syk010-eski-bilgi-gizli"
                )
            );
    }

    // ========================================================
    // HARİTA SOLDA SABİT + SAĞDA DİNAMİK GRID
    // ========================================================

    function haritaPaneliBul() {
        return document.querySelector(
            '.calisma-paneli[data-panel="harita"]'
        );
    }

    function workspaceOlustur() {
        if (document.getElementById("syk010Workspace")) {
            return;
        }

        const harita = haritaPaneliBul();

        if (!harita) {
            return;
        }

        const mevcutParent =
            harita.parentElement;

        const workspace =
            document.createElement("section");

        workspace.id =
            "syk010Workspace";

        workspace.className =
            "syk010-workspace";

        mevcutParent.insertBefore(
            workspace,
            harita
        );

        const haritaBolumu =
            document.createElement("div");

        haritaBolumu.id =
            "syk010HaritaBolumu";

        haritaBolumu.className =
            "syk010-harita-bolumu";

        const sagBolum =
            document.createElement("div");

        sagBolum.id =
            "syk010SagBolum";

        sagBolum.className =
            "syk010-sag-bolum";

        sagBolum.innerHTML = `
            <div
                id="syk010SideGrid"
                class="syk010-side-grid"
            ></div>
        `;

        workspace.appendChild(
            haritaBolumu
        );

        workspace.appendChild(
            sagBolum
        );

        haritaBolumu.appendChild(
            harita
        );

        // Eski katman paneli artık yer tutmayacak.
        const eskiKatman =
            document.querySelector(
                '.calisma-paneli[data-panel="katman"]'
            );

        if (eskiKatman) {
            eskiKatman.classList.add(
                "syk010-eski-bilgi-gizli"
            );
        }
    }

    // ========================================================
    // SEÇİLİ KATMANLARDAN SAĞ GÖRÜNTÜ KUTULARI
    // ========================================================

    function seciliKatmanAdlari() {
        const secili =
            [...document.querySelectorAll(
                ".syk009-secim.secili"
            )];

        const adlar =
            secili
                .map(el => {
                    const text =
                        el.querySelector("span:nth-child(2)")
                            ?.textContent
                        || el.textContent;

                    return metinTemizle(text)
                        .replace("›", "")
                        .trim();
                })
                .filter(Boolean);

        if (adlar.length > 0) {
            return [...new Set(adlar)];
        }

        return [
            "Rota",
            "İz"
        ];
    }

    function gridKolonSayisi(adet) {
        if (adet <= 1) return 1;
        if (adet <= 4) return 2;
        if (adet <= 6) return 2;
        return 2;
    }

    function sideGridCiz() {
        const grid =
            document.getElementById(
                "syk010SideGrid"
            );

        if (!grid) {
            return;
        }

        const adlar =
            seciliKatmanAdlari();

        grid.style.setProperty(
            "--syk-grid-cols",
            String(
                gridKolonSayisi(adlar.length)
            )
        );

        grid.innerHTML = "";

        adlar.forEach((ad, index) => {
            const id =
                `katman-${index}-${ad}`;

            const kart =
                document.createElement("button");

            kart.type =
                "button";

            kart.className =
                "syk010-kamera-karti";

            kart.dataset.kartId =
                id;

            kart.innerHTML = `
                <span class="syk010-kart-etiket">
                    SEÇİLİ KATMAN
                </span>

                <strong>
                    ${ad}
                </strong>

                <div class="syk010-kart-gorsel">
                    <span>
                        ${index + 1}
                    </span>
                </div>
            `;

            kart.addEventListener(
                "click",
                () => sagOdakDegistir(id)
            );

            grid.appendChild(
                kart
            );
        });

        if (odakKartId) {
            sagOdakUygula();
        }
    }

    function sagOdakDegistir(id) {
        if (odakKartId === id) {
            odakKartId = null;
        }
        else {
            odakKartId = id;
        }

        sagOdakUygula();
    }

    function sagOdakUygula() {
        const grid =
            document.getElementById(
                "syk010SideGrid"
            );

        if (!grid) {
            return;
        }

        const kartlar =
            [...grid.querySelectorAll(
                ".syk010-kamera-karti"
            )];

        if (!odakKartId) {
            grid.classList.remove(
                "tek-odak"
            );

            kartlar.forEach(
                kart => {
                    kart.classList.remove(
                        "odak",
                        "odak-disi"
                    );
                }
            );

            return;
        }

        grid.classList.add(
            "tek-odak"
        );

        kartlar.forEach(
            kart => {
                const aktif =
                    kart.dataset.kartId ===
                    odakKartId;

                kart.classList.toggle(
                    "odak",
                    aktif
                );

                kart.classList.toggle(
                    "odak-disi",
                    !aktif
                );
            }
        );
    }

    // ========================================================
    // PANEL ARAÇLARI:
    // Dokununca görün -> 6 saniye sonra kaybol
    // ========================================================

    function panelKontrolMotoru() {
        document
            .querySelectorAll(".calisma-paneli")
            .forEach(panel => {

                const araclar =
                    panel.querySelector(
                        ".syk009-panel-araclari"
                    );

                if (!araclar) {
                    return;
                }

                const goster = () => {
                    panel.classList.add(
                        "syk010-kontroller-gorunur"
                    );

                    if (kontrolTimer) {
                        clearTimeout(
                            kontrolTimer
                        );
                    }

                    kontrolTimer =
                        setTimeout(
                            () => {
                                panel.classList.remove(
                                    "syk010-kontroller-gorunur"
                                );
                            },
                            6000
                        );
                };

                panel.addEventListener(
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
                    () => goster()
                );
            });
    }

    // ========================================================
    // ALT DRAWER KAPAT TUŞU
    // ========================================================

    function drawerKapatTusuKur() {
        const drawer =
            document.getElementById(
                "syk009Drawer"
            );

        if (!drawer) {
            return;
        }

        if (
            document.getElementById(
                "syk010DrawerKapat"
            )
        ) {
            return;
        }

        const button =
            document.createElement("button");

        button.id =
            "syk010DrawerKapat";

        button.type =
            "button";

        button.className =
            "syk010-drawer-kapat";

        button.innerHTML =
            "⌄";

        button.title =
            "Menüyü kapat";

        button.addEventListener(
            "click",
            () => {
                drawer.classList.remove(
                    "acik"
                );
            }
        );

        drawer.appendChild(
            button
        );
    }

    // ========================================================
    // DRAWER SEÇİMLERİNİ İZLE
    // ========================================================

    function secimObserverKur() {
        const drawer =
            document.getElementById(
                "syk009Drawer"
            );

        if (!drawer) {
            return;
        }

        const observer =
            new MutationObserver(
                () => {
                    setTimeout(
                        sideGridCiz,
                        30
                    );
                }
            );

        observer.observe(
            drawer,
            {
                subtree:
                    true,
                attributes:
                    true,
                childList:
                    true,
                attributeFilter:
                    ["class"]
            }
        );
    }

    // ========================================================
    // ALT DURUM SATIRI DAHA MİNİMAL
    // ========================================================

    function durumCubuguSadelestir() {
        const durum =
            document.getElementById(
                "syk009DurumCubugu"
            );

        if (!durum) {
            return;
        }

        durum.classList.add(
            "syk010-minimal-durum"
        );
    }

    function baslat() {
        ustKomutaKatmaniKur();
        eskiBilgiAlanlariniTemizle();
        workspaceOlustur();
        panelKontrolMotoru();
        drawerKapatTusuKur();
        durumCubuguSadelestir();

        sideGridCiz();
        secimObserverKur();

        document.documentElement.dataset
            .syk010Runtime =
            "ready";

        console.info(
            "SPRINT_053_010_RUNTIME_READY"
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
                    250
                );
            }
        );
    }
    else {
        setTimeout(
            baslat,
            250
        );
    }
})();
