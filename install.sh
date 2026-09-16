#!/bin/bash
# Tahta Kilit - kurulum betiği.
# Kullanım: sudo bash install.sh <lightdm_otomatik_giris_kullanicisi>
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Bu betik sudo ile çalıştırılmalı: sudo bash install.sh <kullanici_adi>"
  exit 1
fi

KULLANICI="$1"
if [ -z "$KULLANICI" ]; then
  # LightDM otomatik giriş kullanıcısını tahmin etmeye çalış (garanti değil)
  KULLANICI=$(grep -oP '^autologin-user=\K.*' /etc/lightdm/lightdm.conf.d/*.conf 2>/dev/null | head -n1)
fi
if [ -z "$KULLANICI" ]; then
  echo "Kullanıcı adı belirlenemedi. Elle ver: sudo bash install.sh <kullanici_adi>"
  exit 1
fi
echo "Kurulum kullanıcısı: $KULLANICI"

BURASI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Gerekli paketler kuruluyor..."
apt update
apt install -y python3-gi gir1.2-gtk-3.0 python3-cryptography python3-qrcode

mkdir -p /etc/tahtakilit

if [ -f "$BURASI/tahta-config/okul_acik.key" ]; then
  cp "$BURASI/tahta-config/okul_acik.key" /etc/tahtakilit/okul_acik.key
  echo "okul_acik.key kopyalandı."
else
  echo "UYARI: tahta-config/okul_acik.key yok — USB Anahtar çalışmayacak."
fi

if [ -f "$BURASI/tahta-config/mobil_gizli.key" ]; then
  cp "$BURASI/tahta-config/mobil_gizli.key" /etc/tahtakilit/mobil_gizli.key
  echo "mobil_gizli.key kopyalandı."
else
  echo "UYARI: tahta-config/mobil_gizli.key yok — Mobil Anahtar çalışmayacak."
fi

chmod +x "$BURASI/lockscreen.py" "$BURASI/run.sh"

KULLANICI_EV=$(getent passwd "$KULLANICI" | cut -d: -f6)
if [ -z "$KULLANICI_EV" ]; then
  echo "UYARI: '$KULLANICI' kullanıcısı bulunamadı, autostart kurulamadı."
  exit 1
fi

mkdir -p "$KULLANICI_EV/.config/autostart"
cat > "$KULLANICI_EV/.config/autostart/tahtakilit.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Tahta Kilit
Exec=$BURASI/run.sh
X-GNOME-Autostart-enabled=true
EOF
chown "$KULLANICI:$KULLANICI" "$KULLANICI_EV/.config/autostart/tahtakilit.desktop"

echo ""
echo "Kurulum tamamlandı."
echo "Tahta, '$KULLANICI' oturumu her açıldığında otomatik kilitlenecek."
echo "Test etmek için: sudo -u $KULLANICI $BURASI/run.sh"
