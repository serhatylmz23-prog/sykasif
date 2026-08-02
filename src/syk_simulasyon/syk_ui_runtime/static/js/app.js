const state = {
    snapshot: null,
    soundEnabled: false,
    socket: null,
    reconnectTimer: null,
};

function appendEvent(message) {
    const stream = document.querySelector("#event-stream");
    const row = document.createElement("div");

    row.className = "event-row";
    row.textContent =
        `${new Date().toLocaleTimeString("tr-TR")} · ${message}`;

    stream.prepend(row);

    while (stream.children.length > 8) {
        stream.lastElementChild.remove();
    }
}

function playAudio(filename) {
    if (!state.soundEnabled) {
        return;
    }

    const audio = document.querySelector("#runtime-audio");
    audio.src = `/syk-ui/audio/${filename}`;
    audio.play().catch(() => {});
}

function setConnectionStatus(text, isLive) {
    const element = document.querySelector("#connection-state");

    element.textContent = text;
    element.className =
        isLive ? "connection-live" : "connection-offline";
}

function renderModules(modules, activeId) {
    const list = document.querySelector("#module-list");
    list.replaceChildren();

    modules.forEach((module) => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "syk-module-button";
        button.textContent = module.title;
        button.disabled = !module.enabled;

        if (module.id === activeId) {
            button.classList.add("active");
        }

        button.addEventListener("click", () => {
            document.querySelector("#active-module").textContent =
                module.title;

            document.querySelector("#detail-module").textContent =
                module.title;

            document
                .querySelectorAll(".syk-module-button")
                .forEach((item) => item.classList.remove("active"));

            button.classList.add("active");

            window.SyKModuleViews?.render(
                module.id,
                module.title,
            );

            appendEvent(`${module.title} modülü açıldı`);
            playAudio("notification.wav");
        });

        list.appendChild(button);
    });
}

function applySnapshot(snapshot) {
    state.snapshot = snapshot;

    const active = snapshot.active_module;
    const brand = snapshot.brand;
    const frameState = snapshot.syframe;
    const environment = snapshot.environment;

    document.querySelector("#brand-title").textContent =
        brand.visible ? brand.title.text : "";

    document.querySelector("#system-state").textContent =
        `${snapshot.theme.title} · ${environment.weather}`;

    document.querySelector("#theme-state").textContent =
        snapshot.theme.title;

    document.querySelector("#weather-state").textContent =
        environment.weather;

    document.querySelector("#active-module").textContent =
        active.title;

    document.querySelector("#detail-module").textContent =
        active.title;

    document.querySelector("#detail-season").textContent =
        environment.season;

    document.querySelector("#detail-wind").textContent =
        `${environment.wind} km/sa`;

    document.querySelector("#audio-state").textContent =
        snapshot.assets.audio_ready ? "Hazır" : "Eksik";

    const frame = document.querySelector("#syframe");

    frame.dataset.state = frameState.state.id;
    frame.hidden = !frameState.visible;

    document.querySelector("#syframe-title").textContent =
        frameState.state.title;

    document.querySelector("#syframe-confidence").textContent =
        `Güven: %${frameState.confidence}`;

    document.querySelector("#detail-frame").textContent =
        frameState.state.title;

    document.querySelector("#detail-confidence").textContent =
        `%${frameState.confidence}`;

    renderModules(snapshot.modules, active.id);

    if (!state.selectedModuleId) {
        window.SyKModuleViews?.render(
            active.id,
            active.title,
        );
    }
}

async function loadRuntime() {
    const response = await fetch("/api/syk-ui/runtime-state");

    if (!response.ok) {
        throw new Error(`Runtime API hatası: ${response.status}`);
    }

    applySnapshot(await response.json());
}

function connectLiveRuntime() {
    const protocol =
        window.location.protocol === "https:" ? "wss" : "ws";

    const url =
        `${protocol}://${window.location.host}/api/syk-ui/live`;

    state.socket = new WebSocket(url);

    state.socket.addEventListener("open", () => {
        setConnectionStatus("CANLI", true);
        appendEvent("Canlı veri bağlantısı kuruldu");
    });

    state.socket.addEventListener("message", (event) => {
        const snapshot = JSON.parse(event.data);
        applySnapshot(snapshot);
    });

    state.socket.addEventListener("close", () => {
        setConnectionStatus("KOPTU", false);
        appendEvent("Bağlantı kesildi, yeniden deneniyor");

        clearTimeout(state.reconnectTimer);

        state.reconnectTimer = setTimeout(
            connectLiveRuntime,
            2000,
        );
    });

    state.socket.addEventListener("error", () => {
        state.socket.close();
    });
}

function startClock() {
    const tick = () => {
        document.querySelector("#runtime-clock").textContent =
            new Date().toLocaleTimeString("tr-TR");
    };

    tick();
    setInterval(tick, 1000);
}

document
    .querySelector("#sound-toggle")
    .addEventListener("click", () => {
        state.soundEnabled = !state.soundEnabled;

        document.querySelector("#sound-toggle").textContent =
            state.soundEnabled ? "Ses Açık" : "Ses Kapalı";

        if (state.soundEnabled) {
            playAudio("system.wav");
            appendEvent("Ses sistemi etkinleştirildi");
        }
    });

startClock();

loadRuntime()
    .then(() => {
        connectLiveRuntime();
    })
    .catch((error) => {
        setConnectionStatus("HATA", false);
        appendEvent(error.message);
    });