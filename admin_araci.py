#!/usr/bin/env python3
"""Tahta Kilit - Admin CLI aracı.

Bu araç ADMIN'in kendi bilgisayarında çalışır, tahtalara KURULMAZ.
Ürettiği `okul_ozel.key` dosyası ASLA hiçbir tahtaya veya git'e gitmemeli
(bkz. .gitignore).

Kullanım:
  python3 admin_araci.py kurulum
      -> okul anahtar çiftini ve mobil gizli anahtarı üretir (bir kere).
         Tahtalara kopyalanacak dosyaları da ayrıca yazar (okul_acik.key,
         mobil_gizli.key) - bunlari install.sh /etc/tahtakilit altina koyar.

  python3 admin_araci.py usb-anahtar-uret "Ogretmen Adi" <seri_no> <cikti.json>
      -> imzali USB anahtar dosyasi uretir, ciktiyi verilen yola yazar.
         Sonra bu dosyayi elle USB'nin koekuene kopyala
         (dosya adi: tahtakilit_anahtar.json).

  python3 admin_araci.py mobil-anahtar-uret "Ogretmen Adi" [--kod 042]
      -> bu ogretmen icin bir "ogretmen kodu" atar (verilmezse otomatik
         siradaki bosu secer) ve telefonuna BIR KERE taratacagi kurulum
         karekodunu uretir (admin-gizli/ogretmenler.json'da kayit tutulur,
         ayni kodun iki farkli isme verilmesini engeller).

  python3 admin_araci.py iptal-ekle-mobil <ogretmen_kodu>
  python3 admin_araci.py iptal-ekle-usb "Ogretmen Adi" <seri_no>
      -> ogretmen ayrildiginda/anahtarini kaybettiginde bu kaydi
         tahta-config/iptal.txt'e ekler. Bunu git'e gonderip tahtalarda
         install.sh'i yeniden calistirmak gerekir (Faz 3'te otomatik
         senkronizasyon eklenene kadar).

  python3 admin_araci.py iptal-listele
      -> su anki iptal listesini gosterir.
"""
import argparse
import json
import os
import sys

import keyauth

# GİZLİ - asla git'e gitmez, sadece admin'in bilgisayarında kalır (.gitignore'da)
GIZLI_DIZIN = "admin-gizli"
OZEL_ANAHTAR_DOSYASI = os.path.join(GIZLI_DIZIN, "okul_ozel.key")
OGRETMENLER_DOSYASI = os.path.join(GIZLI_DIZIN, "ogretmenler.json")

# PAYLAŞILAN - bilerek git'e gider, tahtalar bunu install.sh ile alır
TAHTA_CONFIG_DIZINI = "tahta-config"
ACIK_ANAHTAR_DOSYASI = os.path.join(TAHTA_CONFIG_DIZINI, "okul_acik.key")
MOBIL_ANAHTAR_DOSYASI = os.path.join(TAHTA_CONFIG_DIZINI, "mobil_gizli.key")
IPTAL_DOSYASI = os.path.join(TAHTA_CONFIG_DIZINI, "iptal.txt")


def komut_kurulum(_args):
    os.makedirs(GIZLI_DIZIN, exist_ok=True)
    os.makedirs(TAHTA_CONFIG_DIZINI, exist_ok=True)

    if os.path.exists(OZEL_ANAHTAR_DOSYASI):
        print(f"UYARI: {OZEL_ANAHTAR_DOSYASI} zaten var, üzerine yazılmadı.")
        print("Yeniden üretmek istersen dosyayı elle sil ve tekrar çalıştır.")
        return

    ozel_b64, acik_b64 = keyauth.okul_anahtari_uret()
    mobil_b32 = keyauth.mobil_gizli_anahtar_uret()

    with open(OZEL_ANAHTAR_DOSYASI, "w") as f:
        f.write(ozel_b64)
    with open(ACIK_ANAHTAR_DOSYASI, "w") as f:
        f.write(acik_b64)
    with open(MOBIL_ANAHTAR_DOSYASI, "w") as f:
        f.write(mobil_b32)

    print(f"  {OZEL_ANAHTAR_DOSYASI}  <- GİZLİ, hiçbir yere kopyalama, git'e gitmez ({GIZLI_DIZIN}/ .gitignore'da)")
    print(f"  {ACIK_ANAHTAR_DOSYASI}  <- git'e gidecek, install.sh tahtalara kopyalayacak")
    print(f"  {MOBIL_ANAHTAR_DOSYASI} <- git'e gidecek, install.sh tahtalara kopyalayacak")
    print("Şimdi github_gonder.sh/bat ile gönder, sonra Pardus'ta install.sh çalıştır.")


