"""Admin'in yerel, hassas verilerini (özel anahtar, öğretmen listesi, okul
bilgileri, ders programı) tek bir ŞİFRELİ SQLite veritabanında tutar.

Nasıl çalışır:
  - Veritabanının tamamı bellekte (`sqlite3`'ün `:memory:` özelliğiyle) çalışır,
    diskte HİÇBİR ZAMAN düz/şifresiz haliyle bulunmaz.
  - Diskteki tek dosya (admin-gizli/veri.enc): 16 baytlık tuz + Fernet ile
    şifrelenmiş veritabanı baytları. Yönetici şifresinden PBKDF2 ile türetilen
    anahtarla şifreleniyor.
  - `kilidi_ac(sifre)` / `depo_olustur(sifre)` çağrılmadan hiçbir okuma/yazma
    fonksiyonu çalışmaz.

Bu tasarım tercih edildi çünkü SQLCipher (gerçek şifreli SQLite) bu ortama
kurulamadı (C derleyicisi gerektiriyor) - burada ekstra bağımlılık olmadan
(sadece stdlib sqlite3 + zaten kullanılan cryptography) aynı sonuca
(veri diskte asla düz metin olarak bulunmaz) ulaşılıyor.
"""
import base64
import os
import sqlite3

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

GIZLI_DIZIN = "admin-gizli"
VERI_DOSYASI = os.path.join(GIZLI_DIZIN, "veri.enc")

_TUZ_UZUNLUK = 16
_PBKDF2_ITERASYON = 480_000

_baglanti = None
_anahtar = None
_tuz = None


class SifreHatasi(Exception):
    """Yanlış şifre girildiğinde fırlatılır."""


def depo_var_mi():
    return os.path.exists(VERI_DOSYASI)


def acik_mi():
    return _baglanti is not None


def _anahtar_turet(sifre, tuz):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=tuz, iterations=_PBKDF2_ITERASYON)
    return base64.urlsafe_b64encode(kdf.derive(sifre.encode("utf-8")))


def _semayi_olustur(conn):
    conn.execute("CREATE TABLE ayarlar (anahtar TEXT PRIMARY KEY, deger TEXT)")
    conn.execute("CREATE TABLE ogretmenler (kod TEXT PRIMARY KEY, ad TEXT)")
    conn.execute("CREATE TABLE ders_programi (sira INTEGER PRIMARY KEY, tur TEXT, baslama TEXT, bitis TEXT)")
    conn.commit()


def depo_olustur(sifre):
    """İlk kurulum: yeni, boş, şifreli bir depo oluşturur."""
    global _baglanti, _anahtar, _tuz
    os.makedirs(GIZLI_DIZIN, exist_ok=True)
    _tuz = os.urandom(_TUZ_UZUNLUK)
    _anahtar = _anahtar_turet(sifre, _tuz)
    _baglanti = sqlite3.connect(":memory:", check_same_thread=False)
    _semayi_olustur(_baglanti)
    kaydet()


def kilidi_ac(sifre):
    """Var olan şifreli depoyu açar. Şifre yanlışsa SifreHatasi fırlatır."""
    global _baglanti, _anahtar, _tuz
    with open(VERI_DOSYASI, "rb") as f:
        icerik = f.read()
    tuz, sifreli = icerik[:_TUZ_UZUNLUK], icerik[_TUZ_UZUNLUK:]
    anahtar = _anahtar_turet(sifre, tuz)
    try:
        cozulmus = Fernet(anahtar).decrypt(sifreli)
    except InvalidToken:
        raise SifreHatasi("Şifre yanlış.")

    baglanti = sqlite3.connect(":memory:", check_same_thread=False)
    baglanti.deserialize(cozulmus)
    _baglanti, _anahtar, _tuz = baglanti, anahtar, tuz


def kaydet():
    """Bellekteki veritabanını şifreleyip diske yazar. Her değişiklikten sonra çağrılır."""
    if _baglanti is None:
        return
    veri = _baglanti.serialize()
    sifreli = Fernet(_anahtar).encrypt(veri)
    with open(VERI_DOSYASI, "wb") as f:
        f.write(_tuz + sifreli)


def baglanti():
    if _baglanti is None:
        raise RuntimeError("Depo henüz açılmadı - önce kilidi_ac()/depo_olustur() çağrılmalı.")
    return _baglanti
