"""Tahta Kilit - anahtar üretme/doğrulama mantığı (USB + Mobil).

Paylaşılan modül: hem tahtadaki lockscreen.py hem de admin_araci.py bunu kullanır.

Dosyalar (tahtada, /etc/tahtakilit/ altında):
  okul_acik.key   - okulun Ed25519 açık anahtarı (USB anahtarları doğrulamak için)
  mobil_gizli.key - mobil kod üretimi için paylaşılan gizli anahtar (base32)
  tahta_id.txt    - bu tahtanın benzersiz kimliği
  iptal.txt       - iptal edilmiş öğretmen/anahtar listesi (bir satır = bir kayıt)

Admin tarafında (asla tahtaya kopyalanmaz):
  okul_ozel.key   - okulun Ed25519 özel anahtarı

Mobil akışta da (USB'deki gibi) her öğretmen ayrı kimlik taşır: "öğretmen
kodu" + meydan okumaya verilen cevap birleşik olarak girilir, tahta bu
kimliği önceden bir liste tutmadan (master anahtardan türeterek) doğrular.
Bkz. aşağıdaki "Mobil Anahtar" bölümü.
"""
import base64
import hashlib
import hmac
import json
import os
import struct

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

ETC_DIR = "/etc/tahtakilit"
OKUL_ACIK_KEY = os.path.join(ETC_DIR, "okul_acik.key")
MOBIL_GIZLI_KEY = os.path.join(ETC_DIR, "mobil_gizli.key")
TAHTA_ID_FILE = os.path.join(ETC_DIR, "tahta_id.txt")
IPTAL_FILE = os.path.join(ETC_DIR, "iptal.txt")
KULLANIM_LOG_FILE = os.path.join(ETC_DIR, "kullanim.log")

USB_ANAHTAR_DOSYA_ADI = ".tahtakilit_anahtar.json"  # baştaki nokta: Linux'ta gizli dosya


# ---------------------------------------------------------------------------
# Okul ana anahtarı (Ed25519, USB akışı için)
# ---------------------------------------------------------------------------

def okul_anahtari_uret():
    """Yeni bir okul anahtar çifti üretir. (Sadece admin tarafında, bir kere.)"""
    ozel = Ed25519PrivateKey.generate()
    acik = ozel.public_key()
    ozel_b64 = base64.b64encode(
        ozel.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    ).decode()
    acik_b64 = base64.b64encode(
        acik.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode()
    return ozel_b64, acik_b64


def ozel_anahtar_yukle(ozel_b64):
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(ozel_b64))


def acik_anahtar_yukle(acik_b64):
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(acik_b64))


# ---------------------------------------------------------------------------
# USB Anahtar: üretim (admin) ve doğrulama (tahta)
# ---------------------------------------------------------------------------

def _usb_kaydi_uret(ozel_b64, ogretmen_kodu, ogretmen_adi, usb_seri_no):
    """Tek bir okulun imzalı kaydını (dict olarak) üretir."""
    ozel = ozel_anahtar_yukle(ozel_b64)
    mesaj = f"{ogretmen_kodu}|{ogretmen_adi}|{usb_seri_no}".encode()
    imza = ozel.sign(mesaj)
    return {
        "ogretmen_kodu": ogretmen_kodu,
        "ogretmen": ogretmen_adi,
        "seri": usb_seri_no,
        "imza": base64.b64encode(imza).decode(),
    }


def usb_anahtari_olustur(ozel_b64, ogretmen_kodu, ogretmen_adi, usb_seri_no):
    """Tek okulluk basit kullanım (CLI, testler) - tek kayıtlık liste JSON'u döner."""
    kayit = _usb_kaydi_uret(ozel_b64, ogretmen_kodu, ogretmen_adi, usb_seri_no)
    return json.dumps([kayit], ensure_ascii=False, indent=2)


def usb_listesini_oku(dosya_icerigi):
    """Ham USB dosya içeriğini bir kayıt listesine çevirir. Bozuk/boşsa []."""
    if not dosya_icerigi or not dosya_icerigi.strip():
        return []
    try:
        veri = json.loads(dosya_icerigi)
    except json.JSONDecodeError:
        return []
    if isinstance(veri, list):
        return veri
    return [veri]  # tek nesne olarak gelmiş olabilir, tolerans göster


