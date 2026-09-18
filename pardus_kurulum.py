#!/usr/bin/env python3
"""ANKA - Pardus Tahta Kurulum Sihirbazı.

Bu dosya, ANKA'nın "Kurulum Paketi Oluştur" özelliğiyle üretilen klasörün
içinde gelir. Yanındaki `payload.enc` dosyası, tahta kodunu (lockscreen.py,
keyauth.py, run.sh) VE okulun anahtarlarını (okul_acik.key, mobil_gizli.key)
şifreli taşır - USB'ye göz atan biri düz .py kaynak kodu ya da anahtar
dosyası GÖRMEZ, sadece anlamsız bir `payload.enc` görür.

Bu betiğin kendisi (bootstrapper) hiçbir okul-özel sır içermiyor, sadece
kurulum mantığını içeriyor - o yüzden açıkta durması sorun değil. Şifre
kullanıcıdan sorulmuyor; paket her zaman ANKA tarafından üretildiği için
çözme anahtarı burada sabit olarak gömülü. Bu USB yanlışlıkla başka bir
bilgisayara ya da başka bir okulun tahtasına takılırsa zaten içindeki
okul anahtarları o tahtanınkiyle eşleşmeyeceğinden hiçbir şey açılmaz.

Terminal'e hiç yazı yazılmıyor - tüm etkileşim bu grafik pencerede.
Yetki gereken adımlar için `pkexec` kullanılıyor (grafiksel şifre penceresi,
Windows'taki UAC'ın karşılığı).
"""
import json
import os
import shutil
import subprocess
import tempfile

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

KENDI_DIZINI = os.path.dirname(os.path.abspath(__file__))
PAKET_DOSYASI = os.path.join(KENDI_DIZINI, "payload.enc")

# ANKA'nın "Kurulum Paketi Oluştur" adımıyla ortak, sabit paket anahtarı.
# Okula özel bir sır DEĞİL - sadece bu betiğin kendi payload.enc'yi
# çözebilmesi için var; USB'de düz kod/anahtar görünmesini engeller.
PAKET_ANAHTARI = b"OXHKnzcHcNhA-CWC9a9lYE9gRiDwoWEgVYKCb7F5eng="

RENK_ARKA_PLAN = Gdk.RGBA(0.09, 0.09, 0.11, 1)


def _bagimliliklari_kur():
    """Tahta kodunun ihtiyaç duyduğu paketler kurulu değilse (ilk kurulumda
    büyük ihtimalle kurulu değil) pkexec ile kurar."""
    try:
        import cryptography  # noqa: F401
        return True, None
    except ImportError:
        pass
    sonuc = subprocess.run(
        ["pkexec", "bash", "-c", "apt update && apt install -y python3-gi gir1.2-gtk-3.0 python3-cryptography python3-qrcode"]
    )
    if sonuc.returncode != 0:
        return False, "Gerekli paketler kurulamadı (şifre iptal edildi ya da bir hata oluştu)."
    return True, None


def _paketi_coz():
    """(basarili, sonuc) döner - basarili ise sonuc dosya-adı->içerik dict'i,
    değilse sonuc hata mesajı."""
    from cryptography.fernet import Fernet, InvalidToken

    if not os.path.exists(PAKET_DOSYASI):
        return False, f"'payload.enc' bulunamadı: {PAKET_DOSYASI}"

    with open(PAKET_DOSYASI, "rb") as f:
        sifreli = f.read()
    try:
        cozulmus = Fernet(PAKET_ANAHTARI).decrypt(sifreli)
    except InvalidToken:
        return False, "Paket bozuk ya da uyumsuz (payload.enc çözülemedi)."
    try:
        return True, json.loads(cozulmus)
    except json.JSONDecodeError:
        return False, "Paket bozuk görünüyor."


def _yardimci_betik_uret(gecici_dizin):
    """pkexec ile TEK seferde çalıştırılacak, tüm ayrıcalıklı adımları
    içeren betiği üretir. gecici_dizin: çözülmüş dosyaların YEREL DİSKTE
    (USB'de değil) geçici olarak durduğu yer - buradan gerçek yerlerine
    kopyalanıp temizleniyor.

    Autostart /etc/xdg/autostart/ altına (SİSTEM GENELİ) kuruluyor - hangi
    kullanıcı oturum açarsa açsın devreye giriyor.
    """
    satirlar = [
        "set -e",
        "mkdir -p /opt/tahtakilit /etc/tahtakilit /etc/xdg/autostart",
        f'cp "{gecici_dizin}/lockscreen.py" "{gecici_dizin}/keyauth.py" "{gecici_dizin}/run.sh" /opt/tahtakilit/',
        "chmod +x /opt/tahtakilit/lockscreen.py /opt/tahtakilit/run.sh",
        f'cp "{gecici_dizin}/sinif_adi.txt" /etc/tahtakilit/sinif_adi.txt',
    ]
    for dosya in ("okul_acik.key", "mobil_gizli.key", "iptal.txt"):
        satirlar.append(
            f'[ -f "{gecici_dizin}/{dosya}" ] && cp "{gecici_dizin}/{dosya}" "/etc/tahtakilit/{dosya}" || true'
        )
    satirlar += [
        "cat > /etc/xdg/autostart/tahtakilit.desktop <<EOF",
        "[Desktop Entry]",
        "Type=Application",
        "Name=Tahta Kilit",
        "Exec=/opt/tahtakilit/run.sh",
        "X-GNOME-Autostart-enabled=true",
        "EOF",
        f'rm -rf "{gecici_dizin}"',
    ]
    return "\n".join(satirlar) + "\n"


