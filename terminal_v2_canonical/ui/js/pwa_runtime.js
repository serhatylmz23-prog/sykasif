(() => {
  "use strict";

  const state = {
    online: navigator.onLine,
    installed: false,
    serviceWorker: false
  };

  function emit() {
    document.documentElement.dataset.sykNetwork =
      state.online ? "online" : "offline";

    window.dispatchEvent(
      new CustomEvent("syk:pwa-state", {
        detail: { ...state }
      })
    );
  }

  window.addEventListener("online", () => {
    state.online = true;
    emit();
  });

  window.addEventListener("offline", () => {
    state.online = false;
    emit();
  });

  window.addEventListener("appinstalled", () => {
    state.installed = true;
    emit();
  });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", async () => {
      try {
        const registration =
          await navigator.serviceWorker.register(
            "/service-worker.js",
            { scope: "/" }
          );

        state.serviceWorker = true;

        if (registration.waiting) {
          registration.waiting.postMessage({
            type: "SKIP_WAITING"
          });
        }

        emit();

        console.log(
          "[SyKaşif] PWA çevrim dışı çalışma katmanı aktif."
        );
      } catch (error) {
        console.error(
          "[SyKaşif] Service Worker başlatılamadı:",
          error
        );
      }
    });
  }

  window.SYK_PWA = {
    getState() {
      return { ...state };
    }
  };

  emit();
})();
