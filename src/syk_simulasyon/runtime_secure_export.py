from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol


_PROCESS_SECRET = secrets.token_bytes(32)


class ExportRole(StrEnum):
    """Authorization level used while producing external records."""

    INTERNAL = "internal"
    PARTNER = "partner"
    PUBLIC = "public"


@dataclass(frozen=True)
class ExportSecurityProfile:
    """Security policy for one export operation."""

    role: ExportRole
    export_id: str
    secret: bytes

    @classmethod
    def from_environment(
        cls,
        role: ExportRole = ExportRole.PUBLIC,
        export_id: str | None = None,
    ) -> "ExportSecurityProfile":
        raw_secret = os.getenv("SYK_EXPORT_SECRET")

        secret = (
            raw_secret.encode("utf-8")
            if raw_secret
            else _PROCESS_SECRET
        )

        resolved_export_id = (
            export_id
            or os.getenv("SYK_EXPORT_ID")
            or uuid.uuid4().hex
        )

        return cls(
            role=role,
            export_id=resolved_export_id,
            secret=secret,
        )


class _DictionaryRecord(Protocol):
    def sozluk(self) -> dict[str, Any]:
        ...


class _ViewProvider(Protocol):
    def gorunum(self) -> _DictionaryRecord:
        ...


@dataclass(frozen=True)
class SecureExportRecord:
    data: dict[str, Any]

    def sozluk(self) -> dict[str, Any]:
        return dict(self.data)


class SecureExportViewProvider:
    """Builds an authorization-aware, opaque external view."""

    _PARTNER_FIELDS = frozenset(
        {
            "durum",
            "ilerleme_yuzdesi",
            "guncelleme_zamani",
            "olay_sayisi",
            "son_olay_kodu",
        }
    )

    _PUBLIC_FIELDS = frozenset(
        {
            "durum",
            "ilerleme_yuzdesi",
            "guncelleme_zamani",
            "olay_sayisi",
        }
    )

    def __init__(
        self,
        source: _ViewProvider,
        profile: ExportSecurityProfile,
    ) -> None:
        self._source = source
        self._profile = profile

    def gorunum(self) -> SecureExportRecord:
        raw = self._source.gorunum().sozluk()

        return SecureExportRecord(
            self._transform_mapping(
                raw,
                path="root",
            )
        )

    def _transform_mapping(
        self,
        source: Mapping[str, Any],
        path: str,
    ) -> dict[str, Any]:
        output: dict[str, Any] = {}

        for field_name, value in source.items():
            if not self._is_allowed(field_name):
                continue

            field_path = f"{path}.{field_name}"

            external_name = self._opaque_token(
                namespace="field",
                value=field_path,
                length=10,
            )

            output[external_name] = self._transform_value(
                field_name=field_name,
                value=value,
                path=field_path,
            )

        return output

    def _transform_value(
        self,
        field_name: str,
        value: Any,
        path: str,
    ) -> Any:
        if isinstance(value, Mapping):
            return self._transform_mapping(
                value,
                path,
            )

        if isinstance(value, list):
            return [
                self._transform_value(
                    field_name,
                    item,
                    f"{path}[{index}]",
                )
                for index, item in enumerate(value)
            ]

        if value is None or isinstance(
            value,
            (bool, int, float),
        ):
            return value

        if self._profile.role is ExportRole.INTERNAL:
            return value

        return self._opaque_token(
            namespace="value",
            value=f"{path}:{value}",
            length=16,
        )

    def _is_allowed(
        self,
        field_name: str,
    ) -> bool:
        if self._profile.role is ExportRole.INTERNAL:
            return True

        if self._profile.role is ExportRole.PARTNER:
            return field_name in self._PARTNER_FIELDS

        return field_name in self._PUBLIC_FIELDS

    def _opaque_token(
        self,
        namespace: str,
        value: str,
        length: int,
    ) -> str:
        payload = (
            f"{namespace}|"
            f"{self._profile.export_id}|"
            f"{value}"
        ).encode("utf-8")

        digest = hmac.new(
            self._profile.secret,
            payload,
            hashlib.sha256,
        ).digest()

        token = (
            base64.b32encode(digest)
            .decode("ascii")
            .rstrip("=")
        )

        return token[:length]
