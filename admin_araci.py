#!/usr/bin/env python3
"""Tahta Kilit - Admin CLI aracı.

Bu araç ADMIN'in kendi bilgisayarında çalışır, tahtalara KURULMAZ.
Hassas veriler (özel anahtar, öğretmen listesi, okul bilgileri, ders programı)
`veri_deposu.py` üzerinden ŞİFRELİ tek bir dosyada (admin-gizli/veri.enc)
tutuluyor - CLI kullanımı için de önce `veri_deposu` kilidi açılmalı.

Buradaki fonksiyonlar (alt çizgisiz olanlar) hem bu CLI'dan hem de
admin_gui.py'den kullanılıyor - iş mantığı bir kere yazılıp iki arayüzden
de çağrılıyor.

Kullanım (CLI):
  python3 admin_araci.py kurulum
  python3 admin_araci.py usb-anahtar-uret "Ogretmen Adi" <seri_no> <cikti.json>
  python3 admin_araci.py mobil-anahtar-uret "Ogretmen Adi" [--kod 042]
  python3 admin_araci.py iptal-ekle-mobil <ogretmen_kodu>
  python3 admin_araci.py iptal-ekle-usb "Ogretmen Adi" <seri_no>
  python3 admin_araci.py iptal-listele

  Hepsi ilk çalıştırmada yönetici şifresi soracak (depo yoksa oluşturur,
  varsa açar).
"""
import argparse
import getpass
import os
import sys

import keyauth
import veri_deposu

# PAYLAŞILAN - bilerek git'e gider, tahtalar bunu install.sh ile alır
TAHTA_CONFIG_DIZINI = "tahta-config"
ACIK_ANAHTAR_DOSYASI = os.path.join(TAHTA_CONFIG_DIZINI, "okul_acik.key")
MOBIL_ANAHTAR_DOSYASI = os.path.join(TAHTA_CONFIG_DIZINI, "mobil_gizli.key")
IPTAL_DOSYASI = os.path.join(TAHTA_CONFIG_DIZINI, "iptal.txt")

VARSAYILAN_DERS_PROGRAMI = [
    {"tur": "1. Ders", "baslama": "08:00", "bitis": "08:40"},
    {"tur": "1. Teneffüs", "baslama": "08:40", "bitis": "08:50"},
    {"tur": "2. Ders", "baslama": "08:50", "bitis": "09:30"},
    {"tur": "2. Teneffüs", "baslama": "09:30", "bitis": "09:40"},
    {"tur": "3. Ders", "baslama": "09:40", "bitis": "10:20"},
    {"tur": "3. Teneffüs", "baslama": "10:20", "bitis": "10:30"},
    {"tur": "4. Ders", "baslama": "10:30", "bitis": "11:10"},
    {"tur": "4. Teneffüs", "baslama": "11:10", "bitis": "11:20"},
    {"tur": "5. Ders", "baslama": "11:20", "bitis": "12:00"},
    {"tur": "5. Teneffüs", "baslama": "12:00", "bitis": "12:20"},
    {"tur": "6. Ders", "baslama": "12:20", "bitis": "13:00"},
    {"tur": "6. Teneffüs", "baslama": "13:00", "bitis": "13:10"},
    {"tur": "7. Ders", "baslama": "13:10", "bitis": "13:50"},
    {"tur": "7. Teneffüs", "baslama": "13:50", "bitis": "14:00"},
    {"tur": "8. Ders", "baslama": "14:00", "bitis": "14:40"},
]


class AdminHatasi(Exception):
    """CLI'da sys.exit ile, GUI'de bir hata penceresiyle gösterilir."""


# ---------------------------------------------------------------------------
# Okul kurulumu
# ---------------------------------------------------------------------------

def okul_kurulu_mu():
    if not veri_deposu.acik_mi():
        return False
    satir = veri_deposu.baglanti().execute(
        "SELECT deger FROM ayarlar WHERE anahtar='okul_ozel_key'"
    ).fetchone()
    return satir is not None


def okul_kurulumu_yap():
    """Zaten kuruluysa hiçbir şey yapmaz, False döner. Yeni kurulumda True döner."""
    if okul_kurulu_mu():
        return False

    ozel_b64, acik_b64 = keyauth.okul_anahtari_uret()
    mobil_b32 = keyauth.mobil_gizli_anahtar_uret()

    conn = veri_deposu.baglanti()
    conn.execute("INSERT INTO ayarlar VALUES ('okul_ozel_key', ?)", (ozel_b64,))
    conn.commit()
    veri_deposu.kaydet()

    os.makedirs(TAHTA_CONFIG_DIZINI, exist_ok=True)
    with open(ACIK_ANAHTAR_DOSYASI, "w") as f:
        f.write(acik_b64)
    with open(MOBIL_ANAHTAR_DOSYASI, "w") as f:
        f.write(mobil_b32)
    return True


