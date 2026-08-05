from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class NmeaParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NmeaSentence:
    talker: str
    sentence_type: str
    fields: tuple[str, ...]
    checksum: str | None
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "talker": self.talker,
            "sentence_type": self.sentence_type,
            "fields": list(self.fields),
            "checksum": self.checksum,
            "raw": self.raw,
        }


def calculate_checksum(payload: str) -> str:
    value = 0

    for character in payload:
        value ^= ord(character)

    return f"{value:02X}"


def parse_nmea_sentence(
    sentence: str,
    *,
    validate_checksum: bool = True,
) -> NmeaSentence:
    clean = sentence.strip()

    if not clean.startswith("$"):
        raise NmeaParseError(
            "NMEA cÃ¼mlesi '$' iÅŸaretiyle baÅŸlamalÄ±dÄ±r."
        )

    body = clean[1:]
    checksum: str | None = None

    if "*" in body:
        body, checksum = body.rsplit("*", 1)
        checksum = checksum.upper()

        if len(checksum) != 2:
            raise NmeaParseError(
                "NMEA checksum uzunluÄŸu hatalÄ±dÄ±r."
            )

        if validate_checksum:
            expected = calculate_checksum(body)

            if checksum != expected:
                raise NmeaParseError(
                    "NMEA checksum doÄŸrulamasÄ± baÅŸarÄ±sÄ±z."
                )

    parts = body.split(",")

    if not parts or len(parts[0]) < 5:
        raise NmeaParseError(
            "NMEA cÃ¼mle baÅŸlÄ±ÄŸÄ± geÃ§ersizdir."
        )

    header = parts[0]

    return NmeaSentence(
        talker=header[:2],
        sentence_type=header[2:],
        fields=tuple(parts[1:]),
        checksum=checksum,
        raw=clean,
    )


def parse_depth_meters(
    sentence: NmeaSentence,
) -> float | None:
    if sentence.sentence_type == "DPT":
        if not sentence.fields:
            return None

        return _to_float(
            sentence.fields[0]
        )

    if sentence.sentence_type == "DBT":
        if len(sentence.fields) >= 4:
            return _to_float(
                sentence.fields[3]
            )

    return None


def parse_water_temperature_c(
    sentence: NmeaSentence,
) -> float | None:
    if sentence.sentence_type != "MTW":
        return None

    if not sentence.fields:
        return None

    return _to_float(
        sentence.fields[0]
    )


def _to_float(
    value: str,
) -> float | None:
    clean = value.strip()

    if not clean:
        return None

    try:
        return float(clean)
    except ValueError as error:
        raise NmeaParseError(
            f"SayÄ±sal NMEA alanÄ± geÃ§ersiz: {clean}"
        ) from error