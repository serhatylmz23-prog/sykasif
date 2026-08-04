import hashlib
from dataclasses import dataclass



@dataclass
class KanitHashKaydi:

    kanit_kimligi: str

    veri_hashi: str

    durum: str = "kayitli"



class KanitSHA256Dogrulama:


    def __init__(self):

        self.kayitlar = {}



    def hash_uret(
        self,
        veri: str,
    ):

        return hashlib.sha256(
            veri.encode("utf-8")
        ).hexdigest()



    def kaydet(
        self,
        kanit_kimligi: str,
        veri: str,
    ):

        hash_degeri = self.hash_uret(
            veri
        )

        kayit = KanitHashKaydi(
            kanit_kimligi,
            hash_degeri,
        )

        self.kayitlar[
            kanit_kimligi
        ] = kayit

        return kayit



    def dogrula(
        self,
        kanit_kimligi: str,
        veri: str,
    ):

        kayit = self.kayitlar.get(
            kanit_kimligi
        )


        if kayit is None:
            return False


        yeni_hash = self.hash_uret(
            veri
        )


        return (
            yeni_hash
            ==
            kayit.veri_hashi
        )



    def getir(
        self,
        kanit_kimligi: str,
    ):

        return self.kayitlar.get(
            kanit_kimligi
        )
