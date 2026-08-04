from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json



@dataclass
class KanitManifestKaydi:

    kanit_kimligi: str

    dosya_adi: str

    sha256: str

    durum: str = "kayitli"



class KanitPaketManifest:


    def __init__(
        self,
        klasor="syk_kanit_arsiv"
    ):

        self.klasor = Path(
            klasor
        )

        self.klasor.mkdir(
            parents=True,
            exist_ok=True
        )

        self.manifestler = {}



    def hash_uret(
        self,
        veri: bytes,
    ):

        return hashlib.sha256(
            veri
        ).hexdigest()



    def paket_kaydet(
        self,
        kanit_kimligi: str,
        veri: str,
    ):

        dosya = (
            self.klasor
            /
            f"{kanit_kimligi}.txt"
        )


        veri_byte = veri.encode(
            "utf-8"
        )


        dosya.write_bytes(
            veri_byte
        )


        hash_degeri = self.hash_uret(
            veri_byte
        )


        kayit = KanitManifestKaydi(
            kanit_kimligi,
            dosya.name,
            hash_degeri,
        )


        self.manifestler[
            kanit_kimligi
        ] = kayit


        manifest = (
            self.klasor
            /
            "MANIFEST.json"
        )


        manifest.write_text(
            json.dumps(
                {
                    k: asdict(v)
                    for k, v
                    in self.manifestler.items()
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


        return kayit



    def dogrula(
        self,
        kanit_kimligi: str,
    ):

        kayit = self.manifestler.get(
            kanit_kimligi
        )


        if kayit is None:

            return False


        dosya = (
            self.klasor
            /
            kayit.dosya_adi
        )


        if not dosya.exists():

            return False


        mevcut_hash = self.hash_uret(
            dosya.read_bytes()
        )


        return (
            mevcut_hash
            ==
            kayit.sha256
        )
