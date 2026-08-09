# SYKAŞİF TERMINAL V2 — KANONİK ARAYÜZ SÖZLEŞMESİ

## DURUM

Bu belge Terminal V2 arayüzünün kanonik geliştirme sözleşmesidir.

Bu sözleşme bozulmadan geliştirme yapılacaktır.

## TEK AKTİF ARAYÜZ

Aktif geliştirme hattı:

terminal_v2_canonical

Eski / geçici / deneysel arayüzler yeni geliştirme için kaynak kabul edilmez.

## MASAÜSTÜ / TABLET / TELEFON

Üç ayrı arayüz YOKTUR.

Tek kanonik responsive arayüz vardır.

Aynı DOM ve aynı iş mantığı:

- masaüstü
- tablet
- telefon

ekranlarına responsive olarak uyarlanır.

## ANA EKRAN MİMARİSİ

- Üst bölüm minimaldir.
- Kaşif erişimi üst bölümde kompakt tutulur.
- Canlı sistem durumu renk ile gösterilebilir.
- Ana çalışma yüzeyi mümkün olan en büyük alanı kullanır.
- Alt ana menü sabittir ve dokunmatik kullanıma uygundur.
- Sol sabit menü zorunlu değildir.
- Sağ alan sabit klasik GIS paneli değildir.

## SAĞ DİNAMİK MATRİS

Sağ çalışma alanı seçime göre dinamik oluşur.

2 / 4 / 6 / 8 / 12 / 20+ panel olabilir.

Bir panel seçilirse:

- panel büyür,
- sağ alanı kullanır.

Tekrar seçilirse:

- çoklu matris görünümüne döner.

Seçilmeyen ağır katmanlar boş yere RAM / CPU kullanmaz.

## KATMAN MENÜSÜ

Katman yönetimi:

Ana menü
→ alt katman
→ alt-alt katman

mantığında çalışır.

Katman menüsü çalışma alanını sürekli kaplamaz.

Harita menüsünden / alt komut alanından yukarı açılır.

Üst bölümde:

Hepsini Seç

kontrolü bulunur.

Seçilen katmanlar öncelikli görünür.

Seçilmeyenler geri planda kalır veya yüklenmez.

## HARİTA

- Gerçek harita motoru kullanılır.
- Aynı Dünya yatay olarak tekrar edilmez.
- Kullanıcı anlamsız biçimde Dünya dışına uzaklaşamaz.
- Konumuma Git bulunur.
- Konum işaretine dokunulduğunda konuma yaklaşılır.
- Harita / Uydu / Arazi / Topografya tabanları desteklenir.
- Tam ekran çalışma modu bulunur.

## GPS KAPSAMI

Varsayılan veri kapsamı:

kullanıcının bulunduğu il.

İl sınırına yakınsa:

gerekli komşu il verileri de yüklenir.

Tüm Türkiye verileri gereksiz yere aynı anda yüklenmez.

## GÖRSEL DOĞRULAMA

Bir sprint:

kod testi geçti diye tamamlandı sayılmaz.

Görsel arayüz değişikliğinde kullanıcı görsel doğrulaması gerekir.

Görsel doğrulama olmadan:

PASS
COMMIT
KİLİT

yapılmaz.

## LEGO GELİŞTİRME KURALI

Yeni özellik mevcut kanonik yapıya eklenir.

Tamamlanmış parça sebepsiz yere yeniden tasarlanmaz.

Yeni sprint:

mevcut kanonik blok
+
yeni blok

şeklinde ilerler.

## YASAK

- eski arayüzü yeniden aktif geliştirme hattına sokmak
- her gün yeni ana arayüz üretmek
- onaylı ana yapıyı sessizce değiştirmek
- görsel doğrulama yapılmadan tamamlandı demek
- sabit klasik GIS paneline geri dönmek
- ayrı masaüstü/tablet/telefon kod tabanları üretmek

## DEVAM NOKTASI

Sonraki çalışmalar bu sözleşmenin üzerine eklenir.

Bu belge değiştirilirse kanonik SHA-256 zinciri de değişmek zorundadır.
