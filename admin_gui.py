#!/usr/bin/env python3
"""ANKA - Tahta Kilit Yönetim Paneli (PySide6/Qt).

Bu, admin_araci.py'nin (CLI) aynı iş mantığını kullanan görsel arayüzü.
Tkinter yerine PySide6/Qt kullanılıyor - native, profesyonel görünüm için.

Kapsam (şimdilik): Anahtarlar (USB/Mobil/Kayıtlı) + Okul Kurulumu.
Diğer araç çubuğu düğmeleri (Duyurular, Yoklama, Transfer, Kontrol...)
yer tutucu - ileride gerçek işlevle doldurulacak, düzen ona göre kuruldu.
"""
import io
import os
import platform
import shlex
import shutil
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

import admin_araci
import keyauth
import veri_deposu

# Windows'ta subprocess ile dış program (powershell) çalıştırınca kısa süreliğine
# siyah bir konsol penceresi belirip kayboluyordu - bunu bastırmak için:
_GIZLI_KONSOL = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

YAKINDA_SEKMELERI = ["📢 Duyurular ve Bildirimler", "✅ Yoklama", "📤 Transfer", "🔄 Güncelle", "📹 Kontrol"]


def kaynak_yolu(dosya_adi):
    """PyInstaller ile paketlenmiş halde de, python ile doğrudan çalıştırılırken
    de (geliştirme) ikon/veri dosyalarını doğru yerde bulur."""
    taban = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(taban, dosya_adi)


# ---------------------------------------------------------------------------
# Temalar (açık / koyu)
# ---------------------------------------------------------------------------

AÇIK_TEMA = """
QMainWindow, QWidget { background-color: #f4f5f9; color: #1c1c26; font-family: 'Segoe UI'; font-size: 10pt; }
QWidget#aracCubugu { background-color: #ffffff; border-right: 1px solid #dcdde6; }
QWidget#icerikAlani { background-color: #f4f5f9; }
QLabel#logoBaslik { color: #4a7fff; font-size: 16pt; font-weight: 700; }
QLabel#logoAltyazi { color: #8a8a95; font-size: 9pt; }
QPushButton { background-color: #4a7fff; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }
QPushButton:hover { background-color: #3a6fe0; }
QPushButton:disabled { background-color: #d8d9e2; color: #9a9aa5; }
QPushButton[ikincil="true"] { background-color: #e7e8f0; color: #1c1c26; }
QPushButton[ikincil="true"]:hover { background-color: #dadbe6; }
QPushButton[sekme="true"] { background-color: transparent; color: #1c1c26; border-radius: 6px; padding: 10px 14px; font-weight: 600; text-align: left; }
QPushButton[sekme="true"]:checked { background-color: #4a7fff; color: white; }
QPushButton[yakinda="true"] { background-color: transparent; color: #b3b3bd; font-weight: 500; padding: 10px 14px; text-align: left; }
QLineEdit, QTextEdit { background-color: white; border: 1px solid #d3d4de; border-radius: 5px; padding: 6px 8px; }
QLineEdit:focus, QTextEdit:focus { border: 1px solid #4a7fff; }
QTableWidget { background-color: white; alternate-background-color: #f7f7fb; gridline-color: #e5e6ee; border: 1px solid #dcdde6; border-radius: 6px; }
QHeaderView::section { background-color: #eceef5; color: #5a5a68; padding: 7px; border: none; font-weight: 600; }
QTabWidget::pane { border: 1px solid #dcdde6; border-radius: 6px; top: -1px; }
QTabBar::tab { background: #eceef5; color: #5a5a68; padding: 9px 18px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #4a7fff; color: white; }
QCheckBox { spacing: 6px; }
QLabel#durumBasarili { color: #2fa86a; }
QFrame#kart { background-color: white; border: 1px solid #dcdde6; border-radius: 8px; }
"""

