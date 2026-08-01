from pathlib import Path
from uuid import uuid4

from syk_core.entegrasyon.syk_otonom_gelisim_dongusu import (
    SYKOtonomGelisimDogrulamaMotoru,
)
from syk_core.entegrasyon.syk_otonom_islem_jurnali import (
    SYKOtonomIslemJurnali,
)


class SYKOtonomGuvenliIslemMotoru:
    def __init__(
        self,
        karar_defteri,
        durum_deposu,
        islem_jurnali,
        otomatik_kurtarma: bool = False,
    ):
        self.karar_defteri_yolu = Path(karar_defteri)
        self.durum_deposu_yolu = Path(durum_deposu)

        self.motor = SYKOtonomGelisimDogrulamaMotoru(
            karar_defteri=self.karar_defteri_yolu,
            durum_deposu=self.durum_deposu_yolu,
        )
        self.jurnal = SYKOtonomIslemJurnali(
            islem_jurnali
        )

        bekleyen = self.jurnal.bekleyen_islem()

        if bekleyen is not None:
            if not otomatik_kurtarma:
                raise RuntimeError(
                    f"Tamamlanmamis islem nedeniyle sistem "
                    f"baslatilamadi: {bekleyen['islem_id']}"
                )

            self._yarim_islem_kurtar(bekleyen)

    @staticmethod
    def _islem_id_uret() -> str:
        return f"ISLEM-{uuid4().hex.upper()}"

    def _karar_dosyalari_anlik_goruntu(self):
        goruntu = {}

        for yol in (
            self.karar_defteri_yolu,
            self.durum_deposu_yolu,
        ):
            goruntu[yol] = (
                yol.read_bytes()
                if yol.exists()
                else None
            )

        return goruntu

    @staticmethod
    def _karar_dosyalarini_geri_yukle(goruntu):
        for yol, icerik in goruntu.items():
            if icerik is None:
                if yol.exists():
                    yol.unlink()
                continue

            yol.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            yol.write_bytes(icerik)

    def _motoru_yenile(self):
        self.motor = SYKOtonomGelisimDogrulamaMotoru(
            karar_defteri=self.karar_defteri_yolu,
            durum_deposu=self.durum_deposu_yolu,
        )

    def _karar_son_kaydi(self, karar_id: str):
        kayitlar = self.motor.karar_defteri.kayitlari_oku()

        for kayit in reversed(kayitlar):
            if kayit.karar_id == karar_id:
                return kayit

        return None

    def _yarim_islem_tamamlanmis_mi(
        self,
        bekleyen: dict,
    ) -> bool:
        karar_id = bekleyen["karar_id"]
        islem_turu = bekleyen["islem_turu"]
        son_kayit = self._karar_son_kaydi(karar_id)

        if son_kayit is None:
            return False

        if islem_turu == "TASLAK_OLUSTUR":
            taslak = self.motor.karar_taslaklari.get(
                karar_id
            )

            return (
                taslak is not None
                and taslak.get("durum") == "TASLAK"
                and son_kayit.islem == "TASLAK_OLUSTURULDU"
                and son_kayit.karar_sha256
                == taslak.get("sha256")
            )

        if islem_turu == "KURUCU_ONAYI":
            karar = self.motor.muhurlu_kararlar.get(
                karar_id
            )

            return (
                karar is not None
                and karar.get("durum") == "MUHURLENDI"
                and son_kayit.islem == "KURUCU_ONAYI"
                and son_kayit.karar_sha256
                == karar.get("sha256")
            )

        if islem_turu == "KURUCU_REDDETTI":
            taslak = self.motor.karar_taslaklari.get(
                karar_id
            )

            return (
                taslak is not None
                and taslak.get("durum") == "REDDEDILDI"
                and son_kayit.islem == "KURUCU_REDDETTI"
                and son_kayit.karar_sha256
                == taslak.get("sha256")
            )

        return False

    def _yarim_islem_kurtar(self, bekleyen: dict):
        islem_id = bekleyen["islem_id"]

        butunluk = self.motor.butunluk_dogrula()

        if butunluk is None or not butunluk.gecerli:
            self.jurnal.basarisiz(
                islem_id=islem_id,
                hata=(
                    "Yarim islem kurtarma sirasinda "
                    "karar butunlugu dogrulanamadi"
                ),
            )
            return

        if self._yarim_islem_tamamlanmis_mi(
            bekleyen
        ):
            self.jurnal.tamamla(islem_id)
            return

        self.jurnal.basarisiz(
            islem_id=islem_id,
            hata=(
                "Yarim islem karar defteri ve durum "
                "deposunda tamamlanmis bulunamadi"
            ),
        )

    def _guvenli_islem(
        self,
        karar_id: str,
        olay_kimligi: str,
        islem_turu: str,
        islem,
    ):
        islem_id = self._islem_id_uret()
        karar_dosyalari = (
            self._karar_dosyalari_anlik_goruntu()
        )

        self.jurnal.baslat(
            islem_id=islem_id,
            karar_id=karar_id,
            olay_kimligi=olay_kimligi,
            islem_turu=islem_turu,
        )

        try:
            sonuc = islem()
        except Exception as hata:
            self._karar_dosyalarini_geri_yukle(
                karar_dosyalari
            )
            self._motoru_yenile()

            self.jurnal.basarisiz(
                islem_id=islem_id,
                hata=f"{type(hata).__name__}: {hata}",
            )
            raise

        self.jurnal.tamamla(islem_id)
        return sonuc

    def calistir(
        self,
        olay_kimligi: str,
        katmanlar: dict[str, bool],
        mevcut_veri: str = "YETERLI",
        eksik_veri: str = "",
        ek_cihaz_talebi: str = "",
        konum_kaydi: str = "",
        onay_durumu: str = "BEKLIYOR",
    ):
        karar_id = f"OGD-{olay_kimligi}"

        return self._guvenli_islem(
            karar_id=karar_id,
            olay_kimligi=olay_kimligi,
            islem_turu="TASLAK_OLUSTUR",
            islem=lambda: self.motor.calistir(
                olay_kimligi=olay_kimligi,
                katmanlar=katmanlar,
                mevcut_veri=mevcut_veri,
                eksik_veri=eksik_veri,
                ek_cihaz_talebi=ek_cihaz_talebi,
                konum_kaydi=konum_kaydi,
                onay_durumu=onay_durumu,
            ),
        )

    def karar_onayla(
        self,
        karar_id: str,
        onaylayan: str,
    ):
        taslak = self.motor.karar_taslaklari.get(
            karar_id
        )

        olay_kimligi = (
            taslak["olay_kimligi"]
            if taslak is not None
            else karar_id.removeprefix("OGD-")
        )

        return self._guvenli_islem(
            karar_id=karar_id,
            olay_kimligi=olay_kimligi,
            islem_turu="KURUCU_ONAYI",
            islem=lambda: self.motor.karar_onayla(
                karar_id=karar_id,
                onaylayan=onaylayan,
            ),
        )

    def karar_reddet(
        self,
        karar_id: str,
        reddeden: str,
    ):
        taslak = self.motor.karar_taslaklari.get(
            karar_id
        )

        olay_kimligi = (
            taslak["olay_kimligi"]
            if taslak is not None
            else karar_id.removeprefix("OGD-")
        )

        return self._guvenli_islem(
            karar_id=karar_id,
            olay_kimligi=olay_kimligi,
            islem_turu="KURUCU_REDDETTI",
            islem=lambda: self.motor.karar_reddet(
                karar_id=karar_id,
                reddeden=reddeden,
            ),
        )

    def butunluk_dogrula(self):
        return self.motor.butunluk_dogrula()