def _kayit_bu_okula_mi_ait(kayit, acik_b64):
    """Bu kaydın imzası, verilen açık anahtarla doğrulanıyor mu?"""
    try:
        ogretmen_kodu = kayit["ogretmen_kodu"]
        ogretmen_adi = kayit["ogretmen"]
        seri = kayit["seri"]
        imza = base64.b64decode(kayit["imza"])
    except (KeyError, ValueError, TypeError):
        return False
    acik = acik_anahtar_yukle(acik_b64)
    mesaj = f"{ogretmen_kodu}|{ogretmen_adi}|{seri}".encode()
    try:
        acik.verify(imza, mesaj)
        return True
    except InvalidSignature:
        return False


def usb_listesine_ekle(mevcut_icerik, ozel_b64, acik_b64, ogretmen_kodu, ogretmen_adi, usb_seri_no):
    """Çoklu okul desteği: USB'de zaten başka okulların kayıtları olabilir.

    Kendi okulumuza ait eski bir kayıt varsa (imza bizim açık anahtarımızla
    doğrulanıyorsa) çıkarılıp yenisiyle değiştirilir; başka okulların
    kayıtlarına hiç dokunulmaz (onların imzasını zaten doğrulayamayız,
    bu da otomatik izolasyon sağlıyor - ayrı bir "okul kodu" gerekmiyor).
    Yazılacak TAM liste içeriğini (JSON) döner.
    """
    liste = usb_listesini_oku(mevcut_icerik)
    kalanlar = [k for k in liste if not _kayit_bu_okula_mi_ait(k, acik_b64)]
    kalanlar.append(_usb_kaydi_uret(ozel_b64, ogretmen_kodu, ogretmen_adi, usb_seri_no))
    return json.dumps(kalanlar, ensure_ascii=False, indent=2)


def _tek_kayit_dogrula(kayit, gercek_usb_seri_no, acik_b64):
    try:
        ogretmen_kodu = kayit["ogretmen_kodu"]
        ogretmen_adi = kayit["ogretmen"]
        dosyadaki_seri = kayit["seri"]
        imza = base64.b64decode(kayit["imza"])
    except (KeyError, ValueError, TypeError):
        return None

    if dosyadaki_seri != gercek_usb_seri_no:
        return None  # dosya başka bir USB'den kopyalanmış

    acik = acik_anahtar_yukle(acik_b64)
    mesaj = f"{ogretmen_kodu}|{ogretmen_adi}|{dosyadaki_seri}".encode()
    try:
        acik.verify(imza, mesaj)
    except InvalidSignature:
        return None

    if _iptal_edilmis_mi(f"{ogretmen_adi}|{dosyadaki_seri}"):
        return None

    return ogretmen_adi


def usb_anahtari_dogrula(dosya_icerigi, gercek_usb_seri_no, acik_b64):
    """Tahta tarafında çağrılır. USB'deki listeyi dolaşıp KENDİ okuluna ait
    (açık anahtarıyla doğrulanan) kaydı arar - başka okulların kayıtlarını
    yok sayar. Geçerliyse öğretmen adını, hiçbiri tutmazsa None döner.
    """
    for kayit in usb_listesini_oku(dosya_icerigi):
        sonuc = _tek_kayit_dogrula(kayit, gercek_usb_seri_no, acik_b64)
        if sonuc:
            return sonuc
    return None