def komut_usb_anahtar_uret(args):
    if not os.path.exists(OZEL_ANAHTAR_DOSYASI):
        sys.exit(f"Önce 'kurulum' komutunu çalıştır ({OZEL_ANAHTAR_DOSYASI} yok).")

    with open(OZEL_ANAHTAR_DOSYASI) as f:
        ozel_b64 = f.read().strip()

    icerik = keyauth.usb_anahtari_olustur(ozel_b64, args.ogretmen_adi, args.seri_no)
    with open(args.cikti, "w") as f:
        f.write(icerik)

    print(f"Üretildi: {args.cikti}")
    print(f"Şimdi bu dosyayı USB belleğin köküne '{keyauth.USB_ANAHTAR_DOSYA_ADI}' adıyla kopyala.")


def _ogretmenleri_yukle():
    try:
        with open(OGRETMENLER_DOSYASI) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _ogretmenleri_kaydet(kayit):
    os.makedirs(GIZLI_DIZIN, exist_ok=True)
    with open(OGRETMENLER_DOSYASI, "w") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=2)


def _sonraki_bos_kod(kayit):
    for n in range(1000):
        aday = str(n).zfill(keyauth.OGRETMEN_KODU_UZUNLUK)
        if aday not in kayit:
            return aday
    sys.exit("1000 öğretmen kodu da dolu, bu olmamalıydı.")


def komut_mobil_anahtar_uret(args):
    if not os.path.exists(MOBIL_ANAHTAR_DOSYASI):
        sys.exit(f"Önce 'kurulum' komutunu çalıştır ({MOBIL_ANAHTAR_DOSYASI} yok).")
    with open(MOBIL_ANAHTAR_DOSYASI) as f:
        master_gizli = f.read().strip()

    kayit = _ogretmenleri_yukle()

    ogretmen_kodu = args.kod
    if ogretmen_kodu:
        if len(ogretmen_kodu) != keyauth.OGRETMEN_KODU_UZUNLUK or not ogretmen_kodu.isdigit():
            sys.exit(f"Öğretmen kodu {keyauth.OGRETMEN_KODU_UZUNLUK} haneli rakam olmalı.")
        if ogretmen_kodu in kayit and kayit[ogretmen_kodu] != args.ogretmen_adi:
            sys.exit(f"Kod {ogretmen_kodu} zaten '{kayit[ogretmen_kodu]}' için kullanılıyor.")
    else:
        ogretmen_kodu = _sonraki_bos_kod(kayit)

    kayit[ogretmen_kodu] = args.ogretmen_adi
    _ogretmenleri_kaydet(kayit)

    kurulum_verisi = f"{master_gizli}|{ogretmen_kodu}|{args.ogretmen_adi}"
    print(f"Öğretmen: {args.ogretmen_adi}  Kod: {ogretmen_kodu}")
    print(kurulum_verisi)

    try:
        import qrcode
    except ImportError:
        print("(qrcode kütüphanesi yok, sadece metin gösterildi - 'sudo apt install python3-qrcode')")
        return

    cikti = args.karekod_cikti or f"/tmp/mobil_anahtar_{ogretmen_kodu}.png"
    qrcode.make(kurulum_verisi).save(cikti)
    print(f"Karekod kaydedildi: {cikti}")
    print("Öğretmen bunu mobil-anahtar.html'deki 'Karekod Tara' ile BİR KEZ taratacak.")


