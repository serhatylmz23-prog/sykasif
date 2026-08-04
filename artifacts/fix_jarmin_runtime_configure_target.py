from pathlib import Path
import ast


path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)

class_marker = "class JarminRuntime:"

class_start = text.find(
    class_marker
)

if class_start < 0:
    raise RuntimeError(
        "JarminRuntime sınıfı bulunamadı."
    )

start_method = text.find(
    "\n    def start(",
    class_start,
)

if start_method < 0:
    raise RuntimeError(
        "JarminRuntime.start ekleme noktası bulunamadı."
    )

class_prefix = text[
    class_start:start_method
]

configure_method = '''
    def configure(
        self,
        settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Kaşif çalışma ayarlarını günceller."""

        incoming = {
            **dict(settings or {}),
            **kwargs,
        }

        assistant_name = incoming.pop(
            "assistant_name",
            incoming.pop(
                "display_name",
                incoming.pop(
                    "name",
                    None,
                ),
            ),
        )

        maximum_history = incoming.pop(
            "maximum_history",
            incoming.pop(
                "history_limit",
                None,
            ),
        )

        wake_words = incoming.pop(
            "wake_words",
            None,
        )

        wake_word = incoming.pop(
            "wake_word",
            None,
        )

        if assistant_name is not None:
            resolved_name = str(
                assistant_name
            ).strip()

            if not resolved_name:
                raise ValueError(
                    "Asistan adı boş olamaz."
                )

            self.assistant_name = resolved_name
            self.name = resolved_name
            self.display_name = resolved_name

        if maximum_history is not None:
            resolved_limit = int(
                maximum_history
            )

            if resolved_limit <= 0:
                raise ValueError(
                    "Geçmiş sınırı pozitif olmalıdır."
                )

            self.maximum_history = resolved_limit

        voice_settings = {
            key: incoming.pop(key)
            for key in list(incoming)
            if key in {
                "language",
                "locale",
                "enabled",
                "sample_rate",
                "channels",
                "input_device",
                "output_device",
                "speech_to_text_enabled",
                "text_to_speech_enabled",
                "notification_sound_enabled",
            }
        }

        if wake_words is not None:
            voice_settings["wake_words"] = (
                wake_words
            )

        elif wake_word is not None:
            voice_settings["wake_word"] = (
                wake_word
            )

        else:
            voice_settings["wake_words"] = [
                "Kaşif",
                "Babuş",
            ]

        voice_configure = getattr(
            self.voice_runtime,
            "configure",
            None,
        )

        voice_snapshot = None

        if callable(voice_configure):
            voice_snapshot = voice_configure(
                **voice_settings
            )

        if not hasattr(
            self,
            "_settings",
        ):
            self._settings = {}

        self._settings.update(
            incoming
        )

        return {
            **self.snapshot(),
            "assistant_name": (
                self.assistant_name
            ),
            "wake_words": [
                "Kaşif",
                "Babuş",
            ],
            "voice": voice_snapshot,
            "applied_settings": {
                **incoming,
                **voice_settings,
            },
        }

'''

if "\n    def configure(" not in class_prefix:
    text = (
        text[:start_method]
        + configure_method
        + text[start_method:]
    )

path.write_text(
    text,
    encoding="utf-8",
)

ast.parse(
    path.read_text(
        encoding="utf-8"
    )
)

print("JARMIN_RUNTIME_CONFIGURE_TARGET_OK")
