(() => {
    const apiRoot = "/api/syk-ui/device-hub";

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function percentage(value) {
        const number = Number(value);

        if (!Number.isFinite(number)) {
            return 0;
        }

        return Math.max(0, Math.min(100, number));
    }

    function deviceCard(device) {
        const battery = percentage(device.battery);
        const signal = percentage(
            device.signal_quality
        );

        return `
            <article
                class="device-card"
                data-device-id="${escapeHtml(device.id)}"
                data-connected="${Boolean(device.connected)}"
            >
                <header class="device-card-header">
                    <div class="device-card-title">
                        <strong>${escapeHtml(device.title)}</strong>
                        <span>${escapeHtml(device.id)}</span>
                    </div>

                    <span class="device-state">
                        ${
                            device.connected
                                ? "BAĞLI"
                                : "BAĞLI DEĞİL"
                        }
                    </span>
                </header>

                <div class="device-details">
                    <div class="device-detail">
                        <span>Taşıma</span>
                        <strong>
                            ${escapeHtml(device.transport)}
                        </strong>
                    </div>

                    <div class="device-detail">
                        <span>Adres</span>
                        <strong>
                            ${escapeHtml(device.address)}
                        </strong>
                    </div>

                    <div class="device-detail">
                        <span>Modül</span>
                        <strong>
                            ${escapeHtml(
                                device.module_id || "Atanmadı"
                            )}
                        </strong>
                    </div>

                    <div class="device-detail">
                        <span>Firmware</span>
                        <strong>
                            ${escapeHtml(
                                device.firmware || "Bilinmiyor"
                            )}
                        </strong>
                    </div>
                </div>

                <div class="device-bars">
                    <div>
                        <div class="device-bar-label">
                            <span>Pil</span>
                            <strong>%${battery}</strong>
                        </div>

                        <div class="device-bar">
                            <div style="width:${battery}%"></div>
                        </div>
                    </div>

                    <div>
                        <div class="device-bar-label">
                            <span>Sinyal Kalitesi</span>
                            <strong>%${signal}</strong>
                        </div>

                        <div class="device-bar">
                            <div style="width:${signal}%"></div>
                        </div>
                    </div>
                </div>

                <div class="device-card-actions">
                    <button
                        type="button"
                        data-device-action="connection"
                        data-device-id="${escapeHtml(device.id)}"
                        data-next-connected="${!device.connected}"
                    >
                        ${
                            device.connected
                                ? "Bağlantıyı Kes"
                                : "Bağlan"
                        }
                    </button>

                    <button
                        type="button"
                        data-device-action="detail"
                        data-device-id="${escapeHtml(device.id)}"
                    >
                        Ayrıntı
                    </button>
                </div>
            </article>
        `;
    }

    function render(container, payload) {
        const devices = payload.devices || [];
        const transports = payload.transports || [];

        const connected = devices.filter(
            (device) => device.connected
        ).length;

        container.innerHTML = `
            <section class="device-hub">
                <header class="device-hub-header">
                    <div class="device-hub-title">
                        <strong>SYK DEVICE HUB</strong>
                        <span>
                            Seri Port, TCP/IP ve BLE bilimsel cihaz merkezi
                        </span>
                    </div>

                    <div class="device-hub-actions">
                        <button
                            id="device-hub-refresh"
                            type="button"
                        >
                            Cihazları Tara
                        </button>
                    </div>
                </header>

                <section class="device-hub-status">
                    <article class="device-hub-stat">
                        <span>TOPLAM CİHAZ</span>
                        <strong>${devices.length}</strong>
                    </article>

                    <article class="device-hub-stat">
                        <span>BAĞLI CİHAZ</span>
                        <strong>${connected}</strong>
                    </article>

                    <article class="device-hub-stat">
                        <span>TAŞIMA KATMANI</span>
                        <strong>${transports.length}</strong>
                    </article>

                    <article class="device-hub-stat">
                        <span>DURUM</span>
                        <strong>AKTİF</strong>
                    </article>
                </section>

                <section class="device-hub-grid">
                    ${
                        devices.length
                            ? devices.map(
                                deviceCard
                            ).join("")
                            : `
                                <div class="device-hub-empty">
                                    <strong>
                                        Kayıtlı cihaz bulunamadı
                                    </strong>

                                    <span>
                                        Cihazları Tara düğmesini kullanın.
                                    </span>
                                </div>
                            `
                    }
                </section>
            </section>
        `;

        bindActions(container);
    }

    async function load(container) {
        container.innerHTML = `
            <section class="device-hub-loading">
                <strong>Device Hub yükleniyor</strong>
            </section>
        `;

        const response = await fetch(apiRoot);

        if (!response.ok) {
            throw new Error(
                `Device Hub hatası: ${response.status}`
            );
        }

        render(container, await response.json());
    }

    async function refresh(container) {
        const response = await fetch(
            `${apiRoot}/refresh`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    timeout: 4.0,
                }),
            },
        );

        if (!response.ok) {
            throw new Error(
                `Cihaz taraması başarısız: ${response.status}`
            );
        }

        render(container, await response.json());
    }

    async function setConnection(
        container,
        deviceId,
        connected,
    ) {
        const response = await fetch(
            `${apiRoot}/${encodeURIComponent(deviceId)}/connection`,
            {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    connected,
                }),
            },
        );

        if (!response.ok) {
            throw new Error(
                `Cihaz bağlantısı güncellenemedi: ${response.status}`
            );
        }

        await load(container);
    }

    function bindActions(container) {
        container
            .querySelector("#device-hub-refresh")
            ?.addEventListener(
                "click",
                () => refresh(container),
            );

        container
            .querySelectorAll(
                '[data-device-action="connection"]'
            )
            .forEach((button) => {
                button.addEventListener(
                    "click",
                    () => {
                        setConnection(
                            container,
                            button.dataset.deviceId,
                            (
                                button.dataset
                                    .nextConnected
                                === "true"
                            ),
                        );
                    },
                );
            });
    }

    window.SyKDeviceHub = {
        mount(container) {
            load(container).catch((error) => {
                container.innerHTML = `
                    <section class="device-hub-empty">
                        <strong>
                            Device Hub açılamadı
                        </strong>

                        <span>
                            ${escapeHtml(error.message)}
                        </span>
                    </section>
                `;
            });
        },
    };
})();