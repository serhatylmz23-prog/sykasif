from dataclasses import dataclass

from syk_core.entegrasyon.syk_otonom_karar_defteri import (
    SYKOtonomKararDefteri,
)
from syk_core.entegrasyon.syk_otonom_karar_durum_deposu import (
    SYKOtonomKararDurumDeposu,
)


@dataclass(frozen=True)
class OtonomKararTutarlilikSonucu:
    gecerli: bool
    hatalar: list[str]
    defter_kayit_sayisi: int
    taslak_sayisi: int
    muhurlu_karar_sayisi: int


class SYKOtonomKararTutarlilikDogrulayici:
    def __init__(
        self,
        karar_defteri,
        durum_deposu,
    ):
        self.karar_defteri = SYKOtonomKararDefteri(
            karar_defteri
        )
        self.durum_deposu = SYKOtonomKararDurumDeposu(
            durum_deposu
        )

    @staticmethod
    def _son_kayitlari_bul(kayitlar):
        son_kayitlar = {}

        for kayit in kayitlar:
            son_kayitlar[kayit.karar_id] = kayit

        return son_kayitlar

    def dogrula(self) -> OtonomKararTutarlilikSonucu:
        hatalar = []

        if not self.karar_defteri.dogrula():
            hatalar.append(
                "Karar defteri hash zinciri gecersiz"
            )

        if not self.durum_deposu.dogrula():
            hatalar.append(
                "Karar durum deposu hash dogrulamasi gecersiz"
            )

        if hatalar:
            return OtonomKararTutarlilikSonucu(
                gecerli=False,
                hatalar=hatalar,
                defter_kayit_sayisi=0,
                taslak_sayisi=0,
                muhurlu_karar_sayisi=0,
            )

        kayitlar = self.karar_defteri.kayitlari_oku()
        durum = self.durum_deposu.yukle()

        taslaklar = durum["karar_taslaklari"]
        muhurlu_kararlar = durum["muhurlu_kararlar"]
        son_kayitlar = self._son_kayitlari_bul(kayitlar)

        ortak_kimlikler = (
            set(taslaklar)
            & set(muhurlu_kararlar)
        )

        for karar_id in sorted(ortak_kimlikler):
            hatalar.append(
                f"Karar hem taslak hem muhurlu durumda: {karar_id}"
            )

        for karar_id, taslak in sorted(
            taslaklar.items()
        ):
            son_kayit = son_kayitlar.get(karar_id)

            if son_kayit is None:
                hatalar.append(
                    f"Taslak karar defterde bulunamadi: {karar_id}"
                )
                continue

            beklenen_durum = taslak.get("durum")
            beklenen_hash = taslak.get("sha256")

            if son_kayit.durum != beklenen_durum:
                hatalar.append(
                    f"Taslak durum uyusmazligi: {karar_id}"
                )

            if son_kayit.karar_sha256 != beklenen_hash:
                hatalar.append(
                    f"Taslak SHA uyusmazligi: {karar_id}"
                )

            if beklenen_durum == "TASLAK":
                if son_kayit.islem != "TASLAK_OLUSTURULDU":
                    hatalar.append(
                        f"Taslak islem uyusmazligi: {karar_id}"
                    )

            if beklenen_durum == "REDDEDILDI":
                if son_kayit.islem != "KURUCU_REDDETTI":
                    hatalar.append(
                        f"Red islem uyusmazligi: {karar_id}"
                    )

        for karar_id, karar in sorted(
            muhurlu_kararlar.items()
        ):
            son_kayit = son_kayitlar.get(karar_id)

            if son_kayit is None:
                hatalar.append(
                    f"Muhurlu karar defterde bulunamadi: {karar_id}"
                )
                continue

            karar_durumu = karar.get("durum")
            karar_sha256 = karar.get("sha256")

            if karar_durumu != "MUHURLENDI":
                hatalar.append(
                    f"Muhurlu karar durumu gecersiz: {karar_id}"
                )

            if son_kayit.islem != "KURUCU_ONAYI":
                hatalar.append(
                    f"Muhurlu karar islem uyusmazligi: {karar_id}"
                )

            if son_kayit.durum != "MUHURLENDI":
                hatalar.append(
                    f"Muhurlu karar defter durumu uyusmuyor: {karar_id}"
                )

            if son_kayit.karar_sha256 != karar_sha256:
                hatalar.append(
                    f"Muhurlu karar SHA uyusmazligi: {karar_id}"
                )

        return OtonomKararTutarlilikSonucu(
            gecerli=not hatalar,
            hatalar=hatalar,
            defter_kayit_sayisi=len(kayitlar),
            taslak_sayisi=len(taslaklar),
            muhurlu_karar_sayisi=len(muhurlu_kararlar),
        )
