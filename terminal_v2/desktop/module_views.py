from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModulGorunumu:
    baslik: str
    aciklama: str
    durum: str


MODUL_GORUNUMLERI = {
    "dashboard": ModulGorunumu(
        baslik="Ana Çalışma Alanı",
        aciklama=(
            "Sistem durumu, bağlı cihazlar ve aktif görevler "
            "bu çalışma alanında gösterilecek."
        ),
        durum="Ana çalışma alanı hazır.",
    ),
    "harita": ModulGorunumu(
        baslik="Canlı Harita",
        aciklama=(
            "Araştırma noktaları, rotalar, ölçümler ve saha "
            "verileri bu panelde görüntülenecek."
        ),
        durum="Harita çalışma alanı aktif.",
    ),
    "kanit": ModulGorunumu(
        baslik="Kanıt Yönetimi",
        aciklama=(
            "Fotoğraf, video, ses, ölçüm ve doğrulama kayıtları "
            "bu panelde yönetilecek."
        ),
        durum="Kanıt çalışma alanı aktif.",
    ),
    "analiz": ModulGorunumu(
        baslik="Analiz Paneli",
        aciklama=(
            "Canlı veriler, bilimsel incelemeler ve yapay zekâ "
            "destekli değerlendirmeler burada çalışacak."
        ),
        durum="Analiz çalışma alanı aktif.",
    ),
    "rapor": ModulGorunumu(
        baslik="Rapor Merkezi",
        aciklama=(
            "Mühürlü dijital raporlar, kanıt zinciri ve sonuç "
            "çıktıları bu panelden hazırlanacak."
        ),
        durum="Rapor çalışma alanı aktif.",
    ),
    "gorev": ModulGorunumu(
        baslik="Görev Takibi",
        aciklama=(
            "Aktif görevler, saha adımları ve tamamlanma "
            "durumları bu panelde izlenecek."
        ),
        durum="Görev çalışma alanı aktif.",
    ),
    "sensorler": ModulGorunumu(
        baslik="Bilimsel Sensörler",
        aciklama=(
            "Bağlı sensörler, veri kaynakları ve cihaz durumları "
            "bu panelde görüntülenecek."
        ),
        durum="Bilimsel sensör çalışma alanı aktif.",
    ),
}


def modul_gorunumu_getir(modul_kodu: str) -> ModulGorunumu:
    kod = modul_kodu.strip().lower()

    return MODUL_GORUNUMLERI.get(
        kod,
        ModulGorunumu(
            baslik=kod.replace("_", " ").title() or "Çalışma Alanı",
            aciklama="Seçilen modülün çalışma alanı hazırlanıyor.",
            durum="Modül çalışma alanı aktif.",
        ),
    )