class KurulumPenceresi(Gtk.Window):
    def __init__(self):
        super().__init__(title="ANKA Tahta Kurulumu")
        self.set_default_size(420, 260)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.override_background_color(Gtk.StateFlags.NORMAL, RENK_ARKA_PLAN)

        disi = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        disi.set_border_width(24)
        self.add(disi)

        baslik = Gtk.Label()
        baslik.set_markup('<span font="18" foreground="white" weight="bold">ANKA Tahta Kurulumu</span>')
        disi.pack_start(baslik, False, False, 0)

        self._etiket_ekle(disi, "Sınıf ismi:")
        self.sinif_giris = Gtk.Entry()
        self.sinif_giris.set_placeholder_text("örn. 5-A Sınıfı")
        disi.pack_start(self.sinif_giris, False, False, 0)

        self.kur_btn = Gtk.Button(label="Kur")
        self.kur_btn.connect("clicked", self.on_kur)
        disi.pack_start(self.kur_btn, False, False, 8)

        self.durum = Gtk.Label(label="")
        self.durum.set_line_wrap(True)
        disi.pack_start(self.durum, False, False, 0)

        self.kilitle_btn = Gtk.Button(label="Tahtayı Şimdi Kilitle")
        self.kilitle_btn.connect("clicked", self.on_kilitle)
        disi.pack_start(self.kilitle_btn, False, False, 0)
        self.kilitle_btn.hide()

        self.connect("destroy", Gtk.main_quit)

    def _etiket_ekle(self, kap, metin):
        etiket = Gtk.Label(label=metin, xalign=0)
        etiket.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.8, 0.8, 0.85, 1))
        kap.pack_start(etiket, False, False, 0)

    def _durum_yaz(self, metin, hata=False):
        renk = "#ff6b6b" if hata else "#4ade80"
        self.durum.set_markup(f'<span foreground="{renk}">{GLib.markup_escape_text(metin)}</span>')
        while Gtk.events_pending():
            Gtk.main_iteration()

    def on_kur(self, *_):
        sinif_adi = self.sinif_giris.get_text().strip()
        if not sinif_adi:
            self._durum_yaz("Sınıf ismi boş olamaz.", hata=True)
            return

        self._durum_yaz("Paket çözülüyor...")
        basarili, sonuc = _paketi_coz()
        if not basarili:
            self._durum_yaz(sonuc, hata=True)
            return
        dosyalar = sonuc

        self._durum_yaz("Gerekli paketler kontrol ediliyor (gerekirse şifre istenecek)...")
        basarili, hata = _bagimliliklari_kur()
        if not basarili:
            self._durum_yaz(hata, hata=True)
            return

        gecici_dizin = tempfile.mkdtemp(prefix="tahtakilit_kurulum_")
        try:
            for ad, icerik in dosyalar.items():
                with open(os.path.join(gecici_dizin, ad), "w", encoding="utf-8") as f:
                    f.write(icerik)
            with open(os.path.join(gecici_dizin, "sinif_adi.txt"), "w", encoding="utf-8") as f:
                f.write(sinif_adi)
        except OSError as e:
            self._durum_yaz(f"Geçici dosyalar yazılamadı: {e}", hata=True)
            shutil.rmtree(gecici_dizin, ignore_errors=True)
            return

        betik = _yardimci_betik_uret(gecici_dizin)
        yardimci_yol = "/tmp/tahtakilit_kurulum_yardimci.sh"
        with open(yardimci_yol, "w") as f:
            f.write(betik)

        self._durum_yaz("Yönetici şifresi istenecek (grafiksel pencere)...")
        sonuc_pkexec = subprocess.run(["pkexec", "bash", yardimci_yol])

        try:
            os.remove(yardimci_yol)
        except OSError:
            pass
        shutil.rmtree(gecici_dizin, ignore_errors=True)

        if sonuc_pkexec.returncode != 0:
            self._durum_yaz("Kurulum başarısız oldu ya da iptal edildi.", hata=True)
            return

        self._durum_yaz(f"Kurulum tamamlandı — '{sinif_adi}' için hazır.")
        self.sinif_giris.set_sensitive(False)
        self.kur_btn.set_sensitive(False)
        self.kilitle_btn.show()

    def on_kilitle(self, *_):
        subprocess.Popen(["bash", "/opt/tahtakilit/run.sh"])
        self.destroy()


def main():
    win = KurulumPenceresi()
    win.show_all()
    win.kilitle_btn.hide()
    Gtk.main()


if __name__ == "__main__":
    main()
