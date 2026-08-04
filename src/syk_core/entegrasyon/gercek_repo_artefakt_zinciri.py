from dataclasses import dataclass
from pathlib import Path
import hashlib
import json


@dataclass
class RepoArtefaktKaydi:

    dosya_yolu: str

    dosya_turu: str

    boyut: int

    sha256: str


@dataclass
class RepoZincirSonucu:

    toplam_artefakt: int

    toplam_boyut: int

    manifest_sha256: str

    durum: str



class GercekRepoArtefaktZinciri:


    def __init__(self):

        self.kayitlar = []



    def sha_hesapla(
        self,
        dosya_yolu: str,
    ):

        sha = hashlib.sha256()

        with open(
            dosya_yolu,
            "rb",
        ) as dosya:

            while True:

                parca = dosya.read(
                    8192
                )

                if not parca:

                    break

                sha.update(
                    parca
                )

        return sha.hexdigest()



    def tara(
        self,
        klasor: str,
        uzantilar: tuple = (
            ".py",
            ".md",
            ".txt",
        ),
    ):

        root = Path(
            klasor
        )

        self.kayitlar = []

        for dosya in root.rglob("*"):

            if (
                dosya.is_file()
                and
                dosya.suffix in uzantilar
            ):

                sha = self.sha_hesapla(
                    str(dosya)
                )

                kayit = RepoArtefaktKaydi(
                    str(dosya),
                    dosya.suffix,
                    dosya.stat().st_size,
                    sha,
                )

                self.kayitlar.append(
                    kayit
                )

        return self.kayitlar



    def manifest_uret(
        self,
    ):

        veri = [

            {
                "dosya":
                    x.dosya_yolu,

                "sha256":
                    x.sha256,

                "boyut":
                    x.boyut,

            }

            for x in self.kayitlar

        ]


        temiz = json.dumps(
            veri,
            sort_keys=True,
            ensure_ascii=False,
        )


        return hashlib.sha256(
            temiz.encode(
                "utf-8"
            )
        ).hexdigest()



    def zincir_olustur(
        self,
    ):

        toplam_boyut = sum(
            x.boyut
            for x in self.kayitlar
        )


        manifest = self.manifest_uret()


        return RepoZincirSonucu(

            len(
                self.kayitlar
            ),

            toplam_boyut,

            manifest,

            "gercek_repo_zinciri_hazir",

        )
