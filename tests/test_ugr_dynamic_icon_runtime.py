from __future__ import annotations

import json
from pathlib import Path

import pytest

from syk_ui.icons.ugr.runtime import (
    IkonCalismaDurumu,
    IkonGorunumModu,
    IkonOnceligi,
    IkonRuntimeKaydi,
    UgrDinamikIkonServisi,
)
from syk_ui.icons.ugr.runtime.durum_makinesi import (
    GecersizIkonDurumGecisi,
)
from syk_ui.icons.ugr.runtime.kayit_defteri import (
    IkonBulunamadiError,
    IkonZatenKayitliError,
)
from syk_ui.icons.ugr.runtime.manifest_yukleyici import (
    IkonManifestHatasi,
    manifest_oku,
    runtime_kayitlari_uret,
)
from syk_ui.icons.ugr.runtime.stil_kurallari import (
    durum_stili,
    tum_durum_stilleri,
)


def ikon() -> IkonRuntimeKaydi:
    return IkonRuntimeKaydi(
        ikon_kimligi="sys-001",
        kategori="ana_sistem",
        dosya_yolu=(
            "src/syk_ui/icons/ugr/"
            "prototype_icons/ana_sistem/"
            "001_harita.png"
        ),
        etiket="harita",
    )


def test_ikon_modeli_baslangic_durumu_bekliyor() -> None:
    kayit = ikon()

    assert kayit.durum == IkonCalismaDurumu.BEKLIYOR
    assert kayit.gorunum_modu == IkonGorunumModu.MOD_2B
    assert kayit.gecmis == []


def test_ikon_modeli_bos_kimligi_reddeder() -> None:
    with pytest.raises(ValueError):
        IkonRuntimeKaydi(
            ikon_kimligi=" ",
            kategori="ana_sistem",
            dosya_yolu="ikon.png",
            etiket="harita",
        )


def test_kayit_defteri_ikon_ekler() -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    assert servis.kayit_defteri.sayi() == 1
    assert (
        servis.kayit_defteri.getir(
            "sys-001"
        ).etiket
        == "harita"
    )


def test_kayit_defteri_tekrarli_kimligi_reddeder() -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    with pytest.raises(
        IkonZatenKayitliError
    ):
        servis.ikon_ekle(ikon())


def test_kayit_defteri_bilinmeyen_kimligi_reddeder() -> None:
    servis = UgrDinamikIkonServisi()

    with pytest.raises(
        IkonBulunamadiError
    ):
        servis.ikon_ozeti("yok")


def test_bekliyor_baslatiliyor_gecisi_izinli() -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    sonuc = servis.durum_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu.BASLATILIYOR
        ),
        neden="Kullanıcı görevi başlattı.",
    )

    assert (
        sonuc["degisim"]["onceki_durum"]
        == "bekliyor"
    )
    assert (
        sonuc["degisim"]["yeni_durum"]
        == "baslatiliyor"
    )


def test_bekliyor_tamamlandi_gecisi_reddedilir() -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    with pytest.raises(
        GecersizIkonDurumGecisi
    ):
        servis.durum_degistir(
            "sys-001",
            yeni_durum=(
                IkonCalismaDurumu.TAMAMLANDI
            ),
            neden="Geçersiz doğrudan geçiş.",
        )


def test_zorunlu_gecis_kurali_asabilir() -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    sonuc = servis.durum_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu.TAMAMLANDI
        ),
        neden="Yönetici kontrollü geçiş.",
        zorla=True,
    )

    assert (
        sonuc["ikon"]["durum"]
        == "tamamlandi"
    )


def test_durum_gecmisi_tutulur() -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    servis.durum_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu.BASLATILIYOR
        ),
        neden="Başlatma.",
    )

    servis.durum_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu.CALISIYOR
        ),
        neden="Çalışma başladı.",
    )

    kayit = servis.kayit_defteri.getir(
        "sys-001"
    )

    assert len(kayit.gecmis) == 2
    assert (
        kayit.gecmis[-1].yeni_durum
        == IkonCalismaDurumu.CALISIYOR
    )


