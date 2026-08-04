from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json



@dataclass
class ArsivManifestKaydi:

    cekirdek_kimligi: str

    toplam_dosya: int

    sha256sum_yolu: str

    manifest_yolu: str

    kapanis_sha256: str

    durum: str

    zaman: str




class SonArsivManifestSHAUretici:


    def __init__(self):

        self.kayitlar = {}



    def sha_hesapla(
        self,
        veri: str,
    ):

        return hashlib.sha256(
            veri.encode("utf-8")
        ).hexdigest()



    def olustur(
        self,
        cekirdek_kimligi: str,
        dosyalar: list,
        hedef: str,
    ):


        root = Path(
            hedef
        )

        root.mkdir(
            parents=True,
            exist_ok=True,
        )



        sha_kayitlari = []


        for dosya in dosyalar:

            sha = self.sha_hesapla(
                dosya["icerik"]
            )

            sha_kayitlari.append(

                f"{sha}  {dosya['adi']}"

            )



        sha_yolu = root / "SHA256SUMS.txt"


        sha_yolu.write_text(

            "\n".join(
                sha_kayitlari
            ),

            encoding="utf-8",

        )



        manifest = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "dosyalar":
                dosyalar,

        }



        manifest_icerik = json.dumps(

            manifest,

            sort_keys=True,

            ensure_ascii=False,

            indent=2,

        )



        manifest_yolu = root / "manifest.json"



        manifest_yolu.write_text(

            manifest_icerik,

            encoding="utf-8",

        )



        kapanis_sha256 = self.sha_hesapla(

            manifest_icerik
            +
            "\n"
            +
            "\n".join(
                sha_kayitlari
            )

        )



        kayit = ArsivManifestKaydi(

            cekirdek_kimligi,

            len(dosyalar),

            str(sha_yolu),

            str(manifest_yolu),

            kapanis_sha256,

            "son_arsiv_manifest_hazir",

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
        kayit: ArsivManifestKaydi,
    ):


        return (

            Path(
                kayit.sha256sum_yolu
            ).exists()

            and

            Path(
                kayit.manifest_yolu
            ).exists()

            and

            len(
                kayit.kapanis_sha256
            )
            ==
            64

        )
