from dataclasses import dataclass



@dataclass
class DenetimSonucu:

    cekirdek_kimligi: str

    toplam_sprint: int

    eksik_sprint: list[str]

    durum: str



class MuhurOncesiDenetim:


    def kontrol_et(
        self,
        cekirdek_kimligi: str,
        sprint_listesi: list[str],
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

        ]


        eksikler = [

            sprint

            for sprint

            in beklenen

            if sprint not in sprint_listesi

        ]


        if len(eksikler) == 0:

            durum = (
                "bagimsiz_dogrulandi"
            )

        else:

            durum = (
                "eksik_kayit_var"
            )


        return DenetimSonucu(

            cekirdek_kimligi,

            len(sprint_listesi),

            eksikler,

            durum,

        )
