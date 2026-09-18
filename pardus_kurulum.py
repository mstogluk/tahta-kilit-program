#!/usr/bin/env python3
"""ANKA - Pardus Tahta Kurulum Sihirbazı.

Bu dosya, ANKA'nın "Kurulum Paketi Oluştur" özelliğiyle üretilen klasörün
içinde gelir. Klasördeki `dosyalar/` alt klasöründe tahta kodu (lockscreen.py,
keyauth.py, run.sh) ve okulun anahtarları (okul_acik.key, mobil_gizli.key)
hazır bulunur - bu pencere onları /opt/tahtakilit ve /etc/tahtakilit'e
kopyalar, sınıf ismini sorar, gerekirse otomatik giriş kurulumunu yapar.

Terminal'e hiç yazı yazılmıyor - tüm etkileşim bu grafik pencerede.
Yetki gereken adımlar için `pkexec` kullanılıyor (grafiksel şifre penceresi,
Windows'taki UAC'ın karşılığı).
"""
import os
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

KENDI_DIZINI = os.path.dirname(os.path.abspath(__file__))
DOSYALAR_DIZINI = os.path.join(KENDI_DIZINI, "dosyalar")

RENK_ARKA_PLAN = Gdk.RGBA(0.09, 0.09, 0.11, 1)
RENK_VURGU = "#4a7fff"


def _yardimci_betik_uret():
    """pkexec ile TEK seferde çalıştırılacak, tüm ayrıcalıklı adımları
    içeren betiği üretir. Sınıf ismi buraya GÖMÜLMEZ (kullanıcı metni) -
    ayrı bir dosyadan kopyalanır, shell injection riski olmasın diye.

    Autostart /etc/xdg/autostart/ altına (SİSTEM GENELİ) kuruluyor - belirli
    bir kullanıcıya bağlı değil, o tahtada kim oturum açarsa açsın devreye
    giriyor. Tek bir kullanıcı adı sormaya hiç gerek yok.
    """
    kaynak = DOSYALAR_DIZINI
    satirlar = [
        "set -e",
        "mkdir -p /opt/tahtakilit /etc/tahtakilit /etc/xdg/autostart",
        f'cp "{kaynak}/lockscreen.py" "{kaynak}/keyauth.py" "{kaynak}/run.sh" /opt/tahtakilit/',
        "chmod +x /opt/tahtakilit/lockscreen.py /opt/tahtakilit/run.sh",
        "cp /tmp/tahtakilit_sinif_adi.txt /etc/tahtakilit/sinif_adi.txt",
        "rm -f /tmp/tahtakilit_sinif_adi.txt",
    ]
    for dosya in ("okul_acik.key", "mobil_gizli.key", "iptal.txt"):
        kaynak_dosya = os.path.join(kaynak, dosya)
        if os.path.exists(kaynak_dosya):
            satirlar.append(f'cp "{kaynak_dosya}" "/etc/tahtakilit/{dosya}"')

    satirlar += [
        "cat > /etc/xdg/autostart/tahtakilit.desktop <<EOF",
        "[Desktop Entry]",
        "Type=Application",
        "Name=Tahta Kilit",
        "Exec=/opt/tahtakilit/run.sh",
        "X-GNOME-Autostart-enabled=true",
        "EOF",
    ]
    return "\n".join(satirlar) + "\n"


class KurulumPenceresi(Gtk.Window):
    def __init__(self):
        super().__init__(title="ANKA Tahta Kurulumu")
        self.set_default_size(420, 320)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.override_background_color(Gtk.StateFlags.NORMAL, RENK_ARKA_PLAN)

        disi = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        disi.set_border_width(24)
        self.add(disi)

        baslik = Gtk.Label()
        baslik.set_markup('<span font="18" foreground="white" weight="bold">ANKA Tahta Kurulumu</span>')
        disi.pack_start(baslik, False, False, 0)

        self.kurulum_kutusu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        disi.pack_start(self.kurulum_kutusu, False, False, 0)

        etiket1 = Gtk.Label(label="Sınıf ismi:", xalign=0)
        etiket1.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.8, 0.8, 0.85, 1))
        self.kurulum_kutusu.pack_start(etiket1, False, False, 0)
        self.sinif_giris = Gtk.Entry()
        self.sinif_giris.set_placeholder_text("örn. 5-A Sınıfı")
        self.kurulum_kutusu.pack_start(self.sinif_giris, False, False, 0)

        self.kur_btn = Gtk.Button(label="Kur")
        self.kur_btn.connect("clicked", self.on_kur)
        self.kurulum_kutusu.pack_start(self.kur_btn, False, False, 8)

        self.durum = Gtk.Label(label="")
        self.durum.set_line_wrap(True)
        disi.pack_start(self.durum, False, False, 0)

        # Kurulum bitince gösterilecek buton (başta gizli)
        self.kilitle_btn = Gtk.Button(label="Tahtayı Şimdi Kilitle")
        self.kilitle_btn.connect("clicked", self.on_kilitle)
        disi.pack_start(self.kilitle_btn, False, False, 0)
        self.kilitle_btn.hide()

        self.connect("destroy", Gtk.main_quit)

    def _durum_yaz(self, metin, hata=False):
        renk = "#ff6b6b" if hata else "#4ade80"
        self.durum.set_markup(f'<span foreground="{renk}">{GLib.markup_escape_text(metin)}</span>')

    def on_kur(self, *_):
        sinif_adi = self.sinif_giris.get_text().strip()

        if not sinif_adi:
            self._durum_yaz("Sınıf ismi boş olamaz.", hata=True)
            return
        if not os.path.isdir(DOSYALAR_DIZINI):
            self._durum_yaz(f"'dosyalar' klasörü bulunamadı: {DOSYALAR_DIZINI}", hata=True)
            return

        try:
            with open("/tmp/tahtakilit_sinif_adi.txt", "w") as f:
                f.write(sinif_adi)
        except OSError as e:
            self._durum_yaz(f"Geçici dosya yazılamadı: {e}", hata=True)
            return

        betik = _yardimci_betik_uret()
        yardimci_yol = "/tmp/tahtakilit_kurulum_yardimci.sh"
        with open(yardimci_yol, "w") as f:
            f.write(betik)

        self._durum_yaz("Yönetici şifresi istenecek (grafiksel pencere)...")
        while Gtk.events_pending():
            Gtk.main_iteration()

        sonuc = subprocess.run(["pkexec", "bash", yardimci_yol])

        try:
            os.remove(yardimci_yol)
        except OSError:
            pass

        if sonuc.returncode != 0:
            self._durum_yaz("Kurulum başarısız oldu ya da iptal edildi.", hata=True)
            return

        self._durum_yaz(
            f"Kurulum tamamlandı — '{sinif_adi}' için hazır.\n"
            "Test etmeden önce USB belleği çıkarmayı unutma - takılıyken "
            "tahta onu görüp anında kendini açabilir."
        )
        self.kurulum_kutusu.set_sensitive(False)
        self.kilitle_btn.show()

    def on_kilitle(self, *_):
        subprocess.Popen(["bash", "/opt/tahtakilit/run.sh"])
        self._durum_yaz(
            "Tahta kilitlendi (bu pencere açık kalıyor, istersen tekrar "
            "'Tahtayı Şimdi Kilitle'ye basabilirsin)."
        )


def main():
    win = KurulumPenceresi()
    win.show_all()
    win.kilitle_btn.hide()
    Gtk.main()


if __name__ == "__main__":
    main()
