import json
import os

from playwright.sync_api import (
    Page,
)


def test_cevrimdisi_runtime_tarayıcıda_yuklenir(
    page: Page,
):
    url = os.getenv(
        "SYK_UI_TEST_URL",
        "http://127.0.0.1:8013/syk-ui-screen",
    )

    page.route(
        "**/api/syk-ui/mobile-offline/online",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "online": True,
                    "status": "ready",
                }
            ),
        ),
    )

    page.route(
        "**/api/syk-ui/mobile-offline/pairings/verify",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "valid": False,
                }
            ),
        ),
    )

    page.goto(
        url,
        wait_until="networkidle",
    )

    result = page.evaluate(
        """
        async () => {
            const runtime =
                window.SyKMobileOffline;

            await runtime.cachePut(
                "test:006c",
                "test",
                {
                    value: 1,
                },
                60
            );

            const cached =
                await runtime.cacheGet(
                    "test:006c"
                );

            const queued =
                await runtime.enqueue({
                    itemType: "event",
                    endpoint:
                        "/api/test/offline",
                    method: "POST",
                    payload: {
                        test: true,
                    },
                });

            return {
                runtimeReady:
                    Boolean(runtime),
                snapshot:
                    runtime.snapshot(),
                cached,
                queued,
            };
        }
        """
    )

    assert result[
        "runtimeReady"
    ]

    assert (
        result["cached"][
            "value"
        ]["value"]
        == 1
    )

    assert (
        result["queued"][
            "status"
        ]
        == "pending"
    )