from pathlib import Path
import hashlib
import json
import os
import tempfile


class SYKOtonomKararDurumDeposu:
    SURUM = "1.0"

    def __init__(self, dosya_yolu):
        self.dosya_yolu = Path(dosya_yolu)
        self.dosya_yolu.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _hash_hesapla(veri: dict) -> str:
        ham = json.dumps(
            veri,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(
            ham.encode("utf-8")
        ).hexdigest()

    @classmethod
    def _bos_durum(cls) -> dict:
        return {
            "surum": cls.SURUM,
            "karar_taslaklari": {},
            "muhurlu_kararlar": {},
        }

    def kaydet(
        self,
        karar_taslaklari: dict,
        muhurlu_kararlar: dict,
    ) -> str:
        veri = {
            "surum": self.SURUM,
            "karar_taslaklari": karar_taslaklari,
            "muhurlu_kararlar": muhurlu_kararlar,
        }

        durum_hashi = self._hash_hesapla(veri)

        belge = {
            **veri,
            "durum_hashi": durum_hashi,
        }

        fd, gecici_yol = tempfile.mkstemp(
            prefix=f"{self.dosya_yolu.name}.",
            suffix=".tmp",
            dir=str(self.dosya_yolu.parent),
            text=True,
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as dosya:
                json.dump(
                    belge,
                    dosya,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                dosya.write("\n")
                dosya.flush()
                os.fsync(dosya.fileno())

            os.replace(
                gecici_yol,
                self.dosya_yolu,
            )
        except Exception:
            try:
                os.unlink(gecici_yol)
            except FileNotFoundError:
                pass
            raise

        return durum_hashi

    def yukle(self) -> dict:
        if not self.dosya_yolu.exists():
            return self._bos_durum()

        try:
            belge = json.loads(
                self.dosya_yolu.read_text(
                    encoding="utf-8"
                )
            )
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as hata:
            raise ValueError(
                "Karar durum deposu okunamadi"
            ) from hata

        gerekli_alanlar = {
            "surum",
            "karar_taslaklari",
            "muhurlu_kararlar",
            "durum_hashi",
        }

        if set(belge) != gerekli_alanlar:
            raise ValueError(
                "Karar durum deposu alanlari gecersiz"
            )

        if belge["surum"] != self.SURUM:
            raise ValueError(
                f"Desteklenmeyen depo surumu: {belge['surum']}"
            )

        veri = {
            "surum": belge["surum"],
            "karar_taslaklari": belge["karar_taslaklari"],
            "muhurlu_kararlar": belge["muhurlu_kararlar"],
        }

        beklenen_hash = self._hash_hesapla(veri)

        if belge["durum_hashi"] != beklenen_hash:
            raise ValueError(
                "Karar durum deposu hash dogrulamasi basarisiz"
            )

        return veri

    def dogrula(self) -> bool:
        try:
            self.yukle()
        except ValueError:
            return False

        return True
