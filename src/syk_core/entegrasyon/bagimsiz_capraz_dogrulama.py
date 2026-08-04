from dataclasses import dataclass


@dataclass
class CaprazDogrulamaSonucu:

    cekirdek_kimligi: str

    kontrol_sprint_sayisi: int

    kontrol_modul_sayisi: int

    eksikler: list[str]

    durum: str



class BagimsizCaprazDogrulama:


    def kontrol_et(
        self,
        cekirdek_kimligi: str,
        sprint_listesi: list[str],
        modul_listesi: list[str],
    ):


        beklenen_sprintler = [

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
            "SPRINT-053",
            "SPRINT-054",
            "SPRINT-055",

        ]


        beklenen_moduller = [

            "HASH",
            "KANIT",
            "MANIFEST",
            "UZMAN_AGI",
            "KARAR",
            "RAPOR",
            "MUHUR",
            "DEVIR",

        ]


        eksikler = []


        for sprint in beklenen_sprintler:

            if sprint not in sprint_listesi:

                eksikler.append(
                    sprint
                )


        for modul in beklenen_moduller:

            if modul not in modul_listesi:

                eksikler.append(
                    modul
                )


        if len(eksikler) == 0:

            durum = (
                "bagimsiz_capraz_dogrulandi"
            )

        else:

            durum = (
                "eksik_kayit_var"
            )


        return CaprazDogrulamaSonucu(

            cekirdek_kimligi,

            len(
                sprint_listesi
            ),

            len(
                modul_listesi
            ),

            eksikler,

            durum,

        )
