"use strict";

const HARITA_KATMAN_SURUMU =
    "SYK_MAP_LAYER_ARCH_V1";

const HARITA_KATMAN_TURLERI =
    Object.freeze([
        "arastirma_noktasi",
        "fotograf",
        "video",
        "ses",
        "olcum",
        "rota",
        "iz",
        "kamp",
        "kazi",
        "numune",
        "risk",
        "kanit",
    ]);

const HARITA_KATMANLARI =
    Object.freeze({

        arastirma_noktasi: Object.freeze({
            kod: "arastirma_noktasi",
            ad: "Araştırma Noktası",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 10,
        }),

        fotograf: Object.freeze({
            kod: "fotograf",
            ad: "Fotoğraf",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 20,
        }),

        video: Object.freeze({
            kod: "video",
            ad: "Video",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 30,
        }),

        ses: Object.freeze({
            kod: "ses",
            ad: "Ses",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 40,
        }),

        olcum: Object.freeze({
            kod: "olcum",
            ad: "Ölçüm",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 50,
        }),

        rota: Object.freeze({
            kod: "rota",
            ad: "Rota",
            geometri: "LineString",
            varsayilan_aktif: true,
            siralama: 60,
        }),

        iz: Object.freeze({
            kod: "iz",
            ad: "İz",
            geometri: "LineString",
            varsayilan_aktif: true,
            siralama: 70,
        }),

        kamp: Object.freeze({
            kod: "kamp",
            ad: "Kamp",
            geometri: "Point",
            varsayilan_aktif: false,
            siralama: 80,
        }),

        kazi: Object.freeze({
            kod: "kazi",
            ad: "Kazı",
            geometri: "Polygon",
            varsayilan_aktif: false,
            siralama: 90,
        }),

        numune: Object.freeze({
            kod: "numune",
            ad: "Numune",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 100,
        }),

        risk: Object.freeze({
            kod: "risk",
            ad: "Risk",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 110,
        }),

        kanit: Object.freeze({
            kod: "kanit",
            ad: "Kanıt",
            geometri: "Point",
            varsayilan_aktif: true,
            siralama: 120,
        }),
    });

const HARITA_NESNELERI =
    Object.freeze([

        Object.freeze({
            id: "ARASTIRMA-001",
            katman: "arastirma_noktasi",
            ad: "Araştırma Noktası 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2264,
                    38.6814,
                ]),
            }),
            veri: Object.freeze({
                durum: "aktif",
                kaynak: "SyKaşif",
            }),
        }),

        Object.freeze({
            id: "FOTO-001",
            katman: "fotograf",
            ad: "Fotoğraf 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2310,
                    38.6840,
                ]),
            }),
            veri: Object.freeze({
                durum: "hazir",
                dosya: null,
            }),
        }),

        Object.freeze({
            id: "VIDEO-001",
            katman: "video",
            ad: "Video 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2180,
                    38.6760,
                ]),
            }),
            veri: Object.freeze({
                durum: "hazir",
                dosya: null,
            }),
        }),

        Object.freeze({
            id: "SES-001",
            katman: "ses",
            ad: "Ses Kaydı 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2400,
                    38.6900,
                ]),
            }),
            veri: Object.freeze({
                durum: "hazir",
                dosya: null,
            }),
        }),

        Object.freeze({
            id: "OLCUM-001",
            katman: "olcum",
            ad: "Ölçüm 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2050,
                    38.6950,
                ]),
            }),
            veri: Object.freeze({
                tur: "saha",
                deger: null,
                birim: null,
            }),
        }),

        Object.freeze({
            id: "ROTA-001",
            katman: "rota",
            ad: "Saha Rotası 001",
            geometri: Object.freeze({
                type: "LineString",
                coordinates: Object.freeze([
                    Object.freeze([
                        39.1800,
                        38.6600,
                    ]),
                    Object.freeze([
                        39.2050,
                        38.6700,
                    ]),
                    Object.freeze([
                        39.2264,
                        38.6814,
                    ]),
                    Object.freeze([
                        39.2500,
                        38.7000,
                    ]),
                ]),
            }),
            veri: Object.freeze({
                durum: "aktif",
            }),
        }),

        Object.freeze({
            id: "IZ-001",
            katman: "iz",
            ad: "İz 001",
            geometri: Object.freeze({
                type: "LineString",
                coordinates: Object.freeze([
                    Object.freeze([
                        39.2100,
                        38.6710,
                    ]),
                    Object.freeze([
                        39.2180,
                        38.6780,
                    ]),
                    Object.freeze([
                        39.2290,
                        38.6860,
                    ]),
                ]),
            }),
            veri: Object.freeze({
                durum: "kayitli",
            }),
        }),

        Object.freeze({
            id: "KAMP-001",
            katman: "kamp",
            ad: "Kamp Alanı 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2600,
                    38.7050,
                ]),
            }),
            veri: Object.freeze({
                durum: "planlandi",
            }),
        }),

        Object.freeze({
            id: "KAZI-001",
            katman: "kazi",
            ad: "Kazı Alanı 001",
            geometri: Object.freeze({
                type: "Polygon",
                coordinates: Object.freeze([
                    Object.freeze([
                        Object.freeze([
                            39.2000,
                            38.6800,
                        ]),
                        Object.freeze([
                            39.2040,
                            38.6800,
                        ]),
                        Object.freeze([
                            39.2040,
                            38.6830,
                        ]),
                        Object.freeze([
                            39.2000,
                            38.6830,
                        ]),
                        Object.freeze([
                            39.2000,
                            38.6800,
                        ]),
                    ]),
                ]),
            }),
            veri: Object.freeze({
                durum: "taslak",
            }),
        }),

        Object.freeze({
            id: "NUMUNE-001",
            katman: "numune",
            ad: "Numune 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2140,
                    38.6880,
                ]),
            }),
            veri: Object.freeze({
                durum: "kayitli",
                tur: "belirsiz",
            }),
        }),

        Object.freeze({
            id: "RISK-001",
            katman: "risk",
            ad: "Risk Noktası 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2450,
                    38.6750,
                ]),
            }),
            veri: Object.freeze({
                seviye: "orta",
                durum: "aktif",
            }),
        }),

        Object.freeze({
            id: "KANIT-001",
            katman: "kanit",
            ad: "Kanıt 001",
            geometri: Object.freeze({
                type: "Point",
                coordinates: Object.freeze([
                    39.2330,
                    38.6930,
                ]),
            }),
            veri: Object.freeze({
                durum: "dogrulama_bekliyor",
                sha256: null,
            }),
        }),
    ]);

