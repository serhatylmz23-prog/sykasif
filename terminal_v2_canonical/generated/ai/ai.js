(() => {
    "use strict";

    const moduleName = "ai";
    const root = document.querySelector(`#module-${moduleName}`);

    if (!root) {
        return;
    }

    root.dataset.runtimeStatus = "ready";

    window.dispatchEvent(
        new CustomEvent("syk:module-ready", {
            detail: {
                module: moduleName,
                status: "READY",
            },
        }),
    );
})();
