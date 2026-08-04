from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class DosyaSHAKaydi:

    dosya_yolu: str

    dosya_boyutu: int

    sha256: str

    durum: str



class GercekDosyaSHATarayici:


    def __init__(self):

        self.kayitlar = {}



    def sha_hesapla(
        self,
        dosya_yolu: str,
    ):

        yol = Path(
            dosya_yolu
        )

        if not yol.exists():

            return None


        sha256 = hashlib.sha256()


        with yol.open(
            "rb"
        ) as dosya:

            while True:

                parca = dosya.read(
                    8192
                )

                if not parca:

                    break

                sha256.update(
                    parca
                )


        return sha256.hexdigest()



    def tara(
        self,
        dosya_yolu: str,
    ):

        yol = Path(
            dosya_yolu
        )


        sha = self.sha_hesapla(
            dosya_yolu
        )


        if sha is None:

            return None


        kayit = DosyaSHAKaydi(

            dosya_yolu,

            yol.stat().st_size,

            sha,

            "gercek_sha_uretildi",

        )


        self.kayitlar[
            dosya_yolu
        ] = kayit


        return kayit



    def dogrula(
        self,
        dosya_yolu: str,
    ):

        kayit = self.kayitlar.get(
            dosya_yolu
        )


        if kayit is None:

            return False


        yeni_sha = self.sha_hesapla(
            dosya_yolu
        )


        return (
            yeni_sha
            ==
            kayit.sha256
        )
