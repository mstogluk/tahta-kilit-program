#!/usr/bin/env python3
"""Tahta kilit ekranı - Faz 1: tek paylaşılan PIN ile açılan tam ekran kilit.

ponytail: PIN düz metin dosyada tutuluyor (/etc/tahtakilit/pin.txt).
Öğretmen bazlı PIN/karekod gerekirse ileride buraya eklenir.
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

PIN_FILE = "/etc/tahtakilit/pin.txt"
DEFAULT_PIN = "159357"


def read_pin():
    try:
        with open(PIN_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return DEFAULT_PIN


class KilitPenceresi(Gtk.Window):
    def __init__(self):
        super().__init__(title="Tahta Kilitli")
        self.set_decorated(False)
        self.fullscreen()
        self.set_keep_above(True)
        self.stick()
        self.connect("delete-event", lambda *_: True)  # kapatma butonu yok say

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_halign(Gtk.Align.CENTER)
        self.add(vbox)

        baslik = Gtk.Label(label="Tahta Kilitli")
        baslik.set_markup('<span font="28" foreground="white">Tahta Kilitli</span>')
        vbox.pack_start(baslik, False, False, 0)

        alt_yazi = Gtk.Label(label="Açmak için öğretmen PIN'ini girin")
        alt_yazi.set_markup('<span font="14" foreground="#cccccc">Açmak için öğretmen PIN\'ini girin</span>')
        vbox.pack_start(alt_yazi, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.entry.set_width_chars(12)
        self.entry.set_alignment(0.5)
        self.entry.connect("activate", self.on_dene)
        vbox.pack_start(self.entry, False, False, 0)

        self.hata = Gtk.Label(label="")
        self.hata.set_markup('<span foreground="#ff6b6b"></span>')
        vbox.pack_start(self.hata, False, False, 0)

        buton = Gtk.Button(label="Aç")
        buton.connect("clicked", self.on_dene)
        vbox.pack_start(buton, False, False, 0)

        self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.05, 0.05, 0.08, 1))

    def on_dene(self, *_):
        if self.entry.get_text() == read_pin():
            self.grab_kaldir()
            self.destroy()
            Gtk.main_quit()
        else:
            self.hata.set_markup('<span foreground="#ff6b6b">Hatalı PIN</span>')
            self.entry.set_text("")

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
    Gtk.main()


if __name__ == "__main__":
    main()
