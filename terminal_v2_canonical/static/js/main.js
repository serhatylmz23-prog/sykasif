(() => {
    "use strict";

    const state = {
        connected: false,
        streamConnected: false,
        modules: [],
        events: [],
        activeView: "dashboard",
        retryDelay: 1500,
        retryTimer: null,
        eventSource: null,
    };

    const moduleDefinitions = {
        dashboard: {
            title: "Kontrol Merkezi",
            icon: "⌂",
            description: "Runtime ve bağlantı durumu",
        },
        analysis: {
            title: "Analiz",
            icon: "◈",
            description: "Bilimsel inceleme motorları",
        },
        evidence: {
            title: "Kanıtlar",
            icon: "◇",
            description: "Doğrulanmış dijital kanıtlar",
        },
        reports: {
            title: "Raporlar",
            icon: "▤",
            description: "Mühürlü dijital raporlar",
        },
        map: {
            title: "Harita",
            icon: "⌖",
            description: "Araştırma ve konum katmanları",
        },
        ai: {
            title: "Kaşif",
            icon: "◉",
            description: "Yapay zekâ asistanı",
        },
        settings: {
            title: "Ayarlar",
            icon: "⚙",
            description: "Terminal yapılandırması",
        },
        notifications: {
            title: "Bildirimler",
            icon: "◎",
            description: "Canlı olay ve uyarılar",
        },
    };

    const viewDescriptions = {
        dashboard: "Runtime, bağlantı ve modül durumları izleniyor.",
        map: "Harita ve saha nesneleri için çalışma alanı hazırlanıyor.",
        analysis: "Analiz motorları ve bilimsel sensör katmanları hazırlanıyor.",
        evidence: "Kanıt zinciri ve doğrulama kayıtları hazırlanıyor.",
        reports: "Akıllı Sayfa Motoru ve dijital rapor katmanı hazırlanıyor.",
        ai: "Kaşif asistanı ile terminal etkileşimi hazırlanıyor.",
        settings: "Terminal, ağ ve görünüm ayarları hazırlanıyor.",
        notifications: "Canlı bildirim ve olay merkezi hazırlanıyor.",
    };

    const elements = {
        menuButton: document.getElementById("menu-button"),
        sidebar: document.getElementById("sidebar"),
        backdrop: document.getElementById("sidebar-backdrop"),
        topStatusDot: document.getElementById("top-status-dot"),
        topStatusText: document.getElementById("top-status-text"),
        topStatusTime: document.getElementById("top-status-time"),
        runtimeStatus: document.getElementById("runtime-status"),
        sidebarRuntimeStatus: document.getElementById("sidebar-runtime-status"),
        tabletStatus: document.getElementById("tablet-status"),
        streamStatus: document.getElementById("stream-status"),
        lastCheck: document.getElementById("last-check"),
        latencyStatus: document.getElementById("latency-status"),
        moduleGrid: document.getElementById("module-grid"),
        moduleCount: document.getElementById("module-count"),
        activeViewTitle: document.getElementById("active-view-title"),
        activeViewDescription: document.getElementById("active-view-description"),
        kaşifMessage: document.getElementById("kaşif-message"),
        eventList: document.getElementById("event-list"),
        eventCount: document.getElementById("event-count"),
    };

    function formatTime(value = new Date()) {
        return value.toLocaleTimeString("tr-TR", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    }

    function addEvent(title, detail) {
        state.events.unshift({
            title,
            detail,
            time: formatTime(),
        });

        state.events = state.events.slice(0, 6);
        renderEvents();
    }

    function renderEvents() {
        elements.eventList.replaceChildren();

        for (const event of state.events) {
            const item = document.createElement("article");
            item.className = "event-item";

            const title = document.createElement("strong");
            title.textContent = event.title;

            const detail = document.createElement("small");
            detail.textContent = `${event.time} · ${event.detail}`;

            item.append(title, detail);
            elements.eventList.append(item);
        }

        elements.eventCount.textContent = String(state.events.length);
    }

    function renderModules() {
        elements.moduleGrid.replaceChildren();

        for (const moduleName of state.modules) {
            const definition =
                moduleDefinitions[moduleName] ?? {
                    title: moduleName,
                    icon: "◇",
                    description: "SyKaşif modülü",
                };

            const card = document.createElement("article");
            card.className = "module-card";
            card.tabIndex = 0;
            card.dataset.module = moduleName;

            const icon = document.createElement("span");
            icon.className = "module-card__icon";
            icon.textContent = definition.icon;

            const title = document.createElement("h3");
            title.textContent = definition.title;

            const description = document.createElement("p");
            description.textContent = definition.description;

            card.append(icon, title, description);

            const activate = () => setActiveView(moduleName);

            card.addEventListener("click", activate);

            card.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    activate();
                }
            });

            elements.moduleGrid.append(card);
        }

        elements.moduleCount.textContent =
            `${state.modules.length} MODÜL`;
    }

    function setActiveView(viewName) {
        state.activeView = viewName;

        const definition =
            moduleDefinitions[viewName] ?? {
                title: viewName,
            };

        elements.activeViewTitle.textContent = definition.title;

        elements.activeViewDescription.textContent =
            viewDescriptions[viewName] ??
            "Modül çalışma alanı hazırlanıyor.";

        document
            .querySelectorAll(".navigation-item")
            .forEach((item) => {
                item.classList.toggle(
                    "is-active",
                    item.dataset.view === viewName,
                );
            });

        closeSidebar();

        addEvent(
            "Görünüm değişti",
            definition.title,
        );
    }

    function setConnectionState(connected, payload = null) {
        state.connected = connected;

        elements.topStatusDot.classList.remove(
            "status-dot--online",
            "status-dot--offline",
            "status-dot--waiting",
        );

        if (connected) {
            elements.topStatusDot.classList.add(
                "status-dot--online",
            );

            elements.topStatusText.textContent = "ÇEVRİMİÇİ";
            elements.runtimeStatus.textContent =
                payload?.runtime?.status ??
                payload?.runtime ??
                "ONLINE";
            elements.sidebarRuntimeStatus.textContent = "ONLINE";
            elements.tabletStatus.textContent =
                payload?.connection?.tablet
                    ? "BAĞLI"
                    : "HAZIR";
            elements.kaşifMessage.textContent =
                "Terminal V2 bağlantısı aktif. Runtime izleniyor.";
        } else {
            elements.topStatusDot.classList.add(
                "status-dot--offline",
            );

            elements.topStatusText.textContent = "ÇEVRİMDIŞI";
            elements.runtimeStatus.textContent = "OFFLINE";
            elements.sidebarRuntimeStatus.textContent = "OFFLINE";
            elements.tabletStatus.textContent = "BAĞLI DEĞİL";
            elements.kaşifMessage.textContent =
                "Runtime bağlantısı kesildi. Yeniden bağlanılıyor.";
        }

        elements.topStatusTime.textContent = formatTime();
        elements.lastCheck.textContent = formatTime();
    }

    function setStreamState(connected) {
        const changed = state.streamConnected !== connected;

        state.streamConnected = connected;

        elements.streamStatus.textContent =
            connected
                ? "SSE V2 ONLINE"
                : "YENİDEN BAĞLANIYOR";

        if (changed) {
            addEvent(
                "Canlı akış",
                connected
                    ? "SSE V2 bağlantısı kuruldu"
                    : "SSE V2 bağlantısı kesildi",
            );
        }
    }

    function parseEvent(event) {
        try {
            return JSON.parse(event.data);
        } catch {
            return null;
        }
    }

    function connectEventStream() {
        if (!("EventSource" in window)) {
            elements.streamStatus.textContent =
                "TARAYICI DESTEKLEMİYOR";
            return;
        }

        if (state.eventSource) {
            state.eventSource.close();
        }

        const source = new EventSource(
            "/api/v2/events",
        );

        state.eventSource = source;

        source.addEventListener(
            "open",
            () => {
                setStreamState(true);
            },
        );

        source.addEventListener(
            "terminal.snapshot",
            (event) => {
                const payload = parseEvent(event);

                if (!payload) {
                    return;
                }

                setConnectionState(true, payload);
                setStreamState(true);

                elements.lastCheck.textContent = formatTime();
            },
        );

        source.addEventListener(
            "terminal.heartbeat",
            (event) => {
                const payload = parseEvent(event);

                if (!payload) {
                    return;
                }

                setConnectionState(true, payload);
                setStreamState(true);

                elements.lastCheck.textContent = formatTime();
            },
        );

        source.addEventListener(
            "error",
            () => {
                setStreamState(false);

                if (source.readyState === EventSource.CLOSED) {
                    setTimeout(
                        connectEventStream,
                        2000,
                    );
                }
            },
        );
    }

    async function fetchStatus() {
        const started = performance.now();

        try {
            const response = await fetch(
                "/api/v2/status",
                {
                    cache: "no-store",
                    headers: {
                        Accept: "application/json",
                    },
                },
            );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`,
                );
            }

            const payload = await response.json();

            const latency = Math.max(
                0,
                Math.round(performance.now() - started),
            );

            const wasConnected = state.connected;

            setConnectionState(true, payload);

            elements.latencyStatus.textContent =
                `${latency} ms`;

            const incomingModules =
                Array.isArray(payload.modules)
                    ? payload.modules
                    : [];

            if (
                JSON.stringify(incomingModules) !==
                JSON.stringify(state.modules)
            ) {
                state.modules = incomingModules;
                renderModules();
            }

            if (!wasConnected) {
                addEvent(
                    "Runtime bağlantısı",
                    "Bağlantı kuruldu",
                );
            }

            state.retryDelay = 1500;
        } catch {
            const wasConnected = state.connected;

            setConnectionState(false);

            elements.latencyStatus.textContent =
                "Bağlantı yok";

            if (wasConnected || state.events.length === 0) {
                addEvent(
                    "Runtime bağlantısı",
                    "Bağlantı kurulamadı",
                );
            }

            state.retryDelay = Math.min(
                state.retryDelay * 1.5,
                10000,
            );
        } finally {
            clearTimeout(state.retryTimer);

            state.retryTimer = setTimeout(
                fetchStatus,
                state.connected
                    ? 5000
                    : state.retryDelay,
            );
        }
    }

    function openSidebar() {
        elements.sidebar.classList.add("is-open");
        elements.backdrop.hidden = false;

        elements.menuButton.setAttribute(
            "aria-expanded",
            "true",
        );
    }

    function closeSidebar() {
        elements.sidebar.classList.remove("is-open");
        elements.backdrop.hidden = true;

        elements.menuButton.setAttribute(
            "aria-expanded",
            "false",
        );
    }

    function bindEvents() {
        elements.menuButton.addEventListener(
            "click",
            () => {
                const isOpen =
                    elements.sidebar.classList.contains(
                        "is-open",
                    );

                if (isOpen) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            },
        );

        elements.backdrop.addEventListener(
            "click",
            closeSidebar,
        );

        document
            .querySelectorAll(".navigation-item")
            .forEach((item) => {
                item.addEventListener(
                    "click",
                    () => {
                        setActiveView(item.dataset.view);
                    },
                );
            });

        window.addEventListener(
            "resize",
            () => {
                if (window.innerWidth > 820) {
                    closeSidebar();
                }
            },
        );

        window.addEventListener(
            "beforeunload",
            () => {
                state.eventSource?.close();
            },
        );
    }

    function boot() {
        state.modules = Object.keys(moduleDefinitions);

        renderModules();
        bindEvents();

        addEvent(
            "Terminal V2",
            "Arayüz başlatıldı",
        );

        fetchStatus();
        connectEventStream();
    }

    boot();
})();