def usb_seri_no_oku(aygit_yolu):
    """/dev/sdX gibi bir aygıt için donanım seri numarasını udev'den okur.

    sysfs'teki /sys/block/*/device/serial USB depolama aygıtlarında genelde
    yok (SCSI/USB-storage bunu expose etmiyor) - seri no udev'in ID_SERIAL_SHORT
    özelliğinde duruyor, bu yüzden udevadm kullanılıyor.
    """
    import subprocess

    try:
        cikti = subprocess.check_output(
            ["udevadm", "info", "--query=property", "--name", aygit_yolu], text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    for satir in cikti.splitlines():
        if satir.startswith("ID_SERIAL_SHORT="):
            return satir.split("=", 1)[1].strip() or None
    return None


# ---------------------------------------------------------------------------
# Mobil Anahtar: meydan okuma - cevap (challenge-response), zamana bağlı değil.
#
# Tahta her "Karekod Oluştur" tıklamasında rastgele bir NONCE üretir (bu bir
# sır değil, tek kullanımlık bir meydan okuma). Öğretmenin telefonu, kendi
# "öğretmen kodu"ndan türettiği kişisel anahtarla bu nonce'a bir cevap
# hesaplar. Tahta, girilen "öğretmen kodu + cevap" birleşiminden öğretmenin
# kişisel anahtarını KENDİSİ yeniden türetip doğrular - önceden bir öğretmen
# listesi tutmasına gerek yok, yeni öğretmen eklemek tahtaya dokunmayı
# gerektirmez.
# ---------------------------------------------------------------------------

OGRETMEN_KODU_UZUNLUK = 4  # 0000-9999, 10.000 kayda kadar (iptal edilenler dahil, kod tekrar kullanılmıyor)
CEVAP_UZUNLUK = 6


def nonce_uret():
    """Tahta tarafında, her karekod oluşturmada çağrılır."""
    return base64.b32encode(os.urandom(10)).decode().rstrip("=")


def _kisa_hmac(anahtar_bytes, mesaj, basamak=CEVAP_UZUNLUK):
    h = hmac.new(anahtar_bytes, mesaj.encode(), hashlib.sha1).digest()
    ofset = h[-1] & 0x0F
    parca = struct.unpack(">I", h[ofset : ofset + 4])[0] & 0x7FFFFFFF
    return str(parca % (10**basamak)).zfill(basamak)


def _ogretmen_anahtari_turet(master_gizli_bytes, ogretmen_kodu):
    return hmac.new(master_gizli_bytes, ogretmen_kodu.encode(), hashlib.sha1).digest()


def mobil_cevap_uret(master_gizli_b32, ogretmen_kodu, nonce):
    """Telefon/web tarafında çağrılır. Ekranda gösterilecek kodu (sadece
    CEVAP_UZUNLUK haneli) döner - öğretmen kodu ayrıca eklenmez, tahta
    girilen kodu doğrularken hangi öğretmen kodunun uyduğunu kendi bulur.
    """
    master_bytes = base64.b32decode(master_gizli_b32 + "=" * (-len(master_gizli_b32) % 8))
    kisisel_anahtar = _ogretmen_anahtari_turet(master_bytes, ogretmen_kodu)
    return _kisa_hmac(kisisel_anahtar, nonce)


def mobil_cevap_dogrula(master_gizli_b32, girilen_deger, nonce):
    """Tahta tarafında çağrılır. Girilen CEVAP_UZUNLUK haneli kodun hangi
    öğretmene ait olduğunu, olası tüm öğretmen kodlarını (000-999, en
    fazla 1000 ihtimal) deneyerek bulur - bu, milisaniyeden kısa sürer.
    Geçerliyse öğretmen kodunu, değilse None döner.
    """
    if len(girilen_deger) != CEVAP_UZUNLUK or not girilen_deger.isdigit():
        return None

    master_bytes = base64.b32decode(master_gizli_b32 + "=" * (-len(master_gizli_b32) % 8))

    for n in range(10**OGRETMEN_KODU_UZUNLUK):
        ogretmen_kodu = str(n).zfill(OGRETMEN_KODU_UZUNLUK)
        kisisel_anahtar = _ogretmen_anahtari_turet(master_bytes, ogretmen_kodu)
        beklenen_cevap = _kisa_hmac(kisisel_anahtar, nonce)
        if hmac.compare_digest(beklenen_cevap, girilen_deger):
            if _iptal_edilmis_mi(ogretmen_kodu):
                return None
            return ogretmen_kodu
    return None


def mobil_gizli_anahtar_uret():
    """Yeni bir okul mobil ana anahtarı üretir (base32, 20 bayt / 160 bit)."""
    return base64.b32encode(os.urandom(20)).decode()


# ---------------------------------------------------------------------------
# İptal listesi
# ---------------------------------------------------------------------------

def _iptal_edilmis_mi(kayit):
    try:
        with open(IPTAL_FILE) as f:
            iptaller = {satir.strip() for satir in f if satir.strip()}
    except FileNotFoundError:
        return False
    return kayit in iptaller


# ---------------------------------------------------------------------------
# Tahtada kayıtlı ayarları okuma yardımcıları
# ---------------------------------------------------------------------------

def kullanim_logla(tahta_id, yontem, kimlik):
    """Kilit açıldığında çağrılır. Ekranda hiç gösterilmeyen kimlik burada
    (sadece diskte) kayıt altına alınır - ileride istatistik istenirse
    bu dosyadan çıkarılabilir.
    """
    import datetime

    satir = f"{datetime.datetime.now().isoformat()} | {tahta_id} | {yontem} | {kimlik}\n"
    try:
        with open(KULLANIM_LOG_FILE, "a") as f:
            f.write(satir)
    except OSError:
        pass  # loglama basarisiz olsa bile kilit acma islemini engellemesin


def dosyadan_oku(yol):
    try:
        with open(yol) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
