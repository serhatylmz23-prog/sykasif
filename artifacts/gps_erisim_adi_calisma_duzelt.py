from pathlib import Path


path = Path(
    "src/syk_simulasyon/syk_ui_runtime/"
    "static/index.html"
)

text = path.read_text(
    encoding="utf-8",
)

marker = (
    "SYK_GPS_ERISILEBILIR_AD_DUZELTMESI"
)

block = '''
<script>
(() => {
    "use strict";

    const duzelt = () => {
        const dugmeler = document.querySelectorAll(
            "#module-list button.syk-module-button"
        );

        for (const dugme of dugmeler) {
            if (
                dugme.textContent.trim()
                === "GPS"
            ) {
                dugme.setAttribute(
                    "aria-label",
                    "Konum bölümü"
                );
            }
        }
    };

    document.addEventListener(
        "DOMContentLoaded",
        duzelt,
        {
            once: true,
        }
    );

    const gozlemci = new MutationObserver(
        duzelt
    );

    gozlemci.observe(
        document.documentElement,
        {
            childList: true,
            subtree: true,
        }
    );

    window.setTimeout(
        () => {
            duzelt();
            gozlemci.disconnect();
        },
        5000
    );
})();
// SYK_GPS_ERISILEBILIR_AD_DUZELTMESI
</script>
'''

if marker not in text:
    kapanis = "</body>"

    if kapanis not in text:
        raise RuntimeError(
            "HTML kapanış bölümü bulunamadı."
        )

    text = text.replace(
        kapanis,
        block + "\n" + kapanis,
        1,
    )

    path.write_text(
        text,
        encoding="utf-8",
    )

print(
    "GPS_ERISILEBILIR_ADI_DUZELTILDI"
)
