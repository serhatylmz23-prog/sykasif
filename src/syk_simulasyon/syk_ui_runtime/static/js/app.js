const state = {
    snapshot: null,
    modules: [],
    soundEnabled: false,
};

const moduleTitles = {
    dashboard: "Ana Terminal",
    syframe: "SyFrame",
    maps: "Haritalar",
    geology: "Jeoloji",
    sonar: "Sonar",
    frequency: "Frekans",
    material: "Materyal",
    measurement: "Ölçüm",
    gps: "GPS",
    rtk: "RTK",
    lidar: "LiDAR",
    history: "Tarih",
    archaeology: "Arkeoloji",
    astronomy: "Astronomi",
    chemistry: "Kimyasal Analiz",
    spectral: "Spektral Analiz",
    thermal: "Termal Analiz",
    magnetometer: "Manyetometre",
    gravimeter: "Gravimetre",
    ert: "Elektrik Direnç",
    gpr: "GPR",
    seismic: "Sismik",
    hydro: "Hidrojeoloji",
    botany: "Botanik",
    soil: "Toprak",
    water: "Su",
    finance: "SyFinansOtağı",
};

function renderModules(activeId) {
    const list = document.querySelector("#module-list");
    list.replaceChildren();

    Object.entries(moduleTitles).forEach(([id, title]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "syk-module-button";
        button.textContent = title;

        if (id === activeId) {
            button.classList.add("active");
        }

        button.addEventListener("click", () => {
            document.querySelector("#active-module").textContent = title;

            document
                .querySelectorAll(".syk-module-button")
                .forEach((item) => item.classList.remove("active"));

            button.classList.add("active");

            if (state.soundEnabled) {
                playAudio("notification.wav");
            }
        });

        list.appendChild(button);
    });
}

function playAudio(filename) {
    const audio = document.querySelector("#runtime-audio");
    audio.src = `/syk-ui/audio/${filename}`;
    audio.play().catch(() => {});
}

function applySnapshot(snapshot) {
    state.snapshot = snapshot;

    const activeModule = snapshot.active_module;
    const brand = snapshot.brand;
    const syframe = snapshot.syframe;

    document.querySelector("#brand-title").textContent =
        brand.visible ? brand.title.text : "";

    document.querySelector("#system-state").textContent =
        `${snapshot.theme.title} · ${snapshot.environment.weather}`;

    document.querySelector("#active-module").textContent =
        activeModule.title;

    const frame = document.querySelector("#syframe");
    frame.dataset.state = syframe.state.id;
    frame.hidden = !syframe.visible;

    document.querySelector("#syframe-title").textContent =
        syframe.state.title;

    document.querySelector("#syframe-confidence").textContent =
        `Güven: %${syframe.confidence}`;

    renderModules(activeModule.id);
}

async function loadRuntime() {
    const response = await fetch("/api/syk-ui/runtime-state");

    if (!response.ok) {
        throw new Error(`Runtime API hatası: ${response.status}`);
    }

    const snapshot = await response.json();
    applySnapshot(snapshot);
}

document
    .querySelector("#sound-toggle")
    .addEventListener("click", () => {
        state.soundEnabled = !state.soundEnabled;

        document.querySelector("#sound-toggle").textContent =
            state.soundEnabled ? "Ses Açık" : "Ses Kapalı";

        if (state.soundEnabled) {
            playAudio("system.wav");
        }
    });

loadRuntime().catch((error) => {
    document.querySelector("#system-state").textContent =
        `Bağlantı hatası: ${error.message}`;
});