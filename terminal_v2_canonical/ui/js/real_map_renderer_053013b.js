(() => {
    "use strict";

    const DURUM_URL = "/api/v2/map/state";
    const KATMAN_URL = "/api/v2/map/overlays";

    const DUNYA_SINIRI = [
        [-85.0511, -180],
        [85.0511, 180]
    ];

    const EN_UZAK = 3;

    const TABANLAR = {
        harita: {
            url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            ad: "Harita"
        },
        uydu: {
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            ad: "Uydu"
        },
        arazi: {
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
            ad: "Arazi"
        },
        topografya: {
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            ad: "Topografya"
        }
    };

    let harita = null;
    let tabanKatmani = null;
    let konumNoktasi = null;
    let mevcutKonum = null;
    const ciziliKatmanlar = new Map();

    const bul = (secici, kok=document) => kok.querySelector(secici);

    async function veriAl(url) {
        const cevap = await fetch(url, {cache:"no-store"});
        if (!cevap.ok) throw new Error(`${url}:${cevap.status}`);
        return cevap.json();
    }

    function leafletYukle() {
        if (window.L) return Promise.resolve(window.L);

        const css = document.createElement("link");
        css.rel = "stylesheet";
        css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(css);

        return new Promise((tamam,hata) => {
            const js = document.createElement("script");
            js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
            js.onload = () => tamam(window.L);
            js.onerror = hata;
            document.head.appendChild(js);
        });
    }

    function panelBul() {
        return bul('.calisma-paneli[data-panel="harita"]');
    }

    function yuzeyOlustur() {
        const panel = panelBul();
        if (!panel) throw new Error("HARITA_PANELI_YOK");

        panel.querySelectorAll(
            ".harita-yuzeyi,.map-placeholder,.harita-placeholder,.rota-placeholder,.route-preview"
        ).forEach(n => n.style.display="none");

        let alan = bul("#syk013bGercekHarita", panel);

        if (!alan) {
            alan = document.createElement("div");
            alan.id = "syk013bGercekHarita";
            alan.style.cssText =
                "position:absolute;inset:0;width:100%;height:100%;z-index:40;";
            panel.appendChild(alan);
        }

        return alan;
    }

    function haritaOlustur(L, durum) {
        const alan = yuzeyOlustur();

        const enlem = Number(durum?.viewport?.latitude ?? 39);
        const boylam = Number(durum?.viewport?.longitude ?? 35);
        const yakinlik = Math.max(EN_UZAK, Number(durum?.viewport?.zoom ?? 6));

        harita = L.map(alan,{
            center:[enlem,boylam],
            zoom:yakinlik,
            minZoom:EN_UZAK,
            maxBounds:DUNYA_SINIRI,
            maxBoundsViscosity:1,
            worldCopyJump:false,
            zoomControl:true
        });

        harita.setMaxBounds(DUNYA_SINIRI);
    }

    function tabanDegistir(L, ad) {
        if (tabanKatmani) {
            harita.removeLayer(tabanKatmani);
        }

        const secilen = TABANLAR[ad] || TABANLAR.harita;

        tabanKatmani = L.tileLayer(secilen.url,{
            noWrap:true,
            bounds:DUNYA_SINIRI,
            minZoom:EN_UZAK,
            maxZoom:19
        }).addTo(harita);
    }

    function konumaGit() {
        if (!navigator.geolocation) return;

        navigator.geolocation.getCurrentPosition(
            konum => {
                mevcutKonum = {
                    enlem:konum.coords.latitude,
                    boylam:konum.coords.longitude
                };

                const nokta = [
                    mevcutKonum.enlem,
                    mevcutKonum.boylam
                ];

                if (!konumNoktasi) {
                    konumNoktasi = L.circleMarker(nokta,{
                        radius:8,
                        weight:3,
                        fillOpacity:.85
                    }).addTo(harita);

                    konumNoktasi.bindTooltip("Mevcut konum");

                    konumNoktasi.on("click",() => {
                        harita.flyTo(nokta,17,{
                            animate:true,
                            duration:.6
                        });
                    });
                } else {
                    konumNoktasi.setLatLng(nokta);
                }

                harita.flyTo(nokta,16,{
                    animate:true,
                    duration:.6
                });
            },
            () => {},
            {
                enableHighAccuracy:true,
                timeout:7000,
                maximumAge:30000
            }
        );
    }

    async function tamEkran() {
        const panel = panelBul();
        if (!panel) return;

        if (document.fullscreenElement) {
            await document.exitFullscreen();
        } else {
            await panel.requestFullscreen();
        }

        setTimeout(() => harita?.invalidateSize(false),150);
    }

    function aracCubugu(L) {
        const panel = panelBul();

        const cubuk = document.createElement("div");
        cubuk.id = "syk013bHaritaAraclari";

        cubuk.style.cssText =
            "position:absolute;z-index:900;top:12px;left:50%;transform:translateX(-50%);" +
            "display:flex;gap:6px;padding:6px;background:rgba(2,16,20,.85);" +
            "border:1px solid rgba(80,190,200,.3);border-radius:10px;";

        cubuk.innerHTML = `
            <button data-taban="harita">Harita</button>
            <button data-taban="uydu">Uydu</button>
            <button data-taban="arazi">Arazi</button>
            <button data-taban="topografya">Topografya</button>
            <button id="sykKonumGit">Konumuma Git</button>
            <button id="sykTamEkran">Tam Ekran</button>
        `;

        cubuk.querySelectorAll("[data-taban]").forEach(btn => {
            btn.onclick = () => tabanDegistir(L,btn.dataset.taban);
        });

        bul("#sykKonumGit",cubuk).onclick = konumaGit;
        bul("#sykTamEkran",cubuk).onclick = tamEkran;

        panel.appendChild(cubuk);
    }

    async function katmanlariYukle(L) {
        const sonuc = await veriAl(KATMAN_URL);
        const gelen = new Set();

        for (const katman of sonuc.layers || []) {
            gelen.add(katman.id);

            const eski = ciziliKatmanlar.get(katman.id);
            if (eski) harita.removeLayer(eski);

            if (!katman.geojson?.features?.length) {
                ciziliKatmanlar.delete(katman.id);
                continue;
            }

            const yeni = L.geoJSON(katman.geojson,{
                pointToLayer:(_,latlng) =>
                    L.circleMarker(latlng,{
                        radius:7,
                        weight:2,
                        fillOpacity:.7
                    }),
                onEachFeature:(feature,obj) => {
                    const ad =
                        feature?.properties?.ad ||
                        feature?.properties?.title ||
                        katman.title;

                    if (ad) obj.bindTooltip(String(ad));
                }
            }).addTo(harita);

            ciziliKatmanlar.set(katman.id,yeni);
        }

        for (const [id,nesne] of ciziliKatmanlar.entries()) {
            if (!gelen.has(id)) {
                harita.removeLayer(nesne);
                ciziliKatmanlar.delete(id);
            }
        }
    }

    async function baslat() {
        const L = await leafletYukle();
        const durum = await veriAl(DURUM_URL);

        haritaOlustur(L,durum);
        tabanDegistir(L,durum?.viewport?.mode || "harita");
        aracCubugu(L);

        setTimeout(() => harita.invalidateSize(false),300);

        try {
            await katmanlariYukle(L);
        } catch {}

        setInterval(() => {
            katmanlariYukle(L).catch(()=>{});
        },1500);

        document.documentElement.dataset.syk013bRuntime = "ready";

        console.info("SPRINT_053_013B_HARITA_HAZIR");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded",() => {
            setTimeout(() => baslat().catch(console.error),800);
        });
    } else {
        setTimeout(() => baslat().catch(console.error),800);
    }
})();
