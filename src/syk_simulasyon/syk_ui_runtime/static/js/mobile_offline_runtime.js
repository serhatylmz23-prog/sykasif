(() => {
    "use strict";

    const API =
        "/api/syk-ui/mobile-offline";

    const DB_NAME =
        "sykasif-mobile-runtime";

    const DB_VERSION = 1;

    const STORE_QUEUE =
        "offline_queue";

    const STORE_CACHE =
        "local_cache";

    const PAIRING_TOKEN_KEY =
        "sykasif.mobile.pairing";

    const state = {
        online: navigator.onLine,
        syncing: false,
        database: null,
        lastSyncAt: null,
        syncTimer: null,
    };

    function deviceId() {
        return (
            window.SyKMobileRuntime
                ?.snapshot()
                ?.deviceId
            || localStorage.getItem(
                "sykasif.mobile.device_id"
            )
            || "SYK-WEB-UNKNOWN"
        );
    }

    async function fetchJson(
        url,
        options = {}
    ) {
        const response = await fetch(
            url,
            {
                headers: {
                    "Content-Type":
                        "application/json",
                    Accept:
                        "application/json",
                    ...(options.headers || {}),
                },
                ...options,
            }
        );

        let payload = {};

        try {
            payload =
                await response.json();
        }
        catch {
        }

        if (!response.ok) {
            throw new Error(
                payload.detail
                || "Çevrimdışı işlem başarısız."
            );
        }

        return payload;
    }

    function openDatabase() {
        if (state.database) {
            return Promise.resolve(
                state.database
            );
        }

        return new Promise(
            (resolve, reject) => {
                const request =
                    indexedDB.open(
                        DB_NAME,
                        DB_VERSION
                    );

                request.onerror =
                    () => reject(
                        request.error
                    );

                request.onupgradeneeded =
                    event => {
                        const database =
                            event.target
                                .result;

                        if (
                            !database
                                .objectStoreNames
                                .contains(
                                    STORE_QUEUE
                                )
                        ) {
                            const store =
                                database
                                    .createObjectStore(
                                        STORE_QUEUE,
                                        {
                                            keyPath:
                                                "local_id",
                                        }
                                    );

                            store.createIndex(
                                "status",
                                "status",
                                {
                                    unique:
                                        false,
                                }
                            );

                            store.createIndex(
                                "created_at",
                                "created_at",
                                {
                                    unique:
                                        false,
                                }
                            );
                        }

                        if (
                            !database
                                .objectStoreNames
                                .contains(
                                    STORE_CACHE
                                )
                        ) {
                            database
                                .createObjectStore(
                                    STORE_CACHE,
                                    {
                                        keyPath:
                                            "cache_key",
                                    }
                                );
                        }
                    };

                request.onsuccess =
                    () => {
                        state.database =
                            request.result;

                        resolve(
                            state.database
                        );
                    };
            }
        );
    }

    async function transaction(
        storeName,
        mode,
        handler
    ) {
        const database =
            await openDatabase();

        return new Promise(
            (resolve, reject) => {
                const tx =
                    database.transaction(
                        storeName,
                        mode
                    );

                const store =
                    tx.objectStore(
                        storeName
                    );

                let result;

                try {
                    result =
                        handler(
                            store
                        );
                }
                catch (error) {
                    reject(error);
                    return;
                }

                tx.oncomplete =
                    () => resolve(
                        result
                    );

                tx.onerror =
                    () => reject(
                        tx.error
                    );

                tx.onabort =
                    () => reject(
                        tx.error
                    );
            }
        );
    }

    function requestResult(
        request
    ) {
        return new Promise(
            (resolve, reject) => {
                request.onsuccess =
                    () => resolve(
                        request.result
                    );

                request.onerror =
                    () => reject(
                        request.error
                    );
            }
        );
    }

    async function storeQueueItem(
        item
    ) {
        await transaction(
            STORE_QUEUE,
            "readwrite",
            store => {
                store.put(item);
            }
        );

        dispatchQueueChanged();

        return item;
    }

    async function getQueueItems() {
        const database =
            await openDatabase();

        const tx =
            database.transaction(
                STORE_QUEUE,
                "readonly"
            );

        return requestResult(
            tx.objectStore(
                STORE_QUEUE
            ).getAll()
        );
    }

    async function deleteQueueItem(
        localId
    ) {
        await transaction(
            STORE_QUEUE,
            "readwrite",
            store => {
                store.delete(localId);
            }
        );

        dispatchQueueChanged();
    }

    async function enqueue(
        {
            itemType,
            endpoint,
            method = "POST",
            payload = {},
            maximumAttempts = 5,
        }
    ) {
        const localItem = {
            local_id:
                crypto.randomUUID(),

            item_type:
                itemType,

            device_id:
                deviceId(),

            endpoint,

            method:
                String(method)
                    .toUpperCase(),

            payload,

            maximum_attempts:
                maximumAttempts,

            attempt_count: 0,

            status: "pending",

            last_error: null,

            created_at:
                new Date()
                    .toISOString(),

            updated_at:
                new Date()
                    .toISOString(),
        };

        await storeQueueItem(
            localItem
        );

        if (state.online) {
            scheduleSync(100);
        }

        return localItem;
    }

    async function sync() {
        if (
            state.syncing
            || !navigator.onLine
        ) {
            return {
                synced: 0,
                failed: 0,
            };
        }

        state.syncing = true;

        document.body.dataset
            .sykOfflineSync =
                "running";

        let synced = 0;
        let failed = 0;

        try {
            const items =
                await getQueueItems();

            const pending = items
                .filter(
                    item =>
                        item.status
                        !== "completed"
                )
                .sort(
                    (a, b) =>
                        a.created_at
                            .localeCompare(
                                b.created_at
                            )
                );

            for (
                const item
                of pending
            ) {
                try {
                    item.status =
                        "processing";

                    item.attempt_count +=
                        1;

                    item.updated_at =
                        new Date()
                            .toISOString();

                    await storeQueueItem(
                        item
                    );

                    const response =
                        await fetch(
                            item.endpoint,
                            {
                                method:
                                    item.method,
                                headers: {
                                    "Content-Type":
                                        "application/json",
                                    Accept:
                                        "application/json",
                                },
                                body:
                                    item.method
                                    === "DELETE"
                                        ? undefined
                                        : JSON.stringify(
                                            item.payload
                                        ),
                            }
                        );

                    if (!response.ok) {
                        throw new Error(
                            `${response.status} `
                            + response
                                .statusText
                        );
                    }

                    await deleteQueueItem(
                        item.local_id
                    );

                    synced += 1;
                }
                catch (error) {
                    item.last_error =
                        error.message;

                    item.updated_at =
                        new Date()
                            .toISOString();

                    item.status =
                        item.attempt_count
                        >= item
                            .maximum_attempts
                            ? "cancelled"
                            : "failed";

                    await storeQueueItem(
                        item
                    );

                    failed += 1;
                }
            }

            state.lastSyncAt =
                new Date()
                    .toISOString();

            document.dispatchEvent(
                new CustomEvent(
                    "syk:offline-sync-completed",
                    {
                        detail: {
                            synced,
                            failed,
                            completed_at:
                                state
                                    .lastSyncAt,
                        },
                    }
                )
            );

            return {
                synced,
                failed,
            };
        }
        finally {
            state.syncing = false;

            document.body.dataset
                .sykOfflineSync =
                    "idle";
        }
    }

    function scheduleSync(
        delay = 500
    ) {
        clearTimeout(
            state.syncTimer
        );

        state.syncTimer =
            setTimeout(
                () => {
                    sync().catch(
                        () => {}
                    );
                },
                delay
            );
    }

    async function updateOnlineState() {
        state.online =
            navigator.onLine;

        document.body.dataset
            .sykConnection =
                state.online
                    ? "online"
                    : "offline";

        await fetchJson(
            `${API}/online`,
            {
                method: "PATCH",
                body: JSON.stringify({
                    online:
                        state.online,
                }),
            }
        ).catch(
            () => null
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:connection-changed",
                {
                    detail: {
                        online:
                            state.online,
                    },
                }
            )
        );

        if (state.online) {
            scheduleSync(100);
        }
    }

    async function createPairing(
        title = "SyKaşif Cihazı"
    ) {
        const result =
            await fetchJson(
                `${API}/pairings`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        requesting_device_id:
                            deviceId(),
                        requesting_device_title:
                            title,
                        target_role:
                            "trusted_terminal",
                    }),
                }
            );

        document.dispatchEvent(
            new CustomEvent(
                "syk:pairing-created",
                {
                    detail: result,
                }
            )
        );

        return result;
    }

    async function confirmPairing(
        pairingCode
    ) {
        const result =
            await fetchJson(
                `${API}/pairings/confirm`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        pairing_code:
                            pairingCode,
                        paired_device_id:
                            deviceId(),
                    }),
                }
            );

        localStorage.setItem(
            PAIRING_TOKEN_KEY,
            JSON.stringify({
                pairing_id:
                    result
                        .pairing
                        .pairing_id,
                pairing_token:
                    result
                        .pairing_token,
                paired_at:
                    result
                        .pairing
                        .paired_at,
            })
        );

        document.dispatchEvent(
            new CustomEvent(
                "syk:pairing-confirmed",
                {
                    detail:
                        result.pairing,
                }
            )
        );

        return result;
    }

    async function verifyPairing() {
        const stored =
            localStorage.getItem(
                PAIRING_TOKEN_KEY
            );

        if (!stored) {
            return false;
        }

        let payload;

        try {
            payload =
                JSON.parse(stored);
        }
        catch {
            localStorage.removeItem(
                PAIRING_TOKEN_KEY
            );

            return false;
        }

        const result =
            await fetchJson(
                `${API}/pairings/verify`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        pairing_id:
                            payload
                                .pairing_id,
                        pairing_token:
                            payload
                                .pairing_token,
                    }),
                }
            ).catch(
                () => ({
                    valid: false,
                })
            );

        if (!result.valid) {
            localStorage.removeItem(
                PAIRING_TOKEN_KEY
            );
        }

        return result.valid;
    }

    async function cachePut(
        cacheKey,
        category,
        value,
        lifetimeSeconds = null
    ) {
        const entry = {
            cache_key:
                cacheKey,

            category,

            value,

            expires_at:
                lifetimeSeconds
                ? (
                    Date.now()
                    + lifetimeSeconds
                    * 1000
                )
                : null,

            updated_at:
                new Date()
                    .toISOString(),
        };

        await transaction(
            STORE_CACHE,
            "readwrite",
            store => {
                store.put(entry);
            }
        );

        if (state.online) {
            fetchJson(
                `${API}/cache`,
                {
                    method: "PUT",
                    body: JSON.stringify({
                        cache_key:
                            cacheKey,
                        category,
                        value,
                        lifetime_seconds:
                            lifetimeSeconds,
                    }),
                }
            ).catch(
                () => {}
            );
        }

        return entry;
    }

    async function cacheGet(
        cacheKey
    ) {
        const database =
            await openDatabase();

        const tx =
            database.transaction(
                STORE_CACHE,
                "readonly"
            );

        const entry =
            await requestResult(
                tx.objectStore(
                    STORE_CACHE
                ).get(
                    cacheKey
                )
            );

        if (!entry) {
            return null;
        }

        if (
            entry.expires_at
            && entry.expires_at
                <= Date.now()
        ) {
            await cacheDelete(
                cacheKey
            );

            return null;
        }

        return entry;
    }

    async function cacheDelete(
        cacheKey
    ) {
        await transaction(
            STORE_CACHE,
            "readwrite",
            store => {
                store.delete(
                    cacheKey
                );
            }
        );

        return true;
    }

    function dispatchQueueChanged() {
        getQueueItems()
            .then(
                items => {
                    document.dispatchEvent(
                        new CustomEvent(
                            "syk:offline-queue-changed",
                            {
                                detail: {
                                    count:
                                        items
                                            .length,
                                    items,
                                },
                            }
                        )
                    );
                }
            )
            .catch(
                () => {}
            );
    }

    async function interceptEvent(
        eventType,
        endpoint,
        payload
    ) {
        if (navigator.onLine) {
            try {
                const response =
                    await fetch(
                        endpoint,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                                Accept:
                                    "application/json",
                            },
                            body:
                                JSON.stringify(
                                    payload
                                ),
                        }
                    );

                if (response.ok) {
                    return {
                        queued: false,
                        sent: true,
                    };
                }
            }
            catch {
            }
        }

        await enqueue({
            itemType:
                eventType,
            endpoint,
            method: "POST",
            payload,
        });

        return {
            queued: true,
            sent: false,
        };
    }

    function bindSyKEvents() {
        document.addEventListener(
            "syk:mobile-frame-captured",
            event => {
                cachePut(
                    `frame:${
                        event
                            .detail
                            .frame_id
                    }`,
                    "frame",
                    event.detail,
                    86400
                ).catch(
                    () => {}
                );
            }
        );

        document.addEventListener(
            "syk:location-updated",
            event => {
                cachePut(
                    "location:latest",
                    "location",
                    event.detail,
                    3600
                ).catch(
                    () => {}
                );
            }
        );

        document.addEventListener(
            "syk:sealed-report-created",
            event => {
                interceptEvent(
                    "report",
                    "/api/syk-ui/jarmin/integration/events",
                    {
                        event_type:
                            "report_created",
                        source:
                            "mobile_offline_runtime",
                        message:
                            "Mühürlü rapor çevrimdışı kuyruktan aktarıldı.",
                        payload:
                            event.detail
                            || {},
                    }
                );
            }
        );

        document.addEventListener(
            "syk:dtse-evidence",
            event => {
                interceptEvent(
                    "evidence",
                    "/api/syk-ui/jarmin/integration/events",
                    {
                        event_type:
                            "dtse_evidence",
                        source:
                            "mobile_offline_runtime",
                        message:
                            "DTSE kanıt kaydı çevrimdışı kuyruktan aktarıldı.",
                        payload:
                            event.detail
                            || {},
                    }
                );
            }
        );
    }

    function snapshot() {
        return {
            online:
                state.online,
            syncing:
                state.syncing,
            lastSyncAt:
                state.lastSyncAt,
            databaseReady:
                Boolean(
                    state.database
                ),
        };
    }

    async function start() {
        await openDatabase();

        bindSyKEvents();

        window.addEventListener(
            "online",
            updateOnlineState
        );

        window.addEventListener(
            "offline",
            updateOnlineState
        );

        await updateOnlineState();

        verifyPairing()
            .then(
                valid => {
                    document.body.dataset
                        .sykDevicePaired =
                            String(
                                valid
                            );
                }
            )
            .catch(
                () => {}
            );

        dispatchQueueChanged();
    }

    window.SyKMobileOffline = {
        enqueue,
        sync,
        createPairing,
        confirmPairing,
        verifyPairing,
        cachePut,
        cacheGet,
        cacheDelete,
        snapshot,
    };

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            start().catch(
                () => {
                    document.body.dataset
                        .sykOfflineRuntime =
                            "error";
                }
            );
        },
        {
            once: true,
        }
    );
})();