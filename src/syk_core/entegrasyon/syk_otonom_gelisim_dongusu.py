from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json

from syk_core.entegrasyon.syk_karar_kayit_altyapi_motoru import (
    SYKKararKayitAltyapiMotoru,
)
from syk_core.entegrasyon.tam_bagimsiz_yeniden_dogrulama_motoru import (
    TamBagimsizYenidenDogrulamaMotoru,
)
from syk_core.entegrasyon.vbps_veri_yetersizligi_talep_motoru import (
    VBPSVeriYetersizligiTalepMotoru,
)
from syk_core.entegrasyon.syk_otonom_karar_defteri import (
    SYKOtonomKararDefteri,
)
from syk_core.entegrasyon.syk_otonom_karar_durum_deposu import (
    SYKOtonomKararDurumDeposu,
)
from syk_core.entegrasyon.syk_otonom_karar_tutarlilik_dogrulayici import (
    SYKOtonomKararTutarlilikDogrulayici,
)


@dataclass
class OtonomGelisimKaydi:
    olay_kimligi: str
    mevcut_durum: str
    gelisim_onerileri: list[str] = field(default_factory=list)
    zaman: str = ""


@dataclass
class OtonomGelisimDogrulamaSonucu:
    olay_kimligi: str
    dogrulama_durumu: str
    eksikler: list[str]
    gelisim_onerileri: list[str]
    veri_talebi_sonucu: str
    karar_id: str
    karar_sha256: str
    karar_durumu: str
    onay_durumu: str


class SYKOtonomGelisimDongusu:
    def __init__(self):
        self.kayitlar = {}

    def degerlendir(
        self,
        olay_kimligi: str,
        durum: str,
    ):
        if durum == "inceleme_gerekli":
            oneriler = [
                "Ek kanit ve yeniden dogrulama onerildi",
            ]
        elif durum == "zayif_destek":
            oneriler = [
                "Veri kalitesi artirilmali",
            ]
        else:
            oneriler = [
                "Mevcut dogrulama zinciri korunmali",
            ]

        kayit = OtonomGelisimKaydi(
            olay_kimligi=olay_kimligi,
            mevcut_durum=durum,
            gelisim_onerileri=oneriler,
            zaman=datetime.now(timezone.utc).isoformat(),
        )

        self.kayitlar[olay_kimligi] = kayit
        return kayit

    def getir(
        self,
        olay_kimligi: str,
    ):
        return self.kayitlar.get(olay_kimligi)


