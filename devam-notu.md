# Pardus ETAP23 Tahta İmajı Projesi — Devir Notu

## Amaç
Okuldaki bir masaüstü PC'ye kurulan Pardus ETAP23'ü referans imaj haline getirip (ISO), Ventoy ile okulun etkileşimli tahtalarına (akıllı tahtalar) yüklemek. Hedef: tüm kullanıcı/ayarları ve programları önceden hazırlayıp tek imajdan çoğaltmak.

## Makine / hesaplar
- Kullanıcılar: `etapadmin` (yönetici, şifresi bu proje sırasında değiştirildi çünkü öğrenciler eski şifreyi öğrenmişti), `ogretmen`, `ogrenci` (silindi — aşağıya bakın).
- `ogrenci` hesabı **silindi** (`sudo userdel -r ogrenci`): giriş ekranından seçilip Ekilit/kilit devreye girmeden masaüstüne ulaşma açığı kapatıldı.
- LightDM (giriş ekranı) ayarı — "Pardus LightDM Ayarları" adlı GUI araçla yapıldı:
  - Otomatik giriş: **açık**, kullanıcı = `ogretmen`.
  - "Root ile girişi kabul et": **kapatıldı**.
  - Kullanıcı listesi: bilinçli olarak **açık bırakıldı** (etapadmin'e hızlı erişim için, EBA girişini etkilemiyor çünkü o ayrı bir katman).

## Wifi (MT7601U USB çubuğu) — ertelendi
- PC'de dahili wifi yok, harici MT7601U (MediaTek) USB çubuk var. Windows'ta aynı portta sorunsuz çalışıyordu.
- Firmware eksikliği tespit edilip düzeltildi (`/lib/firmware/mediatek/mt7601u.bin`, doğru şekilde kuruldu, md5 doğrulandı).
- Ama hâlâ "MCU resp urb failed:-71" / "probe failed:-110" hatalarıyla sürekli disconnect/reconnect döngüsüne giriyor — bu, Linux mt7601u sürücüsü ile bu makinenin xHCI (USB3) denetleyicisi arasında bilinen bir uyumsuzluk gibi duruyor. `usbcore.old_scheme_first=1` GRUB parametresi denendi, çözmedi.
- **Karar**: Tahtalarda zaten dahili wifi var ve bu Pardus sürümüyle sorunsuz çalışıyor, bu yüzden bu sorun imaj için önemsiz — sadece kişisel olarak bu PC'de Pardus kullanmaya devam edilirse ileride tekrar ele alınacak. Şimdilik bırakıldı.

## Klavye (F klavye) — imajdan ÖNCE MUTLAKA GERİ ALINMALI
- Cinnamon'ın klavye ayarlarında "Düzenler" (Layouts) sekmesi, Pardus ETAP tarafından bilerek devre dışı bırakılmıştı (muhtemelen tahtalarda kafa karışıklığını önlemek için): `/usr/share/cinnamon/cinnamon-settings/modules/cs_keyboard.py` içinde ilgili kod bloğu üçlü tırnak (`"""`) ile yorumlanmıştı (satır 424 ve 440).
- Bu iki satır silinerek (`sudo sed -i '424d;440d' ...`) sekme geri getirildi. **Orijinal dosyanın yedeği aynı klasörde `cs_keyboard.py.bak` olarak duruyor.**
- Türkçe F klavye eklenip varsayılan yapıldı (kullanıcı hızlı yazmak için F kullanıyor).
- Bilinen tuhaflık: F düzeni her reboot'ta (hangi kullanıcı olursa olsun) sıfırlanıyor, panel simgesi kayboluyor. Geçici çözüm: Düzenler sekmesinden F'yi silip tekrar eklemek ya da şu komutu tekrar çalıştırmak:
  ```
  gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'tr+f'), ('xkb', 'tr')]"
  ```
  Kök nedenine inilmedi (öncelik değil, çünkü zaten geri alınacak).
- **İmajı almadan hemen önce yapılacaklar:**
  1. `sudo cp /usr/share/cinnamon/cinnamon-settings/modules/cs_keyboard.py.bak /usr/share/cinnamon/cinnamon-settings/modules/cs_keyboard.py` (Düzenler sekmesini tekrar gizler)
  2. Klavyeyi tek düzene (Q) döndür: `gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'tr')]"` (ilgili kullanıcı hesabında/hesaplarında çalıştırılmalı)

## Tahta Kilit programı (öğrencilerin teneffüste tahtayı suistimal etmesini önlemek için)
- Arka plan: Boardlar EBA karekod ile açılacak şekilde ayarlıydı ama sorunlu; öğrenciler `ogrenci` hesabından girip YouTube açıp halay çekiyordu (gürültü + enerji/yıpranma). Üçüncü parti "Mehcan e-Kilit" (mehcan.net) programı denendi/incelendi — ücretli sürümü zaten merkezi yönetim, uzaktan kontrol, bulut güncelleme gibi özellikler sunuyor, ama kullanıcı **kendi bağımsız kilit programını yazmaya** karar verdi (özgürlük/genişletilebilirlik için).
- **Faz 1 tamamlandı ve test edildi:**
  - `/opt/tahtakilit/lockscreen.py`: Python + GTK3, tam ekran kilit penceresi, `Gdk.Seat.grab()` ile klavye/fare tamamen pencereye kilitleniyor. Test edildi: Alt+Tab, Alt+F4, Ctrl+Alt+T, Süper tuşu, **Ctrl+Alt+F2 (sanal konsol geçişi) dahil hiçbiri kilidi kıramadı.**
  - PIN kontrolü: `/etc/tahtakilit/pin.txt` (düz metin — ponytail notu: ileride hash'lenebilir, şimdilik yeterli çünkü terminale erişim zaten engelleniyor).
  - `/opt/tahtakilit/run.sh`: çökme durumunda otomatik yeniden başlatan sarmalayıcı (doğru PIN ile normal kapanışta tekrar açmıyor, çökerse 1sn sonra tekrar açıyor).
  - `install.sh`: tek dosyalık kurulum betiği, herhangi bir tahtaya kopyalanıp `sudo bash install.sh <kullanici_adi>` ile kurulabiliyor (LightDM otomatik giriş kullanıcısını otomatik bulmaya çalışıyor ama bu makinede tutmadı, sebebi araştırılmadı — şimdilik kullanıcı adı elle veriliyor).
- **PIN dosyası tamamen terk edildi** (bkz. Faz 2 mimarisi aşağıda) — `/etc/tahtakilit/pin.txt` yaklaşımı yerini imza tabanlı anahtar sistemine bırakacak, o yüzden PIN'i hash'leme gibi konularla artık uğraşılmayacak.

## GitHub / paketleme altyapısı (kuruldu, 2026-09-16)
- Repo: `https://github.com/mstogluk/tahta-kilit-program` (private).
- Windows tarafı: bu klasör (`D:\MYPRG\CLAUDE\Tahta Kilit Programı`) git repo olarak init edildi, `origin` bu adrese bağlı.
  - `github_al.bat` → `git pull origin main`
  - `github_gonder.bat` → `git add -A` + commit + `git push -u origin main`
- Pardus tarafı için aynı mantıkta: `github_al.sh`, `github_gonder.sh` (bu klasörde hazırlandı, Pardus'a taşınacak/pull edilecek).
- `pardus-ilk-kurulum.txt`: Pardus'ta bir kereliğine çalıştırılacak bootstrap komutları (`git init`, `remote add`, `pull`, `chmod +x`) + GitHub Personal Access Token oluşturma rehberi + `credential.helper store` ipucu. Bu dosya USB/e-posta ile Pardus'a taşınacak (Claude Code bu makineye erişemiyor, komutlar oraya elle taşınmak zorunda).
- **Önemli kısıt:** Program başka okul/öğretmenlere dağıtılacağı için, bu repo adresi (ya da herhangi bir kişisel hesap bilgisi) **kodun içine hardcoded yazılmayacak** — her kurulum kendi senkronizasyon kaynağını (kendi GitHub reposu ya da başka bir depolama) `install.sh` sırasında kendi girecek.

## Faz 2 Mimarisi — Anahtar Tabanlı Kilit Açma (kararlaştırıldı 2026-09-16, henüz kod yazılmadı)
Referans: 3. parti "Mehcan e-Kilit" (mehcan.net) programının USB Anahtar / Mobil Anahtar / Kayıtlı Anahtarlar akışı incelenip esinlenildi, ama **merkezi sunucuya bağımlı olmayan** kendi bağımsız tasarımımız kuruldu.

**Genel prensip:** Sürekli çalışan bir sunucu (Flask/Node/vs.) yok. Mümkün olduğunca self-contained, stdlib-öncelikli (ponytail prensibi).

1. Kurulumda her okula **bir "okul ana anahtarı" (master secret)** üretilir, tüm o okulun tahtalarına bir kereliğine gömülür.
2. Admin (sen), kendi bilgisayarındaki bir yönetim aracıyla (Mehcan'daki "Anahtar Ekle" ekranına benzer) öğretmenler için **USB Anahtar** ve/veya **Mobil Anahtar** üretir. Sayı sınırsız — istersen her öğretmene ayrı anahtar (ileride kullanım istatistiği için önerilir), istersen tek bir ortak "öğretmen" anahtarı herkese dağıtılır — ikisi de aynı mimarada, sonradan değiştirilebilir.
3. Üretilen her anahtar, okulun ana anahtarıyla imzalanmış, öğretmen adını taşıyan **kendi kendine yeterli** bir veridir. Tahtaya ilk tanıtıldığında **ayrıca bir liste güncellemesi/senkronizasyon gerekmez** — tahta zaten sahip olduğu ana anahtarla imzayı doğrulayabilir.
4. **USB Anahtar akışı:** Admin panelinde üretilir → USB belleğe yazılır → öğretmen tahtaya takar → tahta dosyadaki imzayı okuyup doğrular → otomatik açılır (kod girişi yok). **Önemli:** İmzalanan veri sadece öğretmen adı değil, **öğretmen adı + o USB'nin donanım seri numarası** — tahta hem imzayı hem de takılı USB'nin gerçek seri numarasının dosyadakiyle eşleştiğini kontrol eder. Böylece dosya başka bir USB'ye kopyalanırsa çalışmaz (Mehcan'ın "Seri No" sütununun sebebi de bu). Bu akışta uzunluk kısıtı olmadığı için gerçek asimetrik imza (özel anahtar sadece admin'de, tahtada sadece açık anahtar) kullanılabilir.
5. **Mobil Anahtar akışı:** Admin panelinde üretilir → QR ile öğretmenin telefonundaki **offline web sayfasına** (native APK değil — maliyet/bakım kolaylığı için web sayfası tercih edildi, istenirse ileride "Ana Ekrana Ekle" ile PWA gibi kullanılabilir) bir kereliğine aktarılır. Kullanımda: tahta bir QR gösterir (tahta id + zaman damgası) → öğretmen bu web sayfasıyla tarar → sayfa 6 haneli, kısa süreli geçerli bir kod üretir → öğretmen tuş takımına girer → tahta kendi ana anahtarıyla doğrular. **Not:** 6 haneli elle girilen kod için simetrik (HMAC/TOTP tarzı) yöntem kullanılıyor — asimetrik imza bu uzunlukta anlamlı güvenlik farkı yaratmıyor (imza kısaltılırsa güvenliği bozulur). Ek önlem: yanlış kod denemelerinde kısa bekleme/kilitlenme eklenecek (kaba kuvvet denemesini yavaşlatmak için).
6. **Otomatik tanıma:** Tahtanın listesinde olmayan ama geçerli imzalı (okulun ana anahtarıyla imzalanmış) bir anahtar/USB görüldüğünde, tahta bunu otomatik olarak geçerli kabul edip kendi yerel listesine ekler (senin eski AutoIt3 projendeki davranışın aynısı) — elle senkronizasyon gerekmez.
7. **İptal listesi:** Öğretmen ayrıldığında ya da anahtarını (USB/telefon) kaybettiğinde kullanılır. Bu, tahtalara ara sıra gönderilmesi gereken **tek gerçek liste** — nadir olduğu için (her yeni öğretmende değil) kabul edilebilir bir zahmet.
8. **Kaybolan anahtar bulunursa:** Eski anahtar iptalli kalmaya devam eder (geri açılmaz) — öğretmene yeni bir anahtar üretilir, o da madde 6'daki otomatik tanıma ile kendini tahtalara tanıtır.
9. **Senkronizasyon (sadece iptal listesi ve okul ayarları gibi nadiren değişen veriler için):**
   - Öncelik: tahtanın interneti varsa, kurulumda belirlenen adresten (bkz. "Önemli kısıt" yukarıda) küçük bir dosya indirir — tam git değil, basit bir HTTPS isteği yeterli (Python stdlib `urllib` ile, ekstra paket gerekmez).
   - Yedek: internetsiz tahtalarda elle USB ile taşınarak güncellenir.
   - Aynı ağ şart değil — tahta ile admin PC hiçbir zaman aynı ağda olmayabilir, tasarım buna göre.

## Kod Koruması (kararlaştırıldı 2026-09-16)
- Endişe: sadece öğrenciler değil, programı kuran başka öğretmenler (root yetkisiyle) de kaynak kodu okuyup kopyalayabilir — bunu istemiyoruz.
- Dosya izinleri (root sahipliği vs.) bu tehdide çözüm değil çünkü kuran kişi zaten root oluyor.
- **Karar: Cython ile Python kodunu native binary'ye (gerçek makine koduna) derlemek.** Bytecode'a paketleyen `PyInstaller`'dan çok daha güçlü — kolay decompile edilemiyor.
- Neden direkt C/C# yazılmadı: Cython, elle yazılmış C/C# ile aşağı yukarı aynı tersine-mühendislik zorluğunu çok daha az emekle veriyor; mevcut test edilmiş Python/GTK kodunu (`lockscreen.py`) korumaya devam ediyoruz, sıfırdan yazıp yeniden test etmek gerekmiyor.
- Bunun **kesin/kırılmaz bir koruma olmadığı** biliniyor — kendi donanımında root yetkisi olan, çok kararlı ve uzman biri teorik olarak yine de inceleyebilir. Amaç "casual" erişimi (rastgele dosya açıp okumayı) engellemek, DRM seviyesinde bir garanti değil.
- Gelecekteki özellikler (ekrana mesaj gönderme, uzaktan ekran görüntüsü alma) performans kritik değil, Cython/Python ile devam etmek için bir engel değil.

## Faz 2 — Kod yazıldı, mobil akış meydan okuma-cevap yöntemine geçirildi (2026-09-16, henüz Pardus'ta test edilmedi)

**Mobil akış tasarımı değişti (önemli):** İlk taslakta tek paylaşılan TOTP anahtarı vardı (öğretmen bazlı değildi) — bu, kullanıcının baştan beri istediği "sınırsız öğretmen, ileride kullanım istatistiği" hedefine aykırıydı, düzeltildi. Ayrıca zaman bazlı (TOTP) yöntem, internetsiz tahtalarda saat kayması riski taşıyordu — bunun yerine **meydan okuma-cevap (challenge-response)** yöntemine geçildi:
- Tahta, **sadece "Karekod Oluştur" butonuna basılınca** (açılışta otomatik değil) rastgele bir "nonce" üretir, QR bunu + tahta id'sini taşır.
- Her öğretmenin 3 haneli bir **"öğretmen kodu"** var. Öğretmenin telefonu, `HMAC(okul_mobil_anahtarı, öğretmen_kodu)` ile kendi kişisel anahtarını türetir, `HMAC(kişisel_anahtar, nonce)` ile ekranda gösterilecek/tahtaya girilecek **6 haneli** cevabı üretir (öğretmen kodu koda eklenmez, bkz. aşağıdaki "6 haneye indirildi" notu).
- Tahta, girilen 6 haneli kodun hangi öğretmene ait olduğunu olası tüm öğretmen kodlarını (000-999) deneyerek **kendi kendine bulur** — önceden bir öğretmen listesi tutmasına gerek yok, yeni öğretmen eklemek tahtaya dokunmayı gerektirmiyor (USB akışındaki "otomatik tanıma" prensibiyle aynı).
- Her "Karekod Oluştur" tıklaması eskisini geçersiz kılıyor (aynı anda tek nonce geçerli).
- JS (mobil-anahtar.html) ve Python (keyauth.py) tarafındaki hesaplamalar birebir çapraz test edildi (aynı girdilerle aynı çıktı).

Dosyalar (repo kökünde):
- `keyauth.py` — anahtar üretme/doğrulama: USB için Ed25519 imza (+ USB seri no bağlama), Mobil için meydan okuma-cevap. PIN tamamen kaldırıldı.
- `lockscreen.py` — "Karekod Oluştur" butonu, kod girişi (6 hane), USB otomatik tarama, 3 yanlıştan sonra 15sn kilitlenme.
- `admin_araci.py` — admin CLI: `kurulum` (okul anahtarlarını bir kere üretir), `usb-anahtar-uret`, `mobil-anahtar-uret "Ad" [--kod NNN]` (öğretmen kodu otomatik atanır, `admin-gizli/ogretmenler.json`'da kayıt tutulur, çakışma engellenir).
- `mobil-anahtar.html` — öğretmen telefonunda açılan, tamamen offline (saf JS SHA-1/HMAC, Web Crypto'ya bağımlı değil, `file://` üzerinden çalışır) kod üretme sayfası. Kurulumda hem admin karekodunu tarayıp hem elle girebiliyor.
- `install.sh` — bağımlılıkları kurar, `tahta-config/`'i `/etc/tahtakilit/`'e kopyalar, autostart kurar.
- `.gitignore` — `admin-gizli/` (okul_ozel.key, ogretmenler.json) asla git'e gitmiyor; `tahta-config/` (okul_acik.key, mobil_gizli.key) BİLEREK git'e gidiyor.
- `pardus-gorevler.md` — Pardus'ta test edilecekler, Windows-Pardus arası "görev listesi".

**Henüz yapılmadı:**
- Cython ile native binary'ye derleme (kod koruması kararı verildi ama build adımı henüz eklenmedi).
- Okul bilgileri/ders-teneffüs saatleri özelliği (kapsam dışı, aşağıda).
- İptal güncellemesinin tahtalara ulaşması şu an **manuel** — `iptal.txt` değişince `install.sh`'in yeniden çalıştırılması gerekiyor. Otomatik senkronizasyon (GitHub'dan periyodik çekme) henüz kurulmadı, bkz. "Faz 2" bölümündeki senkronizasyon planı.

## Mobil kod 9 haneden 6 haneye indirildi (2026-09-17)

İlk tasarımda tahtaya girilen kod "öğretmen kodu (3 hane) + cevap (6 hane)" = 9 haneydi. Kullanıcı bunun kullanışsız olduğunu belirtti; çözüm olarak **öğretmen kodu koda hiç eklenmiyor artık** — tahta, girilen 6 haneli kodun hangi öğretmene ait olduğunu olası 1000 öğretmen kodunun (000-999) hepsini deneyerek buluyor (`keyauth.mobil_cevap_dogrula` içinde döngü, ~2ms sürüyor, performans sorunu yok).

**Güvenlik notu (kullanıcıyla birlikte netleştirildi):** Bunun "9 haneye göre 1000 kat zayıf" olduğunu düşünmüştüm ama yanlıştı — öğretmen kodu zaten hiç gizli değildi (telefon ekranında sürekli görünüyor, öğrenciler zaten bilir/görür). Belirli bir öğretmeni hedefleyen biri için gerçek zorluk her iki tasarımda da aynı (6 haneyi bulmak, 1 milyonda 1). Yani 6 haneye inmek gerçek bir güvenlik kaybı getirmiyor, sadece kullanışsız uzunluğu kaldırıyor.

`keyauth.py`, `lockscreen.py`, `mobil-anahtar.html` güncellendi, JS↔Python çapraz test edildi ve gerçek tarayıcı UI'ından uçtan uca doğrulandı (tümü geçti).

## Gizlilik: öğretmen adı/kodu artık hiçbir yerde görünmüyor, sadece loglanıyor (2026-09-17)

Kullanıcı isteği: kilit açılana kadar hiçbir ekranda öğretmen adı/kodu görünmesin, sadece kilidi kimin açtığı (ileride istatistik için) kayıt altına alınsın.

- `mobil-anahtar.html`'de ana ekranın üstündeki "X öğretmeni (kod: 042)" başlığı **kaldırıldı** — artık hiçbir zaman ekranda öğretmen bilgisi görünmüyor.
- `keyauth.kullanim_logla(tahta_id, yontem, kimlik)` eklendi — kilit açıldığında `/etc/tahtakilit/kullanim.log`'a `zaman | tahta_id | mobil/usb | kimlik` satırı yazıyor (sadece diske, ekrana hiç yansımıyor).
- `lockscreen.py`'nin `_ac()` metodu artık `yontem, kimlik` parametresi alıp kilidi açmadan önce bu logu yazıyor.
- Test edildi: log satırı doğru formatta yazılıyor (`2026-09-17T11:01:25 | a3f9c1d2 | mobil | 001` gibi).

## Admin Yönetim Paneli (GUI) eklendi (2026-09-17)

Mehcan e-Kilit'in ekran görüntüleri incelenip esinlenildi (Anahtarlar/USB/Mobil/Kayıtlı Anahtarlar sekmeleri, kara liste). Kod koruması endişesi nedeniyle (kullanıcı .py kaynağının açıkça okunabilir kalmasını istemiyor — bkz. "Kod Koruması" bölümü) **Tkinter + Cython** ile devam kararı verildi; C# değil, çünkü kripto mantığını (`keyauth.py`) ikinci bir dilde yeniden yazmak gerekirdi (senkronizasyon riski) ve düz C# derlemesi de Native AOT olmadan zaten kolayca decompile edilebiliyor.

- `admin_araci.py` refactor edildi: iş mantığı (kurulum, USB/mobil anahtar üretme, iptal ekle/kaldır) artık `AdminHatasi` fırlatan, veri döndüren saf fonksiyonlar — hem CLI hem GUI bunları çağırıyor, kod tekrarı yok. **Yeni**: `iptal_kaldir()` eklendi (Mehcan'daki "Karalisteden Çıkar" karşılığı, önceden sadece ekleme vardı).
- `admin_gui.py` (yeni): Tkinter tabanlı masaüstü uygulaması.
  - **Anahtarlar** sekmesi: USB Anahtar (takılı USB'leri otomatik listeler — Windows'ta `Get-CimInstance`/`Get-CimAssociatedInstance` ile, Linux'ta `lsblk` ile; seçilip "Anahtar Oluştur" ile doğrudan USB köküne gizli dosya olarak yazılıyor), Mobil Anahtar (QR + metin gösterir), Kayıtlı Anahtarlar (liste + QR Göster + Karalisteye Al/Çıkar).
  - **Okul Kurulumu** sayfası: `admin_araci.py kurulum` karşılığı, durum gösterir.
  - Diğer araç çubuğu düğmeleri (Duyurular, Bildirimler, Yoklama, Transfer, Güncelle, Kontrol) **yer tutucu** — tıklanınca "yakında" diyor, ileride (özellikle Kontrol = tahta görüntüleri ızgarası) gerçek işlevle doldurulacak şekilde düzen hazır.
- USB anahtar dosya adı **gizli dosyaya çevrildi**: `tahtakilit_anahtar.json` → `.tahtakilit_anahtar.json` (Mehcan'ın "hidden yapılıyor" davranışından esinlenildi).

**Test sırasında bulunan ve düzeltilen 2 hata:**
1. Windows USB tespiti ilk denemede WMI'ın eski `ASSOCIATORS OF` sorgu sözdizimiyle "Not found" hatası veriyordu — `Get-CimInstance`/`Get-CimAssociatedInstance` cmdlet'lerine geçilince düzeldi, gerçek USB'yle (SanDisk Cruzer Blade) doğrulandı.
2. Tkinter'ın `Treeview` widget'ı, "0000" gibi baştaki sıfırları olan metinleri iç mekanizmada (Tcl) tamsayıya çevirip sıfırları siliyordu — kara listeye alma/çıkarma yanlış kodu arıyordu. Çözüm: satırların `iid`'sini biz veriyoruz (`kod` değerini doğrudan `iid` yapıp `values` yerine `iid`'den okuyoruz) — Tcl'nin tip dönüşümünü bu şekilde atlıyoruz. Ayrıca "Karalisteye Al" sonrası liste yenilenince seçim kayboluyordu, bu da art arda ekle/çıkar işlemini bozuyordu — düzeltildi (yenileme sonrası aynı satır tekrar seçiliyor).

Uçtan uca GUI testi yapıldı (bu Windows makinesinde): USB'ye gerçek anahtar yazma, mobil anahtar+QR üretme, kayıtlı listeleme, kara listeye alma/çıkarma — hepsi doğrulandı.

**Kullanıcı geri bildirimiyle 2 iyileştirme daha yapıldı (aynı gün):**
- **"Tüm sürücüleri göster" seçeneği** eklendi (Mehcan'daki aynı özellikten esinlenildi) — bazı USB bellekler Windows'a "USB" değil farklı bir arayüz tipiyle (örn. "SCSI") görünebiliyor, filtre normalde bunları gizliyordu. Onay kutusu işaretlenince filtre kaldırılıp tüm diskler (dahili olanlar dahil) listeleniyor, admin görüp seçiyor. Listede artık arayüz tipi de gösteriliyor (`"Model (USB)"` gibi) ki admin yanlışlıkla dahili diski seçmesin. Test edildi: normal modda 1 (gerçek USB), tümünü göster modunda 3 disk (dahili SSD dahil) listelendi.
- **Gerçek, isimli bir çalıştırılabilir dosya eksikliği** — kullanıcı haklı olarak "python admin_gui.py" ile çalıştırmanın amatörce kaldığını belirtti. Netleştirildi: Cython tek başına bunu çözmüyor (kaynağı gizler ama isimli/çift-tıklanabilir bir .exe üretmez) — **Cython (kaynak gizleme) + PyInstaller (isimli tek .exe'ye paketleme) birlikte** kullanılması gerekiyor. Ürün adı için kullanıcıya soruldu, cevap bekleniyor.

## Ürün adı belirlendi: ANKA + ilk .exe üretildi (2026-09-17)

**İsim**: **ANKA** = *Akıllı Nesil Kilit Anahtarı* (ATAK/ETAK'ın "kısaltma + anlamlı kelime" tarzında, ama bağımsız). Karar sürecinde birkaç isim önerildi (TAHKİM, KİLİTAŞ, ETKİN), kullanıcı ANKA'yı seçti.

**İkon**: Basit bir kilit ikonu, PIL ile programatik olarak çizildi (harici tasarım aracı gerekmedi) — `anka_ikon.png` / `anka.ico`. Kullanıcı onayladı.

**Paketleme durumu**: Cython için gereken C derleyicisi (MSVC/MinGW) bu makinede kurulu değil — büyük bir indirme gerektirdiği için kullanıcıya soruldu, **şimdilik Cython atlanıp sadece PyInstaller ile devam edilmesine karar verildi** (kaynak koruması yok şu an, ileride derleyici kurulunca eklenecek).

- `python -m PyInstaller --onefile --windowed --icon=anka.ico --name=ANKA admin_gui.py` ile **`ANKA.exe` başarıyla üretildi** (~22MB, tek dosya).
- Çalıştırılıp test edildi: pencere doğru açılıyor, başlık doğru ("Tahta Kilit - Yönetim Paneli"), yanıt veriyor.
- `build_admin.bat` eklendi (tek tıkla yeniden derleme).
- `.gitignore`'a `build/`, `dist/`, `*.spec` eklendi (derleme çıktıları repoya gitmiyor, kaynaktan yeniden üretilebilir).
- `.exe` kullanıcıya doğrudan gönderildi, kendi makinesinde deneyebilir.

**Görsel yenileme (aynı gün, kullanıcı geri bildirimiyle)**: İlk `.exe`'yi deneyen kullanıcı arayüzün "acemice" göründüğünü belirtti — asıl sebep, `ttk.Treeview`/`ttk.Notebook` gibi widget'lara hiç tema verilmemiş olmasıydı (sadece düz `tk` widget'ları renklendirilmişti), bu yüzden tablo/sekmeler varsayılan beyaz Windows temasıyla koyu arka planla çarpışıyordu. Düzeltme:
- `ttk.Style()` ile 'clam' teması üzerine özel bir tema kuruldu (Treeview, Treeview.Heading, Notebook, Notebook.Tab hepsi koyu temaya uyarlandı).
- Tüm `Entry`/`Text` kutuları da elle koyu temaya çevrildi (`giris_kutusu()` ortak yardımcı fonksiyonu eklendi).
- Üst çubuğa **ANKA başlığı + ikon** eklendi, aktif sekme artık mavi ile vurgulanıyor (`_aktif_sekme()`), pencere ikonu (`anka.ico`) ayarlandı.
- Doğrulama: gerçek ekran görüntüleri alınıp (`PIL.ImageGrab` ile) görsel olarak incelendi, üç ekran da (Anahtarlar/USB, Kayıtlı Anahtarlar, Okul Kurulumu) kontrol edildi — artık tutarlı, koyu temalı, profesyonel görünüyor.
- `.exe` yeniden derlenip kullanıcıya tekrar gönderildi.

**3 gerçek hata daha bulunup düzeltildi (kullanıcı .exe'yi deneyince):**
1. **PowerShell konsol penceresi kısa süreliğine açılıp kapanıyordu** (Anahtarlar sekmesine her dönüşte USB taraması yeniden çalıştığı için) — `subprocess.CREATE_NO_WINDOW` bayrağı eklendi, düzeldi.
2. **İkon hiç işe yaramıyordu** (görev çubuğu/pencere başlığında varsayılan "tüy" simgesi görünüyordu) — kök neden: `.ico`/`.png` dosyaları `.exe`'nin içine "veri" olarak gömülmemişti, sadece `.exe`'nin kendi dosya simgesi ayarlanmıştı; program çalışırken kendi ikonunu bulamıyordu. Düzeltme: `kaynak_yolu()` yardımcı fonksiyonu eklendi (PyInstaller'ın `sys._MEIPASS` geçici klasörünü doğru buluyor), `build_admin.bat`'a `--add-data` eklendi. **Gerçek ekran görüntüsüyle doğrulandı**: hem pencere başlığında hem görev çubuğunda artık doğru kilit ikonu görünüyor.
3. **Sekmelere/araç çubuğuna simge eklendi** (kullanıcı isteğiyle) — Unicode emoji karakterleri kullanıldı (harici görsel gerekmedi). İlk denemede 2 simge (Yoklama, Kontrol) boş kutu olarak render oldu, uyumlu alternatiflerle (✅, 📹) değiştirilip düzeltildi, ekran görüntüsüyle doğrulandı.

## Tkinter'dan PySide6/Qt'ye geçiş (2026-09-17, önemli mimari karar)

Kullanıcı ilk `.exe`'yi deneyip kapsamlı bir eleştiri yaptı: arayüz "acemice" görünüyordu, "Okul Kurulumu" ekranında git jargonu ("git'e gönderilecek" gibi) son kullanıcıya sızmıştı, veri dosyaları düz metin/JSON olarak "gizli" hissi vermiyordu, ve genel olarak "piyasada satılan profesyonel bir program" beklentisiyle karşılaştırınca Tkinter'in ulaştığı seviyeden memnun kalınmadı.

**Teşhis**: Sorun Python değil, Tkinter'ın kendisiydi — 90'lardan kalma, ne kadar stil verilirse verilsin belli bir kalite tavanının üstüne çıkamıyor. Gerçek profesyonel görünümlü Python masaüstü uygulamaları genelde **PySide6/Qt** kullanıyor.

**Karar**: `admin_gui.py` **PySide6 ile tamamen yeniden yazıldı** (Tkinter kodu silindi). İş mantığı (`admin_araci.py`, `keyauth.py`) hiç değişmedi, sadece görsel katman değişti.

- **Açık VE koyu tema seçenekleri** eklendi (kullanıcı ikisini de istedi) — sağ üstteki düğmeyle anlık geçiş yapılabiliyor, iki ayrı QSS stil sayfası (`AÇIK_TEMA`, `KOYU_TEMA`) tanımlandı.
- **"git" jargonu tamamen temizlendi** — Okul Kurulumu ekranı artık sadece "Kurulum tamamlandı, anahtarlar hazır" gibi kullanıcı diline uygun metin gösteriyor, dosya yolları/git komutları hiç bahsedilmiyor.
- Tablo bileşeni Qt'nin `QTableWidget`'ına geçti — Tkinter'daki "0000 kodu 0'a dönüyor" hatası burada **hiç oluşmuyor** (Qt, Tcl gibi otomatik tip dönüşümü yapmıyor).
- Sekmelere/araç çubuğuna simgeler korundu (Unicode emoji, aynı seçilmiş glifler).
- Uçtan uca fonksiyonel test edildi (USB'ye yazma, mobil anahtar+QR, kayıtlı listeleme, kara liste ekle/çıkar) — hepsi geçti, gerçek ekran görüntüleriyle her iki tema da görsel olarak doğrulandı.
- `.exe` yeniden derlendi (~59MB, Tkinter'a göre daha büyük — Qt çalışma zamanı kütüphaneleri nedeniyle, beklenen bir bedel) ve kullanıcıya gönderildi.

**Henüz yapılmadı**:
- Cython ile kaynak koruması (derleyici kurulunca eklenecek).
- `lockscreen.py`/board tarafının derlenmesi.
- Admin verilerini (`ogretmenler.json` gibi) düz JSON yerine (istenirse şifreli) bir veritabanına (SQLite) taşımak — kullanıcı isteği, henüz yapılmadı.
- Gerçek kurulum paketi (Windows: Inno Setup, Linux: .deb) — şu anki `.exe` hâlâ taşınabilir tek dosya, kurulum sihirbazı/kaldırma seçeneği yok. Uygulama olgunlaşınca ele alınacak.

## Düzen değişiklikleri: dikey menü + Okul Bilgileri/Ders Programı (2026-09-17)

Kullanıcı isteğiyle üç değişiklik daha yapıldı:
- **Menü yatay üst çubuktan dikey sol kenar çubuğuna çevrildi** (Mehcan'dan bilinçli olarak farklılaşmak için) — logo üstte, sekme düğmeleri altında dikey sıralı, tema düğmesi en altta.
- **"Duyurular" ve "Bildirimler" tek menü öğesinde birleştirildi**: "📢 Duyurular ve Bildirimler".
- **Okul Kurulumu artık 3 alt sekmeli**: "Anahtar Kurulumu" (eskisi), **"Okul Bilgileri"** (Okul Adı/İl/İlçe/Adres/Telefon formu, `admin-gizli/okul_bilgileri.json`'a kaydediliyor) ve **"Ders Programı"** (düzenlenebilir tablo — Tür/Başlama/Bitiş, Satır Ekle/Sil/Kaydet, `admin-gizli/ders_programi.json`'a kaydediliyor, varsayılan olarak Mehcan'ın ekran görüntüsündeki 8 ders + teneffüs saatleriyle geliyor).
- `admin_araci.py`'ye bu iki veri türü için yükle/kaydet fonksiyonları eklendi (`okul_bilgilerini_yukle/kaydet`, `ders_programini_yukle/kaydet`).
- `tablo_olustur()` yardımcı fonksiyonuna `duzenlenebilir` parametresi eklendi (Ders Programı tablosu düzenlenebilir, diğerleri salt okunur kalmaya devam ediyor).
- Hepsi test edildi: form kaydet/yükle, tabloya satır ekleme/hücre düzenleme/kaydetme/yeniden yükleme — gerçek ekran görüntüleriyle de görsel olarak doğrulandı.

**Not**: Okul bilgileri ve ders programı şu an sadece admin'in kendi bilgisayarında (`admin-gizli/`) tutuluyor, tahtalara hiç gitmiyor — çünkü henüz bunları kullanan bir tahta özelliği (örn. "ders saatlerine göre otomatik kilit") yok. İleride böyle bir özellik eklenirse bu veri `tahta-config/`'e taşınıp senkronize edilmesi gerekecek.

## Tüm admin verisi şifreli SQLite deposuna taşındı (2026-09-17, kritik değişiklik)

Kullanıcı ilk yedekleme özelliğini (sadece anahtar dosyasını hedef alan, düz JSON bırakan bir zip) yetersiz buldu ve netleştirdi: **tüm** admin verisi (özel anahtar, öğretmen listesi, okul bilgileri, ders programı) tek bir yerde, gerçek anlamda şifreli olmalı — "hiçbir veri bu kadar kolay ulaşılır olmamalı" (düz JSON/metin dosyaları kabul edilemez).

**Denenen ve elenen yol**: Gerçek SQLCipher (endüstri standardı şifreli SQLite) — `sqlcipher3-binary` ve `pysqlcipher3` ikisi de bu makineye kurulamadı (Cython'da yaşanan aynı sorun: C derleyicisi/hazır paket yok).

**Uygulanan çözüm** (yeni `veri_deposu.py` modülü):
- Python'ın **standart kütüphanesindeki `sqlite3`**, `:memory:` modunda kullanılıyor — veritabanının tamamı bellekte çalışıyor, diske **hiçbir zaman düz/şifresiz haliyle yazılmıyor** (ne kalıcı ne geçici bir dosya olarak).
- Python 3.11+'ta gelen `sqlite3.Connection.serialize()`/`.deserialize()` ile bellekteki DB bir bayt dizisine çevrilip zaten kullandığımız `cryptography` kütüphanesiyle (Fernet, PBKDF2-türetilmiş anahtar) şifreleniyor, tek dosya olarak yazılıyor: `admin-gizli/veri.enc`.
- Program açılışında **yönetici şifresi** soruluyor (ilk seferde belirlenir, sonrasında her açılışta girilir) — doğru şifre olmadan hiçbir veriye erişilemiyor.
- Şema: `ayarlar` (okul özel anahtarı + okul bilgileri key-value), `ogretmenler` (kod→ad), `ders_programi` (sıra/tür/başlama/bitiş) tabloları.
- `admin_araci.py` tamamen bu depoyu kullanacak şekilde yeniden yazıldı (`OZEL_ANAHTAR_DOSYASI`, `OGRETMENLER_DOSYASI` gibi düz dosya yolları kaldırıldı). CLI de artık ilk kullanımda şifre soruyor (`getpass`).
- Yedekleme artık çok daha basit: tek şifreli dosyayı (`veri.enc`) kopyalamak yeterli — zip'e gerek kalmadı, ve yedek dosyasının kendisi de zaten şifreli (sızsa bile şifre olmadan işe yaramaz).

**Neden bu yöntem, neden SQLCipher değil**: Kullanıcı "Python sürümü değişirse bozulur mu, ikisi de RAM'de tutuluyorsa hız farkı ne" diye sorguladı — cevaplandı: (a) `.exe` kendi Python'ını gömdüğü için kullanıcı tarafındaki Python sürümü hiç önemli değil, `serialize`/`deserialize` 2018'den beri stabil bir SQLite çekirdek özelliğinin ince sarmalayıcısı; (b) veri boyutumuzda (birkaç kayıt) performans farkı ölçülemeyecek kadar küçük, asıl karar noktası ileride planlanan kullanım istatistikleri özelliğinin SQL'de çok daha doğal olması.

**Test edildi**: Depo oluşturma, doğru/yanlış şifre, tüm CRUD işlemleri (USB/mobil anahtar üretme, öğretmen listesi, okul bilgisi, ders programı), gerçek dosyanın diskte tamamen okunamaz/şifreli olduğu (`head -c` ile ham baytlara bakılarak), yeni bir Python sürecinde şifreyle yeniden açılabildiği, ve gerçek `.exe`'de "İlk Kurulum" şifre penceresinin doğru göründüğü — hepsi doğrulandı.

**Not**: `tahta-config/` dosyaları (okul_acik.key, mobil_gizli.key, iptal.txt) BİLEREK düz metin kalmaya devam ediyor — bunlar zaten git'e gidiyor (tahtalar okumak zorunda) ve tek başlarına (imza/HMAC doğrulaması olmadan) işe yaramıyorlar, şifrelemenin faydası yok.

## Yarınki oturum için ilk yapılacaklar (kullanıcı notu, 2026-09-17 akşam)

Kullanıcı çıkmadan önce iki madde bıraktı:

**1. ✅ TAMAMLANDI (2026-09-18) — USB anahtarları da "öğretmen kodu" havuzunu kullanmalı, aynı öğretmene aynı kod verilmeli.**
`usb_anahtar_hazirla` artık önce `ogretmenler` tablosunda bu isimde kayıtlı biri var mı diye bakıyor (`_mevcut_kodu_bul`), varsa onun kodunu kullanıyor, yoksa yeni atıyor. USB payload'ına da `ogretmen_kodu` eklendi (imzalanan mesaja dahil: `keyauth.usb_anahtari_olustur` artık `(ozel_b64, ogretmen_kodu, ogretmen_adi, usb_seri_no)` alıyor). Ayrıca **aynı boşluk mobil akışın otomatik-kod-atama yolunda da vardı** (aynı ismi tekrar girip kod belirtmeden mobil anahtar üretilse yeni bir kod harcanıyordu) — o da aynı `_mevcut_kodu_bul` ile düzeltildi. Test edildi: aynı öğretmenin 2 farklı USB'si + mobil anahtarı hepsi aynı kodu paylaşıyor, farklı öğretmen farklı kod alıyor, doğrulama (doğru/yanlış seri) hâlâ doğru çalışıyor.

**2. ✅ TAMAMLANDI (2026-09-18) — Bir öğretmen birden fazla okulda ders veriyorsa, TEK bir USB bellek hepsinde çalışabilmeli.**

Uygulanan tasarım, kullanıcının önerdiği "okul kodu" fikrini sadeleştirdi: **ayrı bir okul kodu icat etmeye gerek olmadığı** ortaya çıktı — kurulumda zaten üretilen `okul_acik.key` aynı işi görüyor.

- USB dosya formatı artık **tek nesne değil, bir liste** (`keyauth.usb_listesini_oku` — eski tek-nesne formatına da tolerans gösteriyor).
- `keyauth.usb_listesine_ekle(mevcut_icerik, ozel_b64, acik_b64, ...)`: USB'de zaten başka okulların kayıtları varsa dokunmuyor; kendi okuluna ait eski bir kayıt varsa (imza kendi açık anahtarıyla doğrulanıyorsa) siliyor, yenisiyle değiştiriyor. Başka okulların kaydını "kendimize ait mi" diye kontrol ederken zaten doğrulayamayız (onların özel anahtarını bilmiyoruz) — bu otomatik izolasyon sağlıyor.
- `keyauth.usb_anahtari_dogrula`: artık listedeki kayıtları tek tek dener, **kendi okulunun açık anahtarıyla doğrulanan** kaydı bulunca döner, diğerlerini yok sayar.
- `admin_araci.usb_anahtar_hazirla` yeni `mevcut_icerik` parametresi aldı; `admin_gui.py`'deki USB sekmesi de anahtar üretmeden önce USB'de zaten dosya var mı diye okuyup bu parametreyi geçiriyor.
- `lockscreen.py` ve CLI'da **hiçbir değişiklik gerekmedi** — `usb_anahtari_dogrula`'nın dış arayüzü (imza) aynı kaldı, liste mantığı içeride gizli.

**Test edildi**: İki farklı "okul" (iki ayrı anahtar çifti) simüle edilip aynı USB'ye sırayla eklendi — her iki okulun tahtası da kendi kaydını buldu, alakasız üçüncü bir okul hiçbirini tanımadı, aynı öğretmen için okul A anahtarını yenileyince sadece A'nın kaydı güncellendi (çoğalmadı), B'nin kaydına dokunulmadı. `admin_araci` katmanından da (gerçek admin akışıyla, USB'de simüle edilmiş yabancı bir kayıtla) doğrulandı.

**Önemli**: Bu, USB anahtar dosya formatında **kırıcı bir değişiklik** — Pardus'taki `keyauth.py` mutlaka güncellenmeli, bkz. `pardus-gorevler.md`.

## Grafik "Kurulum Paketi" özelliği eklendi (2026-09-18)

Pardus'ta anahtarları test etmeye çalışırken ortaya çıkan bir gerçek: `install.sh`'ı çalıştırmak için Pardus'ta `git pull` + terminalde `sudo bash install.sh` gerekiyordu — kullanıcı bunun "gerçek bir program" için kabul edilemez olduğunu belirtti (Mehcan'ın kendi "Kurulum" düğmesiyle karşılaştırınca). İstek: git/terminal'e hiç gerek kalmadan, USB ile taşınıp çift tıklanan, **grafiksel** bir kurulum deneyimi; kurulum sırasında sınıf ismi sorulsun (terminal metniyle değil, gerçek bir popup/editbox ile) ve kilit ekranında gösterilsin; kurulum bitince "Tahtayı Şimdi Kilitle" butonu da olsun.

**Neden tam `.deb` değil**: Debian paketlerinin kurulum sırasında etkileşimli soru sorması (`debconf`) karmaşık/kırılgan; onun yerine daha basit ama aynı "çift tıkla, grafik pencere" deneyimini veren bir yöntem seçildi.

**Uygulanan çözüm**:
- **`pardus_kurulum.py`** (yeni): GTK penceresi — "Sınıf ismi" ve "Kullanıcı adı (opsiyonel)" giriş kutuları + "Kur" butonu. Ayrıcalıklı adımlar (dosyaları `/opt` ve `/etc`'e kopyalama, autostart kurulumu) **tek bir `pkexec` çağrısıyla** yapılıyor — Linux'un grafiksel "yönetici şifresi" penceresi (Windows UAC'ın karşılığı), terminale hiç yazı yazılmıyor. Güvenlik notu: sınıf ismi (kullanıcı serbest metni) shell komutuna doğrudan gömülmüyor — önce ayrı bir geçici dosyaya yazılıp `cp` ile kopyalanıyor, injection riski olmasın diye.
- Kurulum tamamlanınca **"Tahtayı Şimdi Kilitle"** butonu beliriyor — `run.sh`'ı hemen başlatıp kilidi test etme imkanı veriyor (reboot/oturum kapatma beklemeden).
- **`baslat.sh`** (yeni): çift tıklanabilir başlatıcı (`cd` + `python3 pardus_kurulum.py`). Not: USB FAT32/exFAT formatlıysa Linux'un çalıştırılabilir izin biti taşınmayabilir — paketteki `OKU.txt` bu durumda sağ tık > Özellikler > "Çalıştırılabilir olarak çalıştır" ile grafiksel çözümü anlatıyor (yine terminal gerekmiyor).
- **`keyauth.SINIF_ADI_FILE`** eklendi, **`lockscreen.py`** artık `/etc/tahtakilit/sinif_adi.txt` varsa kilit ekranında "<sınıf ismi> — Tahta Kilitli" gösteriyor (Pango markup injection'a karşı `GLib.markup_escape_text` ile kaçış yapılıyor).
- **`admin_gui.py`**'ye yeni **"Kurulum Paketi"** sekmesi (Okul Kurulumu altında): bir USB/klasör seçtirip içine `ANKA-Kurulum/` klasörü oluşturuyor — `pardus_kurulum.py`, `baslat.sh`, `dosyalar/` (tahta kodu + bu okulun `okul_acik.key`/`mobil_gizli.key`/`iptal.txt`) + kullanım talimatlı `OKU.txt`.
- `.exe` artık bu yeni dosyaları da (`--add-data`) içine gömüyor; `kaynak_yolu()` yardımcı fonksiyonu (ikon için zaten vardı) burada da kullanıldı — paketleme kodu önce yanlışlıkla `__file__` ile kendi yolunu hesaplıyordu, bu paketlenmiş `.exe` içinde yanlış çalışırdı, düzeltildi.

**Test durumu**: Paket klasörünün doğru dosyalarla oluştuğu ve frozen `.exe` içindeki yol çözümlemesinin (`sys._MEIPASS` simülasyonuyla) doğru çalıştığı doğrulandı. **`pardus_kurulum.py`'nin kendisi (GTK penceresi, pkexec akışı) gerçek Pardus donanımında henüz hiç test edilmedi** — bu makinede GTK yok, sadece syntax kontrolü yapılabildi. Bir sonraki Pardus oturumunda mutlaka gerçek kurulum denenmeli.

## İlk gerçek Pardus testi: 3 sorun bulundu, 2'si düzeltildi (2026-09-18)

Kullanıcı `pardus_kurulum.py`'yi ilk kez gerçek donanımda denedi, üç sorunla karşılaştı:

1. **"İki farklı öğretmen kabul etti" (aynı okula ait olmalarına rağmen)** — bu bir kod hatası DEĞİL, benim işletim hatam: `1. madde`/`2. madde` özelliklerini test ederken kendi test verilerim için `veri_deposu.depo_olustur(...)`'u defalarca çağırdım, her seferinde **yepyeni rastgele bir okul anahtarı** üretilip kullanıcının gerçek ("Ali Veli") anahtarının üzerine yazıldı. USB'deki iki kayıt aslında **farklı okul anahtarlarıyla** imzalanmış oldu, sistem onları haklı olarak ayrı okul sayıp ikisini de bıraktı — mantık doğru çalıştı, ama ben araya girip zemin kaydırdım. **Ders çıkarımı**: bundan sonra kendi testlerim için `admin-gizli/`'yi hiç kullanmayacağım, izole bir yerde test edeceğim. **Sonuç**: kullanıcının gerçek okul kurulumu kayboldu, yeniden yapılması gerekiyor (aşağıda).

2. **✅ DÜZELTİLDİ — "Kullanıcı adı neden soruldu, kurulum tüm kullanıcılar için geçerli olmalı".** Kullanıcı haklıydı, bu gerçek bir tasarım hatasıydı. Autostart, tek bir kullanıcının `~/.config/autostart/`'ına kuruluyordu. Düzeltme: **sistem geneli** `/etc/xdg/autostart/` kullanılıyor artık — hangi kullanıcı oturum açarsa açsın devreye giriyor, kullanıcı adı sorma ihtiyacı tamamen kalktı (`pardus_kurulum.py`'den o alan silindi). Aynı düzeltme tutarlılık için eski `install.sh`'a da yapıldı (artık parametre almıyor, `sudo bash install.sh` yeterli).

3. **"Tahtayı Kilitle" tepki vermedi, USB çıkarınca da kilitlenmedi** — muhtemel sebep: USB hâlâ takılıyken tahta anında (2sn'de bir taranan) geçerli anahtarı bulup kendini otomatik açtı, çok kısa süreliğine görünüp kaybolmuş olabilir. Ayrıca gerçek bir hata buldum ve **düzelttim**: "Tahtayı Şimdi Kilitle" butonu ilk tıklamadan hemen sonra **kurulum penceresini kapatıyordu** — tekrar denemek isteyen kullanıcının tıklayacağı bir buton kalmıyordu. Artık pencere açık kalıyor, buton tekrar tekrar kullanılabiliyor, ve kurulum bitince "USB'yi çıkarmayı unutma" uyarısı da ekrana ekleniyor.

**Kullanıcı için yapılacaklar (bir sonraki oturumda)**:
- `github_gonder.bat` ile bu düzeltmeleri gönder.
- ANKA'da okulu **yeniden kur** (eski kurulum kayboldu) ve yeni bir kurulum paketi üret.
- Pardus'ta yeni paketle tekrar dene: kurulum sırasında artık kullanıcı adı sormayacak; "Tahtayı Kilitle"ye bastıktan sonra USB'yi çıkarıp gerçekten kilitli kaldığını doğrula.

## Arayüz sadeleştirmesi + dokunmatik tuş takımı (2026-09-17)

Kullanıcının testler sırasında fark ettiği sorunlar üzerine:
1. **`mobil-anahtar.html` sadeleştirildi**: hem kurulum hem kullanım ekranındaki "elle gir" alanları kaldırıldı (gerçekçi değildi — kimse uzun rastgele bir nonce'u elle okuyup yazamaz), "Kod Üret" butonu kaldırıldı (kamera zaten taradığı anda otomatik kod üretiyordu, ayrı bir adım gereksizdi).
2. **"Anahtarı değiştir" butonu kaldırıldı**: kullanıcının önerisiyle, yerine zaman aşımı geldi (bkz. madde 4) — bir öğretmen karekod üretip girişi yapmadan tahtayı terk ederse, karekod/tuş takımı kendiliğinden kaybolur, ayrı bir "sıfırla" butonuna hiç gerek kalmadı.
3. **Fiziksel klavye yerine ekran tuş takımı** (önemli güvenlik notu): `Gdk.Seat.grab()` klavye olaylarının başka uygulamalara/VT'lere kaçmasını engelliyor ama fiziksel klavyeye takılan donanım bir keylogger'ı (ucuz, USB üzerinden, öğrencinin fark ettirmeden takabileceği bir cihaz) hiçbir yazılımsal önlem durduramaz — çünkü işletim sistemine ulaşmadan önce donanım seviyesinde tuşları kaydediyor. Çözüm: `lockscreen.py` artık kodu fiziksel klavyeden okumuyor, ekranda banka tarzı dokunmatik bir 0-9 + Sil tuş takımı var (`Gtk.Grid` + butonlar), 6. rakamda otomatik deniyor. "Karekod Oluştur"a basılana kadar hem karekod hem tuş takımı gizli; **45 saniye** içinde kullanılmazsa otomatik gizleniyor (zaman aşımı `GLib.timeout_add_seconds` ile, yeniden "Karekod Oluştur"a basınca sıfırlanıyor).
4. `keyauth.py`'de mantık değişmedi, sadece `lockscreen.py`'nin sunum katmanı yeniden yazıldı. Syntax kontrolü yapıldı, Pardus'ta gerçek donanımda (özellikle "fiziksel klavye hiç etki etmemeli" kısmı) henüz test edilmedi — bkz. `pardus-gorevler.md`.

## Öğretmen kodu 3 haneden 4 haneye çıkarıldı (2026-09-17)

Kullanıcının uyarısı: program başka okullara/öğretmenlere dağıtılacağı ve gidenlerin kodu geri alınmadığı senaryoda (kayıtlar hiç temizlenmezse), 3 hane = 1000 kayıt tavanı yıllar içinde gerçekten dolabilir. `OGRETMEN_KODU_UZUNLUK` 4'e çıkarıldı (10.000 kayıt kapasitesi). Tahtanın arama süresi ölçüldü: en kötü durumda (10.000 denemenin hepsi) ~170ms — insan gözüyle fark edilmeyecek kadar hızlı, sorun değil. `admin_araci.py`'deki "kod dolu" hata mesajı da, gerçekten dolarsa ne yapılması gerektiğini (ayrılan öğretmenleri `ogretmenler.json`'dan silip kodlarını yeniden kullanma) açıklayacak şekilde güncellendi.

**Test edildi ve doğrulandı (2026-09-17):**
- `mobil-anahtar.html` gerçek bir tarayıcı ortamında (yerel HTTP sunucusu üzerinden) test edildi — kurulum/kayıt, kalıcılık (sayfa yenileme sonrası tekrar sormuyor), ve kod üretme Python'daki gerçek `keyauth.mobil_cevap_dogrula` ile çapraz doğrulandı. Sıfırlama butonu koda bakılınca doğru ama native onay penceresi otomasyon aracıyla test edilemedi (küçük, önemsiz bir kısıt).
- **İptal listesi komutları eklendi ve test edildi**: `admin_araci.py iptal-ekle-mobil <kod>`, `iptal-ekle-usb "<ad>" <seri>`, `iptal-listele`. `tahta-config/iptal.txt`'e yazıyor (git'e gidecek, `install.sh` artık bunu da `/etc/tahtakilit/`'e kopyalıyor). Board tarafında hem mobil hem USB akışında iptal edilmiş kayıtların reddedildiği doğrulandı.

## Gerçek Pardus donanımında test edildi — BAŞARILI (2026-09-17)

Pardus'taki ayrı Claude Desktop oturumu `pardus-gorevler.md`'yi uygulayıp gerçek donanımda test etti:
- **Mobil Anahtar**: doğru kod açıyor OK; eski nonce'tan üretilen kod reddediliyor OK; 3 yanlış denemeden sonra 15sn kilitlenip sonra tekrar açılıyor OK.
- **USB Anahtar**: gerçek bir USB bellekle (SanDisk Cruzer Blade, seri `4C530001310920108400`) test edildi, takılınca ~2sn içinde otomatik açılıyor OK, yanlış/kopyalanmış seri no ile reddediliyor OK.
- Dosyayı kopyalayıp başka USB'ye taşıma + isim/seri alanlarını elle değiştirme saldırısı da burada (Windows'ta) ayrıca simüle edilip doğrulandı: imza her durumda geçersiz kılıyor, hiçbir tahrifat işe yaramıyor.

**Bulunan ve düzeltilen bug**: `keyauth.usb_seri_no_oku`, seri numarasını `/sys/block/<aygıt>/device/serial` gibi sysfs yollarından okumaya çalışıyordu — normal USB bellekler (USB mass storage) bunu o yoldan sunmadığı için fonksiyon hep `None` dönüyordu, USB Anahtar akışı hiç çalışmıyordu. **Düzeltme** (Pardus tarafında yapıldı, git'e geldi): `udevadm info --query=property --name <aygıt>` çalıştırıp `ID_SERIAL_SHORT` özelliğini okuyacak şekilde değiştirildi — bu, USB depolama aygıtlarının gerçek seri no'sunu tuttuğu doğru yer.

**Sonuç**: Faz 2'nin çekirdek kilit açma mekanizması (USB + Mobil, ikisi de) artık gerçek donanımda çalıştığı doğrulanmış durumda. Kalan işler yukarıdaki "Henüz yapılmadı" listesinde.

## Ertelenen / belirsiz konular (kapsam dışı, şimdilik)
- EBA karekodu ile doğrudan tahtayı açma: resmi bir API olup olmadığı belirsiz, araştırılmadı, muhtemelen mümkün değil.
- Yoklama, duyurular, bildirimler gibi ek özellikler (Mehcan'da var): ileride değerlendirilebilir, ağ/sunucu gerektirebilir.
- Ders/teneffüs saatlerine göre otomatik kilit/açma: ayrı bir özellik olarak ileride değerlendirilebilir.
- `.deb` paket haline getirme: artık `pardus_kurulum.py` ile git/terminal'siz kurulum var, gerçek `.deb`'e gerek kalmayabilir — bkz. "Grafik Kurulum Paketi" bölümü.
- **Kilit açıldıktan sonra sağ alt köşede küçük bir kontrol penceresi** (kullanıcı notu, 2026-09-18): Mehcan'da, USB/mobil anahtarla açıldıktan sonra ekranın sağ altında küçük bir pencerecik beliriyor — içinde "Yoklama Al", "Tahtayı Kilitle" gibi birkaç hızlı seçenek var (kullanıcı tüm seçenekleri tam hatırlamıyor). İleride gerekip gerekmeyeceği belirsiz, şimdilik sadece not düşülüyor.

## Genel yaklaşım notu
Bu proje boyunca "ponytail" (en yalın/en az kod, YAGNI, stdlib/native önce) prensibiyle ilerlendi — her yeni özellik için önce en basit çözüm denendi, karmaşıklaştırma ihtiyaç doğunca yapıldı.
