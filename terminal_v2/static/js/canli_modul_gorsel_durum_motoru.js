"use strict";

const SYK_MODULE_VISUAL_EVENT =
    "sykasif:aktif-modul-guncellendi";

const SYK_MODULE_SELECTOR =
    "[data-modul-kodu]";

const DURUMLAR = Object.freeze({
    AKTIF: "aktif",
    PASIF: "pasif",
    CALISIYOR: "calisiyor",
    BEKLIYOR: "bekliyor",
    DURDU: "durdu",
    CEVRIMDISI: "cevrimdisi",
});

function normalize(value) {
    return String(value ?? "")
        .trim()
        .toLocaleLowerCase("tr-TR")
        .replaceAll("ç", "c")
        .replaceAll("ğ", "g")
        .replaceAll("ı", "i")
        .replaceAll("ö", "o")
        .replaceAll("ş", "s")
        .replaceAll("ü", "u");
}

function runtimeDurumunuNormalizeEt(value) {
    const normalized = normalize(value);

    const aliases = Object.freeze({
        aktif: DURUMLAR.AKTIF,
        active: DURUMLAR.AKTIF,
        pasif: DURUMLAR.PASIF,
        passive: DURUMLAR.PASIF,
        calisiyor: DURUMLAR.CALISIYOR,
        working: DURUMLAR.CALISIYOR,
        running: DURUMLAR.CALISIYOR,
        bekliyor: DURUMLAR.BEKLIYOR,
        waiting: DURUMLAR.BEKLIYOR,
        idle: DURUMLAR.BEKLIYOR,
        durdu: DURUMLAR.DURDU,
        stopped: DURUMLAR.DURDU,
        cevrimdisi: DURUMLAR.CEVRIMDISI,
        offline: DURUMLAR.CEVRIMDISI,
    });

    return aliases[normalized] ?? DURUMLAR.BEKLIYOR;
}

function aktifModulKodunuEventtenAl(event) {
    return String(
        event?.detail?.aktif_modul ?? ""
    ).trim();
}

function modulKartlariniBul(root = document) {
    return Array.from(
        root.querySelectorAll(
            SYK_MODULE_SELECTOR
        )
    );
}

function kartRuntimeDurumunuOku(kart) {
    return runtimeDurumunuNormalizeEt(
        kart
            ?.querySelector(
                "[data-runtime-durum]"
            )
            ?.textContent
    );
}

function kartDurumunuUygula(
    kart,
    aktifModul
) {
    const kartKodu =
        String(
            kart?.dataset?.modulKodu ?? ""
        ).trim();

    const secili =
        Boolean(kartKodu) &&
        kartKodu === aktifModul;

    const runtimeDurum =
        kartRuntimeDurumunuOku(kart);

    kart.dataset.sykModulSecim =
        secili
            ? DURUMLAR.AKTIF
            : DURUMLAR.PASIF;

    kart.dataset.sykModulDurum =
        runtimeDurum;

    kart.dataset.sykModulHareket =
        runtimeDurum === DURUMLAR.CALISIYOR
            ? DURUMLAR.AKTIF
            : DURUMLAR.PASIF;

    kart.setAttribute(
        "aria-current",
        secili ? "true" : "false"
    );

    return Object.freeze({
        modul_kodu: kartKodu,
        secili,
        runtime_durum: runtimeDurum,
    });
}

function aktifModulGorselDurumunuUygula(
    aktifModul,
    root = document
) {
    const normalized =
        String(aktifModul ?? "").trim();

    const kartlar =
        modulKartlariniBul(root);

    const sonuclar =
        kartlar.map(
            (kart) =>
                kartDurumunuUygula(
                    kart,
                    normalized
                )
        );

    return Object.freeze({
        aktif_modul: normalized,
        kart_sayisi: kartlar.length,
        kartlar: Object.freeze(sonuclar),
    });
}

function aktifModulEventiniIsle(event) {
    return aktifModulGorselDurumunuUygula(
        aktifModulKodunuEventtenAl(event)
    );
}

function bindCanliModulGorselDurumMotoru(
    target = window
) {
    target.addEventListener(
        SYK_MODULE_VISUAL_EVENT,
        aktifModulEventiniIsle
    );

    return Object.freeze({
        bound: true,
        event: SYK_MODULE_VISUAL_EVENT,
        selector: SYK_MODULE_SELECTOR,
    });
}

export {
    SYK_MODULE_VISUAL_EVENT,
    SYK_MODULE_SELECTOR,
    DURUMLAR,
    normalize,
    runtimeDurumunuNormalizeEt,
    aktifModulKodunuEventtenAl,
    modulKartlariniBul,
    kartRuntimeDurumunuOku,
    kartDurumunuUygula,
    aktifModulGorselDurumunuUygula,
    aktifModulEventiniIsle,
    bindCanliModulGorselDurumMotoru,
};
