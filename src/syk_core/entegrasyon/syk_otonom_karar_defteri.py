from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json


@dataclass(frozen=True)
class OtonomKararDefteriKaydi:
    sira: int
    olay_kimligi: str
    karar_id: str
    islem: str
    durum: str
    onaylayan: str
    karar_sha256: str
    onceki_kayit_hashi: str
    zaman: str
    kayit_hashi: str


class SYKOtonomKararDefteri:
    ILK_HASH = "0" * 64

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

    def kayitlari_oku(self) -> list[OtonomKararDefteriKaydi]:
        if not self.dosya_yolu.exists():
            return []

        kayitlar = []

        with self.dosya_yolu.open(
            "r",
            encoding="utf-8",
        ) as dosya:
            for satir_no, satir in enumerate(
                dosya,
                start=1,
            ):
                satir = satir.strip()

                if not satir:
                    continue

                try:
                    veri = json.loads(satir)
                    kayitlar.append(
                        OtonomKararDefteriKaydi(**veri)
                    )
                except (
                    json.JSONDecodeError,
                    TypeError,
                ) as hata:
                    raise ValueError(
                        f"Gecersiz karar defteri satiri: {satir_no}"
                    ) from hata

        return kayitlar

    def ekle(
        self,
        olay_kimligi: str,
        karar_id: str,
        islem: str,
        durum: str,
        onaylayan: str,
        karar_sha256: str,
    ) -> OtonomKararDefteriKaydi:
        if not self.dogrula():
            raise ValueError(
                "Karar defteri butunlugu bozuk; "
                "yeni kayit eklenemez"
            )

        mevcut = self.kayitlari_oku()

        onceki_hash = (
            mevcut[-1].kayit_hashi
            if mevcut
            else self.ILK_HASH
        )

        temel_veri = {
            "sira": len(mevcut) + 1,
            "olay_kimligi": olay_kimligi,
            "karar_id": karar_id,
            "islem": islem,
            "durum": durum,
            "onaylayan": onaylayan,
            "karar_sha256": karar_sha256,
            "onceki_kayit_hashi": onceki_hash,
            "zaman": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        kayit_hashi = self._hash_hesapla(
            temel_veri
        )

        kayit = OtonomKararDefteriKaydi(
            **temel_veri,
            kayit_hashi=kayit_hashi,
        )

        with self.dosya_yolu.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as dosya:
            dosya.write(
                json.dumps(
                    asdict(kayit),
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            dosya.write("\n")

        return kayit

    def dogrula(self) -> bool:
        try:
            kayitlar = self.kayitlari_oku()
        except ValueError:
            return False

        onceki_hash = self.ILK_HASH

        for beklenen_sira, kayit in enumerate(
            kayitlar,
            start=1,
        ):
            if kayit.sira != beklenen_sira:
                return False

            if kayit.onceki_kayit_hashi != onceki_hash:
                return False

            veri = asdict(kayit)
            kayit_hashi = veri.pop("kayit_hashi")

            if self._hash_hesapla(veri) != kayit_hashi:
                return False

            onceki_hash = kayit.kayit_hashi

        return True
