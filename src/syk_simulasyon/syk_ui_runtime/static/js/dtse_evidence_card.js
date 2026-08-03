(() => {
    "use strict";

    const state = {
        socket: null,
        activeEventId: null,
        latestPayload: null,
        reconnectTimer: null,
    };

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function shortHash(value) {
        const text = String(value ?? "");

        if (text.length <= 18) {
            return text || "—";
        }

        return `${text.slice(0, 9)}…${text.slice(-8)}`;
    }

    function apiBase() {
        return "/api/syk-ui";
    }

    function ensureHost() {
    let host = document.querySelector(
        "#dtse-evidence-card-host"
    );

    if (host) {
        if (host.parentElement !== document.body) {
            document.body.appendChild(host);
        }

        return host;
    }

    host = document.createElement("aside");
    host.id = "dtse-evidence-card-host";
    host.className = "dtse-evidence-card-host";

    host.setAttribute(
        "aria-live",
        "polite"
    );

    host.setAttribute(
        "aria-label",
        "DTSE kanıt kartı"
    );

    document.body.appendChild(host);

    return host;
}

    async function fetchJson(url) {
        const response = await fetch(
            url,
            {
                headers: {
                    Accept: "application/json",
                },
            }
        );

        if (!response.ok) {
            throw new Error(
                `${response.status} ${response.statusText}`
            );
        }

        return response.json();
    }

    async function loadEvidence(
        mediaId
    ) {
        const encodedId =
            encodeURIComponent(mediaId);

        const chainUrl =
            `${apiBase()}/goruntu/kayitlar/`
            + `${encodedId}/kanit-zinciri`;

        const manifestUrl =
            `${apiBase()}/goruntu/kayitlar/`
            + `${encodedId}/kanit-manifesti`;

        const verifyUrl =
            `${apiBase()}/goruntu/kayitlar/`
            + `${encodedId}/kanit-dogrula`;

        const [
            chain,
            manifest,
            verification,
        ] = await Promise.all([
            fetchJson(chainUrl),
            fetchJson(manifestUrl),
            fetchJson(verifyUrl),
        ]);

        return {
            chain,
            manifest,
            verification,
        };
    }

    function stateLabel(stateId) {
        const labels = {
            verified: "Doğrulandı",
            analyzing: "Analiz Ediliyor",
            review: "İncelenmeli",
            low_confidence: "Düşük Güven",
            inconsistent: "Tutarsız Veri",
            rare_anomaly: "Nadir Anomali",
            reference: "Referans Veri",
        };

        return labels[stateId]
            || stateId
            || "Bilinmiyor";
    }

    function renderLoading(event) {
        const host = ensureHost();

        host.innerHTML = `
            <article
                class="dtse-evidence-card"
                data-state="${escapeHtml(
                    event.syframe?.state
                )}"
                data-loading="true"
            >
                <header>
                    <span class="dtse-evidence-kicker">
                        DTSE KANIT KARTI
                    </span>

                    <strong>
                        ${escapeHtml(
                            event.signal?.label
                        )}
                    </strong>
                </header>

                <div class="dtse-evidence-loading">
                    Kanıt zinciri doğrulanıyor…
                </div>
            </article>
        `;
    }

    function renderError(
        event,
        error
    ) {
        const host = ensureHost();

        host.innerHTML = `
            <article
                class="dtse-evidence-card"
                data-state="review"
                data-error="true"
            >
                <header>
                    <span class="dtse-evidence-kicker">
                        DTSE KANIT KARTI
                    </span>

                    <strong>
                        ${escapeHtml(
                            event.signal?.label
                        )}
                    </strong>
                </header>

                <div class="dtse-evidence-warning">
                    Kanıt verisi henüz hazır değil.
                </div>

                <small>
                    ${escapeHtml(
                        error.message
                    )}
                </small>
            </article>
        `;
    }

    function renderEvidence(
        event,
        evidence
    ) {
        const host = ensureHost();

        const verification =
            evidence.verification || {};

        const manifest =
            evidence.manifest || {};

        const records =
            evidence.chain?.records || [];

        const latestRecord =
            records.at(-1) || {};

        const valid =
            verification.valid === true;

        const stateId =
            event.syframe?.state
            || (
                valid
                    ? "verified"
                    : "review"
            );

        const confidence =
            Number(
                event.signal?.confidence
                ?? event.syframe?.confidence
                ?? 0
            );

        const box =
            event.visual_layer?.box || {};

        host.innerHTML = `
            <article
                class="dtse-evidence-card"
                data-state="${escapeHtml(
                    stateId
                )}"
                data-valid="${valid}"
                data-event-id="${escapeHtml(
                    event.id
                )}"
                data-media-id="${escapeHtml(
                    event.media_id
                )}"
            >
                <header>
                    <div>
                        <span class="dtse-evidence-kicker">
                            DTSE KANIT KARTI
                        </span>

                        <strong>
                            ${escapeHtml(
                                event.signal?.label
                            )}
                        </strong>
                    </div>

                    <span
                        class="dtse-evidence-state"
                    >
                        ${escapeHtml(
                            stateLabel(stateId)
                        )}
                    </span>
                </header>

                <section
                    class="dtse-evidence-summary"
                >
                    <div>
                        <span>Kaynak</span>
                        <b>
                            ${escapeHtml(
                                event.source_kind
                            )}
                        </b>
                    </div>

                    <div>
                        <span>Güven</span>
                        <b>
                            %${confidence.toFixed(1)}
                        </b>
                    </div>

                    <div>
                        <span>Kare</span>
                        <b>
                            ${escapeHtml(
                                event.frame_index
                            )}
                        </b>
                    </div>

                    <div>
                        <span>Kayıt</span>
                        <b>
                            ${escapeHtml(
                                verification.record_count
                                ?? records.length
                            )}
                        </b>
                    </div>
                </section>

                <section
                    class="dtse-evidence-region"
                >
                    <span>Dikkat Bölgesi</span>

                    <code>
                        x=${Number(
                            box.x ?? 0
                        ).toFixed(3)}
                        y=${Number(
                            box.y ?? 0
                        ).toFixed(3)}
                        w=${Number(
                            box.width ?? 0
                        ).toFixed(3)}
                        h=${Number(
                            box.height ?? 0
                        ).toFixed(3)}
                    </code>
                </section>

                <section
                    class="dtse-evidence-hashes"
                >
                    <div>
                        <span>Olay SHA</span>
                        <code title="${escapeHtml(
                            event.event_sha256
                        )}">
                            ${escapeHtml(
                                shortHash(
                                    event.event_sha256
                                )
                            )}
                        </code>
                    </div>

                    <div>
                        <span>Kayıt SHA</span>
                        <code title="${escapeHtml(
                            latestRecord.record_sha256
                        )}">
                            ${escapeHtml(
                                shortHash(
                                    latestRecord.record_sha256
                                )
                            )}
                        </code>
                    </div>

                    <div>
                        <span>Manifest SHA</span>
                        <code title="${escapeHtml(
                            manifest.manifest_sha256
                        )}">
                            ${escapeHtml(
                                shortHash(
                                    manifest.manifest_sha256
                                )
                            )}
                        </code>
                    </div>
                </section>

                <footer>
                    <span
                        class="dtse-evidence-verification"
                        data-valid="${valid}"
                    >
                        ${
                            valid
                                ? "SHA zinciri doğrulandı"
                                : "SHA zinciri doğrulanamadı"
                        }
                    </span>

                    <small>
                        Saha doğrulaması gereklidir
                    </small>
                </footer>
            </article>
        `;

        state.latestPayload = {
            event,
            evidence,
        };

        document.dispatchEvent(
            new CustomEvent(
                "syk:dtse-evidence-rendered",
                {
                    detail: state.latestPayload,
                }
            )
        );
    }

    async function renderEvent(
        event
    ) {
        if (
            !event
            || !event.id
            || !event.media_id
        ) {
            return;
        }

        if (
            state.activeEventId
            === event.id
        ) {
            return;
        }

        state.activeEventId =
            event.id;

        renderLoading(event);

        try {
            const evidence =
                await loadEvidence(
                    event.media_id
                );

            renderEvidence(
                event,
                evidence
            );
        }
        catch (error) {
            renderError(
                event,
                error
            );
        }
    }

    function handleSnapshot(
        snapshot
    ) {
        const latestEvent =
            snapshot?.latest_event;

        if (!latestEvent) {
            return;
        }

        renderEvent(latestEvent);
    }

    function connect() {
        if (
            state.socket
            && (
                state.socket.readyState
                === WebSocket.OPEN
                || state.socket.readyState
                === WebSocket.CONNECTING
            )
        ) {
            return;
        }

        const protocol =
            window.location.protocol
            === "https:"
                ? "wss"
                : "ws";

        const url =
            `${protocol}://`
            + `${window.location.host}`
            + "/api/syk-ui/dtse/live";

        state.socket =
            new WebSocket(url);

        state.socket.addEventListener(
            "message",
            (message) => {
                try {
                    handleSnapshot(
                        JSON.parse(
                            message.data
                        )
                    );
                }
                catch {
                    return;
                }
            }
        );

        state.socket.addEventListener(
            "close",
            () => {
                state.socket = null;

                clearTimeout(
                    state.reconnectTimer
                );

                state.reconnectTimer =
                    window.setTimeout(
                        connect,
                        1500
                    );
            }
        );
    }

    function reset() {
        state.activeEventId = null;
        state.latestPayload = null;

        const host = document.querySelector(
            "#dtse-evidence-card-host"
        );

        if (host) {
            host.replaceChildren();
        }
    }

    window.SyKDTSEEvidenceCard = {
        connect,
        renderEvent,
        handleSnapshot,
        reset,
        getLatest: () => (
            state.latestPayload
        ),
    };

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            ensureHost();
            connect();
        }
    );
})();