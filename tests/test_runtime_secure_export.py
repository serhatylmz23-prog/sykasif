from dataclasses import dataclass

from syk_simulasyon.runtime_secure_export import (
    ExportRole,
    ExportSecurityProfile,
    SecureExportViewProvider,
)


@dataclass(frozen=True)
class _Record:

    def sozluk(self):
        return {
            "durum": "haz?r",
            "aktif_modul": "runtime",
            "ilerleme_yuzdesi": 42.5,
            "guncelleme_zamani": (
                "2026-07-30T10:30:00+03:00"
            ),
            "olay_sayisi": 7,
            "son_olay_kodu": "EVT-001",
        }


class _Provider:

    def gorunum(self):
        return _Record()


def _profile(
    role,
    export_id="batch-a",
):
    return ExportSecurityProfile(
        role=role,
        export_id=export_id,
        secret=b"test-secret-only",
    )


def test_public_export_hides_internal_field_names_and_text_values():
    result = SecureExportViewProvider(
        _Provider(),
        _profile(ExportRole.PUBLIC),
    ).gorunum().sozluk()

    serialized = str(result)

    assert "durum" not in serialized
    assert "aktif_modul" not in serialized
    assert "haz?r" not in serialized
    assert "runtime" not in serialized
    assert 42.5 in result.values()
    assert 7 in result.values()


def test_partner_export_has_more_fields_than_public_export():
    public = SecureExportViewProvider(
        _Provider(),
        _profile(ExportRole.PUBLIC),
    ).gorunum().sozluk()

    partner = SecureExportViewProvider(
        _Provider(),
        _profile(ExportRole.PARTNER),
    ).gorunum().sozluk()

    assert len(partner) > len(public)


def test_mapping_rotates_between_export_operations():
    first = SecureExportViewProvider(
        _Provider(),
        _profile(
            ExportRole.PUBLIC,
            "batch-a",
        ),
    ).gorunum().sozluk()

    second = SecureExportViewProvider(
        _Provider(),
        _profile(
            ExportRole.PUBLIC,
            "batch-b",
        ),
    ).gorunum().sozluk()

    assert first != second


def test_mapping_is_stable_inside_same_export_operation():
    first = SecureExportViewProvider(
        _Provider(),
        _profile(
            ExportRole.PUBLIC,
            "batch-a",
        ),
    ).gorunum().sozluk()

    second = SecureExportViewProvider(
        _Provider(),
        _profile(
            ExportRole.PUBLIC,
            "batch-a",
        ),
    ).gorunum().sozluk()

    assert first == second


def test_internal_role_preserves_values_but_masks_field_names():
    result = SecureExportViewProvider(
        _Provider(),
        _profile(ExportRole.INTERNAL),
    ).gorunum().sozluk()

    assert "durum" not in result
    assert "haz?r" in result.values()
    assert "runtime" in result.values()
