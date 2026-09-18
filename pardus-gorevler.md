# Pardus'ta Yapılacaklar / Test Edilecekler

## YENİ (2026-09-18) — pardus_kurulum.py hiç test edilmedi, ÖNCELİKLİ

ANKA'da "Kurulum Paketi Oluştur" (Okul Kurulumu > Kurulum Paketi) ile bir
`ANKA-Kurulum` klasörü üretilip USB'ye kopyalanabiliyor. Bu klasördeki
`pardus_kurulum.py` (grafik kurulum penceresi) **bu makinede hiç GTK
olmadığı için sadece syntax kontrolünden geçti, gerçek donanımda hiç
çalıştırılmadı.**

Test et:
1. Windows'ta ANKA'da "Kurulum Paketi Oluştur" ile bir paket üret (bir USB'ye).
2. USB'yi Pardus'a tak, `ANKA-Kurulum` klasörünü aç.
3. `baslat.sh`'a çift tıkla. Çalışmazsa (metin editöründe açılırsa): sağ tık
   > Özellikler > İzinler > "Çalıştırılabilir olarak çalıştırmaya izin ver"
   kutucuğunu işaretleyip tekrar dene (bkz. klasördeki `OKU.txt`).
4. Açılan pencerede sınıf ismi gir (örn. "5-A Sınıfı"), kullanıcı adını boş
   bırak (otomatik bulunsun), "Kur"a bas.
5. `pkexec` grafiksel şifre penceresi çıkmalı — `etapadmin` şifresini gir.
6. Kurulum bitince "Tahtayı Şimdi Kilitle" butonu çıkmalı — tıklayınca kilit
   ekranı hemen açılmalı, üstünde "5-A Sınıfı — Tahta Kilitli" yazmalı.
7. Kontrol et: `/opt/tahtakilit/` ve `/etc/tahtakilit/` doğru dolmuş mu,
   `cat /etc/tahtakilit/sinif_adi.txt` doğru ismi gösteriyor mu.
8. USB/mobil anahtarların hâlâ çalıştığını doğrula (bu kurulum yöntemi
   git tabanlısının yerini tutuyor, aynı sonucu vermeli).


## YENİ (2026-09-18) — USB anahtar dosya formatı değişti, DİKKAT

`keyauth.usb_anahtari_olustur`/`usb_anahtari_dogrula` iki büyük değişiklik
geçirdi:
1. İmzalanan mesaja `ogretmen_kodu` eklendi (aynı öğretmenin birden fazla
   USB'sinin/mobil anahtarının aynı kodu paylaşması için).
2. Dosya formatı tek bir nesneden **listeye** döndü (çoklu okul desteği —
   aynı USB'ye birden fazla okulun kaydı sığabiliyor, tahta kendi okuluna
   ait olanı bulup açıyor).

**Bu, eski formatla üretilmiş USB anahtar dosyalarını geçersiz kılan bir
değişiklik** — Pardus'taki `keyauth.py` mutlaka güncellenmeli (`git pull`),
yoksa eski/yeni format uyuşmaz, hiçbir USB anahtarı açılmaz. Güncelledikten
sonra yeni bir USB anahtarı üretip gerçek donanımda test et. İki farklı
"okul" (iki ayrı `okul_kurulumu_yap` ile üretilmiş anahtar çifti) simüle
edip aynı USB'ye ekleyerek çoklu okul senaryosunu da gerçek donanımda
denemek iyi olur — şu ana kadar sadece mantık seviyesinde test edildi.

Ayrıca admin arayüzü Tkinter'dan **PySide6/Qt**'ye geçti (aşağıdaki eski
notlardaki Tkinter/`python3-tk` talimatları artık geçersiz) ve tüm admin
verisi artık şifreli bir SQLite deposunda (`admin-gizli/veri.enc`) — program
açılışında yönetici şifresi soruyor. Pardus'ta admin aracını denemek
istersen: `pip install PySide6 qrcode Pillow cryptography` (ya da
`python3-pyside6` gibi bir paket varsa onu), sonra `python3 admin_gui.py`.

## YENİ (2026-09-17, akşam) — admin_gui.py eklendi, Linux tarafı hiç test edilmedi (ESKİ, Tkinter dönemi notları)

Windows'ta (Tkinter + WMI ile USB tespiti) uçtan uca test edildi, çalışıyor.
Linux/Pardus tarafındaki USB tespiti (`lsblk` ile) **hiç test edilmedi** —
admin bu aracı büyük ihtimalle Windows'ta kullanacak ama yine de çalışsın:

```bash
sudo apt install -y python3-tk   # Tkinter Pardus'ta ayrı paket olabilir
cd /opt/tahtakilit
python3 admin_gui.py
```

Test et: "Anahtarlar" > "USB Anahtar" sekmesinde takılı bir USB gerçekten
listeleniyor mu (seri no dahil), "Anahtar Oluştur" ile dosya gerçekten
USB köküne `.tahtakilit_anahtar.json` (gizli) olarak yazılıyor mu.

## YENİ (2026-09-17, öğleden sonra) — arayüz değişikliği, tekrar test gerekiyor

- `lockscreen.py` baştan yazıldı: artık fiziksel klavye ile kod girilmiyor,
  ekranda dokunmatik bir tuş takımı (0-9 + Sil) var — "Karekod Oluştur"a
  basınca çıkıyor, 45 saniye içinde kullanılmazsa karekod+tuş takımı
  otomatik gizleniyor (tekrar "Karekod Oluştur" gerekiyor).
- Mobil kod artık **6 haneli** (öğretmen kodu ayrıca yazılmıyor, tahta
  kendi buluyor — bkz. `keyauth.mobil_cevap_dogrula`).
- Öğretmen kodu uzunluğu 3'ten 4'e çıktı (`OGRETMEN_KODU_UZUNLUK`).
- `mobil-anahtar.html` sadeleşti: elle giriş alanları ve "Anahtarı
  değiştir" butonu kaldırıldı, sadece "Karekod Tara" butonu kaldı.
- `keyauth.kullanim_logla` eklendi: kilit her açıldığında
  `/etc/tahtakilit/kullanim.log`'a kimlik (isim yerine sadece kod/isim)
  kaydediliyor, ekranda hiç görünmüyor.

**Test et:**
1. `python3 admin_araci.py mobil-anahtar-uret "Test Ogretmen"` ile yeni
   (4 haneli) bir kod üret, telefonuna taratıp kur.
2. Tahtada "Karekod Oluştur"a bas, ekranda dokunmatik tuş takımının
   çıktığını doğrula. Fiziksel klavyeden rakam basmanın **hiçbir etkisi
   olmaması** lazım (sadece ekrandaki butonlar çalışmalı).
3. Telefonla tara, üretilen 6 haneli kodu **ekrandaki tuş takımıyla**
   gir — 6. rakamda otomatik denemesi lazım (ayrı bir "Aç" butonuna
   basmaya gerek yok).
4. "Karekod Oluştur"a bas, **45 saniye hiçbir şey yapma** — karekod ve
   tuş takımının otomatik kaybolduğunu doğrula.
5. `cat /etc/tahtakilit/kullanim.log` ile kilit açma kaydının doğru
   yazıldığını kontrol et.


Bu dosyayı Windows tarafında ben (Claude) güncelliyorum. Sen `git pull`
(ya da `./github_al.sh`) ile çektikten sonra, Pardus'taki Claude'a
"pardus-gorevler.md dosyasını oku ve uygula" diyebilirsin.

## Durum: 2026-09-16 (güncellendi) — Faz 2, meydan okuma-cevap tasarımıyla test edilmeyi bekliyor

**Önemli değişiklik**: Mobil akış artık zaman bazlı (TOTP) değil, "meydan okuma-cevap"
(challenge-response) yöntemiyle çalışıyor, ve her öğretmen ayrı kimlik taşıyor
(sınırsız öğretmen desteği). Kilit ekranı artık QR'ı açılışta göstermiyor,
sadece "Karekod Oluştur" butonuna basılınca üretiyor.

### Yeni/değişen dosyalar
- `keyauth.py` — anahtar üretme/doğrulama mantığı (yeni)
- `lockscreen.py` — PIN yerine USB+Mobil anahtar kullanacak şekilde yeniden yazıldı
- `admin_araci.py` — admin'in anahtar üretmek için kullanacağı CLI aracı (yeni)
- `mobil-anahtar.html` — öğretmenin telefonunda açacağı kod üretme sayfası (yeni)
- `install.sh` — eksikti, yeniden yazıldı
- `.gitignore` — gizli anahtarların yanlışlıkla git'e gitmesini engelliyor

### Yapılması gerekenler (sırayla)

1. **Bağımlılıkları kur** (`install.sh` zaten bunu yapıyor, ama emin olmak için):
   ```bash
   sudo apt update
   sudo apt install -y python3-gi gir1.2-gtk-3.0 python3-cryptography python3-qrcode
   ```

2. **Admin anahtarlarını üret** (henüz hiç üretilmedi — bunu Pardus'ta ya da
   Windows'ta çalıştırabilirsin, fark etmez, sonucu `tahta-config/` klasörüne
   yazıyor):
   ```bash
   cd /opt/tahtakilit
   python3 admin_araci.py kurulum
   ```
   Bu `tahta-config/okul_acik.key` ve `tahta-config/mobil_gizli.key`
   üretecek — bunları git'e gönder (`./github_gonder.sh`) ki `install.sh`
   tahtalara kopyalayabilsin. Bu komut artık önce bir yönetici şifresi
   soracak (ilk seferde belirlersin) — özel anahtar `admin-gizli/veri.enc`
   içinde şifreli tutuluyor, ASLA git'e gitmemeli (`.gitignore`'da zaten
   hariç tutuldu, kontrol et).

3. **Kurulumu çalıştır**:
   ```bash
   sudo bash install.sh
   ```
   (artık kullanıcı adı sormuyor — sistem geneli autostart kuruluyor,
   kim oturum açarsa açsın çalışır)

4. **Elle test et** (otomatik başlamasını beklemeden):
   ```bash
   python3 /opt/tahtakilit/lockscreen.py
   ```
   Beklenen: tam ekran kilit açılsın, ortada bir karekod görünsün, altında
   6 haneli kod girme kutusu olsun.

5. **Mobil Anahtar akışını test et**:
   - Bir test öğretmeni için kurulum karekodu üret:
     ```bash
     python3 admin_araci.py mobil-anahtar-uret "Test Ogretmen"
     ```
     (öğretmen kodu otomatik atanır, `/tmp/mobil_anahtar_XXX.png` üretilir)
   - `mobil-anahtar.html` dosyasını telefona aktar (ya da Pardus'ta bir
     tarayıcıda aç, ekran görüntüsüyle telefona bakabilirsin ilk testte).
   - "Karekod Tara" ile yukarıdaki kurulum karekodunu **bir kez** tara
     (ya da terminaldeki `master_gizli|kod|isim` satırını elle yapıştır).
   - Tahtada **"Karekod Oluştur"** butonuna bas — QR o an üretilir.
   - Telefon uygulamasında "Karekodu Tara" ile bu QR'ı tara.
   - Uygulamanın ürettiği (6 haneli) kodu
     tahtaya gir, açılması lazım.
   - **Ayrıca test et**: "Karekod Oluştur"a tekrar bas (yeni nonce), ESKİ
     QR'dan üretilmiş kod artık çalışMAMALI.

6. **USB Anahtar akışını test et**:
   - Bir USB bellek tak, gerçek seri numarasını öğren:
     ```bash
     lsblk -o NAME,SERIAL
     ```
   - Admin aracıyla o USB için anahtar üret:
     ```bash
     python3 admin_araci.py usb-anahtar-uret "Test Ogretmen" <SERI_NO> /tmp/anahtar.json
     ```
   - `/tmp/anahtar.json` dosyasını USB'nin köküne `.tahtakilit_anahtar.json`
     adıyla kopyala.
   - USB'yi tahtaya (bu makineye) tak, birkaç saniye içinde kilidin
     otomatik açılması lazım.
   - **Ayrıca test et**: aynı dosyayı BAŞKA bir USB'ye kopyala, o USB'yi
     takınca açılMAMASI lazım (seri no uyuşmadığı için).

7. **Yanlış kod / kilitlenme testi**: kod kutusuna 3 kere yanlış kod gir,
   15 saniyeliğine kilitlenmesi lazım (giriş kutusu pasif, geri sayım
   yazısı görünmeli).

### Bulunan hatalar / notlar için
Buraya (dosyanın sonuna) madde ekleyerek yaz, ben Windows'ta okuyup
düzelteceğim. Format:

```
## Bulunan sorun (2026-09-16)
- Ne oldu:
- Beklenen:
- Hata mesajı (varsa):
```

## Test sonuçları (2026-09-17, Pardus'ta yapıldı)

- **Mobil Anahtar**: doğru kod ile açılma OK; eski karekoddan (nonce
  değişince) üretilen kod reddediliyor OK; 3 yanlış deneme → 15sn
  kilitlenme → süre sonu tekrar açık OK. Otomatik test scriptleriyle
  (nonce sabitlenerek, gerçek `mobil_cevap_dogrula` ile) doğrulandı.
- **USB Anahtar**: aşağıdaki bug düzeltildikten sonra gerçek bir USB
  bellekle (SanDisk Cruzer Blade, seri `4C530001310920108400`) test
  edildi — takılınca ~2sn içinde otomatik açılma OK, yanlış seri no ile
  reddedilme OK.

## Bulunan sorun (2026-09-17) — DÜZELTİLDİ

- Ne oldu: USB Anahtar akışı hiç çalışmıyordu. `keyauth.usb_seri_no_oku`
  seri numarasını `/sys/block/<aygıt>/device/serial` ya da
  `/sys/block/<aygıt>/serial` dosyalarından okumaya çalışıyordu, ama
  normal USB bellekler (USB mass storage/SCSI) bu sysfs yollarını
  expose etmiyor — bu yüzden fonksiyon her zaman `None` dönüyordu.
- Beklenen: USB takılınca birkaç saniye içinde otomatik açılması.
- Kök neden: doğru seri no aslında udev'in `ID_SERIAL_SHORT`
  özelliğinde duruyor (`udevadm info --query=property --name /dev/sdX`
  ile doğrulandı).
- Düzeltme: `keyauth.usb_seri_no_oku`, `lockscreen.py`'de zaten
  kullanılan `subprocess` deseniyle (bkz. `usb_aygit_yolunu_tahmin_et`)
  `udevadm info --query=property --name <aygıt>` çalıştırıp
  `ID_SERIAL_SHORT` satırını okuyacak şekilde değiştirildi. Gerçek
  USB'yle test edilip doğrulandı, bkz. yukarıdaki test sonuçları.
