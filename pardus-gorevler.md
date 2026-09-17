# Pardus'ta Yapılacaklar / Test Edilecekler

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
   tahtalara kopyalayabilsin. `admin-gizli/okul_ozel.key` ASLA git'e gitmemeli
   (`.gitignore`'da zaten hariç tutuldu, kontrol et).

3. **Kurulumu çalıştır**:
   ```bash
   sudo bash install.sh ogretmen
   ```
   (kullanıcı adı farklıysa değiştir)

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
   - Uygulamanın ürettiği (öğretmen kodu + cevap, toplam 9 haneli) kodu
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
   - `/tmp/anahtar.json` dosyasını USB'nin köküne `tahtakilit_anahtar.json`
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
