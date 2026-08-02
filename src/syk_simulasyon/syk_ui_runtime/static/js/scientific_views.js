(() => {
    const modules = {
        geology: {
            title: "JEOLOJİ",
            subtitle: "Katman, kayaç, fay ve mineral inceleme paneli",
            unit: "m",
            liveValue: "12.48",
            metrics: [
                ["Katman Derinliği", "12.48 m", "Aktif kesit"],
                ["Kayaç Sınıfı", "Kireçtaşı", "Ön sınıflandırma"],
                ["Fay Yakınlığı", "184 m", "Referans uzaklık"],
                ["Mineral İşareti", "3", "İncelenecek alan"],
            ],
            fields: [
                ["Yüzey Yapısı", "Sedimanter"],
                ["Katman Sayısı", "5"],
                ["Eğim", "14.7°"],
                ["Nem Etkisi", "Orta"],
            ],
            layers: [
                ["Yüzey", "Aktif"],
                ["Toprak", "Aktif"],
                ["Kayaç", "Aktif"],
                ["Mineral", "Ön izleme"],
            ],
            confidence: 82,
        },

        frequency: {
            title: "FREKANS",
            subtitle: "Rezonans, titreşim ve sinyal yoğunluğu paneli",
            unit: "Hz",
            liveValue: "847.20",
            metrics: [
                ["Ana Frekans", "847.20 Hz", "Canlı örnek"],
                ["Bant Genişliği", "41.8 Hz", "Filtrelenmiş"],
                ["Sinyal Gücü", "-32 dB", "Kararlı"],
                ["Gürültü", "-71 dB", "Düşük"],
            ],
            fields: [
                ["Örnekleme", "44.1 kHz"],
                ["Filtre", "Bant geçiren"],
                ["Rezonans", "Orta"],
                ["Kanal", "A-01"],
            ],
            layers: [
                ["Ham Sinyal", "Aktif"],
                ["Filtreli", "Aktif"],
                ["Rezonans", "Aktif"],
                ["Referans", "Hazır"],
            ],
            confidence: 88,
        },

        lidar: {
            title: "LiDAR",
            subtitle: "Üç boyutlu nokta bulutu ve yüzey tarama paneli",
            unit: "nokta",
            liveValue: "1.28M",
            metrics: [
                ["Nokta Sayısı", "1.28M", "Ön görünüm"],
                ["Tarama Alanı", "84 m²", "Seçili bölge"],
                ["Yükseklik Farkı", "3.42 m", "Maksimum"],
                ["Yoğunluk", "92%", "Yeterli"],
            ],
            fields: [
                ["Tarama Modu", "3B yüzey"],
                ["Çözünürlük", "Yüksek"],
                ["Kayıp Bölge", "%4.2"],
                ["Koordinat", "Yerel"],
            ],
            layers: [
                ["Nokta Bulutu", "Aktif"],
                ["Yüzey", "Aktif"],
                ["Yükseklik", "Aktif"],
                ["Anomali", "Ön izleme"],
            ],
            confidence: 91,
        },

        astronomy: {
            title: "ASTRONOMİ / ARKEOASTRONOMİ",
            subtitle: "Gökyüzü doğrultusu ve tarihsel hizalanma paneli",
            unit: "°",
            liveValue: "127.40",
            metrics: [
                ["Azimut", "127.40°", "Güncel doğrultu"],
                ["Yükseklik", "34.18°", "Ufuk üstü"],
                ["Güneş Açısı", "18.72°", "Hesaplanan"],
                ["Hizalanma", "%76", "Ön değerlendirme"],
            ],
            fields: [
                ["Gökyüzü Durumu", "Açık"],
                ["Ay Evresi", "Referans"],
                ["Ufuk Profili", "Doğu"],
                ["Tarih Katmanı", "Seçili"],
            ],
            layers: [
                ["Güneş", "Aktif"],
                ["Ay", "Aktif"],
                ["Yıldız", "Referans"],
                ["Yapı Ekseni", "Aktif"],
            ],
            confidence: 76,
        },

        chemistry: {
            title: "KİMYASAL ANALİZ",
            subtitle: "Numune bileşimi ve element işareti paneli",
            unit: "ppm",
            liveValue: "24.80",
            metrics: [
                ["Ana İşaret", "Fe", "Ön sonuç"],
                ["Yoğunluk", "24.8 ppm", "Örnek değer"],
                ["pH", "7.18", "Nötr yakın"],
                ["Numune", "K-014", "Seçili"],
            ],
            fields: [
                ["Numune Türü", "Toprak"],
                ["Hazırlama", "Kuru"],
                ["Referans", "Laboratuvar"],
                ["Durum", "İnceleniyor"],
            ],
            layers: [
                ["Element", "Aktif"],
                ["Bileşik", "Ön izleme"],
                ["Referans", "Aktif"],
                ["Sapma", "Aktif"],
            ],
            confidence: 79,
        },

        spectral: {
            title: "SPEKTRAL ANALİZ",
            subtitle: "Dalga boyu, yansıma ve bant karşılaştırma paneli",
            unit: "nm",
            liveValue: "742.6",
            metrics: [
                ["Ana Bant", "742.6 nm", "Yakın kızılötesi"],
                ["Yansıma", "%63", "Ön değer"],
                ["Bant Sayısı", "12", "Aktif"],
                ["Sapma", "%8.4", "Referansa göre"],
            ],
            fields: [
                ["Spektrum", "Görünür + NIR"],
                ["Kalibrasyon", "Uygulandı"],
                ["Referans", "Beyaz yüzey"],
                ["Örnek", "SP-008"],
            ],
            layers: [
                ["Görünür", "Aktif"],
                ["NIR", "Aktif"],
                ["Yansıma", "Aktif"],
                ["Referans", "Hazır"],
            ],
            confidence: 84,
        },

        thermal: {
            title: "TERMAL ANALİZ",
            subtitle: "Sıcaklık dağılımı ve termal sapma paneli",
            unit: "°C",
            liveValue: "24.72",
            metrics: [
                ["Ortalama", "24.72 °C", "Seçili alan"],
                ["Minimum", "19.84 °C", "Soğuk bölge"],
                ["Maksimum", "31.16 °C", "Sıcak bölge"],
                ["Sapma", "6.44 °C", "İncelenmeli"],
            ],
            fields: [
                ["Palet", "Uyarlanabilir"],
                ["Emisivite", "0.94"],
                ["Ortam", "23.1 °C"],
                ["Durum", "Kararlı"],
            ],
            layers: [
                ["Ham Termal", "Aktif"],
                ["Soğuk Bölge", "Aktif"],
                ["Sıcak Bölge", "Aktif"],
                ["Sapma", "Aktif"],
            ],
            confidence: 87,
        },

        magnetometer: {
            title: "MANYETOMETRE",
            subtitle: "Manyetik alan yoğunluğu ve sapma paneli",
            unit: "nT",
            liveValue: "48,720",
            metrics: [
                ["Toplam Alan", "48,720 nT", "Canlı değer"],
                ["Sapma", "184 nT", "Yerel fark"],
                ["Yön", "Kuzeydoğu", "Ön yön"],
                ["Anomali", "2", "İncelenecek"],
            ],
            fields: [
                ["Sensör Ekseni", "XYZ"],
                ["Dengeleme", "Aktif"],
                ["Referans Alan", "48,536 nT"],
                ["Kanal", "M-02"],
            ],
            layers: [
                ["X Ekseni", "Aktif"],
                ["Y Ekseni", "Aktif"],
                ["Z Ekseni", "Aktif"],
                ["Toplam Alan", "Aktif"],
            ],
            confidence: 89,
        },

        gravimeter: {
            title: "GRAVİMETRE",
            subtitle: "Yerçekimi farkı ve yoğunluk sapması paneli",
            unit: "mGal",
            liveValue: "-2.84",
            metrics: [
                ["Yerel Fark", "-2.84 mGal", "Ön değer"],
                ["Referans", "0.00 mGal", "Kalibre"],
                ["Yoğunluk Farkı", "%12", "Tahmini"],
                ["Anomali", "1", "İncelenmeli"],
            ],
            fields: [
                ["Düzeltme", "Uygulandı"],
                ["Yükseklik", "742 m"],
                ["Ölçüm Süresi", "18 sn"],
                ["Durum", "Kararlı"],
            ],
            layers: [
                ["Ham Ölçüm", "Aktif"],
                ["Düzeltme", "Aktif"],
                ["Yoğunluk", "Ön izleme"],
                ["Anomali", "Aktif"],
            ],
            confidence: 74,
        },

        ert: {
            title: "ELEKTRİK DİRENÇ — ERT",
            subtitle: "Özdirenç kesiti ve yeraltı katman paneli",
            unit: "Ωm",
            liveValue: "184.6",
            metrics: [
                ["Özdirenç", "184.6 Ωm", "Seçili hücre"],
                ["Kesit Derinliği", "18.0 m", "Model sınırı"],
                ["Elektrot", "24", "Aktif dizilim"],
                ["Sapma", "%14", "Referansa göre"],
            ],
            fields: [
                ["Dizilim", "Wenner"],
                ["Hücre Sayısı", "128"],
                ["Ters Çözüm", "Ön model"],
                ["Hata", "%4.8"],
            ],
            layers: [
                ["Yüzey", "Aktif"],
                ["Düşük Direnç", "Aktif"],
                ["Yüksek Direnç", "Aktif"],
                ["Model", "Ön izleme"],
            ],
            confidence: 85,
        },

        gpr: {
            title: "GPR — YER RADARI",
            subtitle: "Radargram, yansıma ve tabaka süre paneli",
            unit: "ns",
            liveValue: "46.2",
            metrics: [
                ["Yansıma Süresi", "46.2 ns", "Seçili iz"],
                ["Tahmini Derinlik", "2.84 m", "Ortam varsayımı"],
                ["Hat Uzunluğu", "18.5 m", "Aktif tarama"],
                ["Hedef Sayısı", "3", "Ön işaret"],
            ],
            fields: [
                ["Anten", "400 MHz"],
                ["Örnekleme", "Yüksek"],
                ["Kazanç", "Otomatik"],
                ["Hat", "GPR-03"],
            ],
            layers: [
                ["Ham Radargram", "Aktif"],
                ["Kazanç", "Aktif"],
                ["Yansıma", "Aktif"],
                ["Hedef", "Ön izleme"],
            ],
            confidence: 83,
        },

        seismic: {
            title: "SİSMİK",
            subtitle: "Dalga varış süresi ve tabaka hızı paneli",
            unit: "m/s",
            liveValue: "1,842",
            metrics: [
                ["P Dalga Hızı", "1,842 m/s", "Ön model"],
                ["S Dalga Hızı", "924 m/s", "Ön model"],
                ["Varış Süresi", "18.4 ms", "İlk kırılma"],
                ["Hat Uzunluğu", "42 m", "Aktif"],
            ],
            fields: [
                ["Jeofon", "24"],
                ["Örnekleme", "2 kHz"],
                ["Tetik", "Dahili"],
                ["Hat", "S-01"],
            ],
            layers: [
                ["Ham Kayıt", "Aktif"],
                ["P Dalgası", "Aktif"],
                ["S Dalgası", "Aktif"],
                ["Hız Modeli", "Ön izleme"],
            ],
            confidence: 81,
        },

        hydro: {
            title: "HİDROJEOLOJİ",
            subtitle: "Yeraltı suyu ve geçirgenlik değerlendirme paneli",
            unit: "m",
            liveValue: "8.42",
            metrics: [
                ["Su Seviyesi", "8.42 m", "Tahmini"],
                ["Geçirgenlik", "Orta", "Ön sınıf"],
                ["Akış Yönü", "Güneybatı", "Model"],
                ["Nem İşareti", "%68", "Yüksek"],
            ],
            fields: [
                ["Akifer Türü", "Serbest"],
                ["Beslenme", "Yağış"],
                ["Drenaj", "Orta"],
                ["Model", "Ön değerlendirme"],
            ],
            layers: [
                ["Yüzey Suyu", "Referans"],
                ["Nem", "Aktif"],
                ["Akifer", "Ön izleme"],
                ["Akış", "Aktif"],
            ],
            confidence: 77,
        },

        botany: {
            title: "BOTANİK",
            subtitle: "Bitki örtüsü, tür yoğunluğu ve stres paneli",
            unit: "NDVI",
            liveValue: "0.72",
            metrics: [
                ["Bitki İndeksi", "0.72", "Yoğun örtü"],
                ["Tür Sayısı", "18", "Ön sınıflandırma"],
                ["Stres Alanı", "%9", "Düşük"],
                ["Nem", "%61", "Uygun"],
            ],
            fields: [
                ["Örtü Türü", "Karışık"],
                ["Mevsim", "Yaz"],
                ["Gölgeleme", "%34"],
                ["Durum", "Sağlıklı"],
            ],
            layers: [
                ["Yeşil Örtü", "Aktif"],
                ["Stres", "Aktif"],
                ["Yoğunluk", "Aktif"],
                ["Referans", "Hazır"],
            ],
            confidence: 86,
        },

        soil: {
            title: "TOPRAK ANALİZİ",
            subtitle: "Toprak sınıfı, nem, pH ve yoğunluk paneli",
            unit: "pH",
            liveValue: "7.18",
            metrics: [
                ["pH", "7.18", "Nötr yakın"],
                ["Nem", "%28", "Orta"],
                ["Yoğunluk", "1.42 g/cm³", "Ön değer"],
                ["Organik Madde", "%3.8", "Orta"],
            ],
            fields: [
                ["Toprak Türü", "Tınlı"],
                ["Renk", "Koyu kahve"],
                ["Numune", "T-021"],
                ["Katman", "2"],
            ],
            layers: [
                ["Yüzey", "Aktif"],
                ["Nem", "Aktif"],
                ["Organik", "Aktif"],
                ["Mineral", "Ön izleme"],
            ],
            confidence: 88,
        },

        water: {
            title: "SU ANALİZİ",
            subtitle: "Su kalitesi, iletkenlik ve bulanıklık paneli",
            unit: "µS/cm",
            liveValue: "412",
            metrics: [
                ["İletkenlik", "412 µS/cm", "Örnek değer"],
                ["pH", "7.42", "Normal"],
                ["Bulanıklık", "3.8 NTU", "Düşük"],
                ["Sıcaklık", "18.6 °C", "Anlık"],
            ],
            fields: [
                ["Numune", "W-009"],
                ["Kaynak", "Tatlı su"],
                ["Renk", "Şeffaf"],
                ["Koku", "Belirgin değil"],
            ],
            layers: [
                ["Fiziksel", "Aktif"],
                ["Kimyasal", "Aktif"],
                ["Bulanıklık", "Aktif"],
                ["Referans", "Hazır"],
            ],
            confidence: 90,
        },
    };

    function wavePoints(seed) {
        const points = [];

        for (let index = 0; index <= 40; index += 1) {
            const x = index * 25;
            const y =
                35 +
                Math.sin((index + seed) * 0.72) * 17 +
                Math.sin((index + seed) * 1.87) * 7;

            points.push(`${x},${y.toFixed(2)}`);
        }

        return points.join(" ");
    }

    function renderMetrics(metrics) {
        return metrics.map(([label, value, note]) => `
            <article class="scientific-metric">
                <span>${label}</span>
                <strong>${value}</strong>
                <em>${note}</em>
            </article>
        `).join("");
    }

    function renderFields(fields) {
        return fields.map(([label, value]) => `
            <div class="scientific-field">
                <span>${label}</span>
                <strong>${value}</strong>
            </div>
        `).join("");
    }

    function renderLayers(layers) {
        return layers.map(([label, state]) => `
            <div class="scientific-layer">
                <span>${label}</span>
                <strong>${state}</strong>
            </div>
        `).join("");
    }

    function render(moduleId) {
        const config = modules[moduleId];

        if (!config) {
            return null;
        }

        const seed =
            Object.keys(modules).indexOf(moduleId) + 1;

        return `
            <section
                class="scientific-screen module-${moduleId}"
                data-scientific-module="${moduleId}"
            >
                <header class="scientific-header">
                    <div class="scientific-title">
                        <strong>${config.title}</strong>
                        <span>${config.subtitle}</span>
                    </div>

                    <div class="scientific-runtime-state">
                        DİJİTAL ÖN İZLEME AKTİF
                    </div>
                </header>

                <div class="scientific-layout">
                    <div class="scientific-main">
                        <section class="scientific-scan">
                            <div class="scientific-grid"></div>
                            <div class="scientific-axis"></div>

                            <span class="scientific-orbit one"></span>
                            <span class="scientific-orbit two"></span>
                            <span class="scientific-orbit three"></span>
                            <span class="scientific-core"></span>

                            <span class="scientific-mark a"></span>
                            <span class="scientific-mark b"></span>
                            <span class="scientific-mark c"></span>

                            <span class="scientific-scan-label">
                                CANLI DEĞER
                            </span>

                            <strong class="scientific-scan-value">
                                ${config.liveValue} ${config.unit}
                            </strong>

                            <div class="scientific-wave">
                                <svg
                                    viewBox="0 0 1000 70"
                                    preserveAspectRatio="none"
                                    aria-hidden="true"
                                >
                                    <polyline
                                        points="${wavePoints(seed)}"
                                    ></polyline>
                                </svg>
                            </div>
                        </section>

                        <section class="scientific-metrics">
                            ${renderMetrics(config.metrics)}
                        </section>
                    </div>

                    <aside class="scientific-side">
                        <section class="scientific-card">
                            <h3>ÖLÇÜM BİLGİLERİ</h3>
                            ${renderFields(config.fields)}
                        </section>

                        <section class="scientific-card">
                            <h3>KATMANLAR</h3>

                            <div class="scientific-layer-list">
                                ${renderLayers(config.layers)}
                            </div>
                        </section>

                        <section class="scientific-card">
                            <h3>DİJİTAL GÜVEN</h3>

                            <div class="scientific-confidence">
                                <strong>
                                    %${config.confidence}
                                </strong>

                                <div class="scientific-confidence-bar">
                                    <div
                                        style="width:${config.confidence}%"
                                    ></div>
                                </div>
                            </div>
                        </section>

                        <div class="scientific-warning">
                            Bu ekran gerçek saha sonucu değildir.
                            Donanım veya doğrulanmış veri bağlandığında
                            değerler canlı ölçümle güncellenecektir.
                        </div>
                    </aside>
                </div>
            </section>
        `;
    }

    window.SyKScientificViews = {
        has(moduleId) {
            return Boolean(modules[moduleId]);
        },

        render,
    };
})();