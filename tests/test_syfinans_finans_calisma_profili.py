from datetime import UTC, datetime
from decimal import Decimal

from syk_finans_otagi.capraz_dogrulama import (
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
    KaynakTuru,
)
from syk_finans_otagi.finans_calisma_profili import (
    KasifFinansGecidi,
    OncelikliVarlik,
    SyFinansCalismaProfili,
)
from syk_finans_otagi.finans_kaynak_merkezi import (
    FinansKaynakMerkezi,
)
from syk_finans_otagi.gercek_kaynak_sozlesmeleri import (
    FinansKaynakSinifi,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from syk_finans_otagi.veri_saglayicilari import (
    PiyasaVerisi,
    VeriDogruLamaMotoru,
)


ZAMAN = datetime.now(
    UTC
).isoformat()


class DenemeKaynak:
    def __init__(
        self,
        *,
        kimlik: str,
        kaynak_sinifi: FinansKaynakSinifi,
        varlik_turu: VarlikTuru,
        fiyatlar: dict[str, str],
        hata_sembolleri=(),
    ):
        self._kimlik = kimlik
        self._kaynak_sinifi = (
            kaynak_sinifi
        )
        self.varlik_turu = varlik_turu
        self.fiyatlar = {
            sembol.upper(): Decimal(
                fiyat
            )
            for sembol, fiyat
            in fiyatlar.items()
        }
        self.hata_sembolleri = {
            sembol.upper()
            for sembol in hata_sembolleri
        }

    @property
    def saglayici_id(self):
        return self._kimlik

    @property
    def kaynak_sinifi(self):
        return self._kaynak_sinifi

    def piyasa_verisi_getir(
        self,
        *,
        sembol,
    ):
        sembol = sembol.upper()

        if sembol in self.hata_sembolleri:
            raise ConnectionError(
                "Deneme kaynak hatası"
            )

        if sembol not in self.fiyatlar:
            raise KeyError(
                sembol
            )

        veri = PiyasaVerisi(
            sembol=sembol,
            varlik_turu=(
                self.varlik_turu
            ),
            fiyat=(
                self.fiyatlar[
                    sembol
                ]
            ),
            para_birimi="TRY",
            zaman_damgasi=ZAMAN,
            kaynak=self._kimlik,
            saglayici_id=(
                self._kimlik
            ),
            veri_durumu=(
                VeriAkisDurumu.ANLIK
            ),
            dogrulandi=True,
        )

        veri = (
            VeriDogruLamaMotoru
            .muhurle(
                veri
            )
        )

        profil = KaynakGuvenProfili(
            saglayici_id=(
                self._kimlik
            ),
            kaynak_turu=(
                KaynakTuru
                .LISANSLI_PIYASA
            ),
            temel_guven_puani=90,
            guncellik_puani=90,
            gecmis_tutarlilik_puani=90,
            kesinti_dayanim_puani=85,
            lisansli=True,
            resmi=False,
        )

        return KaynakliPiyasaVerisi(
            veri=veri,
            guven_profili=profil,
        )


def profil():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemeKaynak(
                kimlik="bist-a",
                kaynak_sinifi=(
                    FinansKaynakSinifi.BIST
                ),
                varlik_turu=(
                    VarlikTuru.HISSE
                ),
                fiyatlar={
                    "ASELS": "300",
                    "THYAO": "410",
                },
            ),
            DenemeKaynak(
                kimlik="fon-a",
                kaynak_sinifi=(
                    FinansKaynakSinifi.FON
                ),
                varlik_turu=(
                    VarlikTuru.FON
                ),
                fiyatlar={
                    "FON-A": "2.50",
                },
            ),
        ]
    )

    return SyFinansCalismaProfili(
        merkez=merkez,
        oncelikli_varliklar=[
            OncelikliVarlik(
                sembol="ASELS",
                varlik_turu=(
                    VarlikTuru.HISSE
                ),
                oncelik=100,
            ),
            OncelikliVarlik(
                sembol="FON-A",
                varlik_turu=(
                    VarlikTuru.FON
                ),
                oncelik=80,
            ),
        ],
    )