KOYU_TEMA = """
QMainWindow, QWidget { background-color: #16161d; color: #f0f0f0; font-family: 'Segoe UI'; font-size: 10pt; }
QWidget#aracCubugu { background-color: #20202a; border-right: 1px solid #34343f; }
QWidget#icerikAlani { background-color: #16161d; }
QLabel#logoBaslik { color: #6d94ff; font-size: 16pt; font-weight: 700; }
QLabel#logoAltyazi { color: #8a8a95; font-size: 9pt; }
QPushButton { background-color: #4a7fff; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }
QPushButton:hover { background-color: #5c8bff; }
QPushButton:disabled { background-color: #34343f; color: #6a6a75; }
QPushButton[ikincil="true"] { background-color: #2a2a36; color: #f0f0f0; }
QPushButton[ikincil="true"]:hover { background-color: #34343f; }
QPushButton[sekme="true"] { background-color: transparent; color: #f0f0f0; border-radius: 6px; padding: 10px 14px; font-weight: 600; text-align: left; }
QPushButton[sekme="true"]:checked { background-color: #4a7fff; color: white; }
QPushButton[yakinda="true"] { background-color: transparent; color: #55555f; font-weight: 500; padding: 10px 14px; text-align: left; }
QLineEdit, QTextEdit { background-color: #0e0e13; color: #f0f0f0; border: 1px solid #34343f; border-radius: 5px; padding: 6px 8px; }
QLineEdit:focus, QTextEdit:focus { border: 1px solid #4a7fff; }
QTableWidget { background-color: #0e0e13; alternate-background-color: #17171f; gridline-color: #2a2a36; border: 1px solid #34343f; border-radius: 6px; color: #f0f0f0; }
QHeaderView::section { background-color: #20202a; color: #9a9aa8; padding: 7px; border: none; font-weight: 600; }
QTabWidget::pane { border: 1px solid #34343f; border-radius: 6px; top: -1px; }
QTabBar::tab { background: #20202a; color: #9a9aa8; padding: 9px 18px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #4a7fff; color: white; }
QCheckBox { spacing: 6px; color: #f0f0f0; }
QLabel#durumBasarili { color: #4ade80; }
QFrame#kart { background-color: #20202a; border: 1px solid #34343f; border-radius: 8px; }
"""


# ---------------------------------------------------------------------------
# USB sürücü tespiti (Windows: WMI / Linux: lsblk)
# ---------------------------------------------------------------------------

def usb_disklerini_bul(tumunu_goster=False):
    if platform.system() == "Windows":
        return _usb_disklerini_bul_windows(tumunu_goster)
    return _usb_disklerini_bul_linux(tumunu_goster)


def _usb_disklerini_bul_windows(tumunu_goster):
    # Bazı USB bellekler Windows'a "USB" değil "SCSI" gibi farklı bir
    # InterfaceType ile görünebiliyor (özellikle büyük kapasiteli/bazı
    # markalar) - bu yüzden "tümünü göster" seçeneğinde filtre kaldırılıyor.
    filtre = "" if tumunu_goster else " | Where-Object {$_.InterfaceType -eq 'USB'}"
    komut = (
        f"Get-CimInstance Win32_DiskDrive{filtre} | "
        "ForEach-Object { $disk=$_; "
        "$parts = Get-CimAssociatedInstance -InputObject $disk -ResultClassName Win32_DiskPartition; "
        "foreach ($p in $parts) { "
        "$lds = Get-CimAssociatedInstance -InputObject $p -ResultClassName Win32_LogicalDisk; "
        "foreach ($ld in $lds) { \"$($ld.DeviceID)|$($disk.SerialNumber)|$($disk.Model)|$($disk.InterfaceType)\" } } }"
    )
    try:
        cikti = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", komut], text=True, timeout=15,
            creationflags=_GIZLI_KONSOL,
        )
    except Exception:
        return []

    sonuc = []
    for satir in cikti.splitlines():
        satir = satir.strip()
        if not satir or "|" not in satir:
            continue
        parcalar = satir.split("|")
        if len(parcalar) < 3:
            continue
        harf, seri, model = parcalar[0], parcalar[1].strip(), parcalar[2].strip()
        tur = parcalar[3].strip() if len(parcalar) > 3 else ""
        bilgi = f"{model} ({tur})" if tur else model
        sonuc.append({"kok": harf + "\\", "seri": seri, "bilgi": bilgi})
    return sonuc


def _usb_disklerini_bul_linux(tumunu_goster):
    try:
        cikti = subprocess.check_output(
            ["lsblk", "-o", "NAME,SERIAL,MOUNTPOINT,TRAN,MODEL", "-P", "-n"], text=True, timeout=10
        )
    except Exception:
        return []

    sonuc = []
    for satir in cikti.splitlines():
        try:
            alanlar = dict(t.split("=", 1) for t in shlex.split(satir))
        except ValueError:
            continue
        alanlar = {k: v.strip('"') for k, v in alanlar.items()}
        if not tumunu_goster and alanlar.get("TRAN") != "usb":
            continue
        mount = alanlar.get("MOUNTPOINT")
        if not mount:
            continue
        model = alanlar.get("MODEL", "").strip() or alanlar.get("NAME", "")
        tur = alanlar.get("TRAN", "")
        sonuc.append({
            "kok": mount + "/",
            "seri": alanlar.get("SERIAL", ""),
            "bilgi": f"{model} ({tur})" if tur else model,
        })
    return sonuc


