from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json


@dataclass
class ManifestKaydi:

    cekirdek_kimligi: str

    artefakt_sayisi: int

    manifest_yolu: str

    manifest_sha256: str

    durum: str

    zaman: str



class GercekRepoManifestKayitMotoru:


    def __init__(self):

        self.kayitlar = {}



    def sha_hesapla(
        self,
        veri: str,
    ):

        return hashlib.sha256(
            veri.encode("utf-8")
        ).hexdigest()



    def manifest_uret(
        self,
        cekirdek_kimligi: str,
        artefaktlar: list,
        hedef_yol: str,
    ):

        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "artefaktlar":
                artefaktlar,

        }


        icerik = json.dumps(
            veri,
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
        )


        yol = Path(
            hedef_yol
        )

        yol.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


        yol.write_text(
            icerik,
            encoding="utf-8",
        )


        sha = self.sha_hesapla(
            icerik
        )


        kayit = ManifestKaydi(

            cekirdek_kimligi,

            len(
                artefaktlar
            ),

            str(yol),

            sha,

            "kalici_manifest_uretildi",

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            cekirdek_kimligi
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: ManifestKaydi,
    ):

        yol = Path(
            kayit.manifest_yolu
        )


        if not yol.exists():

            return False


        icerik = yol.read_text(
            encoding="utf-8"
        )


        return (
            self.sha_hesapla(
                icerik
            )
            ==
            kayit.manifest_sha256
        )
