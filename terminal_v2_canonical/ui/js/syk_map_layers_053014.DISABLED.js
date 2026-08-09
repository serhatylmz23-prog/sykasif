(() => {
"use strict";

const SYK = window.SYK_MAP_LAYER_SYSTEM = {
    activeBase: "harita",
    selected: new Set(),
    expanded: new Set(),
    focusLayer: null,

    groups: [
        {
            id:"ulasim",
            title:"Ulaşım",
            icon:"◉",
            children:[
                {id:"yollar",title:"Yollar"},
                {id:"demiryollari",title:"Demiryolları"},
                {id:"havaalanlari",title:"Havaalanları"}
            ]
        },
        {
            id:"yerlesim",
            title:"Yerleşim",
            icon:"▦",
            children:[
                {id:"mahalle",title:"Mahalle Sınırları"},
                {id:"binalar",title:"Binalar"}
            ]
        },
        {
            id:"dogal",
            title:"Doğal",
            icon:"◇",
            children:[
                {id:"orman",title:"Ormanlık Alanlar"},
                {id:"su",title:"Su Alanları"}
            ]
        },
        {
            id:"idari",
            title:"İdari",
            icon:"⬡",
            children:[
                {id:"ilce",title:"İlçe Sınırları"},
                {id:"il",title:"İl Sınırları"}
            ]
        }
    ]
};

function findMap() {
    return document.querySelector(
        "#map, .map, .map-container, .leaflet-container, [data-map], .syk-map"
    );
}

function create(tag, cls, text) {
    const el=document.createElement(tag);
    if(cls) el.className=cls;
    if(text!==undefined) el.textContent=text;
    return el;
}

function dispatch(name,detail={}) {
    window.dispatchEvent(new CustomEvent(name,{detail}));
}

function setBase(id) {
    SYK.activeBase=id;

    document.querySelectorAll(".syk-base-button").forEach(b=>{
        b.classList.toggle("active",b.dataset.base===id);
    });

    dispatch("syk:map-base-change",{id});
}

function toggleLayer(id) {
    if(SYK.selected.has(id)) SYK.selected.delete(id);
    else SYK.selected.add(id);

    render();
    dispatch("syk:layer-selection-change",{
        selected:[...SYK.selected]
    });
}

function toggleGroup(group) {
    const ids=group.children.map(x=>x.id);
    const all=ids.every(id=>SYK.selected.has(id));

    ids.forEach(id=>{
        if(all) SYK.selected.delete(id);
        else SYK.selected.add(id);
    });

    render();
    dispatch("syk:layer-selection-change",{
        selected:[...SYK.selected]
    });
}

function toggleAll() {
    const ids=SYK.groups.flatMap(g=>g.children.map(x=>x.id));
    const all=ids.every(id=>SYK.selected.has(id));

    if(all) SYK.selected.clear();
    else ids.forEach(id=>SYK.selected.add(id));

    render();
    dispatch("syk:layer-selection-change",{
        selected:[...SYK.selected]
    });
}

function focusLayer(id) {
    SYK.focusLayer = SYK.focusLayer===id ? null : id;
    renderMatrix();
    dispatch("syk:matrix-focus",{id:SYK.focusLayer});
}

function createTopControls(map) {
    let bar=document.querySelector(".syk-map-floating-controls");

    if(!bar){
        bar=create("div","syk-map-floating-controls");
        map.appendChild(bar);
    }

    bar.innerHTML="";

    [
        ["harita","Harita"],
        ["uydu","Uydu"],
        ["arazi","Arazi"],
        ["topografya","Topografya"]
    ].forEach(([id,title])=>{
        const b=create("button","syk-base-button",title);
        b.dataset.base=id;
        b.onclick=()=>setBase(id);
        bar.appendChild(b);
    });

    const loc=create("button","syk-map-action","⌖ Konumuma Git");
    loc.onclick=()=>{
        dispatch("syk:go-location");

        if(navigator.geolocation){
            navigator.geolocation.getCurrentPosition(pos=>{
                dispatch("syk:gps-location",{
                    lat:pos.coords.latitude,
                    lon:pos.coords.longitude,
                    accuracy:pos.coords.accuracy
                });
            });
        }
    };

    const full=create("button","syk-map-action","⛶ Tam Ekran");
    full.onclick=()=>{
        if(!document.fullscreenElement){
            map.requestFullscreen?.();
        }else{
            document.exitFullscreen?.();
        }
    };

    bar.append(loc,full);
    setBase(SYK.activeBase);
}

function createLayerDrawer() {
    let drawer=document.querySelector(".syk-layer-drawer");

    if(!drawer){
        drawer=create("section","syk-layer-drawer");
        document.body.appendChild(drawer);
    }

    return drawer;
}

function renderDrawer() {
    const drawer=createLayerDrawer();
    drawer.innerHTML="";

    const head=create("div","syk-layer-head");

    const title=create("strong","", "Katmanlar");

    const all=create("button","syk-all-button","Hepsini Seç");
    all.onclick=toggleAll;

    const close=create("button","syk-drawer-close","×");
    close.onclick=()=>{
        drawer.classList.remove("open");
    };

    head.append(title,all,close);
    drawer.appendChild(head);

    SYK.groups.forEach(group=>{
        const block=create("div","syk-layer-group");

        const groupHead=create("button","syk-layer-group-head");

        const ids=group.children.map(x=>x.id);
        const count=ids.filter(id=>SYK.selected.has(id)).length;

        groupHead.innerHTML=
            `<span>${group.icon} ${group.title}</span>`+
            `<span>${count}/${ids.length}　⌃</span>`;

        groupHead.onclick=()=>{
            if(SYK.expanded.has(group.id))
                SYK.expanded.delete(group.id);
            else
                SYK.expanded.add(group.id);

            renderDrawer();
        };

        groupHead.ondblclick=(e)=>{
            e.preventDefault();
            toggleGroup(group);
        };

        block.appendChild(groupHead);

        if(SYK.expanded.has(group.id)){
            const children=create("div","syk-layer-children");

            group.children.forEach(layer=>{
                const b=create(
                    "button",
                    "syk-layer-button" +
                    (SYK.selected.has(layer.id) ? " active":""),
                    layer.title
                );

                b.onclick=()=>toggleLayer(layer.id);
                children.appendChild(b);
            });

            block.appendChild(children);
        }

        drawer.appendChild(block);
    });
}

function renderMatrix() {
    let matrix=document.querySelector(".syk-layer-matrix");

    if(!matrix){
        matrix=create("aside","syk-layer-matrix");
        document.body.appendChild(matrix);
    }

    matrix.innerHTML="";

    const selected=[...SYK.selected];

    if(SYK.focusLayer){
        const layer=
            SYK.groups.flatMap(g=>g.children)
            .find(x=>x.id===SYK.focusLayer);

        const focused=create("button","syk-matrix-focus");

        focused.innerHTML=
            `<small>SEÇİLİ KATMAN</small>`+
            `<strong>${layer?.title || SYK.focusLayer}</strong>`+
            `<span>Tekrar dokun → matrise dön</span>`;

        focused.onclick=()=>focusLayer(SYK.focusLayer);

        matrix.appendChild(focused);
        matrix.classList.add("focused");
        return;
    }

    matrix.classList.remove("focused");

    if(!selected.length){
        const empty=create(
            "div",
            "syk-matrix-empty",
            "Seçilen katmanlar burada dinamik olarak görüntülenecek."
        );
        matrix.appendChild(empty);
        return;
    }

    const count=selected.length;

    matrix.style.setProperty(
        "--matrix-cols",
        count<=2 ? 1 :
        count<=6 ? 2 :
        count<=12 ? 3 : 4
    );

    selected.forEach(id=>{
        const layer=
            SYK.groups.flatMap(g=>g.children)
            .find(x=>x.id===id);

        const cell=create("button","syk-matrix-cell");

        cell.innerHTML=
            `<small>SEÇİLİ KATMAN</small>`+
            `<strong>${layer?.title || id}</strong>`+
            `<span class="syk-layer-runtime">Canlı veri alanı</span>`;

        cell.onclick=()=>focusLayer(id);

        matrix.appendChild(cell);
    });
}

function renderBottomLauncher() {
    let launcher=document.querySelector(".syk-layer-launcher");

    if(!launcher){
        launcher=create("button","syk-layer-launcher","Katmanlar");
        document.body.appendChild(launcher);
    }

    launcher.onclick=()=>{
        document.querySelector(".syk-layer-drawer")?.classList.add("open");
    };
}

function render() {
    renderDrawer();
    renderMatrix();

    const launcher=document.querySelector(".syk-layer-launcher");
    if(launcher)
        launcher.textContent=`Katmanlar · ${SYK.selected.size}`;
}

function boot() {
    const map=findMap();

    if(!map){
        setTimeout(boot,500);
        return;
    }

    map.classList.add("syk-map-runtime");

    createTopControls(map);
    renderBottomLauncher();
    render();

    window.addEventListener("syk:external-layer-data",e=>{
        const {id,html}=e.detail || {};
        if(!id) return;

        const cell=document.querySelector(
            `.syk-matrix-cell[data-layer="${id}"]`
        );

        if(cell && html) cell.innerHTML=html;
    });

    console.log("SYK HARİTA KATMAN MOTORU AKTİF");
}

if(document.readyState==="loading")
    document.addEventListener("DOMContentLoaded",boot);
else
    boot();

})();
