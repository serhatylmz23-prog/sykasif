(() => {
    const fish = [
        ["SAZAN", "Cyprinus carpio", "40 - 120 cm", "Göl, Baraj, Nehir, Gölet", "Omnivor", "verified", "deep"],
        ["YAYIN BALIĞI", "Silurus glanis", "60 - 300 cm", "Nehir, Baraj, Göl, Geniş Akarsu", "Etçil", "analysis", "long"],
        ["ALABALK", "Salmo trutta", "20 - 80 cm", "Soğuk Sular, Akarsu, Göl", "Etçil", "analysis", ""],
        ["TURNA", "Esox lucius", "40 - 100 cm", "Göl, Baraj, Sazlık Alanlar", "Etçil", "analysis", "long"],
        ["KEFAL", "Mugil cephalus", "30 - 70 cm", "Nehir, Acı Göl, Hafif Tuzlu Alanlar", "Omnivor", "verified", ""],
        ["HAVUZ BALIĞI", "Carassius gibelio", "15 - 40 cm", "Göl, Gölet, Durgun Sular", "Omnivor", "verified", "deep"],
        ["İSTAVRİT", "Perca fluviatilis", "15 - 40 cm", "Nehir, Göl, Taşlık Alanlar", "Etçil", "review", ""],
        ["KAYA LEVREĞİ", "Lota lota", "25 - 60 cm", "Soğuk Göl, Baraj, Derin Sular", "Etçil", "rare", "long"],
        ["KIZILKANAT", "Scardinius erythrophthalmus", "15 - 35 cm", "Göl, Gölet, Yavaş Akarsu", "Omnivor", "verified", ""],
        ["SUDAK", "Sander lucioperca", "30 - 80 cm", "Nehir, Baraj, Derin Sular", "Etçil", "analysis", "long"],
        ["YILAN BALIĞI", "Anguilla anguilla", "50 - 120 cm", "Nehir, Gölet, Bataklık Alanlar", "Etçil", "review", "eel"],
        ["AMUR", "Ctenopharyngodon idella", "40 - 120 cm", "Nehir, Baraj, Bitkisel Alanlar", "Otçul", "verified", ""],
    ];

    const evidence = [
        ["YAZIT", "Doğrulandı", 97, "verified"],
        ["YAPI KALINTISI", "Analiz Ediliyor", 82, "analysis"],
        ["SERAMİK", "İncelenmeli", 65, "review"],
        ["BOŞLUK / MAĞARA", "Düşük Güven", 40, "low"],
        ["MANYETİK ANOMALİ", "Nadir Anomali", 93, "rare"],
        ["TERMAL SAPMA", "Tutarsız Veri", 22, "inconsistent"],
    ];

    function fishCard(item) {
        const [name, latin, size, habitat, feeding, status, shape] = item;

        return `
            <article class="fish-card" data-status="${status}">
                <div class="fish-stage">
                    <div class="fish-body ${shape}"></div>
                </div>

                <div class="fish-info">
                    <span class="fish-dot"></span>
                    <strong class="fish-name">${name}</strong>
                    <span class="fish-latin">${latin}</span>
                    <div class="fish-size">◁ ${size}</div>

                    <div class="fish-field">
                        <span>Yaşam Alanı</span>
                        <strong>${habitat}</strong>
                    </div>

                    <div class="fish-field">
                        <span>Beslenme</span>
                        <strong>${feeding}</strong>
                    </div>
                </div>
            </article>
        `;
    }

    function fishView() {
        return `
            <section class="module-screen">
                <header class="module-header">
                    <div>
                        <h2>TATLI SU BALIK REHBERİ</h2>
                        <p>SyKaşif Balık Bulucu Sistemi · Akustik tarama ve tür sınıflandırma</p>
                    </div>

                    <div class="status-legend">
                        <span class="status-badge status-verified">Tespit Edildi</span>
                        <span class="status-badge status-analysis">Olası Tür</span>
                        <span class="status-badge status-rare">Nadir Tür</span>
                        <span class="status-badge status-review">Küçük Tür</span>
                        <span class="status-badge status-inconsistent">Koruma Altında</span>
                    </div>
                </header>

                <div class="fish-grid">
                    ${fish.map(fishCard).join("")}
                </div>

                <footer class="fish-footer">
                    <section>
                        <h4>BOYUT SINIFLANDIRMASI</h4>
                        <div class="fish-scale">
                            <span>Küçük<br>0-20 cm</span>
                            <span>Orta<br>20-50 cm</span>
                            <span>Büyük<br>50-100 cm</span>
                            <span>Çok Büyük<br>100 cm+</span>
                        </div>
                    </section>

                    <section>
                        <h4>HABİTAT GÖSTERİMİ</h4>
                        <div class="habitat-scale">
                            <span><strong>≋</strong>Nehir</span>
                            <span><strong>◒</strong>Göl</span>
                            <span><strong>▥</strong>Baraj</span>
                            <span><strong>◉</strong>Gölet</span>
                            <span><strong>♆</strong>Sazlık</span>
                        </div>
                    </section>

                    <section>
                        <h4>AKUSTİK TESPİT İNDİKATÖRÜ</h4>
                        <div class="acoustic-line"></div>
                    </section>
                </footer>
            </section>
        `;
    }

    function evidenceCard(item) {
        const [title, result, score, status] = item;

        return `
            <article class="syframe-evidence" data-status="${status}">
                <div class="evidence-thumbnail"></div>

                <div class="evidence-body">
                    <strong>${title}</strong>
                    <span>${result}</span>

                    <div class="evidence-progress">
                        <div style="width:${score}%"></div>
                    </div>

                    <span>Güven: %${score}</span>
                </div>
            </article>
        `;
    }

    function syframeView() {
        return `
            <section class="module-screen syframe-demo">
                <header class="module-header">
                    <div>
                        <h2>SyFrame™</h2>
                        <p>SyKaşif Anomali İşaretleme Dili</p>
                    </div>

                    <div class="status-legend">
                        <span class="status-badge status-verified">Doğrulandı</span>
                        <span class="status-badge status-analysis">Analiz Ediliyor</span>
                        <span class="status-badge status-review">İncelenmeli</span>
                        <span class="status-badge status-low">Düşük Güven</span>
                        <span class="status-badge status-inconsistent">Tutarsız Veri</span>
                        <span class="status-badge status-rare">Nadir Anomali</span>
                        <span class="status-badge status-reference">Referans Veri</span>
                    </div>
                </header>

                <div class="syframe-scene">
                    <div class="syframe-ruins"></div>
                    <div class="statue"></div>

                    <div class="focus-frame">
                        <span class="corner top-left"></span>
                        <span class="corner top-right"></span>
                        <span class="corner bottom-left"></span>
                        <span class="corner bottom-right"></span>
                    </div>
                </div>

                <aside class="detail-panel">
                    <h3>HEYKEL</h3>
                    <span>TAŞ HEYKEL</span>

                    <div class="detail-row"><span>TÜR</span><strong>İnsan Figürü</strong></div>
                    <div class="detail-row"><span>DÖNEM</span><strong>Geç Hitit Dönemi</strong></div>
                    <div class="detail-row"><span>TAHMİNİ TARİH</span><strong>M.Ö. 1200 - 700</strong></div>
                    <div class="detail-row"><span>KATMAN</span><strong>3. Katman</strong></div>
                    <div class="detail-row"><span>KOORDİNAT</span><strong>37.128456° N<br>38.789123° E</strong></div>
                    <div class="detail-row"><span>UZMAN</span><strong>Arkeoloji Uzmanı</strong></div>
                    <div class="detail-row"><span>GÜVEN</span><strong class="score">%98</strong></div>
                    <div class="detail-row"><span>KAYNAK</span><strong>Fotoğraf + 3B Tarama</strong></div>
                    <div class="detail-row"><span>KANIT SAYISI</span><strong>12</strong></div>
                </aside>

                <div class="syframe-evidence-grid">
                    ${evidence.map(evidenceCard).join("")}
                </div>
            </section>
        `;
    }

    function genericView(title) {
        return `
            <section class="module-screen generic-module">
                <div>
                    <strong>${title}</strong>
                    <span>Modül çalışma alanı hazır.</span>
                </div>
            </section>
        `;
    }

    function render(moduleId, title) {
        const container = document.querySelector("#module-view");
        const mapStage = document.querySelector("#map-stage");
        const frame = document.querySelector("#syframe");

        if (!container) {
            return;
        }

        if (moduleId === "dashboard" || moduleId === "maps") {
            container.hidden = true;
            mapStage.hidden = false;
            frame.hidden = false;
            return;
        }

        container.hidden = false;
        mapStage.hidden = true;
        frame.hidden = true;

        if (moduleId === "sonar") {
            container.innerHTML = fishView();
            return;
        }

        if (moduleId === "syframe") {
            container.innerHTML = syframeView();
            return;
        }

        container.innerHTML = genericView(title);
    }

    window.SyKModuleViews = { render };
})();