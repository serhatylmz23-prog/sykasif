from pathlib import Path
import ast


path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

text = path.read_text(
    encoding="utf-8"
)


voice_class = '''
class _KasifVoiceCompatibilityRuntime:
    """Kaşif ses ayarları için uyumluluk katmanı."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {
            "language": "tr-TR",
            "wake_words": [
                "Kaşif",
                "Babuş",
            ],
        }

    def configure(
        self,
        settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        incoming = {
            **dict(settings or {}),
            **kwargs,
        }

        wake_word = incoming.pop(
            "wake_word",
            None,
        )

        wake_words = incoming.pop(
            "wake_words",
            None,
        )

        if wake_words is not None:
            resolved = [
                str(value).strip()
                for value in wake_words
                if str(value).strip()
            ]

            if resolved:
                self.settings[
                    "wake_words"
                ] = resolved

        elif wake_word is not None:
            resolved = str(
                wake_word
            ).strip()

            if resolved:
                current = list(
                    self.settings.get(
                        "wake_words",
                        [],
                    )
                )

                if resolved not in current:
                    current.insert(
                        0,
                        resolved,
                    )

                self.settings[
                    "wake_words"
                ] = current

        self.settings.update(
            incoming
        )

        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-kasif-voice-compatibility/v1"
            ),
            "assistant_name": "Kaşif",
            "settings": dict(
                self.settings
            ),
            "status": "ready",
        }


'''


if (
    "class _KasifVoiceCompatibilityRuntime:"
    not in text
):
    anchor = "class JarminRuntime:"

    if anchor not in text:
        raise RuntimeError(
            "JarminRuntime sınıfı bulunamadı."
        )

    text = text.replace(
        anchor,
        voice_class + anchor,
        1,
    )


old_voice = (
    "        self.voice_runtime = "
    "voice_runtime\n"
)

new_voice = '''        if voice_runtime is None:
            voice_runtime = (
                _KasifVoiceCompatibilityRuntime()
            )

        self.voice_runtime = voice_runtime
'''

if (
    old_voice in text
    and (
        "_KasifVoiceCompatibilityRuntime()"
        not in text.split(
            old_voice,
            1,
        )[0][-400:]
    )
):
    text = text.replace(
        old_voice,
        new_voice,
        1,
    )


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

        if assistant_name is not None:
            resolved_name = str(
                assistant_name
            ).strip()

            if not resolved_name:
                raise ValueError(
                    "Asistan adı boş olamaz."
                )

            self.assistant_name = (
                resolved_name
            )

            self.name = resolved_name
            self.display_name = (
                resolved_name
            )

        if maximum_history is not None:
            resolved_limit = int(
                maximum_history
            )

            if resolved_limit <= 0:
                raise ValueError(
                    "Geçmiş sınırı pozitif "
                    "olmalıdır."
                )

            self.maximum_history = (
                resolved_limit
            )

        wake_words = incoming.pop(
            "wake_words",
            None,
        )

        wake_word = incoming.pop(
            "wake_word",
            None,
        )

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
            voice_settings[
                "wake_words"
            ] = wake_words

        elif wake_word is not None:
            voice_settings[
                "wake_word"
            ] = wake_word

        # Kaşif ve Babuş varsayılan
        # uyandırma sözcükleridir.
        if (
            "wake_words"
            not in voice_settings
            and "wake_word"
            not in voice_settings
        ):
            voice_settings[
                "wake_words"
            ] = [
                "Kaşif",
                "Babuş",
            ]

        voice_snapshot = None

        voice_configure = getattr(
            self.voice_runtime,
            "configure",
            None,
        )

        if callable(voice_configure):
            voice_snapshot = (
                voice_configure(
                    **voice_settings
                )
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


if "\n    def configure(\n" not in text:
    anchor = "\n    def start("

    if anchor not in text:
        raise RuntimeError(
            "configure metodu için "
            "ekleme noktası bulunamadı."
        )

    text = text.replace(
        anchor,
        configure_method + anchor,
        1,
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

print(
    "KASIF_CONFIGURE_AND_VOICE_PATCH_OK"
)
