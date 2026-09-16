#!/usr/bin/env python3
"""Tahta kilit ekranı - Faz 2: USB Anahtar + Mobil Anahtar ile açılan tam ekran kilit.

PIN yöntemi tamamen kaldırıldı, yerine keyauth.py'deki anahtar sistemi geldi.
"""
import glob
import os
import uuid

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

import keyauth

USB_TARAMA_ARALIGI_MS = 2000
YANLIS_DENEME_LIMITI = 3
KILITLENME_SANIYE = 15

USB_TAKILI_DIZINLER = [
    "/media/*/*",
    "/run/media/*/*",
]


def tahta_id_al():
    tid = keyauth.dosyadan_oku(keyauth.TAHTA_ID_FILE)
    if tid:
        return tid
    tid = uuid.uuid4().hex[:8]
    try:
        os.makedirs(keyauth.ETC_DIR, exist_ok=True)
        with open(keyauth.TAHTA_ID_FILE, "w") as f:
            f.write(tid)
    except PermissionError:
        pass  # kurulum tamamlanmadan test edilirse sorun çıkarmasın
    return tid


def qr_pixbuf_uret(metin, boyut=220):
    try:
        import qrcode
    except ImportError:
        return None
    img = qrcode.make(metin)
    yol = "/tmp/tahtakilit_qr.png"
    img.save(yol)
    return GdkPixbuf.Pixbuf.new_from_file_at_size(yol, boyut, boyut)


def takili_usb_dosyalarini_bul():
    bulunan = []
    for desen in USB_TAKILI_DIZINLER:
        for kok in glob.glob(desen):
            aday = os.path.join(kok, keyauth.USB_ANAHTAR_DOSYA_ADI)
            if os.path.isfile(aday):
                bulunan.append((kok, aday))
    return bulunan


def usb_aygit_yolunu_tahmin_et(mount_noktasi):
    try:
        import subprocess

        cikti = subprocess.check_output(
            ["findmnt", "-n", "-o", "SOURCE", mount_noktasi], text=True
        ).strip()
        return cikti
    except Exception:
        return None


class KilitPenceresi(Gtk.Window):
    def __init__(self):
        super().__init__(title="Tahta Kilitli")
        self.set_decorated(False)
        self.fullscreen()
        self.set_keep_above(True)
        self.stick()
        self.connect("delete-event", lambda *_: True)

        self.tahta_id = tahta_id_al()
        self.nonce = None
        self.yanlis_sayisi = 0
        self.kilitli_mi = False

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_halign(Gtk.Align.CENTER)
        self.add(vbox)

        baslik = Gtk.Label()
        baslik.set_markup('<span font="28" foreground="white">Tahta Kilitli</span>')
        vbox.pack_start(baslik, False, False, 0)

        self.qr_resim = Gtk.Image()
        vbox.pack_start(self.qr_resim, False, False, 0)

        self.qr_butonu = Gtk.Button(label="Karekod Oluştur")
        self.qr_butonu.connect("clicked", self.on_karekod_olustur)
        vbox.pack_start(self.qr_butonu, False, False, 0)

        alt_yazi = Gtk.Label()
        alt_yazi.set_markup(
            '<span font="13" foreground="#cccccc">'
            "Mobil Anahtar uygulamasıyla karekodu tarayın,\n"
            "gelen kodu aşağıya girin — ya da USB Anahtarınızı takın."
            "</span>"
        )
        alt_yazi.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(alt_yazi, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_max_length(keyauth.OGRETMEN_KODU_UZUNLUK + keyauth.CEVAP_UZUNLUK)
        self.entry.set_width_chars(12)
        self.entry.set_alignment(0.5)
        self.entry.connect("activate", self.on_kod_dene)
        vbox.pack_start(self.entry, False, False, 0)

        self.durum = Gtk.Label()
        vbox.pack_start(self.durum, False, False, 0)

        buton = Gtk.Button(label="Aç")
        buton.connect("clicked", self.on_kod_dene)
        vbox.pack_start(buton, False, False, 0)

        self.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.05, 0.05, 0.08, 1)
        )

    def on_karekod_olustur(self, *_):
        # Her tıklamada yeni bir nonce - öncekini geçersiz kılar.
        self.nonce = keyauth.nonce_uret()
        pixbuf = qr_pixbuf_uret(f"{self.tahta_id}:{self.nonce}")
        if pixbuf:
            self.qr_resim.set_from_pixbuf(pixbuf)
        else:
            self._durum_yaz("qrcode kütüphanesi kurulu değil", renk="#ffb020")

    def _durum_yaz(self, metin, renk="#ff6b6b"):
        self.durum.set_markup(f'<span foreground="{renk}">{metin}</span>')

    # -- Mobil Anahtar (kod girişi) -----------------------------------

    def on_kod_dene(self, *_):
        if self.kilitli_mi:
            return

        kod = self.entry.get_text().strip()
        self.entry.set_text("")

        gizli = keyauth.dosyadan_oku(keyauth.MOBIL_GIZLI_KEY)
        if not gizli:
            self._durum_yaz("Mobil anahtar henüz kurulmamış")
            return

        if not self.nonce:
            self._durum_yaz("Önce Karekod Oluştur'a basın")
            return

        if keyauth.mobil_cevap_dogrula(gizli, kod, self.nonce):
            self._ac()
            return

        self.yanlis_sayisi += 1
        if self.yanlis_sayisi >= YANLIS_DENEME_LIMITI:
            self._gecici_kilitle()
        else:
            self._durum_yaz("Hatalı kod")

    def _gecici_kilitle(self):
        self.kilitli_mi = True
        self.entry.set_sensitive(False)
        kalan = [KILITLENME_SANIYE]

        def geri_sayim():
            kalan[0] -= 1
            if kalan[0] <= 0:
                self.kilitli_mi = False
                self.yanlis_sayisi = 0
                self.entry.set_sensitive(True)
                self._durum_yaz("")
                return False
            self._durum_yaz(f"Çok fazla hatalı deneme — {kalan[0]} sn bekleyin")
            return True

        self._durum_yaz(f"Çok fazla hatalı deneme — {KILITLENME_SANIYE} sn bekleyin")
        GLib.timeout_add(1000, geri_sayim)

    # -- USB Anahtar (periyodik tarama) --------------------------------

    def usb_tara(self):
        acik = keyauth.dosyadan_oku(keyauth.OKUL_ACIK_KEY)
        if acik:
            for mount_noktasi, dosya_yolu in takili_usb_dosyalarini_bul():
                aygit = usb_aygit_yolunu_tahmin_et(mount_noktasi)
                gercek_seri = keyauth.usb_seri_no_oku(aygit) if aygit else None
                if not gercek_seri:
                    continue
                try:
                    with open(dosya_yolu) as f:
                        icerik = f.read()
                except OSError:
                    continue
                ogretmen = keyauth.usb_anahtari_dogrula(icerik, gercek_seri, acik)
                if ogretmen:
                    self._ac()
                    return False
        return True  # taramaya devam et

    def _ac(self):
        self.grab_kaldir()
        self.destroy()
        Gtk.main_quit()

    def grab_al(self):
        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        seat.grab(self.get_window(), Gdk.SeatCapabilities.ALL, True)

    def grab_kaldir(self):
        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        seat.ungrab()


def main():
    win = KilitPenceresi()
    win.show_all()
    win.entry.grab_focus()
    GLib.timeout_add(300, lambda: (win.grab_al(), False)[1])
    GLib.timeout_add(USB_TARAMA_ARALIGI_MS, win.usb_tara)
    Gtk.main()


if __name__ == "__main__":
    main()
