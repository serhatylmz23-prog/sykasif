from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json


class SYKKararAltyapiDogrulamaManifesti:
    SURUM = "1.0"

    DOSYALAR = (
        "src/syk_core/entegrasyon/syk_otonom_gelisim_dongusu.py",
        "src/syk_core/entegrasyon/syk_otonom_karar_defteri.py",
        "src/syk_core/entegrasyon/syk_otonom_karar_durum_deposu.py",
        "src/syk_core/entegrasyon/syk_otonom_karar_tutarlilik_dogrulayici.py",
        "src/syk_core/entegrasyon/syk_otonom_islem_jurnali.py",
        "src/syk_core/entegrasyon/syk_otonom_guvenli_islem_motoru.py",
    )

    def __init__(self, kok_dizin):
        self.kok_dizin = Path(kok_dizin)

    @staticmethod
    def _dosya_hashi(dosya_yolu: Path) -> str:
        sha256 = hashlib.sha256()

        with dosya_yolu.open("rb") as dosya:
            while True:
                parca = dosya.read(65536)

                if not parca:
                    break

                sha256.update(parca)

        return sha256.hexdigest()

    @staticmethod
    def _manifest_hashi(veri: dict) -> str:
        ham = json.dumps(
            veri,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            ham.encode("utf-8")
        ).hexdigest()

    def olustur(self) -> dict:
        dosyalar = {}

        for goreli_yol in self.DOSYALAR:
            tam_yol = self.kok_dizin / goreli_yol

            if not tam_yol.is_file():
                raise FileNotFoundError(
                    f"Dogrulama dosyasi bulunamadi: {goreli_yol}"
                )

            dosyalar[goreli_yol] = {
                "sha256": self._dosya_hashi(tam_yol),
                "boyut": tam_yol.stat().st_size,
            }

        veri = {
            "surum": self.SURUM,
            "olusturma_zamani": datetime.now(
                timezone.utc
            ).isoformat(),
            "dosyalar": dosyalar,
        }

        return {
            **veri,
            "manifest_sha256": self._manifest_hashi(veri),
        }

    def kaydet(self, cikti_yolu) -> dict:
        belge = self.olustur()
        cikti_yolu = Path(cikti_yolu)

        cikti_yolu.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cikti_yolu.write_text(
            json.dumps(
                belge,
                ensure_ascii=True,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return belge

    def dogrula(self, manifest_yolu) -> bool:
        manifest_yolu = Path(manifest_yolu)

        try:
            belge = json.loads(
                manifest_yolu.read_text(
                    encoding="utf-8"
                )
            )
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return False

        gerekli_alanlar = {
            "surum",
            "olusturma_zamani",
            "dosyalar",
            "manifest_sha256",
        }

        if set(belge) != gerekli_alanlar:
            return False

        if belge["surum"] != self.SURUM:
            return False

        veri = {
            "surum": belge["surum"],
            "olusturma_zamani": belge["olusturma_zamani"],
            "dosyalar": belge["dosyalar"],
        }

        if (
            belge["manifest_sha256"]
            != self._manifest_hashi(veri)
        ):
            return False

        if set(belge["dosyalar"]) != set(self.DOSYALAR):
            return False

        for goreli_yol, kayit in belge["dosyalar"].items():
            tam_yol = self.kok_dizin / goreli_yol

            if not tam_yol.is_file():
                return False

            if set(kayit) != {"sha256", "boyut"}:
                return False

            if kayit["boyut"] != tam_yol.stat().st_size:
                return False

            if (
                kayit["sha256"]
                != self._dosya_hashi(tam_yol)
            ):
                return False

        return True
