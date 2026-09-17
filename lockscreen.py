#!/usr/bin/env python3
"""Tahta kilit ekranı - Faz 2: USB Anahtar + Mobil Anahtar ile açılan tam ekran kilit.

PIN yöntemi tamamen kaldırıldı, yerine keyauth.py'deki anahtar sistemi geldi.

Mobil kod girişi fiziksel klavye ile YAPILMIYOR - ekrandaki dokunmatik tuş
takımıyla giriliyor. Sebep: Gdk.Seat.grab() klavye olaylarının başka
uygulamalara kaçmasını engeller ama fiziksel klavyeye takılan donanım bir
keylogger'ı hiçbir yazılımsal önlem durduramaz (USB üzerinden, işletim
sistemine ulaşmadan önce tuşları kaydeder). Dokunmatik giriş bu riski
tamamen ortadan kaldırıyor.
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
KAREKOD_ZAMAN_ASIMI_SANIYE = 45  # oluşturulup kullanılmazsa karekod/tuş takımı kaybolur

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
        self.girilen_kod = ""
        self.yanlis_sayisi = 0
        self.kilitli_mi = False
        self.zaman_asimi_id = None

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
            "gelen kodu aşağıdaki tuş takımıyla girin — ya da USB Anahtarınızı takın."
            "</span>"
        )
        alt_yazi.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(alt_yazi, False, False, 0)

        self.kod_goster = Gtk.Label()
        self.kod_goster.set_markup('<span font="24" foreground="white">      </span>')
        vbox.pack_start(self.kod_goster, False, False, 0)

        self.tus_takimi = self._tus_takimi_olustur()
        vbox.pack_start(self.tus_takimi, False, False, 0)

        self.durum = Gtk.Label()
        vbox.pack_start(self.durum, False, False, 0)

        self.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.05, 0.05, 0.08, 1)
        )

        self.qr_resim.hide()
        self.tus_takimi.hide()

    def _tus_takimi_olustur(self):
        izgara = Gtk.Grid(row_spacing=8, column_spacing=8)
        izgara.set_halign(Gtk.Align.CENTER)
        duzen = [("1", 0, 0), ("2", 1, 0), ("3", 2, 0),
                 ("4", 0, 1), ("5", 1, 1), ("6", 2, 1),
                 ("7", 0, 2), ("8", 1, 2), ("9", 2, 2),
                 ("Sil", 0, 3), ("0", 1, 3)]
        for etiket, sutun, satir in duzen:
            buton = Gtk.Button(label=etiket)
            buton.set_size_request(64, 56)
            if etiket == "Sil":
                buton.connect("clicked", self.on_tus_sil)
            else:
                buton.connect("clicked", self.on_tus_basildi, etiket)
            izgara.attach(buton, sutun, satir, 1, 1)
        return izgara

    def on_karekod_olustur(self, *_):
        # Her tıklamada yeni bir nonce - öncekini geçersiz kılar.
        self.nonce = keyauth.nonce_uret()
        self.girilen_kod = ""
        self._kod_gosterimini_guncelle()

        pixbuf = qr_pixbuf_uret(f"{self.tahta_id}:{self.nonce}")
        if pixbuf:
            self.qr_resim.set_from_pixbuf(pixbuf)
            self.qr_resim.show()
        else:
            self._durum_yaz("qrcode kütüphanesi kurulu değil", renk="#ffb020")
        self.tus_takimi.show()

        if self.zaman_asimi_id:
            GLib.source_remove(self.zaman_asimi_id)
        self.zaman_asimi_id = GLib.timeout_add_seconds(
            KAREKOD_ZAMAN_ASIMI_SANIYE, self._zaman_asimi
        )

    def _zaman_asimi(self):
        self.nonce = None
        self.girilen_kod = ""
        self._kod_gosterimini_guncelle()
        self.qr_resim.hide()
        self.tus_takimi.hide()
        self.zaman_asimi_id = None
        self._durum_yaz("")
        return False

    def _durum_yaz(self, metin, renk="#ff6b6b"):
        self.durum.set_markup(f'<span foreground="{renk}">{metin}</span>')

    def _kod_gosterimini_guncelle(self):
        gosterim = self.girilen_kod.ljust(keyauth.CEVAP_UZUNLUK, "_")
        self.kod_goster.set_markup(f'<span font="24" foreground="white">{gosterim}</span>')

    # -- Mobil Anahtar (dokunmatik tuş takımı) --------------------------

    def on_tus_basildi(self, _buton, rakam):
        if self.kilitli_mi or not self.nonce:
            return
        if len(self.girilen_kod) >= keyauth.CEVAP_UZUNLUK:
            return
        self.girilen_kod += rakam
        self._kod_gosterimini_guncelle()
        if len(self.girilen_kod) == keyauth.CEVAP_UZUNLUK:
            self._kod_dene()

    def on_tus_sil(self, *_):
        if self.kilitli_mi:
            return
        self.girilen_kod = self.girilen_kod[:-1]
        self._kod_gosterimini_guncelle()

    def _kod_dene(self):
        kod = self.girilen_kod
        self.girilen_kod = ""
        self._kod_gosterimini_guncelle()

        gizli = keyauth.dosyadan_oku(keyauth.MOBIL_GIZLI_KEY)
        if not gizli:
            self._durum_yaz("Mobil anahtar henüz kurulmamış")
            return

        ogretmen_kodu = keyauth.mobil_cevap_dogrula(gizli, kod, self.nonce)
        if ogretmen_kodu:
            if self.zaman_asimi_id:
                GLib.source_remove(self.zaman_asimi_id)
            self._ac("mobil", ogretmen_kodu)
            return

        self.yanlis_sayisi += 1
        if self.yanlis_sayisi >= YANLIS_DENEME_LIMITI:
            self._gecici_kilitle()
        else:
            self._durum_yaz("Hatalı kod")

    def _gecici_kilitle(self):
        self.kilitli_mi = True
        self.tus_takimi.set_sensitive(False)
        kalan = [KILITLENME_SANIYE]

        def geri_sayim():
            kalan[0] -= 1
            if kalan[0] <= 0:
                self.kilitli_mi = False
                self.yanlis_sayisi = 0
                self.tus_takimi.set_sensitive(True)
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
                    self._ac("usb", ogretmen)
                    return False
        return True  # taramaya devam et

    def _ac(self, yontem, kimlik):
        keyauth.kullanim_logla(self.tahta_id, yontem, kimlik)
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
    win.qr_resim.hide()
    win.tus_takimi.hide()
    GLib.timeout_add(300, lambda: (win.grab_al(), False)[1])
    GLib.timeout_add(USB_TARAMA_ARALIGI_MS, win.usb_tara)
    Gtk.main()


if __name__ == "__main__":
    main()
