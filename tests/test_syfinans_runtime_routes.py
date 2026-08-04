from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.syfinans_runtime_routes import (
    AlarmKuyrukIstegi,
    SyFinansRuntimeServisi,
    finans_router,
)


def istemci() -> TestClient:
    app = FastAPI()
    app.include_router(finans_router)
    return TestClient(app)


def test_runtime_snapshot_uretilir():
    yanit = istemci().get(
        "/syfinans/runtime"
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert veri["modul"] == "SyFinansOtağı"
    assert veri["sekmeler"] == [
        "piyasa",
        "kasam",
        "analiz",
        "planlar",
    ]
    assert veri["otomatik_al_sat"] is False
    assert len(veri["snapshot_sha256"]) == 64


def test_dort_finans_sekmesi_yayinlanir():
    client = istemci()

    for sekme in (
        "piyasa",
        "kasam",
        "analiz",
        "planlar",
    ):
        yanit = client.get(
            f"/syfinans/sekmeler/{sekme}"
        )

        assert yanit.status_code == 200

        veri = yanit.json()

        assert veri["sekme"] == sekme
        assert len(veri["sozlesme_sha256"]) == 64


def test_bilinmeyen_sekme_404_doner():
    yanit = istemci().get(
        "/syfinans/sekmeler/bilinmeyen"
    )

    assert yanit.status_code == 404


def test_uc_cihaz_profili_yayinlanir():
    yanit = istemci().get(
        "/syfinans/cihaz-profilleri"
    )

    assert yanit.status_code == 200

    profiller = {
        profil["profil_id"]
        for profil
        in yanit.json()["profiller"]
    }

    assert profiller == {
        "iphone",
        "samsung_tab_a_2019_8",
        "masaustu",
    }


def test_kaynak_durumlari_yayinlanir():
    yanit = istemci().get(
        "/syfinans/kaynaklar"
    )

    assert yanit.status_code == 200

    kaynaklar = {
        kaynak["kaynak_id"]: kaynak
        for kaynak
        in yanit.json()["kaynaklar"]
    }

    assert kaynaklar["tcmb"]["durum"] == "hazir"
    assert kaynaklar["bist"]["durum"] == "beklemede"
    assert kaynaklar["tefas"]["durum"] == "beklemede"


def test_alarm_kuyruga_alinir():
    client = istemci()

    yanit = client.post(
        "/syfinans/alarmlar",
        json={
            "alarm_id": "ASELS-450",
            "alarm_turu": "fiyat",
            "sembol": "ASELS",
            "baslik": "Fiyat hedefine ulaşıldı",
            "mesaj": (
                "ASELS izlenen fiyat "
                "seviyesine ulaştı."
            ),
            "onem": "dikkat",
        },
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert veri["durum"] == "kuyruga_alindi"
    assert len(
        veri["alarm"]["alarm_sha256"]
    ) == 64


def test_ayni_alarm_tekrar_kuyruga_alinmaz():
    servis = SyFinansRuntimeServisi()

    istek = AlarmKuyrukIstegi(
        alarm_id="TEKRAR-001",
        alarm_turu="fiyat",
        sembol="ASELS",
        baslik="Deneme",
        mesaj="Deneme alarmı",
    )

    ilk = servis.alarm_ekle(istek)
    ikinci = servis.alarm_ekle(istek)

    assert ilk["durum"] == "kuyruga_alindi"
    assert ikinci["durum"] == "tekrar_engellendi"