import asyncio

import pytest

from terminal_v2.core.runtime_state import RuntimeState


def run(coroutine):
    return asyncio.run(coroutine)


def test_runtime_state_initial_snapshot():
    state = RuntimeState()

    snapshot = run(state.snapshot())

    assert snapshot["revision"] == 0
    assert (
        snapshot["durum"]["sistem"]["durum"]
        == "BEKLIYOR"
    )
    assert (
        snapshot["durum"]["cihazlar"]["masaustu"]["bagli"]
        is True
    )


def test_runtime_state_device_connection():
    state = RuntimeState()

    snapshot = run(
        state.set_device(
            cihaz_turu="tablet",
            bagli=True,
        )
    )

    assert snapshot["revision"] == 1
    assert (
        snapshot["durum"]["cihazlar"]["tablet"]["bagli"]
        is True
    )
    assert (
        snapshot["durum"]["cihazlar"]["tablet"]["durum"]
        == "CALISIYOR"
    )


def test_runtime_state_active_module():
    state = RuntimeState()

    snapshot = run(
        state.set_active_module(
            "analysis",
            kaynak="masaustu",
        )
    )

    assert (
        snapshot["durum"]["aktif_modul"]
        == "analysis"
    )
    assert (
        snapshot["durum"]["moduller"]["analysis"]["durum"]
        == "CALISIYOR"
    )


def test_runtime_state_turkish_status():
    state = RuntimeState()

    snapshot = run(
        state.set_system_status(
            durum="DOGRULANIYOR",
            mesaj="Saha verileri doğrulanıyor.",
            kaynak="tablet",
        )
    )

    assert (
        snapshot["durum"]["sistem"]["durum"]
        == "DOGRULANIYOR"
    )
    assert (
        snapshot["durum"]["sistem"]["mesaj"]
        == "Saha verileri doğrulanıyor."
    )


def test_runtime_state_rejects_invalid_status():
    state = RuntimeState()

    with pytest.raises(ValueError):
        run(
            state.set_system_status(
                durum="GECERSIZ",
                mesaj="Geçersiz durum.",
            )
        )


def test_runtime_state_listener_receives_change():
    state = RuntimeState()
    received = []

    async def scenario():
        async def listener(snapshot):
            received.append(snapshot)

        await state.subscribe(listener)

        await state.set_device(
            cihaz_turu="telefon",
            bagli=True,
        )

        await state.unsubscribe(listener)

    run(scenario())

    assert len(received) == 1
    assert received[0]["revision"] == 1
    assert (
        received[0]["durum"]["cihazlar"]["telefon"]["bagli"]
        is True
    )


def test_runtime_state_reset():
    state = RuntimeState()

    async def scenario():
        await state.set_device(
            cihaz_turu="tablet",
            bagli=True,
        )

        return await state.reset()

    snapshot = run(scenario())

    assert snapshot["revision"] == 0
    assert (
        snapshot["durum"]["cihazlar"]["tablet"]["bagli"]
        is False
    )
