from __future__ import annotations

from typing import Any

from syk_jarmin.runtime.event_bridge import (
    JarminEventBridge,
)
from syk_jarmin.runtime.persistent_settings import (
    PersistentJarminSettings,
)
from syk_jarmin.runtime.runtime import (
    JarminRuntime,
    jarmin_runtime,
)
from syk_jarmin.runtime.system_adapters import (
    JarminSystemAdapters,
)


class JarminIntegrationRuntime:
    def __init__(
        self,
        *,
        runtime: JarminRuntime | None = None,
        settings: (
            PersistentJarminSettings
            | None
        ) = None,
        event_bridge: (
            JarminEventBridge | None
        ) = None,
        adapters: (
            JarminSystemAdapters | None
        ) = None,
    ) -> None:
        self.runtime = (
            runtime or jarmin_runtime
        )

        self.settings = (
            settings
            or PersistentJarminSettings()
        )

        self.event_bridge = (
            event_bridge
            or JarminEventBridge(
                self.runtime.notifications
            )
        )

        self.adapters = (
            adapters
            or JarminSystemAdapters()
        )

        self._connect_command_handlers()
        self.apply_settings()

    def _connect_command_handlers(
        self,
    ) -> None:
        commands = (
            self.runtime
            .assistant
            .core
            .commands
        )

        commands.register(
            "theme_change",
            self.adapters.theme_change,
        )

        commands.register(
            "system_status",
            self.adapters.system_status,
        )

    def apply_settings(
        self,
    ) -> dict[str, Any]:
        settings = self.settings.get()

        self.runtime.assistant.configure(
            active=True,
            voice_enabled=(
                settings.voice_enabled
            ),
            notification_enabled=(
                settings
                .notification_enabled
            ),
        )

        self.runtime.voice.configure(
            profile_id=(
                settings.voice_profile_id
            ),
            language=settings.language,
        )

        return self.snapshot()

    def update_settings(
        self,
        **changes: Any,
    ) -> dict[str, Any]:
        self.settings.update(
            **changes
        )

        return self.apply_settings()

    def ingest_event(
        self,
        *,
        event_type: str,
        source: str,
        message: str,
        payload: dict[str, Any] | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        event = self.event_bridge.publish(
            event_type=event_type,
            source=source,
            message=message,
            payload=payload,
            title=title,
        )

        return event.as_dict()

    def snapshot(
        self,
    ) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-jarmin-integration/v1"
            ),
            "runtime": (
                self.runtime.snapshot()
            ),
            "settings": (
                self.settings.snapshot()
            ),
            "events": (
                self.event_bridge.snapshot()
            ),
            "status": "ready",
        }


def _build_default() -> (
    JarminIntegrationRuntime
):
    adapters = JarminSystemAdapters()

    try:
        from syk_simulasyon.syk_ui_runtime.theme_engine import (
            theme_engine,
        )

        adapters.theme_runtime = (
            theme_engine.runtime
        )

    except (
        ImportError,
        AttributeError,
    ):
        pass

    try:
        from syk_simulasyon.syk_ui_runtime.adaptive_environment_routes import (
            adaptive_environment,
        )

        adapters.environment = (
            adaptive_environment
        )

    except (
        ImportError,
        AttributeError,
    ):
        pass

    return JarminIntegrationRuntime(
        adapters=adapters
    )


jarmin_integration_runtime = (
    _build_default()
)