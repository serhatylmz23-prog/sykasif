(() => {
"use strict";

const SECIM = {
    acikGrup: null,
    secili: new Set(),
    odak: null,
    menuler: [
        {
            id:"harita",
            ad:"Harita",
            alt:[
                {
                    id:"taban",
                    ad:"Taban Haritaları",
                    alt:[
                        {id:"harita",ad:"Harita"},
                        {id:"uydu",ad:"Uydu"},
                        {id:"arazi",ad:"Arazi"},
                        {id:"topografya",ad:"Topografya"}
                    ]
                },
                {
                    id:"ulasim",
                    ad:"Ulaşım",
                    alt:[
                        {id:"yollar",ad:"Yollar"},
                        {id:"demiryollari",ad:"Demiryolları"},
                        {id:"havaalanlari",ad:"Havaalanları"}
                    ]
                },
                {
                    id:"yerlesim",
                    ad:"Yerleşim",
                    alt:[
                        {id:"mahalle",ad:"Mahalle Sınırları"},
                        {id:"binalar",ad:"Binalar"}
                    ]
                },
                {
                    id:"dogal",
                    ad:"Doğal",
                    alt:[
                        {id:"orman",ad:"Ormanlık Alanlar"},
                        {id:"su",ad:"Su Alanları"}
                    ]
                },
                {
                    id:"idari",
                    ad:"İdari",
                    alt:[
                        {id:"ilce",ad:"İlçe Sınırları"},
                        {id:"il",ad:"İl Sınırları"}
                    ]
                }
            ]
        }
    ]
};

const $ = (s,r=document) => r.querySelector(s);
const $$ = (s,r=document) => [...r.querySelectorAll(s)];

function olay(ad,detay={}) {
    window.dispatchEvent(
        new CustomEvent(ad,{detail:detay})
    );
}

function haritaPaneli() {
    return $('.calisma-paneli[data-panel="harita"]')
        || $('.leaflet-container')?.parentElement
        || $('#syk013bGercekHarita')?.parentElement;
}

function altAnaMenuBul() {
    return document.querySelector(
        '.syk010-komuta, #syk010Komuta, .bottom-nav, .alt-menu'
    );
}

function gereksizEskiUIyiTemizle() {
    [
        ".syk-layer-launcher",
        ".syk-layer-drawer",
        ".syk-layer-matrix",
        ".syk-map-floating-controls"
    ].forEach(sel=>{
        $$(sel).forEach(x=>x.remove());
    });
}

function ustHaritaKontrolleriniKucult() {
    const panel = haritaPaneli();
    if(!panel) return;

    let bar = $('#syk053014bHaritaKontrol',panel);

    if(!bar){
        bar=document.createElement("div");
        bar.id="syk053014bHaritaKontrol";
        bar.innerHTML=`
            <button data-m="harita">Harita</button>
            <button data-m="uydu">Uydu</button>
            <button data-m="arazi">Arazi</button>
            <button data-m="topografya">Topografya</button>
            <button id="syk053014bKonum">⌖</button>
            <button id="syk053014bTam">⛶</button>
        `;
        panel.appendChild(bar);
    }

    bar.querySelectorAll("[data-m]").forEach(btn=>{
        btn.onclick=()=>{
            olay("syk:map-base-change",{id:btn.dataset.m});
        };
    });

    $('#syk053014bKonum',bar).onclick=()=>{
        olay("syk:go-location");
    };

    $('#syk053014bTam',bar).onclick=async()=>{
        if(document.fullscreenElement){
            await document.exitFullscreen();
        }else{
            await panel.requestFullscreen?.();
        }
    };

    let timer;

    const goster=()=>{
        bar.classList.add("goster");
        clearTimeout(timer);
        timer=setTimeout(
            ()=>bar.classList.remove("goster"),
            5500
        );
    };

    panel.addEventListener("pointerdown",e=>{
        if(!e.target.closest("#syk053014bHaritaKontrol")){
            goster();
        }
    });

    goster();
}

function katmanMenuKoku() {
    let root=$('#syk053014bKatmanSecici');

    if(root) return root;

    root=document.createElement("section");
    root.id="syk053014bKatmanSecici";

    document.body.appendChild(root);

    return root;
}

function tumAltKatmanlar() {
    return SECIM.menuler
        .flatMap(m=>m.alt)
        .flatMap(g=>g.alt || []);
}

function secimDegistir(id) {
    if(SECIM.secili.has(id)){
        SECIM.secili.delete(id);
    }else{
        SECIM.secili.add(id);
    }

    katmanMenuyuCiz();
    sagMatrisiCiz();

    olay("syk:layer-selection-change",{
        selected:[...SECIM.secili]
    });
}

function hepsiniSec() {
    const tum=tumAltKatmanlar()
        .filter(x=>!["harita","uydu","arazi","topografya"].includes(x.id));

    const hepsiSecili=tum.every(x=>SECIM.secili.has(x.id));

    if(hepsiSecili){
        tum.forEach(x=>SECIM.secili.delete(x.id));
    }else{
        tum.forEach(x=>SECIM.secili.add(x.id));
    }

    katmanMenuyuCiz();
    sagMatrisiCiz();

    olay("syk:layer-selection-change",{
        selected:[...SECIM.secili]
    });
}

function katmanMenuyuCiz() {
    const root=katmanMenuKoku();
    root.innerHTML="";

    const ust=document.createElement("div");
    ust.className="syk053014b-katman-ust";

    const baslik=document.createElement("strong");
    baslik.textContent="Katmanlar";

    const hepsi=document.createElement("button");
    hepsi.textContent="Hepsini Seç";
    hepsi.onclick=hepsiniSec;

    const kapat=document.createElement("button");
    kapat.textContent="×";
    kapat.onclick=()=>root.classList.remove("acik");

    ust.append(baslik,hepsi,kapat);
    root.appendChild(ust);

    const anaSatir=document.createElement("div");
    anaSatir.className="syk053014b-ana-satir";

    SECIM.menuler[0].alt.forEach(grup=>{
        const b=document.createElement("button");
        b.textContent=grup.ad;
        b.className=SECIM.acikGrup===grup.id ? "aktif" : "";
        b.onclick=()=>{
            SECIM.acikGrup =
                SECIM.acikGrup===grup.id
                    ? null
                    : grup.id;
            katmanMenuyuCiz();
        };
        anaSatir.appendChild(b);
    });

    root.appendChild(anaSatir);

    const grup=SECIM.menuler[0].alt
        .find(g=>g.id===SECIM.acikGrup);

    if(grup){
        const alt=document.createElement("div");
        alt.className="syk053014b-alt-satir";

        grup.alt.forEach(item=>{
            const b=document.createElement("button");
            b.textContent=item.ad;

            if(["harita","uydu","arazi","topografya"].includes(item.id)){
                b.onclick=()=>{
                    olay("syk:map-base-change",{id:item.id});
                };
            }else{
                b.className=SECIM.secili.has(item.id) ? "secili" : "";
                b.onclick=()=>secimDegistir(item.id);
            }

            alt.appendChild(b);
        });

        root.appendChild(alt);
    }
}

function katmanAcButonu() {
    const altMenu=altAnaMenuBul();
    if(!altMenu) return;

    if($('#syk053014bKatmanAc',altMenu)) return;

    const buton=document.createElement("button");
    buton.id="syk053014bKatmanAc";
    buton.textContent="Katmanlar";

    buton.onclick=()=>{
        const root=katmanMenuKoku();
        root.classList.add("acik");
        katmanMenuyuCiz();
    };

    altMenu.appendChild(buton);
}

function katmanAdi(id) {
    return tumAltKatmanlar()
        .find(x=>x.id===id)?.ad || id;
}

function sagMatrisKoku() {
    let root=$('#syk053014bSagMatris');

    if(root) return root;

    root=document.createElement("aside");
    root.id="syk053014bSagMatris";

    document.body.appendChild(root);

    return root;
}

function sagMatrisiCiz() {
    const root=sagMatrisKoku();
    root.innerHTML="";

    if(SECIM.odak){
        root.className="odak";

        const kart=document.createElement("button");
        kart.className="syk053014b-odak-kart";
        kart.innerHTML=`
            <small>SEÇİLİ KATMAN</small>
            <strong>${katmanAdi(SECIM.odak)}</strong>
            <span>Tekrar dokun → çoklu görünüme dön</span>
        `;

        kart.onclick=()=>{
            SECIM.odak=null;
            sagMatrisiCiz();
        };

        root.appendChild(kart);
        return;
    }

    root.className="";

    const liste=[...SECIM.secili];

    if(!liste.length){
        root.classList.add("bos");
        return;
    }

    const adet=liste.length;

    let sutun=1;

    if(adet>=3 && adet<=6) sutun=2;
    else if(adet>=7 && adet<=12) sutun=3;
    else if(adet>=13) sutun=4;

    root.style.setProperty("--sutun",sutun);

    liste.forEach(id=>{
        const kart=document.createElement("button");
        kart.className="syk053014b-matris-kart";
        kart.dataset.layer=id;

        kart.innerHTML=`
            <small>SEÇİLİ KATMAN</small>
            <strong>${katmanAdi(id)}</strong>
            <span class="icerik">Canlı içerik bekleniyor</span>
        `;

        kart.onclick=()=>{
            SECIM.odak=id;
            sagMatrisiCiz();
        };

        root.appendChild(kart);
    });
}

function baslat() {
    gereksizEskiUIyiTemizle();
    ustHaritaKontrolleriniKucult();
    katmanAcButonu();
    katmanMenuyuCiz();
    sagMatrisiCiz();

    document.documentElement.dataset.syk053014b="ready";

    console.info(
        "SPRINT_053_014B_DINAMIK_HARITA_MIMARISI_HAZIR"
    );
}

if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",()=>{
        setTimeout(baslat,900);
    });
}else{
    setTimeout(baslat,900);
}

})();
