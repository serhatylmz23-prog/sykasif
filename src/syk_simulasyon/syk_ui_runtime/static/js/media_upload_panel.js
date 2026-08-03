(() => {
    "use strict";

    function apiBase() {
        return "/api/syk-ui";
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function ensurePanel() {
        let panel = document.querySelector(
            "#syk-media-upload-panel"
        );

        if (panel) {
            return panel;
        }

        panel = document.createElement(
            "section"
        );

        panel.id =
            "syk-media-upload-panel";

        panel.className =
            "syk-media-upload-panel";

        panel.innerHTML = `
            <header>
                <div>
                    <span>
                        GÖRÜNTÜ ANALİZİ
                    </span>

                    <strong>
                        Fotoğraf Yükle
                    </strong>
                </div>

                <button
                    type="button"
                    id="syk-media-upload-toggle"
                    aria-expanded="false"
                >
                    Görüntü
                </button>
            </header>

            <form
                id="syk-media-upload-form"
                hidden
            >
                <label>
                    <span>Fotoğraf</span>

                    <input
                        id="syk-media-upload-file"
                        name="file"
                        type="file"
                        accept=".jpg,.jpeg,.png,.webp,.bmp,image/jpeg,image/png,image/webp,image/bmp"
                        required
                    >
                </label>

                <label>
                    <span>Konum bilgisi</span>

                    <input
                        id="syk-media-upload-location"
                        name="location"
                        type="text"
                        value="Belirtilmedi"
                    >
                </label>

                <button
                    id="syk-media-upload-submit"
                    type="submit"
                >
                    Analizi Başlat
                </button>

                <div
                    id="syk-media-upload-status"
                    aria-live="polite"
                ></div>

                <div
                    id="syk-media-upload-result"
                ></div>
            </form>
        `;

        document.body.appendChild(panel);

        bind(panel);

        return panel;
    }

    function bind(panel) {
        const toggle = panel.querySelector(
            "#syk-media-upload-toggle"
        );

        const form = panel.querySelector(
            "#syk-media-upload-form"
        );

        toggle.addEventListener(
            "click",
            () => {
                form.hidden = !form.hidden;

                toggle.setAttribute(
                    "aria-expanded",
                    String(!form.hidden)
                );
            }
        );

        form.addEventListener(
            "submit",
            submit
        );
    }

    async function submit(event) {
        event.preventDefault();

        const form = event.currentTarget;

        const fileInput =
            form.querySelector(
                "#syk-media-upload-file"
            );

        const locationInput =
            form.querySelector(
                "#syk-media-upload-location"
            );

        const status =
            form.querySelector(
                "#syk-media-upload-status"
            );

        const result =
            form.querySelector(
                "#syk-media-upload-result"
            );

        const file =
            fileInput.files?.[0];

        if (!file) {
            status.textContent =
                "Fotoğraf seçilmedi.";
            return;
        }

        status.textContent =
            "Görüntü analiz ediliyor…";

        result.innerHTML = "";

        const body = new FormData();

        body.append(
            "file",
            file,
            file.name
        );

        body.append(
            "location",
            locationInput.value
                || "Belirtilmedi"
        );

        try {
            const response = await fetch(
                `${apiBase()}/media-analysis`,
                {
                    method: "POST",
                    body,
                }
            );

            const payload =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    payload.detail
                    || "Analiz başarısız."
                );
            }

            status.textContent =
                "Analiz tamamlandı.";

            renderResult(
                result,
                payload
            );

            document.dispatchEvent(
                new CustomEvent(
                    "syk:media-analysis-completed",
                    {
                        detail: payload,
                    }
                )
            );
        }
        catch (error) {
            status.textContent =
                error.message;
        }
    }

    function renderResult(
        host,
        payload
    ) {
        host.innerHTML = `
            <article
                class="syk-media-analysis-result"
                data-analysis-id="${escapeHtml(
                    payload.analysis_id
                )}"
            >
                <header>
                    <strong>
                        Analiz Tamamlandı
                    </strong>

                    <b>
                        ${escapeHtml(
                            payload.candidate_count
                        )}
                        aday
                    </b>
                </header>

                <dl>
                    <div>
                        <dt>Medya</dt>
                        <dd>
                            ${escapeHtml(
                                payload.media_id
                            )}
                        </dd>
                    </div>

                    <div>
                        <dt>DTSE kaydı</dt>
                        <dd>
                            ${escapeHtml(
                                payload.dtse_created_count
                            )}
                        </dd>
                    </div>

                    <div>
                        <dt>Rapor SHA</dt>
                        <dd>
                            <code>
                                ${escapeHtml(
                                    payload.report_sha256
                                )}
                            </code>
                        </dd>
                    </div>
                </dl>

                <div class="syk-media-result-actions">
                    <a
                        href="${escapeHtml(
                            payload.download_url
                        )}"
                        target="_blank"
                        rel="noopener"
                    >
                        PDF Raporu Aç
                    </a>

                    <a
                        href="${escapeHtml(
                            payload.manifest_url
                        )}"
                        target="_blank"
                        rel="noopener"
                    >
                        Manifest
                    </a>
                </div>
            </article>
        `;
    }

    window.SyKMediaUpload = {
        open: () => {
            const panel = ensurePanel();

            const form =
                panel.querySelector(
                    "#syk-media-upload-form"
                );

            form.hidden = false;
        },
    };

    document.addEventListener(
        "DOMContentLoaded",
        ensurePanel
    );
})();