def _iptal_satirlarini_oku():
    try:
        with open(IPTAL_DOSYASI) as f:
            return [s.rstrip("\n") for s in f if s.strip()]
    except FileNotFoundError:
        return []


def _iptal_satirlarini_yaz(satirlar):
    os.makedirs(TAHTA_CONFIG_DIZINI, exist_ok=True)
    with open(IPTAL_DOSYASI, "w") as f:
        for s in satirlar:
            f.write(s + "\n")


def komut_iptal_ekle_mobil(args):
    satirlar = _iptal_satirlarini_oku()
    if args.kod in satirlar:
        print(f"'{args.kod}' zaten iptal listesinde.")
        return
    satirlar.append(args.kod)
    _iptal_satirlarini_yaz(satirlar)
    print(f"Eklendi: mobil öğretmen kodu '{args.kod}' artık geçersiz.")
    print(f"{IPTAL_DOSYASI}'i git'e gönder ki tahtalar alsın (install.sh yeniden çalıştırılmalı).")


def komut_iptal_ekle_usb(args):
    kayit = f"{args.ogretmen_adi}|{args.seri_no}"
    satirlar = _iptal_satirlarini_oku()
    if kayit in satirlar:
        print(f"'{kayit}' zaten iptal listesinde.")
        return
    satirlar.append(kayit)
    _iptal_satirlarini_yaz(satirlar)
    print(f"Eklendi: USB anahtarı '{kayit}' artık geçersiz.")
    print(f"{IPTAL_DOSYASI}'i git'e gönder ki tahtalar alsın (install.sh yeniden çalıştırılmalı).")


def komut_iptal_listele(_args):
    satirlar = _iptal_satirlarini_oku()
    if not satirlar:
        print("İptal listesi boş.")
        return
    for s in satirlar:
        print(s)


def main():
    ust = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ust.add_subparsers(required=True)

    p1 = alt.add_parser("kurulum", help="Okul anahtar çiftini bir kere üret")
    p1.set_defaults(fn=komut_kurulum)

    p2 = alt.add_parser("usb-anahtar-uret", help="Bir öğretmen için USB anahtar dosyası üret")
    p2.add_argument("ogretmen_adi")
    p2.add_argument("seri_no", help="USB'nin gerçek seri no'su (tahtadaki/admin PC'deki komutla okunur)")
    p2.add_argument("cikti", help="Üretilecek json dosyasının yolu")
    p2.set_defaults(fn=komut_usb_anahtar_uret)

    p3 = alt.add_parser("mobil-anahtar-uret", help="Bir öğretmen için mobil kurulum karekodu üret")
    p3.add_argument("ogretmen_adi")
    p3.add_argument("--kod", help=f"{keyauth.OGRETMEN_KODU_UZUNLUK} haneli öğretmen kodu (verilmezse otomatik atanır)")
    p3.add_argument("--karekod-cikti", dest="karekod_cikti", default=None)
    p3.set_defaults(fn=komut_mobil_anahtar_uret)

    p4 = alt.add_parser("iptal-ekle-mobil", help="Bir öğretmenin mobil kodunu iptal et (ayrıldı/kaybetti)")
    p4.add_argument("kod", help="İptal edilecek öğretmen kodu")
    p4.set_defaults(fn=komut_iptal_ekle_mobil)

    p5 = alt.add_parser("iptal-ekle-usb", help="Bir öğretmenin USB anahtarını iptal et (ayrıldı/kaybetti)")
    p5.add_argument("ogretmen_adi")
    p5.add_argument("seri_no", help="İptal edilecek USB'nin seri no'su")
    p5.set_defaults(fn=komut_iptal_ekle_usb)

    p6 = alt.add_parser("iptal-listele", help="Şu anki iptal listesini göster")
    p6.set_defaults(fn=komut_iptal_listele)

    args = ust.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
