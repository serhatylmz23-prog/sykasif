(() => {
    "use strict";

    const DB_NAME = "sykasif_terminal_v2";
    const DB_VERSION = 1;
    const STORE_NAME = "offline_queue";

    function veritabaniAc() {
        return new Promise((resolve, reject) => {

            const request =
                indexedDB.open(
                    DB_NAME,
                    DB_VERSION
                );

            request.onupgradeneeded = () => {

                const db =
                    request.result;

                if (
                    !db.objectStoreNames.contains(
                        STORE_NAME
                    )
                ) {
                    db.createObjectStore(
                        STORE_NAME,
                        {
                            keyPath: "id",
                            autoIncrement: true
                        }
                    );
                }
            };

            request.onsuccess =
                () => resolve(
                    request.result
                );

            request.onerror =
                () => reject(
                    request.error
                );
        });
    }

    async function kuyruğaEkle(
        tur,
        veri
    ) {

        const db =
            await veritabaniAc();

        return new Promise(
            (resolve, reject) => {

                const tx =
                    db.transaction(
                        STORE_NAME,
                        "readwrite"
                    );

                const store =
                    tx.objectStore(
                        STORE_NAME
                    );

                store.add({
                    tur,
                    veri,
                    olusturulma:
                        new Date().toISOString(),

                    senkronize:
                        false
                });

                tx.oncomplete =
                    () => resolve(true);

                tx.onerror =
                    () => reject(
                        tx.error
                    );
            }
        );
    }

    async function tumunuGetir() {

        const db =
            await veritabaniAc();

        return new Promise(
            (resolve, reject) => {

                const tx =
                    db.transaction(
                        STORE_NAME,
                        "readonly"
                    );

                const request =
                    tx.objectStore(
                        STORE_NAME
                    ).getAll();

                request.onsuccess =
                    () => resolve(
                        request.result || []
                    );

                request.onerror =
                    () => reject(
                        request.error
                    );
            }
        );
    }

    async function kaydiSil(id) {

        const db =
            await veritabaniAc();

        return new Promise(
            (resolve, reject) => {

                const tx =
                    db.transaction(
                        STORE_NAME,
                        "readwrite"
                    );

                tx.objectStore(
                    STORE_NAME
                ).delete(id);

                tx.oncomplete =
                    () => resolve(true);

                tx.onerror =
                    () => reject(
                        tx.error
                    );
            }
        );
    }

    async function kuyrukSayisi() {

        const db =
            await veritabaniAc();

        return new Promise(
            (resolve, reject) => {

                const tx =
                    db.transaction(
                        STORE_NAME,
                        "readonly"
                    );

                const request =
                    tx.objectStore(
                        STORE_NAME
                    ).count();

                request.onsuccess =
                    () => resolve(
                        request.result || 0
                    );

                request.onerror =
                    () => reject(
                        request.error
                    );
            }
        );
    }

    window.SYK_OFFLINE = {
        ekle: kuyruğaEkle,
        tumunuGetir,
        sil: kaydiSil,
        sayi: kuyrukSayisi
    };

    document.documentElement
        .dataset.sykOfflineStore =
        "ready";

    console.info(
        "[SyKaşif] Çevrim dışı veri kuyruğu hazır."
    );
})();
