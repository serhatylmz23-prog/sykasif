from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModulGorunumu:
    baslik: str
    aciklama: str
    durum: str
    islemler: tuple[str, ...]

    @property
    def islem_metni(self) -> str:
        return "\n".join(
            f"• {islem}"
            for islem in self.islemler
        )


MODUL_GORUNUMLERI = {
    "dashboard": ModulGorunumu(
        baslik="Ana Çalışma Alanı",
        aciklama=(
            "Sistem durumu, bağlı cihazlar ve aktif görevler "
            "bu çalışma alanında gösterilir."
        ),
        durum="Ana çalışma alanı hazır.",
        islemler=(
            "Runtime bağlantı durumunu izle",
            "Bağlı cihazları görüntüle",
            "Aktif görevleri takip et",
            "Son bildirimleri incele",
        ),
    ),
    "harita": ModulGorunumu(
        baslik="Canlı Harita",
        aciklama=(
            "Araştırma noktaları, rotalar, ölçümler ve saha "
            "verileri bu panelde görüntülenir."
        ),
        durum="Harita çalışma alanı aktif.",
        islemler=(
            "Araştırma noktalarını görüntüle",
            "Canlı konum ve rota takibi yap",
            "Harita katmanlarını yönet",
            "Fotoğraf ve ölçüm işaretlerini aç",
        ),
    ),
    "kanit": ModulGorunumu(
        baslik="Kanıt Yönetimi",
        aciklama=(
            "Fotoğraf, video, ses, ölçüm ve doğrulama kayıtları "
            "bu panelde yönetilir."
        ),
        durum="Kanıt çalışma alanı aktif.",
        islemler=(
            "Yeni kanıt kaydı oluştur",
            "Kanıt zincirini doğrula",
            "Fotoğraf ve videoları incele",
            "Manifest ve SHA kayıtlarını görüntüle",
        ),
    ),
    "analiz": ModulGorunumu(
        baslik="Analiz Paneli",
        aciklama=(
            "Canlı veriler, bilimsel incelemeler ve yapay zekâ "
            "destekli değerlendirmeler burada çalışır."
        ),
        durum="Analiz çalışma alanı aktif.",
        islemler=(
            "Yeni analiz başlat",
            "Canlı verileri karşılaştır",
            "Bilimsel bulguları görüntüle",
            "Doğrulama sonuçlarını incele",
        ),
    ),
    "rapor": ModulGorunumu(
        baslik="Rapor Merkezi",
        aciklama=(
            "Mühürlü dijital raporlar, kanıt zinciri ve sonuç "
            "çıktıları bu panelden hazırlanır."
        ),
        durum="Rapor çalışma alanı aktif.",
        islemler=(
            "Yeni rapor oluştur",
            "Kanıt bloklarını rapora ekle",
            "Manifest ve SHA üret",
            "Mühürlü rapor çıktısını hazırla",
        ),
    ),
    "gorev": ModulGorunumu(
        baslik="Görev Takibi",
        aciklama=(
            "Aktif görevler, saha adımları ve tamamlanma "
            "durumları bu panelde izlenir."
        ),
        durum="Görev çalışma alanı aktif.",
        islemler=(
            "Yeni görev oluştur",
            "Görev durumunu güncelle",
            "Saha adımlarını takip et",
            "Tamamlanan görevleri görüntüle",
        ),
    ),
    "sensorler": ModulGorunumu(
        baslik="Bilimsel Sensörler",
        aciklama=(
            "Bağlı sensörler, veri kaynakları ve cihaz durumları "
            "bu panelde görüntülenir."
        ),
        durum="Bilimsel sensör çalışma alanı aktif.",
        islemler=(
            "Bağlı sensörleri görüntüle",
            "Canlı veri akışını izle",
            "Sensör durumlarını doğrula",
            "Yeni cihaz bağlantısı başlat",
        ),
    ),
}


def modul_gorunumu_getir(
    modul_kodu: str,
) -> ModulGorunumu:
    kod = modul_kodu.strip().lower()

    return MODUL_GORUNUMLERI.get(
        kod,
        ModulGorunumu(
            baslik=(
                kod.replace("_", " ").title()
                or "Çalışma Alanı"
            ),
            aciklama=(
                "Seçilen modülün çalışma alanı hazırlanıyor."
            ),
            durum="Modül çalışma alanı aktif.",
            islemler=(
                "Modül durumunu görüntüle",
                "Canlı veriyi takip et",
            ),
        ),
    )