def komut_kurulum(_args):
    if not okul_kurulumu_yap():
        print("UYARI: okul zaten kurulu, üzerine yazılmadı.")
        return
    print(f"  Özel anahtar  <- GİZLİ, şifreli depoda ({veri_deposu.VERI_DOSYASI})")
    print(f"  {ACIK_ANAHTAR_DOSYASI}  <- git'e gidecek, install.sh tahtalara kopyalayacak")
    print(f"  {MOBIL_ANAHTAR_DOSYASI} <- git'e gidecek, install.sh tahtalara kopyalayacak")
    print("Şimdi github_gonder.sh/bat ile gönder, sonra Pardus'ta install.sh çalıştır.")


# ---------------------------------------------------------------------------
# USB Anahtar
# ---------------------------------------------------------------------------

def usb_anahtar_hazirla(ogretmen_adi, seri_no):
    """(icerik) döner - USB'ye yazılacak dosyanın tam içeriği."""
    if not okul_kurulu_mu():
        raise AdminHatasi("Önce okul kurulumu yapılmalı.")
    ozel_b64 = veri_deposu.baglanti().execute(
        "SELECT deger FROM ayarlar WHERE anahtar='okul_ozel_key'"
    ).fetchone()[0]
    return keyauth.usb_anahtari_olustur(ozel_b64, ogretmen_adi, seri_no)


def komut_usb_anahtar_uret(args):
    try:
        icerik = usb_anahtar_hazirla(args.ogretmen_adi, args.seri_no)
    except AdminHatasi as e:
        sys.exit(str(e))

    with open(args.cikti, "w") as f:
        f.write(icerik)

    print(f"Üretildi: {args.cikti}")
    print(f"Şimdi bu dosyayı USB belleğin köküne '{keyauth.USB_ANAHTAR_DOSYA_ADI}' adıyla kopyala.")


# ---------------------------------------------------------------------------
# Öğretmen kayıtları
# ---------------------------------------------------------------------------

def ogretmenleri_yukle():
    if not veri_deposu.acik_mi():
        return {}
    satirlar = veri_deposu.baglanti().execute("SELECT kod, ad FROM ogretmenler").fetchall()
    return dict(satirlar)


def _ogretmen_kaydet(kod, ad):
    conn = veri_deposu.baglanti()
    conn.execute("INSERT OR REPLACE INTO ogretmenler (kod, ad) VALUES (?, ?)", (kod, ad))
    conn.commit()
    veri_deposu.kaydet()


def sonraki_bos_kod(kayit):
    toplam = 10**keyauth.OGRETMEN_KODU_UZUNLUK
    for n in range(toplam):
        aday = str(n).zfill(keyauth.OGRETMEN_KODU_UZUNLUK)
        if aday not in kayit:
            return aday
    raise AdminHatasi(
        f"{toplam} öğretmen kodu da kullanılmış. Muhtemelen ayrılan öğretmenlerin "
        f"kayıtları hiç temizlenmedi - Kayıtlı Anahtarlar'dan artık aktif olmayanları "
        f"silip kodlarını yeniden kullanabilirsin (o kişinin eski anahtarı zaten "
        f"iptal listesindeyse güvenlik sorunu olmaz)."
    )


def mobil_anahtar_hazirla(ogretmen_adi, kod=None):
    """(ogretmen_kodu, kurulum_verisi) döner."""
    if not os.path.exists(MOBIL_ANAHTAR_DOSYASI):
        raise AdminHatasi("Önce okul kurulumu yapılmalı.")
    with open(MOBIL_ANAHTAR_DOSYASI) as f:
        master_gizli = f.read().strip()

    kayit = ogretmenleri_yukle()

    ogretmen_kodu = kod
    if ogretmen_kodu:
        if len(ogretmen_kodu) != keyauth.OGRETMEN_KODU_UZUNLUK or not ogretmen_kodu.isdigit():
            raise AdminHatasi(f"Öğretmen kodu {keyauth.OGRETMEN_KODU_UZUNLUK} haneli rakam olmalı.")
        if ogretmen_kodu in kayit and kayit[ogretmen_kodu] != ogretmen_adi:
            raise AdminHatasi(f"Kod {ogretmen_kodu} zaten '{kayit[ogretmen_kodu]}' için kullanılıyor.")
    else:
        ogretmen_kodu = sonraki_bos_kod(kayit)

    _ogretmen_kaydet(ogretmen_kodu, ogretmen_adi)

    kurulum_verisi = f"{master_gizli}|{ogretmen_kodu}|{ogretmen_adi}"
    return ogretmen_kodu, kurulum_verisi


