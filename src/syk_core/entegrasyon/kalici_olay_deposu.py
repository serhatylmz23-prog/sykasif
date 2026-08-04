from dataclasses import dataclass, asdict
from pathlib import Path
import json



@dataclass
class KaliciOlayKaydi:

    olay_kimligi: str

    kanitlar: list[str]

    uzman_sonuclari: list[str]

    guven_puani: float

    konsensus_puani: float



class KaliciOlayDeposu:


    def __init__(
        self,
        klasor="syk_arsiv"
    ):

        self.klasor = Path(
            klasor
        )

        self.klasor.mkdir(
            parents=True,
            exist_ok=True
        )



    def kaydet(
        self,
        kayit: KaliciOlayKaydi,
    ):

        hedef = (
            self.klasor
            /
            f"{kayit.olay_kimligi}.json"
        )


        hedef.write_text(
            json.dumps(
                asdict(kayit),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


        return hedef



    def yukle(
        self,
        olay_kimligi: str,
    ):

        hedef = (
            self.klasor
            /
            f"{olay_kimligi}.json"
        )


        if not hedef.exists():

            return None



        veri = json.loads(
            hedef.read_text(
                encoding="utf-8"
            )
        )


        return KaliciOlayKaydi(
            **veri
        )



    def mevcut_mu(
        self,
        olay_kimligi: str,
    ):

        return (
            self.klasor
            /
            f"{olay_kimligi}.json"
        ).exists()