function katmanGetir(
    katmanKodu
) {
    return (
        HARITA_KATMANLARI[
            katmanKodu
        ]
        ?? null
    );
}

function katmanNesneleri(
    katmanKodu
) {
    return HARITA_NESNELERI.filter(
        (nesne) =>
            nesne.katman
            === katmanKodu
    );
}

function aktifKatmanKodlari() {
    return Object.values(
        HARITA_KATMANLARI
    )
        .filter(
            (katman) =>
                katman.varsayilan_aktif
        )
        .sort(
            (a, b) =>
                a.siralama
                - b.siralama
        )
        .map(
            (katman) =>
                katman.kod
        );
}

function katmanOzeti() {

    const sonuc = {};

    for (
        const katmanKodu
        of HARITA_KATMAN_TURLERI
    ) {

        sonuc[katmanKodu] =
            katmanNesneleri(
                katmanKodu
            ).length;
    }

    return Object.freeze(
        sonuc
    );
}

const HARITA_KATMAN_SOZLESMESI =
    Object.freeze({
        surum:
            HARITA_KATMAN_SURUMU,

        katman_sayisi:
            HARITA_KATMAN_TURLERI.length,

        nesne_sayisi:
            HARITA_NESNELERI.length,

        aktif_katmanlar:
            Object.freeze(
                aktifKatmanKodlari()
            ),

        ozet:
            katmanOzeti(),
    });

globalThis.SyKasifHaritaKatmanlari =
    Object.freeze({
        surum:
            HARITA_KATMAN_SURUMU,

        katmanlar:
            HARITA_KATMANLARI,

        nesneler:
            HARITA_NESNELERI,

        sozlesme:
            HARITA_KATMAN_SOZLESMESI,

        katmanGetir,
        katmanNesneleri,
        aktifKatmanKodlari,
        katmanOzeti,
    });

export {
    HARITA_KATMAN_SURUMU,
    HARITA_KATMAN_TURLERI,
    HARITA_KATMANLARI,
    HARITA_NESNELERI,
    HARITA_KATMAN_SOZLESMESI,
    katmanGetir,
    katmanNesneleri,
    aktifKatmanKodlari,
    katmanOzeti,
};
