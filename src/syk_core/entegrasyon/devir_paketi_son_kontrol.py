from dataclasses import dataclass


@dataclass
class DevirKontrolSonucu:

    cekirdek_kimligi: str

    kontrol_edilen_sprint: int

    eksik_sprint: list[str]

    modul_sayisi: int

    durum: str



class DevirPaketiSonKontrol:


    def kontrol_et(
        self,
        cekirdek_kimligi: str,
        sprint_listesi: list[str],
        modul_listesi: list[str],
    ):

        beklenen = [

            "SPRINT-035",
            "SPRINT-036",
            "SPRINT-037",
            "SPRINT-038",
            "SPRINT-039",
            "SPRINT-040",
            "SPRINT-041",
            "SPRINT-042",
            "SPRINT-043",
            "SPRINT-044",
            "SPRINT-045",
            "SPRINT-046",
            "SPRINT-047",
            "SPRINT-048",
            "SPRINT-049",
            "SPRINT-050",
            "SPRINT-051",
            "SPRINT-052",

        ]


        eksikler = [

            sprint

            for sprint
            in beklenen

            if sprint not in sprint_listesi

        ]


        if len(eksikler) == 0:

            durum = (
                "devir_adayi_hazir"
            )

        else:

            durum = (
                "eksik_kayit_var"
            )


        return DevirKontrolSonucu(

            cekirdek_kimligi,

            len(sprint_listesi),

            eksikler,

            len(modul_listesi),

            durum,

        )