def komut_mobil_anahtar_uret(args):
    try:
        ogretmen_kodu, kurulum_verisi = mobil_anahtar_hazirla(args.ogretmen_adi, args.kod)
    except AdminHatasi as e:
        sys.exit(str(e))

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


# ---------------------------------------------------------------------------
# İptal (kara) listesi - tahta-config/iptal.txt, düz metin kalıyor
# (tahtalar bunu okumak zorunda, hassas veri değil - sadece iptal edilmiş
# kod/seri listesi, tek başına işe yaramaz)
# ---------------------------------------------------------------------------

def iptal_satirlarini_oku():
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


def iptal_ekle(kayit):
    """kayit: mobil için 'kod', usb için 'ad|seri'. Zaten varsa False döner."""
    satirlar = iptal_satirlarini_oku()
    if kayit in satirlar:
        return False
    satirlar.append(kayit)
    _iptal_satirlarini_yaz(satirlar)
    return True


def iptal_kaldir(kayit):
    satirlar = iptal_satirlarini_oku()
    if kayit not in satirlar:
        return False
    satirlar.remove(kayit)
    _iptal_satirlarini_yaz(satirlar)
    return True


def komut_iptal_ekle_mobil(args):
    if not iptal_ekle(args.kod):
        print(f"'{args.kod}' zaten iptal listesinde.")
        return
    print(f"Eklendi: mobil öğretmen kodu '{args.kod}' artık geçersiz.")
    print(f"{IPTAL_DOSYASI}'i git'e gönder ki tahtalar alsın (install.sh yeniden çalıştırılmalı).")


def komut_iptal_ekle_usb(args):
    kayit = f"{args.ogretmen_adi}|{args.seri_no}"
    if not iptal_ekle(kayit):
        print(f"'{kayit}' zaten iptal listesinde.")
        return
    print(f"Eklendi: USB anahtarı '{kayit}' artık geçersiz.")
    print(f"{IPTAL_DOSYASI}'i git'e gönder ki tahtalar alsın (install.sh yeniden çalıştırılmalı).")


def komut_iptal_listele(_args):
    satirlar = iptal_satirlarini_oku()
    if not satirlar:
        print("İptal listesi boş.")
        return
    for s in satirlar:
        print(s)


# ---------------------------------------------------------------------------
# Okul Bilgileri / Ders Programı
# ---------------------------------------------------------------------------

def okul_bilgilerini_yukle():
    if not veri_deposu.acik_mi():
        return {}
    satirlar = veri_deposu.baglanti().execute(
        "SELECT anahtar, deger FROM ayarlar WHERE anahtar LIKE 'okul_bilgi_%'"
    ).fetchall()
    return {k[len("okul_bilgi_"):]: v for k, v in satirlar}


def okul_bilgilerini_kaydet(bilgiler):
    conn = veri_deposu.baglanti()
    for anahtar, deger in bilgiler.items():
        conn.execute(
            "INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)",
            (f"okul_bilgi_{anahtar}", deger),
        )
    conn.commit()
    veri_deposu.kaydet()


def ders_programini_yukle():
    if not veri_deposu.acik_mi():
        return [dict(satir) for satir in VARSAYILAN_DERS_PROGRAMI]
    satirlar = veri_deposu.baglanti().execute(
        "SELECT tur, baslama, bitis FROM ders_programi ORDER BY sira"
    ).fetchall()
    if not satirlar:
        return [dict(satir) for satir in VARSAYILAN_DERS_PROGRAMI]
    return [{"tur": t, "baslama": b, "bitis": bt} for t, b, bt in satirlar]


def ders_programini_kaydet(satirlar):
    conn = veri_deposu.baglanti()
    conn.execute("DELETE FROM ders_programi")
    for i, s in enumerate(satirlar):
        conn.execute(
            "INSERT INTO ders_programi (sira, tur, baslama, bitis) VALUES (?, ?, ?, ?)",
            (i, s["tur"], s["baslama"], s["bitis"]),
        )
    conn.commit()
    veri_deposu.kaydet()


# ---------------------------------------------------------------------------
# CLI giriş noktası
# ---------------------------------------------------------------------------

def _depoyu_cli_icin_ac():
    if veri_deposu.depo_var_mi():
        sifre = getpass.getpass("Yönetici şifresi: ")
        try:
            veri_deposu.kilidi_ac(sifre)
        except veri_deposu.SifreHatasi:
            sys.exit("Şifre yanlış.")
    else:
        print("İlk kurulum - yeni bir yönetici şifresi belirle.")
        sifre = getpass.getpass("Yeni şifre: ")
        tekrar = getpass.getpass("Şifreyi tekrar gir: ")
        if sifre != tekrar:
            sys.exit("Şifreler eşleşmedi.")
        veri_deposu.depo_olustur(sifre)


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
    _depoyu_cli_icin_ac()
    args.fn(args)


if __name__ == "__main__":
    main()
