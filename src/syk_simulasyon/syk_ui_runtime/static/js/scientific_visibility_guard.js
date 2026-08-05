(() => {
    "use strict";

    const scientificModules = new Set([
        "astronomy",
        "chemical",
        "spectral",
        "thermal",
        "magnetometer",
        "gravimeter",
        "ert",
        "gpr",
        "seismic",
        "hydro",
        "botany",
        "soil",
        "water"
    ]);

    function restoreScientificView() {
        const moduleView =
            document.querySelector("#module-view");

        if (!moduleView) {
            return;
        }

        const moduleId = (
            moduleView.dataset
                .activeScientificModule
            || ""
        ).trim();

        if (!scientificModules.has(moduleId)) {
            return;
        }

        moduleView.hidden = false;

        const mapStage =
            document.querySelector("#map-stage");

        if (mapStage) {
            mapStage.hidden = true;
        }

        const frame =
            document.querySelector("#syframe");

        if (frame) {
            frame.hidden = true;
        }
    }

    function scheduleRestore() {
        restoreScientificView();

        requestAnimationFrame(
            restoreScientificView
        );

        setTimeout(
            restoreScientificView,
            50
        );

        setTimeout(
            restoreScientificView,
            250
        );
    }

    document.addEventListener(
        "click",
        () => {
            setTimeout(
                scheduleRestore,
                0
            );
        },
        true
    );

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            const moduleView =
                document.querySelector(
                    "#module-view"
                );

            if (moduleView) {
                const observer =
                    new MutationObserver(
                        scheduleRestore
                    );

                observer.observe(
                    moduleView,
                    {
                        attributes: true,
                        attributeFilter: [
                            "hidden",
                            "data-active-scientific-module"
                        ]
                    }
                );
            }

            scheduleRestore();
        }
    );

    window.SyKScientificVisibilityGuard = {
        restore: scheduleRestore
    };
})();