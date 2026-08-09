
const API_BASE =
    window.SYK_API_BASE
    || `${window.location.protocol}//${window.location.hostname}:8013`;

const durumMetni =
    document.getElementById("durumMetni");

const aktifModul =
    document.getElementById("aktifModul");

const surum =
    document.getElementById("surum");

const modulBasligi =
    document.getElementById("modulBasligi");

const modulAciklamasi =
    document.getElementById("modulAciklamasi");

const kartAlani =
    document.getElementById("modulKartlari");

const islemAlani =
    document.getElementById("islemAlani");

const baglantiDurumu =
    document.getElementById("baglantiDurumu");

let sonImza = "";

function metin(value, fallback = "") {
    return String(value ?? fallback);
}

async function jsonIstek(path, options = {}) {
    const response = await fetch(
        `${API_BASE}${path}`,
        {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            ...options,
        },
    );

    if (!response.ok) {
        throw new Error(
            `HTTP ${response.status}`,
        );
    }

    return response.json();
}

async function modulAc(kod) {
    durumMetni.textContent =
        "\u004d\u006f\u0064\u00fc\u006c \u0061\u00e7\u0131\u006c\u0131\u0079\u006f\u0072\u002e\u002e\u002e";

    await jsonIstek(
        "/api/v2/modul-kartlari/aktif",
        {
            method: "POST",
            body: JSON.stringify({
                modul_kodu: kod,
            }),
        },
    );

    await yenile();
}

function islemleriCiz(islemler = []) {
    islemAlani.replaceChildren();

    for (const islem of islemler) {
        const button =
            document.createElement("button");

        button.type = "button";
        button.className = "islem-dugmesi";
        button.textContent = metin(islem);

        button.addEventListener(
            "click",
            () => {
                durumMetni.textContent =
                    `\u0130\u015f\u006c\u0065\u006d \u0073\u0065\u00e7\u0069\u006c\u0064\u0069\u003a ${metin(islem)}`;
            },
        );

        islemAlani.append(button);
    }
}

function kartlariCiz(kartlar = []) {
    kartAlani.replaceChildren();

    for (const kart of kartlar) {
        const kod =
            metin(kart.kod, "dashboard");

        const button =
            document.createElement("button");

        button.type = "button";
        button.className =
            `kart${kart.aktif ? " aktif" : ""}`;

        const baslik =
            document.createElement("h3");

        baslik.textContent =
            metin(kart.ad, "Mod\u00fcl");

        const durum =
            document.createElement("p");

        durum.className = "kart-durum";
        durum.textContent =
            metin(
                kart.durum_metni,
                kart.aktif
                    ? "\u00c7\u0061\u006c\u0131\u015f\u0131\u0079\u006f\u0072"
                    : "\u0042\u0065\u006b\u006c\u0069\u0079\u006f\u0072",
            );

        button.append(
            baslik,
            durum,
        );

        button.addEventListener(
            "click",
            () => modulAc(kod),
        );

        kartAlani.append(button);
    }
}

async function yenile() {
    try {
        const [state, kartlar] =
            await Promise.all([
                jsonIstek(
                    "/api/v2/runtime-state",
                ),
                jsonIstek(
                    "/api/v2/modul-kartlari",
                ),
            ]);

        const imza =
            JSON.stringify([
                state,
                kartlar,
            ]);

        if (imza === sonImza) {
            return;
        }

        sonImza = imza;

        baglantiDurumu.textContent =
            "\u00c7\u0065\u0076\u0072\u0069\u006d \u0069\u00e7\u0069";

        baglantiDurumu.className =
            "durum calismiyor";

        const aktif =
            metin(
                kartlar.aktif_modul
                ?? state.aktif_modul,
                "dashboard",
            );

        aktifModul.textContent =
            `\u0041\u006b\u0074\u0069\u0066 \u006d\u006f\u0064\u00fc\u006c\u003a ${aktif}`;

        surum.textContent =
            `\u0053\u00fc\u0072\u00fc\u006d\u003a ${metin(state.surum, "-")}`;

        durumMetni.textContent =
            metin(
                state.durum_metni,
                "\u0053\u0079\u004b\u0061\u015f\u0069\u0066 \u00e7\u0061\u006c\u0131\u015f\u006d\u0061 \u0061\u006c\u0061\u006e\u0131 \u0068\u0061\u007a\u0131\u0072\u002e",
            );

        modulBasligi.textContent =
            metin(
                kartlar.gorunum?.baslik,
                aktif,
            );

        modulAciklamasi.textContent =
            metin(
                kartlar.gorunum?.aciklama,
                "\u0043\u0061\u006e\u006c\u0131 \u00e7\u0061\u006c\u0131\u015f\u006d\u0061 \u0061\u006c\u0061\u006e\u0131\u002e",
            );

        islemleriCiz(
            kartlar.gorunum?.islemler || [],
        );

        kartlariCiz(
            kartlar.kartlar || [],
        );
    } catch (error) {
        baglantiDurumu.textContent =
            "\u0042\u0061\u011f\u006c\u0061\u006e\u0074\u0131 \u0079\u006f\u006b";

        baglantiDurumu.className =
            "durum hata";
    }
}

if ("serviceWorker" in navigator) {
    window.addEventListener(
        "load",
        () => {
            navigator.serviceWorker.register(
                "./service-worker.js",
            );
        },
    );
}

yenile();
setInterval(
    yenile,
    2000,
);
