from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json


class SYKMuhurTeslimOncesiManifesti:
    SURUM = "1.0"

    KAYNAKLAR = (
        "src/syk_core/entegrasyon/cekirdek_muhur_adayi.py",
        "src/syk_core/entegrasyon/cekirdek_zincir_denetim_raporu.py",
        "src/syk_core/entegrasyon/muhur_oncesi_denetim.py",
        "src/syk_core/entegrasyon/teslim_oncesi_kontrol_orkestratoru.py",
        "src/syk_core/entegrasyon/nihai_muhur_adayi_ozet.py",
    )

    TESTLER = (
        "tests/test_cekirdek_muhur_adayi.py",
        "tests/test_cekirdek_zincir_denetim_raporu.py",
        "tests/test_muhur_oncesi_denetim.py",
        "tests/test_teslim_oncesi_kontrol_orkestratoru.py",
        "tests/test_nihai_muhur_adayi_ozet.py",
    )

    def __init__(self, kok_dizin):
        self.kok_dizin = Path(kok_dizin)

    @staticmethod
    def _sha256(yol: Path) -> str:
        hesap = hashlib.sha256()

        with yol.open("rb") as akis:
            for parca in iter(lambda: akis.read(65536), b""):
                hesap.update(parca)

        return hesap.hexdigest()

    @staticmethod
    def _belge_hashi(veri: dict) -> str:
        ham = json.dumps(
            veri,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(ham).hexdigest()

    @property
    def tum_dosyalar(self):
        return self.KAYNAKLAR + self.TESTLER

    def olustur(self) -> dict:
        dosyalar = {}

        for goreli in self.tum_dosyalar:
            tam_yol = self.kok_dizin / goreli

            if not tam_yol.is_file():
                raise FileNotFoundError(
                    f"Muhur teslim oncesi dosyasi bulunamadi: {goreli}"
                )

            dosyalar[goreli] = {
                "sha256": self._sha256(tam_yol),
                "boyut": tam_yol.stat().st_size,
            }

        veri = {
            "surum": self.SURUM,
            "olusturma_zamani": datetime.now(
                timezone.utc
            ).isoformat(),
            "kaynak_sayisi": len(self.KAYNAKLAR),
            "test_dosyasi_sayisi": len(self.TESTLER),
            "dosyalar": dosyalar,
        }

        return {
            **veri,
            "manifest_sha256": self._belge_hashi(veri),
        }

    def kaydet(self, cikti_yolu) -> dict:
        cikti_yolu = Path(cikti_yolu)
        cikti_yolu.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        belge = self.olustur()

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
        try:
            belge = json.loads(
                Path(manifest_yolu).read_text(
                    encoding="utf-8"
                )
            )
        except (
            FileNotFoundError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return False

        beklenen_alanlar = {
            "surum",
            "olusturma_zamani",
            "kaynak_sayisi",
            "test_dosyasi_sayisi",
            "dosyalar",
            "manifest_sha256",
        }

        if set(belge) != beklenen_alanlar:
            return False

        if belge["surum"] != self.SURUM:
            return False

        if belge["kaynak_sayisi"] != len(self.KAYNAKLAR):
            return False

        if belge["test_dosyasi_sayisi"] != len(self.TESTLER):
            return False

        if set(belge["dosyalar"]) != set(self.tum_dosyalar):
            return False

        veri = {
            anahtar: belge[anahtar]
            for anahtar in (
                "surum",
                "olusturma_zamani",
                "kaynak_sayisi",
                "test_dosyasi_sayisi",
                "dosyalar",
            )
        }

        if (
            belge["manifest_sha256"]
            != self._belge_hashi(veri)
        ):
            return False

        for goreli, kayit in belge["dosyalar"].items():
            tam_yol = self.kok_dizin / goreli

            if not tam_yol.is_file():
                return False

            if set(kayit) != {"sha256", "boyut"}:
                return False

            if kayit["boyut"] != tam_yol.stat().st_size:
                return False

            if kayit["sha256"] != self._sha256(tam_yol):
                return False

        return True