# ---------------------------------------------------------------------------
# Ortak yardımcılar
# ---------------------------------------------------------------------------

def ikincil_buton(metin):
    b = QPushButton(metin)
    b.setProperty("ikincil", True)
    b.setCursor(Qt.PointingHandCursor)
    return b


def buton(metin):
    b = QPushButton(metin)
    b.setCursor(Qt.PointingHandCursor)
    return b


def qr_pixmap(veri, boyut=170):
    try:
        import qrcode
    except ImportError:
        return None
    img = qrcode.make(veri).resize((boyut, boyut))
    tampon = io.BytesIO()
    img.save(tampon, format="PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(tampon.getvalue())
    return pixmap


def tablo_olustur(basliklar, duzenlenebilir=False):
    tablo = QTableWidget(0, len(basliklar))
    tablo.setHorizontalHeaderLabels(basliklar)
    tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tablo.verticalHeader().setVisible(False)
    tablo.setSelectionBehavior(QTableWidget.SelectRows)
    tablo.setSelectionMode(QTableWidget.SingleSelection)
    if not duzenlenebilir:
        tablo.setEditTriggers(QTableWidget.NoEditTriggers)
    tablo.setAlternatingRowColors(True)
    return tablo


# ---------------------------------------------------------------------------
# Anahtarlar - USB sekmesi
# ---------------------------------------------------------------------------

class UsbSekmesi(QWidget):
    def __init__(self):
        super().__init__()
        self.disker = []

        ust = QHBoxLayout()
        yenile_btn = ikincil_buton("Yenile")
        yenile_btn.clicked.connect(self.yenile)
        ust.addWidget(yenile_btn)
        self.tumunu_goster_kutu = QCheckBox("Tüm sürücüleri göster")
        self.tumunu_goster_kutu.stateChanged.connect(self.yenile)
        ust.addWidget(self.tumunu_goster_kutu)
        ust.addStretch()

        self.tablo = tablo_olustur(["Sürücü", "Seri No", "Bilgi"])

        alt = QHBoxLayout()
        alt.addWidget(QLabel("Öğretmen adı:"))
        self.ad_giris = QLineEdit()
        alt.addWidget(self.ad_giris)
        olustur_btn = buton("Anahtar Oluştur")
        olustur_btn.clicked.connect(self.anahtar_olustur)
        alt.addWidget(olustur_btn)

        self.durum = QLabel("")
        self.durum.setObjectName("durumBasarili")

        duzen = QVBoxLayout(self)
        duzen.addLayout(ust)
        duzen.addWidget(self.tablo)
        duzen.addLayout(alt)
        duzen.addWidget(self.durum)

        self.yenile()

    def yenile(self):
        self.disker = usb_disklerini_bul(self.tumunu_goster_kutu.isChecked())
        self.tablo.setRowCount(0)
        for d in self.disker:
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            self.tablo.setItem(satir, 0, QTableWidgetItem(d["kok"]))
            self.tablo.setItem(satir, 1, QTableWidgetItem(d["seri"]))
            self.tablo.setItem(satir, 2, QTableWidgetItem(d["bilgi"]))

    def anahtar_olustur(self):
        satir = self.tablo.currentRow()
        if satir < 0:
            QMessageBox.warning(self, "Uyarı", "Önce listeden bir USB seç.")
            return
        disk = self.disker[satir]
        ad = self.ad_giris.text().strip()
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Öğretmen adı boş olamaz.")
            return

        yol = disk["kok"] + keyauth.USB_ANAHTAR_DOSYA_ADI
        mevcut_icerik = None
        if os.path.exists(yol):
            # USB'de zaten başka bir okulun (ya da bu okulun eski) kaydı
            # olabilir - çoklu okul desteği için okunup korunuyor.
            try:
                with open(yol) as f:
                    mevcut_icerik = f.read()
            except OSError:
                pass

        try:
            icerik = admin_araci.usb_anahtar_hazirla(ad, disk["seri"], mevcut_icerik)
        except admin_araci.AdminHatasi as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        try:
            with open(yol, "w") as f:
                f.write(icerik)
        except OSError as e:
            QMessageBox.critical(self, "Hata", f"USB'ye yazılamadı: {e}")
            return

        self.durum.setText(f"'{ad}' için anahtar {disk['kok']}'e yazıldı.")


# ---------------------------------------------------------------------------
# Anahtarlar - Mobil sekmesi
# ---------------------------------------------------------------------------

class MobilSekmesi(QWidget):
    def __init__(self):
        super().__init__()

        ust = QHBoxLayout()
        ust.addWidget(QLabel("Öğretmen adı:"))
        self.ad_giris = QLineEdit()
        ust.addWidget(self.ad_giris, 2)
        ust.addWidget(QLabel("Kod (boş=otomatik):"))
        self.kod_giris = QLineEdit()
        self.kod_giris.setMaximumWidth(70)
        ust.addWidget(self.kod_giris)
        olustur_btn = buton("Anahtar Oluştur")
        olustur_btn.clicked.connect(self.anahtar_olustur)
        ust.addWidget(olustur_btn)

        sonuc = QHBoxLayout()
        self.qr_etiketi = QLabel()
        self.qr_etiketi.setFixedSize(170, 170)
        self.qr_etiketi.setAlignment(Qt.AlignCenter)
        sonuc.addWidget(self.qr_etiketi)
        self.metin_kutu = QTextEdit()
        self.metin_kutu.setReadOnly(True)
        sonuc.addWidget(self.metin_kutu)

        duzen = QVBoxLayout(self)
        duzen.addLayout(ust)
        duzen.addLayout(sonuc)
        duzen.addStretch()

    def anahtar_olustur(self):
        ad = self.ad_giris.text().strip()
        kod = self.kod_giris.text().strip() or None
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Öğretmen adı boş olamaz.")
            return
        try:
            ogretmen_kodu, kurulum_verisi = admin_araci.mobil_anahtar_hazirla(ad, kod)
        except admin_araci.AdminHatasi as e:
            QMessageBox.critical(self, "Hata", str(e))
            return

        self.metin_kutu.setPlainText(f"Öğretmen: {ad}   Kod: {ogretmen_kodu}\n\n{kurulum_verisi}")
        pixmap = qr_pixmap(kurulum_verisi)
        if pixmap:
            self.qr_etiketi.setPixmap(pixmap)


# ---------------------------------------------------------------------------
# Anahtarlar - Kayıtlı Anahtarlar sekmesi
# ---------------------------------------------------------------------------

class KayitliSekmesi(QWidget):
    def __init__(self):
        super().__init__()
        self.kayitlar = {}

        ust = QHBoxLayout()
        yenile_btn = ikincil_buton("Yenile")
        yenile_btn.clicked.connect(self.yenile)
        ust.addWidget(yenile_btn)
        qr_btn = ikincil_buton("QR Göster")
        qr_btn.clicked.connect(self.qr_goster)
        ust.addWidget(qr_btn)
        kara_ekle_btn = ikincil_buton("Karalisteye Al")
        kara_ekle_btn.clicked.connect(self.karaliste_ekle)
        ust.addWidget(kara_ekle_btn)
        kara_cikar_btn = ikincil_buton("Karalisteden Çıkar")
        kara_cikar_btn.clicked.connect(self.karaliste_kaldir)
        ust.addWidget(kara_cikar_btn)
        ust.addStretch()

        self.tablo = tablo_olustur(["Kod", "Öğretmen", "Durum"])

        alt = QHBoxLayout()
        self.qr_etiketi = QLabel()
        self.qr_etiketi.setFixedSize(150, 150)
        self.qr_etiketi.setAlignment(Qt.AlignCenter)
        alt.addWidget(self.qr_etiketi)
        alt.addStretch()

        duzen = QVBoxLayout(self)
        duzen.addLayout(ust)
        duzen.addWidget(self.tablo)
        duzen.addLayout(alt)

        self.yenile()

    def yenile(self):
        self.kayitlar = admin_araci.ogretmenleri_yukle()
        iptaller = set(admin_araci.iptal_satirlarini_oku())
        self.tablo.setRowCount(0)
        for kod, ad in self.kayitlar.items():
            durum = "İPTAL" if kod in iptaller else "Aktif"
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            self.tablo.setItem(satir, 0, QTableWidgetItem(kod))
            self.tablo.setItem(satir, 1, QTableWidgetItem(ad))
            self.tablo.setItem(satir, 2, QTableWidgetItem(durum))

    def _secili_kod(self):
        satir = self.tablo.currentRow()
        if satir < 0:
            QMessageBox.warning(self, "Uyarı", "Önce listeden bir öğretmen seç.")
            return None
        return self.tablo.item(satir, 0).text()

    def qr_goster(self):
        kod = self._secili_kod()
        if kod is None:
            return
        ad = self.kayitlar.get(kod, "")
        try:
            _, kurulum_verisi = admin_araci.mobil_anahtar_hazirla(ad, kod)
        except admin_araci.AdminHatasi as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        pixmap = qr_pixmap(kurulum_verisi, 150)
        if pixmap:
            self.qr_etiketi.setPixmap(pixmap)

    def karaliste_ekle(self):
        kod = self._secili_kod()
        if kod is None:
            return
        admin_araci.iptal_ekle(kod)
        self.yenile()

    def karaliste_kaldir(self):
        kod = self._secili_kod()
        if kod is None:
            return
        admin_araci.iptal_kaldir(kod)
        self.yenile()


# ---------------------------------------------------------------------------
# Okul Kurulumu - Anahtar Kurulumu sekmesi
# ---------------------------------------------------------------------------

class AnahtarKurulumuSekmesi(QWidget):
    def __init__(self):
        super().__init__()
        self.etiket = QLabel()
        self.etiket.setWordWrap(True)
        self.kur_btn = buton("Okulu Kur (bir kereliğine)")
        self.kur_btn.clicked.connect(self.kur)

        uyari = QLabel(
            "⚠️ Bu bilgisayardaki okul anahtarının YEDEĞİ yoksa, disk arızası/format "
            "durumunda TÜM dağıtılmış USB ve mobil anahtarlar kalıcı olarak işe "
            "yaramaz hale gelir (tahtalardaki eski açık anahtarla yeni üretilenler "
            "eşleşmez). Kurulumdan hemen sonra yedek al ve güvenli bir yerde (başka "
            "bir USB, bulut vb.) sakla."
        )
        uyari.setWordWrap(True)
        uyari.setStyleSheet("color: #e0a030;")

        yedek_satiri = QHBoxLayout()
        self.yedekle_btn = ikincil_buton("💾 Yedekle (.zip)")
        self.yedekle_btn.clicked.connect(self.yedekle)
        yedek_satiri.addWidget(self.yedekle_btn)
        self.geri_yukle_btn = ikincil_buton("♻️ Yedekten Geri Yükle")
        self.geri_yukle_btn.clicked.connect(self.geri_yukle)
        yedek_satiri.addWidget(self.geri_yukle_btn)
        yedek_satiri.addStretch()

        duzen = QVBoxLayout(self)
        duzen.addWidget(self.etiket)
        duzen.addWidget(self.kur_btn, alignment=Qt.AlignLeft)
        duzen.addSpacing(16)
        duzen.addWidget(uyari)
        duzen.addLayout(yedek_satiri)
        duzen.addStretch()
        self.guncelle()

    def guncelle(self):
        if admin_araci.okul_kurulu_mu():
            self.etiket.setText(
                "Bu okul için kurulum tamamlandı — anahtarlar hazır.\n\n"
                "Yeni bir öğretmen için anahtar üretmek üzere \"Anahtarlar\" sekmesine geçebilirsin."
            )
            self.kur_btn.setEnabled(False)
        else:
            self.etiket.setText("Bu okul için henüz kurulum yapılmadı.")
            self.kur_btn.setEnabled(True)
        self.yedekle_btn.setEnabled(admin_araci.okul_kurulu_mu())

    def kur(self):
        admin_araci.okul_kurulumu_yap()
        self.guncelle()
        QMessageBox.information(
            self, "Tamam", "Kurulum tamamlandı. Şimdi hemen bir yedek almanı öneririm."
        )

    def yedekle(self):
        veri_deposu.kaydet()  # bellekteki en güncel hali diske yazılsın
        hedef, _ = QFileDialog.getSaveFileName(
            self, "Yedek Dosyasını Kaydet", "anka_yedek.enc", "Şifreli yedek (*.enc)"
        )
        if not hedef:
            return
        try:
            shutil.copyfile(veri_deposu.VERI_DOSYASI, hedef)
        except OSError as e:
            QMessageBox.critical(self, "Hata", f"Yedek kaydedilemedi: {e}")
            return
        QMessageBox.information(
            self, "Tamam",
            f"Yedek kaydedildi: {hedef}\n\nBu dosya şifreli — yönetici şifren olmadan "
            "işe yaramaz. Yine de bu bilgisayarın dışında (başka bir USB, bulut vb.) "
            "da sakla; disk bu bilgisayarda bozulursa yedek de burada olursa işe yaramaz."
        )

    def geri_yukle(self):
        if admin_araci.okul_kurulu_mu():
            cevap = QMessageBox.question(
                self, "Emin misin?",
                "Bu bilgisayarda zaten bir kurulum var. Yedekten geri yüklemek "
                "üzerine yazacak — bu işlem geri alınamaz. Devam edilsin mi?"
            )
            if cevap != QMessageBox.Yes:
                return

        kaynak, _ = QFileDialog.getOpenFileName(self, "Yedek Dosyasını Seç", "", "Şifreli yedek (*.enc)")
        if not kaynak:
            return
        try:
            os.makedirs(veri_deposu.GIZLI_DIZIN, exist_ok=True)
            shutil.copyfile(kaynak, veri_deposu.VERI_DOSYASI)
        except OSError as e:
            QMessageBox.critical(self, "Hata", f"Geri yükleme başarısız: {e}")
            return
        QMessageBox.information(
            self, "Tamam",
            "Dosya geri yüklendi. Bu yedeğin şifresiyle açmak için programı kapatıp "
            "yeniden aç."
        )


# ---------------------------------------------------------------------------
# Okul Kurulumu - Okul Bilgileri sekmesi
# ---------------------------------------------------------------------------

class OkulBilgileriSekmesi(QWidget):
    ALANLAR = [
        ("okul_adi", "Okul Adı"),
        ("il", "İl"),
        ("ilce", "İlçe"),
        ("adres", "Adres"),
        ("telefon", "Telefon"),
    ]

    def __init__(self):
        super().__init__()
        self.girisler = {}

        duzen = QVBoxLayout(self)
        for anahtar, etiket in self.ALANLAR:
            satir = QHBoxLayout()
            baslik = QLabel(etiket)
            baslik.setFixedWidth(90)
            satir.addWidget(baslik)
            giris = QLineEdit()
            satir.addWidget(giris)
            self.girisler[anahtar] = giris
            duzen.addLayout(satir)

        kaydet_btn = buton("Kaydet")
        kaydet_btn.clicked.connect(self.kaydet)
        duzen.addWidget(kaydet_btn, alignment=Qt.AlignLeft)
        duzen.addStretch()

        self.yukle()

    def yukle(self):
        veri = admin_araci.okul_bilgilerini_yukle()
        for anahtar, giris in self.girisler.items():
            giris.setText(veri.get(anahtar, ""))

    def kaydet(self):
        veri = {anahtar: giris.text().strip() for anahtar, giris in self.girisler.items()}
        admin_araci.okul_bilgilerini_kaydet(veri)
        QMessageBox.information(self, "Tamam", "Okul bilgileri kaydedildi.")


# ---------------------------------------------------------------------------
# Okul Kurulumu - Ders Programı sekmesi
# ---------------------------------------------------------------------------

class DersProgramiSekmesi(QWidget):
    def __init__(self):
        super().__init__()

        ust = QHBoxLayout()
        ekle_btn = ikincil_buton("Satır Ekle")
        ekle_btn.clicked.connect(self.satir_ekle)
        ust.addWidget(ekle_btn)
        sil_btn = ikincil_buton("Satır Sil")
        sil_btn.clicked.connect(self.satir_sil)
        ust.addWidget(sil_btn)
        kaydet_btn = buton("Kaydet")
        kaydet_btn.clicked.connect(self.kaydet)
        ust.addWidget(kaydet_btn)
        ust.addStretch()

        self.tablo = tablo_olustur(["Tür", "Başlama", "Bitiş"], duzenlenebilir=True)

        duzen = QVBoxLayout(self)
        duzen.addLayout(ust)
        duzen.addWidget(self.tablo)

        self.yukle()

    def _satir_doldur(self, satir, veri):
        self.tablo.setItem(satir, 0, QTableWidgetItem(veri.get("tur", "")))
        self.tablo.setItem(satir, 1, QTableWidgetItem(veri.get("baslama", "")))
        self.tablo.setItem(satir, 2, QTableWidgetItem(veri.get("bitis", "")))

    def yukle(self):
        self.tablo.setRowCount(0)
        for veri in admin_araci.ders_programini_yukle():
            satir = self.tablo.rowCount()
            self.tablo.insertRow(satir)
            self._satir_doldur(satir, veri)

    def satir_ekle(self):
        satir = self.tablo.rowCount()
        self.tablo.insertRow(satir)
        self._satir_doldur(satir, {"tur": "", "baslama": "", "bitis": ""})

    def satir_sil(self):
        satir = self.tablo.currentRow()
        if satir >= 0:
            self.tablo.removeRow(satir)

    def kaydet(self):
        def metin(satir, sutun):
            oge = self.tablo.item(satir, sutun)
            return oge.text().strip() if oge else ""

        satirlar = [
            {"tur": metin(s, 0), "baslama": metin(s, 1), "bitis": metin(s, 2)}
            for s in range(self.tablo.rowCount())
        ]
        admin_araci.ders_programini_kaydet(satirlar)
        QMessageBox.information(self, "Tamam", "Ders programı kaydedildi.")


# ---------------------------------------------------------------------------
# Okul Kurulumu sayfası (üç alt sekme)
# ---------------------------------------------------------------------------

class OkulKurulumuSayfasi(QTabWidget):
    def __init__(self):
        super().__init__()
        self.anahtar_sekmesi = AnahtarKurulumuSekmesi()
        self.addTab(self.anahtar_sekmesi, "Anahtar Kurulumu")
        self.addTab(OkulBilgileriSekmesi(), "Okul Bilgileri")
        self.addTab(DersProgramiSekmesi(), "Ders Programı")

    def guncelle(self):
        self.anahtar_sekmesi.guncelle()


# ---------------------------------------------------------------------------
# Ana pencere
# ---------------------------------------------------------------------------

class AnaPencere(QMainWindow):
    def __init__(self, uygulama):
        super().__init__()
        self.uygulama = uygulama
        self.koyu_mu = True

        self.setWindowTitle("ANKA - Tahta Kilit Yönetim Paneli")
        self.resize(880, 620)
        self.setMinimumSize(700, 480)
        try:
            self.setWindowIcon(QIcon(kaynak_yolu("anka.ico")))
        except Exception:
            pass

        merkez = QWidget()
        self.setCentralWidget(merkez)
        ana_duzen = QHBoxLayout(merkez)
        ana_duzen.setContentsMargins(0, 0, 0, 0)
        ana_duzen.setSpacing(0)

        # --- Sol dikey menü (logo + sekme butonları + tema düğmesi) ---
        kenar_cubugu = QWidget()
        kenar_cubugu.setObjectName("aracCubugu")
        kenar_cubugu.setFixedWidth(220)
        kenar_duzen = QVBoxLayout(kenar_cubugu)
        kenar_duzen.setContentsMargins(14, 18, 14, 14)
        kenar_duzen.setSpacing(4)

        logo_baslik = QLabel("ANKA")
        logo_baslik.setObjectName("logoBaslik")
        kenar_duzen.addWidget(logo_baslik)
        logo_alt = QLabel("Akıllı Nesil Kilit Anahtarı")
        logo_alt.setObjectName("logoAltyazi")
        logo_alt.setWordWrap(True)
        kenar_duzen.addWidget(logo_alt)
        kenar_duzen.addSpacing(18)

        self._sekme_butonlari = {}
        self._ekle_sekme_butonu(kenar_duzen, "🔑 Anahtarlar", self.anahtarlar_goster)
        self._ekle_sekme_butonu(kenar_duzen, "🏫 Okul Kurulumu", self.okul_goster)
        for isim in YAKINDA_SEKMELERI:
            b = QPushButton(isim)
            b.setProperty("yakinda", True)
            b.setCursor(Qt.ArrowCursor)
            b.clicked.connect(lambda checked=False, i=isim: self.yakinda(i))
            kenar_duzen.addWidget(b)

        kenar_duzen.addStretch()
        self.tema_btn = ikincil_buton("☀️ Açık Tema")
        self.tema_btn.clicked.connect(self.temayi_degistir)
        kenar_duzen.addWidget(self.tema_btn)

        ana_duzen.addWidget(kenar_cubugu)

        # --- İçerik alanı ---
        icerik_sarmalayici = QWidget()
        icerik_sarmalayici.setObjectName("icerikAlani")
        self.icerik_duzen = QVBoxLayout(icerik_sarmalayici)
        self.icerik_duzen.setContentsMargins(16, 16, 16, 16)

        self.yigin = QStackedWidget()
        self.icerik_duzen.addWidget(self.yigin)
        ana_duzen.addWidget(icerik_sarmalayici, 1)

        self.anahtarlar_sayfasi = None
        self.okul_sayfasi = None

        self.temayi_uygula()
        self.anahtarlar_goster()

    def temayi_uygula(self):
        self.uygulama.setStyleSheet(KOYU_TEMA if self.koyu_mu else AÇIK_TEMA)
        self.tema_btn.setText("☀️ Açık Tema" if self.koyu_mu else "🌙 Koyu Tema")

    def temayi_degistir(self):
        self.koyu_mu = not self.koyu_mu
        self.temayi_uygula()

    def _ekle_sekme_butonu(self, layout, isim, komut):
        b = QPushButton(isim)
        b.setProperty("sekme", True)
        b.setCheckable(True)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(komut)
        layout.addWidget(b)
        self._sekme_butonlari[isim] = b

    def _aktif_sekme(self, isim):
        for ad, b in self._sekme_butonlari.items():
            b.setChecked(ad == isim)

    def anahtarlar_goster(self):
        self._aktif_sekme("🔑 Anahtarlar")
        if self.anahtarlar_sayfasi is None:
            self.anahtarlar_sayfasi = QTabWidget()
            self.anahtarlar_sayfasi.addTab(UsbSekmesi(), "🔌 USB Anahtar")
            self.anahtarlar_sayfasi.addTab(MobilSekmesi(), "📱 Mobil Anahtar")
            self.anahtarlar_sayfasi.addTab(KayitliSekmesi(), "📋 Kayıtlı Anahtarlar")
            self.yigin.addWidget(self.anahtarlar_sayfasi)
        self.yigin.setCurrentWidget(self.anahtarlar_sayfasi)

    def okul_goster(self):
        self._aktif_sekme("🏫 Okul Kurulumu")
        if self.okul_sayfasi is None:
            self.okul_sayfasi = OkulKurulumuSayfasi()
            self.yigin.addWidget(self.okul_sayfasi)
        else:
            self.okul_sayfasi.guncelle()
        self.yigin.setCurrentWidget(self.okul_sayfasi)

    def yakinda(self, isim):
        QMessageBox.information(self, isim, f"'{isim}' henüz eklenmedi, yakında geliyor.")


def _sifre_sor(baslik, etiket):
    sifre, tamam = QInputDialog.getText(None, baslik, etiket, QLineEdit.Password)
    if not tamam:
        return None
    return sifre


def _depoyu_ac_veya_cik():
    """Depo yoksa yeni şifre belirletir, varsa açar. Kullanıcı vazgeçerse
    programdan çıkar (True/False değil, direkt sys.exit)."""
    if not veri_deposu.depo_var_mi():
        while True:
            sifre = _sifre_sor(
                "İlk Kurulum",
                "Bu, verilerini korumak için kullanılacak yönetici şifresi.\n"
                "Unutursan verilerine erişilemez — güvenli bir yere not al.\n\n"
                "Yeni yönetici şifresi belirle:",
            )
            if sifre is None:
                sys.exit(0)
            if not sifre:
                QMessageBox.warning(None, "Uyarı", "Şifre boş olamaz.")
                continue
            tekrar = _sifre_sor("İlk Kurulum", "Şifreyi tekrar gir:")
            if tekrar is None:
                sys.exit(0)
            if sifre != tekrar:
                QMessageBox.warning(None, "Uyarı", "Şifreler eşleşmedi, tekrar dene.")
                continue
            veri_deposu.depo_olustur(sifre)
            return
    else:
        while True:
            sifre = _sifre_sor("Giriş", "Yönetici şifresi:")
            if sifre is None:
                sys.exit(0)
            try:
                veri_deposu.kilidi_ac(sifre)
                return
            except veri_deposu.SifreHatasi:
                QMessageBox.critical(None, "Hata", "Şifre yanlış, tekrar dene.")


def main():
    uygulama = QApplication(sys.argv)
    _depoyu_ac_veya_cik()
    pencere = AnaPencere(uygulama)
    pencere.show()
    sys.exit(uygulama.exec())


if __name__ == "__main__":
    main()