class SYKOtonomGelisimDogrulamaMotoru:
    GECERLI_ONAY_DURUMLARI = {
        "BEKLIYOR",
        "ONAYLANDI",
        "REDDEDILDI",
    }

    def __init__(
        self,
        karar_defteri=None,
        durum_deposu=None,
    ):
        self.gelisim_motoru = SYKOtonomGelisimDongusu()
        self.dogrulama_motoru = TamBagimsizYenidenDogrulamaMotoru()
        self.karar_motoru = SYKKararKayitAltyapiMotoru()
        self.veri_talep_motoru = VBPSVeriYetersizligiTalepMotoru()
        self.karar_defteri = (
            SYKOtonomKararDefteri(karar_defteri)
            if karar_defteri is not None
            else None
        )
        self.durum_deposu = (
            SYKOtonomKararDurumDeposu(durum_deposu)
            if durum_deposu is not None
            else None
        )

        if self.durum_deposu is None:
            self.karar_taslaklari = {}
            self.muhurlu_kararlar = {}
        else:
            durum = self.durum_deposu.yukle()
            self.karar_taslaklari = durum["karar_taslaklari"]
            self.muhurlu_kararlar = durum["muhurlu_kararlar"]

        self._butunluk_kontrolu()

    def _butunluk_kontrolu(self):
        if (
            self.karar_defteri is None
            or self.durum_deposu is None
        ):
            return None

        sonuc = SYKOtonomKararTutarlilikDogrulayici(
            karar_defteri=self.karar_defteri.dosya_yolu,
            durum_deposu=self.durum_deposu.dosya_yolu,
        ).dogrula()

        if not sonuc.gecerli:
            hata_metni = "; ".join(sonuc.hatalar)
            raise RuntimeError(
                f"Otonom karar butunluk kontrolu basarisiz: "
                f"{hata_metni}"
            )

        return sonuc

    def butunluk_dogrula(self):
        return self._butunluk_kontrolu()

    @staticmethod
    def _muhurlu_karari_serilestir(karar):
        if isinstance(karar, dict):
            return karar

        return asdict(karar)

    def _durumu_kaydet(self):
        if self.durum_deposu is None:
            return None

        muhurlu_kararlar = {
            karar_id: self._muhurlu_karari_serilestir(karar)
            for karar_id, karar in self.muhurlu_kararlar.items()
        }

        return self.durum_deposu.kaydet(
            karar_taslaklari=self.karar_taslaklari,
            muhurlu_kararlar=muhurlu_kararlar,
        )

    def _deftere_yaz(
        self,
        olay_kimligi: str,
        karar_id: str,
        islem: str,
        durum: str,
        onaylayan: str,
        karar_sha256: str,
    ):
        if self.karar_defteri is None:
            return None

        return self.karar_defteri.ekle(
            olay_kimligi=olay_kimligi,
            karar_id=karar_id,
            islem=islem,
            durum=durum,
            onaylayan=onaylayan,
            karar_sha256=karar_sha256,
        )

    @staticmethod
    def _taslak_hashi(
        karar_id: str,
        olay_kimligi: str,
        dogrulama_durumu: str,
        eksikler: list[str],
        oneriler: list[str],
        onay_durumu: str,
    ) -> str:
        veri = {
            "karar_id": karar_id,
            "olay_kimligi": olay_kimligi,
            "dogrulama_durumu": dogrulama_durumu,
            "eksikler": sorted(eksikler),
            "oneriler": oneriler,
            "onay_durumu": onay_durumu,
        }
        ham = json.dumps(
            veri,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(ham.encode("utf-8")).hexdigest()

    def _karar_muhurle(
        self,
        karar_id: str,
        aciklama: str,
    ):
        if karar_id in self.muhurlu_kararlar:
            raise ValueError(
                f"Karar zaten muhurlu: {karar_id}"
            )

        karar = self.karar_motoru.karar_kaydet(
            karar_id=karar_id,
            baslik="Otonom gelisim ve dogrulama sonucu",
            kategori="OTONOM_GELISIM",
            aciklama=aciklama,
            versiyon="v1.0",
            karar_sahibi="KURUCU_KAAN",
            hazirlayan="BILGE_KAAN",
        )

        self.muhurlu_kararlar[karar_id] = karar
        return karar

    def karar_onayla(
        self,
        karar_id: str,
        onaylayan: str,
    ):
        self._butunluk_kontrolu()

        if onaylayan != "KURUCU_KAAN":
            raise PermissionError(
                "Karar yalnizca KURUCU_KAAN tarafindan onaylanabilir"
            )

        if karar_id in self.muhurlu_kararlar:
            raise ValueError(
                f"Karar zaten muhurlu: {karar_id}"
            )

        taslak = self.karar_taslaklari.get(karar_id)

        if taslak is None:
            raise KeyError(
                f"Karar taslagi bulunamadi: {karar_id}"
            )

        if taslak["onay_durumu"] == "REDDEDILDI":
            raise ValueError(
                f"Reddedilen karar onaylanamaz: {karar_id}"
            )

        karar = self._karar_muhurle(
            karar_id=karar_id,
            aciklama=taslak["aciklama"],
        )

        del self.karar_taslaklari[karar_id]
        self._durumu_kaydet()

        self._deftere_yaz(
            olay_kimligi=taslak["olay_kimligi"],
            karar_id=karar_id,
            islem="KURUCU_ONAYI",
            durum=karar.durum,
            onaylayan=onaylayan,
            karar_sha256=karar.sha256,
        )

        return karar

    def karar_reddet(
        self,
        karar_id: str,
        reddeden: str,
    ):
        self._butunluk_kontrolu()

        if reddeden != "KURUCU_KAAN":
            raise PermissionError(
                "Karar yalnizca KURUCU_KAAN tarafindan reddedilebilir"
            )

        if karar_id in self.muhurlu_kararlar:
            raise ValueError(
                f"Muhurlu karar reddedilemez: {karar_id}"
            )

        taslak = self.karar_taslaklari.get(karar_id)

        if taslak is None:
            raise KeyError(
                f"Karar taslagi bulunamadi: {karar_id}"
            )

        taslak["onay_durumu"] = "REDDEDILDI"
        taslak["durum"] = "REDDEDILDI"
        taslak["sha256"] = self._taslak_hashi(
            karar_id=taslak["karar_id"],
            olay_kimligi=taslak["olay_kimligi"],
            dogrulama_durumu=taslak["dogrulama_durumu"],
            eksikler=taslak["eksikler"],
            oneriler=taslak["oneriler"],
            onay_durumu="REDDEDILDI",
        )

        self._durumu_kaydet()

        self._deftere_yaz(
            olay_kimligi=taslak["olay_kimligi"],
            karar_id=karar_id,
            islem="KURUCU_REDDETTI",
            durum="REDDEDILDI",
            onaylayan=reddeden,
            karar_sha256=taslak["sha256"],
        )

        return taslak

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
        self._butunluk_kontrolu()

        if onay_durumu not in self.GECERLI_ONAY_DURUMLARI:
            raise ValueError(
                f"Gecersiz onay durumu: {onay_durumu}"
            )

        if onay_durumu != "BEKLIYOR":
            raise PermissionError(
                "Karar calistir metodu icinden dogrudan "
                "onaylanamaz veya reddedilemez; "
                "Kurucu Kaan karar metotlari kullanilmalidir"
            )

        dogrulama = self.dogrulama_motoru.calistir(
            olay_kimligi,
            katmanlar,
        )

        gelisim = self.gelisim_motoru.degerlendir(
            olay_kimligi,
            dogrulama.durum,
        )

        veri_talebi = self.veri_talep_motoru.kaydet(
            talep_id=f"TALEP-{olay_kimligi}",
            mevcut_veri=mevcut_veri,
            eksik_veri=eksik_veri,
            ek_cihaz_talebi=ek_cihaz_talebi,
            konum_kaydi=konum_kaydi,
            onay_durumu=onay_durumu,
        )

        karar_id = f"OGD-{olay_kimligi}"

        if (
            karar_id in self.karar_taslaklari
            or karar_id in self.muhurlu_kararlar
        ):
            raise ValueError(
                f"Karar kimligi zaten mevcut: {karar_id}"
            )

        aciklama = (
            f"Dogrulama durumu: {dogrulama.durum}; "
            f"Eksikler: {', '.join(dogrulama.eksikler) or 'yok'}; "
            f"Oneriler: {', '.join(gelisim.gelisim_onerileri)}"
        )

        if onay_durumu == "ONAYLANDI":
            karar = self._karar_muhurle(
                karar_id=karar_id,
                aciklama=aciklama,
            )
            karar_sha256 = karar.sha256
            karar_durumu = karar.durum

            self._durumu_kaydet()

            self._deftere_yaz(
                olay_kimligi=olay_kimligi,
                karar_id=karar_id,
                islem="KURUCU_ONAYI",
                durum=karar_durumu,
                onaylayan="KURUCU_KAAN",
                karar_sha256=karar_sha256,
            )
        else:
            karar_sha256 = self._taslak_hashi(
                karar_id=karar_id,
                olay_kimligi=olay_kimligi,
                dogrulama_durumu=dogrulama.durum,
                eksikler=dogrulama.eksikler,
                oneriler=gelisim.gelisim_onerileri,
                onay_durumu=onay_durumu,
            )
            karar_durumu = (
                "TASLAK"
                if onay_durumu == "BEKLIYOR"
                else "REDDEDILDI"
            )

            self.karar_taslaklari[karar_id] = {
                "karar_id": karar_id,
                "olay_kimligi": olay_kimligi,
                "dogrulama_durumu": dogrulama.durum,
                "eksikler": list(dogrulama.eksikler),
                "oneriler": list(gelisim.gelisim_onerileri),
                "aciklama": aciklama,
                "onay_durumu": onay_durumu,
                "durum": karar_durumu,
                "sha256": karar_sha256,
            }

            self._durumu_kaydet()

            self._deftere_yaz(
                olay_kimligi=olay_kimligi,
                karar_id=karar_id,
                islem=(
                    "TASLAK_OLUSTURULDU"
                    if onay_durumu == "BEKLIYOR"
                    else "KURUCU_REDDETTI"
                ),
                durum=karar_durumu,
                onaylayan=(
                    "SISTEM"
                    if onay_durumu == "BEKLIYOR"
                    else "KURUCU_KAAN"
                ),
                karar_sha256=karar_sha256,
            )

        return OtonomGelisimDogrulamaSonucu(
            olay_kimligi=olay_kimligi,
            dogrulama_durumu=dogrulama.durum,
            eksikler=dogrulama.eksikler,
            gelisim_onerileri=gelisim.gelisim_onerileri,
            veri_talebi_sonucu=veri_talebi.sonuc,
            karar_id=karar_id,
            karar_sha256=karar_sha256,
            karar_durumu=karar_durumu,
            onay_durumu=onay_durumu,
        )