def test_oncelikli_varliklar_siralanir():
    calisma = profil()

    varliklar = (
        calisma
        .oncelikli_varliklar()
    )

    assert (
        varliklar[0].sembol
        == "ASELS"
    )

    assert (
        varliklar[1].sembol
        == "FON-A"
    )


def test_hisse_verisi_merkezden_alinir():
    calisma = profil()

    sonuc = (
        calisma
        .varlik_verisi_getir(
            sembol="ASELS",
            varlik_turu=(
                VarlikTuru.HISSE
            ),
        )
    )

    assert (
        sonuc.secilen_fiyat
        == Decimal("300")
    )

    assert (
        sonuc.kullanilan_kaynaklar
        == ("bist-a",)
    )


def test_fon_verisi_dogru_kaynak_sinifindan_alinir():
    calisma = profil()

    sonuc = (
        calisma
        .varlik_verisi_getir(
            sembol="FON-A",
            varlik_turu=(
                VarlikTuru.FON
            ),
        )
    )

    assert (
        sonuc.secilen_fiyat
        == Decimal("2.50")
    )

    assert (
        sonuc.kullanilan_kaynaklar
        == ("fon-a",)
    )


def test_toplu_guncelleme_oncelikli_varliklari_isler():
    calisma = profil()

    sonuc = (
        calisma.toplu_guncelle()
    )

    assert (
        sonuc.toplam_varlik
        == 2
    )

    assert (
        sonuc.basarili_varlik
        == 2
    )

    assert (
        sonuc.basarisiz_varlik
        == 0
    )

    assert len(
        sonuc.toplu_sha256
    ) == 64


def test_toplu_guncelleme_hatasi_donguyu_durdurmaz():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemeKaynak(
                kimlik="bist-a",
                kaynak_sinifi=(
                    FinansKaynakSinifi.BIST
                ),
                varlik_turu=(
                    VarlikTuru.HISSE
                ),
                fiyatlar={
                    "ASELS": "300",
                },
                hata_sembolleri={
                    "HATALI",
                },
            )
        ]
    )

    calisma = SyFinansCalismaProfili(
        merkez=merkez,
        oncelikli_varliklar=[
            OncelikliVarlik(
                sembol="ASELS",
                varlik_turu=(
                    VarlikTuru.HISSE
                ),
            ),
            OncelikliVarlik(
                sembol="HATALI",
                varlik_turu=(
                    VarlikTuru.HISSE
                ),
                oncelik=50,
            ),
        ],
    )

    sonuc = (
        calisma.toplu_guncelle()
    )

    assert (
        sonuc.basarili_varlik
        == 1
    )

    assert (
        sonuc.basarisiz_varlik
        == 1
    )


def test_kaynak_saglik_ozeti_uretilir():
    calisma = profil()

    calisma.varlik_verisi_getir(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    ozet = (
        calisma
        .kaynak_saglik_ozeti()
    )

    assert (
        ozet["kaynak_sayisi"]
        == 2
    )

    assert (
        ozet["hazir_kaynak_sayisi"]
        == 1
    )

    assert len(
        ozet["snapshot_sha256"]
    ) == 64


def test_kasif_finans_gecidi_yalniz_profili_kullanir():
    gecit = KasifFinansGecidi(
        calisma_profili=profil(),
    )

    sonuc = gecit.varlik_bilgisi(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    assert sonuc[
        "schema"
    ] == "syfinans-kasif-gecidi/v1"

    assert sonuc[
        "fiyat"
    ] == 300.0

    assert (
        "nihai karar kullanıcıya aittir"
        in sonuc[
            "kesinlik_uyarisi"
        ]
    )

    assert len(
        sonuc["kanit_sha256"]
    ) == 64


def test_varlik_silinebilir():
    calisma = profil()

    silindi = calisma.varlik_sil(
        sembol="FON-A",
        varlik_turu=(
            VarlikTuru.FON
        ),
    )

    assert silindi

    assert [
        varlik.sembol
        for varlik
        in calisma
        .oncelikli_varliklar()
    ] == [
        "ASELS"
    ]