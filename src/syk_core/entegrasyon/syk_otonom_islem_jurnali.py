from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import tempfile


class SYKOtonomIslemJurnali:
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

    def _atomik_yaz(self, belge: dict):
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

    def baslat(
        self,
        islem_id: str,
        karar_id: str,
        olay_kimligi: str,
        islem_turu: str,
    ) -> dict:
        if self.dosya_yolu.exists():
            mevcut = self.yukle()

            if mevcut["durum"] == "HAZIRLANIYOR":
                raise RuntimeError(
                    f"Tamamlanmamis islem mevcut: "
                    f"{mevcut['islem_id']}"
                )

        veri = {
            "surum": self.SURUM,
            "islem_id": islem_id,
            "karar_id": karar_id,
            "olay_kimligi": olay_kimligi,
            "islem_turu": islem_turu,
            "durum": "HAZIRLANIYOR",
            "baslama_zamani": datetime.now(
                timezone.utc
            ).isoformat(),
            "tamamlanma_zamani": "",
            "hata": "",
        }

        belge = {
            **veri,
            "islem_hashi": self._hash_hesapla(veri),
        }

        self._atomik_yaz(belge)
        return belge

    def tamamla(self, islem_id: str) -> dict:
        belge = self.yukle()

        if belge["islem_id"] != islem_id:
            raise ValueError(
                f"Islem kimligi uyusmuyor: {islem_id}"
            )

        if belge["durum"] != "HAZIRLANIYOR":
            raise ValueError(
                f"Islem tamamlanabilir durumda degil: "
                f"{belge['durum']}"
            )

        veri = {
            "surum": belge["surum"],
            "islem_id": belge["islem_id"],
            "karar_id": belge["karar_id"],
            "olay_kimligi": belge["olay_kimligi"],
            "islem_turu": belge["islem_turu"],
            "durum": "TAMAMLANDI",
            "baslama_zamani": belge["baslama_zamani"],
            "tamamlanma_zamani": datetime.now(
                timezone.utc
            ).isoformat(),
            "hata": "",
        }

        tamamlanan = {
            **veri,
            "islem_hashi": self._hash_hesapla(veri),
        }

        self._atomik_yaz(tamamlanan)
        return tamamlanan

    def basarisiz(
        self,
        islem_id: str,
        hata: str,
    ) -> dict:
        belge = self.yukle()

        if belge["islem_id"] != islem_id:
            raise ValueError(
                f"Islem kimligi uyusmuyor: {islem_id}"
            )

        if belge["durum"] != "HAZIRLANIYOR":
            raise ValueError(
                f"Islem basarisiz olarak kapatilabilir durumda degil: "
                f"{belge['durum']}"
            )

        hata = str(hata).strip()

        if not hata:
            raise ValueError(
                "Basarisiz islem icin hata aciklamasi zorunludur"
            )

        veri = {
            "surum": belge["surum"],
            "islem_id": belge["islem_id"],
            "karar_id": belge["karar_id"],
            "olay_kimligi": belge["olay_kimligi"],
            "islem_turu": belge["islem_turu"],
            "durum": "BASARISIZ",
            "baslama_zamani": belge["baslama_zamani"],
            "tamamlanma_zamani": datetime.now(
                timezone.utc
            ).isoformat(),
            "hata": hata,
        }

        basarisiz_belge = {
            **veri,
            "islem_hashi": self._hash_hesapla(veri),
        }

        self._atomik_yaz(basarisiz_belge)
        return basarisiz_belge

    def yukle(self) -> dict:
        if not self.dosya_yolu.exists():
            raise FileNotFoundError(
                f"Islem jurnali bulunamadi: {self.dosya_yolu}"
            )

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
                "Islem jurnali okunamadi"
            ) from hata

        gerekli_alanlar = {
            "surum",
            "islem_id",
            "karar_id",
            "olay_kimligi",
            "islem_turu",
            "durum",
            "baslama_zamani",
            "tamamlanma_zamani",
            "hata",
            "islem_hashi",
        }

        if set(belge) != gerekli_alanlar:
            raise ValueError(
                "Islem jurnali alanlari gecersiz"
            )

        if belge["surum"] != self.SURUM:
            raise ValueError(
                f"Desteklenmeyen jurnal surumu: "
                f"{belge['surum']}"
            )

        veri = {
            alan: belge[alan]
            for alan in gerekli_alanlar
            if alan != "islem_hashi"
        }

        if belge["islem_hashi"] != self._hash_hesapla(veri):
            raise ValueError(
                "Islem jurnali hash dogrulamasi basarisiz"
            )

        return belge

    def bekleyen_islem(self):
        if not self.dosya_yolu.exists():
            return None

        belge = self.yukle()

        if belge["durum"] == "HAZIRLANIYOR":
            return belge

        return None

    def temizle(self):
        if self.dosya_yolu.exists():
            self.dosya_yolu.unlink()

    def dogrula(self) -> bool:
        if not self.dosya_yolu.exists():
            return True

        try:
            self.yukle()
        except (
            ValueError,
            FileNotFoundError,
        ):
            return False

        return True
