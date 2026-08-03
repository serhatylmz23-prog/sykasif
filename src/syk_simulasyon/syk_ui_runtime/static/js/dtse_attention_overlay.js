(() => {
    "use strict";

    const state = {
        socket: null,
        activeMediaId: null,
        events: new Map(),
    };

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function getStage() {
        return document.querySelector(
            "[data-dtse-media-stage]"
        );
    }

    function ensureOverlay(stage) {
        let overlay = stage.querySelector(
            ".dtse-attention-overlay"
        );

        if (overlay) {
            return overlay;
        }

        overlay = document.createElement("div");
        overlay.className =
            "dtse-attention-overlay";

        overlay.innerHTML = `
            <svg
                class="dtse-attention-svg"
                viewBox="0 0 1000 1000"
                preserveAspectRatio="none"
                aria-label="DTSE dikkat katmanı"
            ></svg>
            <div
                class="dtse-attention-labels"
            ></div>
        `;

        stage.appendChild(overlay);

        return overlay;
    }

    function svgElement(name, attributes = {}) {
        const node = document.createElementNS(
            "http://www.w3.org/2000/svg",
            name
        );

        Object.entries(attributes).forEach(
            ([key, value]) => {
                node.setAttribute(key, value);
            }
        );

        return node;
    }

    function renderCorners(group, event) {
        const box = event.visual_layer.box;
        const palette =
            event.visual_layer.palette;

        const x = box.x * 1000;
        const y = box.y * 1000;
        const width = box.width * 1000;
        const height = box.height * 1000;

        const radius = Math.max(
            18,
            Math.min(
                width,
                height
            ) * 0.18
        );

        const paths = [
            `M ${x + radius} ${y}
             Q ${x} ${y} ${x} ${y + radius}`,

            `M ${x + width - radius} ${y}
             Q ${x + width} ${y}
               ${x + width} ${y + radius}`,

            `M ${x} ${y + height - radius}
             Q ${x} ${y + height}
               ${x + radius} ${y + height}`,

            `M ${x + width - radius}
               ${y + height}
             Q ${x + width} ${y + height}
               ${x + width}
               ${y + height - radius}`,
        ];

        paths.forEach((pathDefinition) => {
            group.appendChild(
                svgElement("path", {
                    d: pathDefinition,
                    fill: "none",
                    stroke: palette.primary,
                    "stroke-width": "7",
                    "stroke-linecap": "round",
                    "vector-effect":
                        "non-scaling-stroke",
                })
            );
        });

        group.appendChild(
            svgElement("rect", {
                x,
                y,
                width,
                height,
                rx: radius * 0.15,
                fill: "transparent",
                stroke: palette.primary,
                "stroke-width": "2",
                "stroke-dasharray": "8 10",
                "vector-effect":
                    "non-scaling-stroke",
            })
        );
    }

    function renderConnector(group, event) {
        const connector =
            event.visual_layer.connector;
        const palette =
            event.visual_layer.palette;

        group.appendChild(
            svgElement("line", {
                x1: connector.from.x * 1000,
                y1: connector.from.y * 1000,
                x2: connector.to.x * 1000,
                y2: connector.to.y * 1000,
                stroke: palette.primary,
                "stroke-width": "2",
                "stroke-dasharray": "5 9",
                "vector-effect":
                    "non-scaling-stroke",
            })
        );

        group.appendChild(
            svgElement("circle", {
                cx: connector.to.x * 1000,
                cy: connector.to.y * 1000,
                r: "7",
                fill: palette.primary,
                "vector-effect":
                    "non-scaling-stroke",
            })
        );
    }

    function renderLabel(
        labels,
        event
    ) {
        const anchor =
            event.visual_layer.label_anchor;
        const signal = event.signal;
        const syframe = event.syframe;

        const label =
            document.createElement("article");

        label.className =
            "dtse-attention-card";

        label.dataset.state =
            syframe.state;

        label.style.left =
            `${anchor.x * 100}%`;

        label.style.top =
            `${anchor.y * 100}%`;

        label.innerHTML = `
            <strong>
                ${escapeHtml(signal.label)}
            </strong>

            <span>
                ${escapeHtml(signal.kind)}
            </span>

            <small>
                Güven: %${signal.confidence}
            </small>

            <em>
                ${escapeHtml(
                    event.analysis.status
                )}
            </em>
        `;

        labels.appendChild(label);
    }

    function render(events) {
        const stage = getStage();

        if (!stage) {
            return;
        }

        const overlay = ensureOverlay(stage);
        const svg = overlay.querySelector(
            ".dtse-attention-svg"
        );
        const labels = overlay.querySelector(
            ".dtse-attention-labels"
        );

        svg.replaceChildren();
        labels.replaceChildren();

        events.forEach((event) => {
            if (
                state.activeMediaId
                && event.media_id
                    !== state.activeMediaId
            ) {
                return;
            }

            const group = svgElement("g", {
                "data-event-id": event.id,
                "data-state":
                    event.syframe.state,
                class:
                    event.visual_layer.pulse
                        ? "dtse-overlay-pulse"
                        : "",
            });

            renderCorners(group, event);
            renderConnector(group, event);

            svg.appendChild(group);
            renderLabel(labels, event);
        });
    }

    function connect() {
        if (
            state.socket
            && state.socket.readyState
                <= WebSocket.OPEN
        ) {
            return;
        }

        const protocol =
            window.location.protocol === "https:"
                ? "wss"
                : "ws";

        const url =
            `${protocol}://` +
            `${window.location.host}` +
            `/api/syk-ui/dtse/live`;

        state.socket = new WebSocket(url);

        state.socket.addEventListener(
            "message",
            (message) => {
                const payload =
                    JSON.parse(message.data);

                const events =
                    payload.events || [];

                events.forEach((event) => {
                    state.events.set(
                        event.id,
                        event
                    );
                });

                render(
                    Array.from(
                        state.events.values()
                    )
                );
            }
        );

        state.socket.addEventListener(
            "close",
            () => {
                window.setTimeout(
                    connect,
                    1500
                );
            }
        );
    }

    function mount(
        stage,
        mediaId = null
    ) {
        stage.setAttribute(
            "data-dtse-media-stage",
            ""
        );

        state.activeMediaId = mediaId;

        ensureOverlay(stage);
        connect();
    }

    function setMedia(mediaId) {
        state.activeMediaId = mediaId;

        render(
            Array.from(
                state.events.values()
            )
        );
    }

    window.SyKDTSEAttention = {
        mount,
        setMedia,
        connect,
    };

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            const stage = getStage();

            if (stage) {
                mount(
                    stage,
                    stage.dataset.mediaId || null
                );
            }
        }
    );
})();