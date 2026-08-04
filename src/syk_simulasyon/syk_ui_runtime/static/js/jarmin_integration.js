(() => {
    "use strict";

    const EVENT_API =
        "/api/syk-ui/jarmin/integration/events";

    async function publish(
        eventType,
        source,
        message,
        payload = {},
        title = null
    ) {
        try {
            const response = await fetch(
                EVENT_API,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",
                        Accept:
                            "application/json",
                    },
                    body: JSON.stringify({
                        event_type:
                            eventType,
                        source,
                        title,
                        message,
                        payload,
                    }),
                }
            );

            if (!response.ok) {
                return null;
            }

            const result =
                await response.json();

            document.dispatchEvent(
                new CustomEvent(
                    "syk:jarmin-event-recorded",
                    {
                        detail: result,
                    }
                )
            );

            return result;
        }
        catch {
            return null;
        }
    }

    document.addEventListener(
        "syk:theme-changed",
        event => {
            const theme =
                event.detail || {};

            publish(
                "theme_changed",
                "theme_runtime",
                "SyKaşif görünüm teması güncellendi.",
                {
                    theme_id:
                        theme.id || null,
                }
            );
        }
    );

    document.addEventListener(
        "syk:environment-updated",
        event => {
            const environment =
                event.detail || {};

            publish(
                "environment_changed",
                "adaptive_environment",
                "Dinamik ortam görünümü güncellendi.",
                {
                    weather:
                        environment.weather
                        || null,
                    season:
                        environment.season
                        || null,
                    daylight_factor:
                        environment
                            .daylight_factor
                        ?? null,
                }
            );
        }
    );

    document.addEventListener(
        "syk:dtse-attention",
        event => {
            const detail =
                event.detail || {};

            publish(
                "dtse_attention",
                "dtse_attention_overlay",
                "Görüntü üzerinde dikkat gerektiren bölge algılandı.",
                detail
            );
        }
    );

    document.addEventListener(
        "syk:dtse-evidence",
        event => {
            const detail =
                event.detail || {};

            publish(
                "dtse_evidence",
                "dtse_evidence_card",
                "DTSE kanıt kaydı oluşturuldu.",
                detail
            );
        }
    );

    document.addEventListener(
        "syk:media-analysis-completed",
        event => {
            const detail =
                event.detail || {};

            publish(
                "analysis_completed",
                "media_analysis",
                "Görüntü analizi tamamlandı.",
                detail
            );
        }
    );

    document.addEventListener(
        "syk:sealed-report-created",
        event => {
            const detail =
                event.detail || {};

            publish(
                "report_created",
                "sealed_report",
                "Mühürlü dijital rapor hazırlandı.",
                detail
            );
        }
    );

    window.SyKJarminIntegration = {
        publish,
    };
})();