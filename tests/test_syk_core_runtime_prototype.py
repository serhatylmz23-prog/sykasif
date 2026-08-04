from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from syk_core.runtime_prototype import (
    PrototipAyarlari,
    PrototipDurumu,
    PrototipGuvenlikAyarlari,
    PrototipHatasi,
    SyKasifBirlesikPrototip,
)
from syk_core.runtime_terminal import (
    CanliSunucuAyarlari,
    TerminalUygulamasiAyarlari,
)


def ayarlar_olustur(
    tmp_path: Path,
    *,
    canli: bool = False,
) -> PrototipAyarlari:
    varsayilan = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    terminal = TerminalUygulamasiAyarlari(
        ana_makine="127.0.0.1",
        baglanti_noktasi=8714,
        panel_yolu="/terminal",
        panel_veri_yolu="/terminal/veri",
        dis_ag_erisimine_izin_ver=False,
        ana_makine_cihaz_kimligi=(
            varsayilan
            .ana_makine_cihaz_kimligi
        ),
        sykasif_uygulama_kimligi=(
            varsayilan
            .sykasif_uygulama_kimligi
        ),
        sykasif_calistirma_yolu=str(
            tmp_path
        ),
        durum_dosyasi=str(
            tmp_path
            / "birlesik_prototip.json"
        ),
        yetkili_cihazlar=(
            varsayilan.yetkili_cihazlar
        ),
    )

    canli_sunucu = None

    if canli:
        canli_sunucu = CanliSunucuAyarlari(
            ana_makine="127.0.0.1",
            baglanti_noktasi=0,
            gunluk_seviyesi="warning",
            erisim_gunlugu=False,
        )

    return PrototipAyarlari(
        terminal=terminal,
        guvenlik=PrototipGuvenlikAyarlari(
            ana_masaustu_anahtari=(
                "MASAUSTU-ANAHTARI"
            ),
            samsung_tablet_anahtari=(
                "TABLET-ANAHTARI"
            ),
            iphone_anahtari=(
                "IPHONE-ANAHTARI"
            ),
            saha_ana_gizli_degeri=(
                "SAHA-ANA-GIZLI-DEGERI"
            ),
        ),
        canli_sunucu=canli_sunucu,
    )


def test_uc_runtime_tek_uygulamada_birlesir(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path
        )
    )

    istemci = TestClient(
        prototip.terminal.uygulama
    )

    assert istemci.get(
        "/terminal"
    ).status_code == 200

    assert istemci.get(
        "/cihaz-iletisimi/saglik"
    ).status_code == 200

    assert istemci.get(
        "/saha-cihazlari/saglik"
    ).status_code == 200


def test_prototip_hazir_durumunda_olusturulur(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path
        )
    )

    assert (
        prototip.durum
        is PrototipDurumu.HAZIR
    )


def test_prototip_uygulama_durumuna_kaydedilir(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path
        )
    )

    assert (
        prototip
        .terminal
        .uygulama
        .state
        .birlesik_prototip
        is prototip
    )


def test_gercek_islem_varsayilan_kapali(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path
        )
    )

    assert (
        prototip
        .terminal
        .uygulama_isletmeni
        .gercek_isleme_izin_ver
        is False
    )


def test_canli_prototip_baslatilir(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path,
            canli=True,
        )
    )

    try:
        adres = prototip.baslat()

        assert adres.startswith(
            "http://127.0.0.1:"
        )

        assert prototip.calisiyor_mu

    finally:
        prototip.durdur()


def test_canli_prototip_guvenli_durdurulur(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path,
            canli=True,
        )
    )

    prototip.baslat()
    prototip.durdur()

    assert (
        prototip.durum
        is PrototipDurumu.DURDURULDU
    )

    assert not prototip.calisiyor_mu


def test_sunucusuz_prototip_baslatilamaz(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path
        )
    )

    try:
        prototip.baslat()
    except PrototipHatasi:
        return

    raise AssertionError(
        "Sunucusuz prototip başlatıldı."
    )


def test_birlesik_durum_ozeti_turkcedir(
    tmp_path: Path,
) -> None:
    prototip = SyKasifBirlesikPrototip(
        ayarlar=ayarlar_olustur(
            tmp_path
        )
    )

    ozet = prototip.durum_ozeti()

    assert ozet["sistem"] == "SyKaşif"
    assert ozet["durum"] == "hazır"
    assert "runtime_terminal" in ozet
    assert "cihaz_iletişimi" in ozet
    assert "saha_terminali" in ozet
    assert ozet["gerçek_işlem"] is False
