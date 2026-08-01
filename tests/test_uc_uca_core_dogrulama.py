from syk_core.entegrasyon.uc_uca_core_dogrulama import (
    UcUcaCoreDogrulama,
)


class SahteCore:


    def degerlendir(
        self,
        olay,
        veri,
    ):

        class Sonuc:

            kanitlar = [
                "KANIT-001"
            ]

            goruntu_sonuclari = [
                "GOR-001"
            ]

            guven_puani = 90

            konsensus_puani = 90


        return Sonuc()



class SahteOlayZinciri:


    def __init__(self):

        self.kayit = {}



    def kaydet(
        self,
        olay,
    ):

        self.kayit[olay] = True



    def kanit_ekle(
        self,
        olay,
        kanit,
    ):

        pass



    def uzman_sonucu_ekle(
        self,
        olay,
        sonuc,
    ):

        pass



class SahteHash:


    def paket_olustur(
        self,
        *args,
    ):

        return {
            "hash":
            "64-KARAKTER-HASH"
        }



def test_uc_uca_core_dogrulama():

    sistem = UcUcaCoreDogrulama(
        SahteOlayZinciri(),
        SahteCore(),
        SahteHash(),
    )


    sonuc = sistem.calistir(
        "SPRINT-038",
        "VERI",
    )


    assert (
        sonuc["hash"]
        ==
        "64-KARAKTER-HASH"
    )
