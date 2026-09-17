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
- Her öğretmenin 3 haneli bir **"öğretmen kodu"** var. Öğretmenin telefonu, `HMAC(okul_mobil_anahtarı, öğretmen_kodu)` ile kendi kişisel anahtarını türetir, `HMAC(kişisel_anahtar, nonce)` ile 6 haneli cevap üretir. Ekranda gösterilen/tahtaya girilecek tam kod: **öğretmen kodu + cevap (9 hane)**.
- Tahta, girilen 9 haneyi ayırıp öğretmen kodundan kişisel anahtarı **kendi kendine yeniden türetir** — önceden bir öğretmen listesi tutmasına gerek yok, yeni öğretmen eklemek tahtaya dokunmayı gerektirmiyor (USB akışındaki "otomatik tanıma" prensibiyle aynı).
- Her "Karekod Oluştur" tıklaması eskisini geçersiz kılıyor (aynı anda tek nonce geçerli).
- JS (mobil-anahtar.html) ve Python (keyauth.py) tarafındaki hesaplamalar birebir çapraz test edildi (aynı girdilerle aynı çıktı).

Dosyalar (repo kökünde):
- `keyauth.py` — anahtar üretme/doğrulama: USB için Ed25519 imza (+ USB seri no bağlama), Mobil için meydan okuma-cevap. PIN tamamen kaldırıldı.
- `lockscreen.py` — "Karekod Oluştur" butonu, kod girişi (9 hane), USB otomatik tarama, 3 yanlıştan sonra 15sn kilitlenme.
- `admin_araci.py` — admin CLI: `kurulum` (okul anahtarlarını bir kere üretir), `usb-anahtar-uret`, `mobil-anahtar-uret "Ad" [--kod NNN]` (öğretmen kodu otomatik atanır, `admin-gizli/ogretmenler.json`'da kayıt tutulur, çakışma engellenir).
- `mobil-anahtar.html` — öğretmen telefonunda açılan, tamamen offline (saf JS SHA-1/HMAC, Web Crypto'ya bağımlı değil, `file://` üzerinden çalışır) kod üretme sayfası. Kurulumda hem admin karekodunu tarayıp hem elle girebiliyor.
- `install.sh` — bağımlılıkları kurar, `tahta-config/`'i `/etc/tahtakilit/`'e kopyalar, autostart kurar.
- `.gitignore` — `admin-gizli/` (okul_ozel.key, ogretmenler.json) asla git'e gitmiyor; `tahta-config/` (okul_acik.key, mobil_gizli.key) BİLEREK git'e gidiyor.
- `pardus-gorevler.md` — Pardus'ta test edilecekler, Windows-Pardus arası "görev listesi".

**Henüz yapılmadı:**
- Cython ile native binary'ye derleme (kod koruması kararı verildi ama build adımı henüz eklenmedi).
- Okul bilgileri/ders-teneffüs saatleri özelliği (kapsam dışı, aşağıda).
- İptal güncellemesinin tahtalara ulaşması şu an **manuel** — `iptal.txt` değişince `install.sh`'in yeniden çalıştırılması gerekiyor. Otomatik senkronizasyon (GitHub'dan periyodik çekme) henüz kurulmadı, bkz. "Faz 2" bölümündeki senkronizasyon planı.

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
- `.deb` paket haline getirme: ileride yapılabilir, şu an `install.sh` yeterli.

## Genel yaklaşım notu
Bu proje boyunca "ponytail" (en yalın/en az kod, YAGNI, stdlib/native önce) prensibiyle ilerlendi — her yeni özellik için önce en basit çözüm denendi, karmaşıklaştırma ihtiyaç doğunca yapıldı.