def test_hata_durumu_titresim_stili_kullanir() -> None:
    stil = durum_stili(
        IkonCalismaDurumu.HATA
    )

    assert stil.animasyon.value == "titresim"
    assert stil.renk_rolu.value == "hata"
    assert stil.tekrarli is True


def test_tamamlandi_durumu_basari_stili_kullanir() -> None:
    stil = durum_stili(
        IkonCalismaDurumu.TAMAMLANDI
    )

    assert stil.renk_rolu.value == "basari"
    assert stil.tekrarli is False


def test_butun_durumlarin_stili_var() -> None:
    stiller = tum_durum_stilleri()

    assert len(stiller) == len(
        IkonCalismaDurumu
    )

    assert {
        stil.durum
        for stil in stiller
    } == set(IkonCalismaDurumu)


@pytest.mark.parametrize(
    "mod",
    [
        IkonGorunumModu.MOD_2B,
        IkonGorunumModu.MOD_3B,
        IkonGorunumModu.MOD_AR,
    ],
)
def test_gorunum_modlari_desteklenir(
    mod: IkonGorunumModu,
) -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    sonuc = servis.gorunum_modu_degistir(
        "sys-001",
        mod,
    )

    assert sonuc["gorunum_modu"] == mod.value


def test_olay_yolu_durum_degisimi_yayinlar() -> None:
    servis = UgrDinamikIkonServisi()
    olaylar = []

    servis.olay_yolu.abone_ol(
        "ikon_durumu_degisti",
        olaylar.append,
    )

    servis.ikon_ekle(ikon())

    servis.durum_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu.BASLATILIYOR
        ),
        neden="Başlatma.",
        oncelik=IkonOnceligi.YUKSEK,
    )

    assert len(olaylar) == 1
    assert (
        olaylar[0].ikon_kimligi
        == "sys-001"
    )


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    servis = UgrDinamikIkonServisi()
    servis.ikon_ekle(ikon())

    ozet = servis.durum_ozeti()

    assert ozet["toplam_ikon"] == 1
    assert ozet["aktif_ikon"] == 1
    assert (
        ozet["durum_sayilari"]["bekliyor"]
        == 1
    )
    assert (
        ozet["kategori_sayilari"][
            "ana_sistem"
        ]
        == 1
    )


def test_manifest_utf8_bom_ile_okunabilir(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"

    manifest.write_text(
        json.dumps(
            {
                "icon_count": 1,
                "icons": [
                    {
                        "temporary_id": "sys-001",
                        "category": "ana_sistem",
                        "label": "harita",
                        "path": "harita.png",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8-sig",
    )

    veri = manifest_oku(manifest)

    assert veri["icon_count"] == 1


def test_manifest_runtime_kaydi_uretir(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"

    manifest.write_text(
        json.dumps(
            {
                "icon_count": 1,
                "icons": [
                    {
                        "temporary_id": "sys-001",
                        "category": "ana_sistem",
                        "label": "harita",
                        "path": "harita.png",
                        "sha256": "ABC",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    kayitlar = runtime_kayitlari_uret(
        manifest
    )

    assert len(kayitlar) == 1
    assert (
        kayitlar[0].ikon_kimligi
        == "sys-001"
    )
    assert (
        kayitlar[0].meta_veri["sha256"]
        == "ABC"
    )


def test_gecersiz_manifest_reddedilir(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        "[]",
        encoding="utf-8",
    )

    with pytest.raises(
        IkonManifestHatasi
    ):
        manifest_oku(manifest)


def test_gercek_215_ikon_manifesti_yuklenir() -> None:
    manifest = Path(
        "src/syk_ui/icons/ugr/manifests/"
        "ugr_prototype_icons_manifest.json"
    )

    if not manifest.exists():
        pytest.skip(
            "Gerçek UGR ikon manifesti bulunamadı."
        )

    servis = UgrDinamikIkonServisi()

    yuklenen = servis.manifest_yukle(
        manifest
    )

    assert yuklenen == 215
    assert (
        servis.kayit_defteri.sayi()
        == 215
    )

    ozet = servis.durum_ozeti()

    assert ozet["toplam_ikon"] == 215
    assert (
        ozet["kalici_kimlik_durumu"]
        == "prototip_sonrasina_ertelendi"
    )
