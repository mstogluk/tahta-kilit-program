#!/bin/bash
# Tahta Kilit - kurulum betiği (git tabanlı, geliştirme/test için).
# Kullanım: sudo bash install.sh
#
# Not: Asıl son-kullanıcı kurulum yöntemi artık ANKA'nın ürettiği
# pardus_kurulum.py (grafik pencere) - bkz. devam-notu.md. Bu betik git
# reposunu doğrudan çalıştıranlar için hâlâ duruyor.
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Bu betik sudo ile çalıştırılmalı: sudo bash install.sh"
  exit 1
fi

BURASI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Gerekli paketler kuruluyor..."
apt update
apt install -y python3-gi gir1.2-gtk-3.0 python3-cryptography python3-qrcode

mkdir -p /etc/tahtakilit /etc/xdg/autostart

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

if [ -f "$BURASI/tahta-config/iptal.txt" ]; then
  cp "$BURASI/tahta-config/iptal.txt" /etc/tahtakilit/iptal.txt
  echo "iptal.txt kopyalandı."
fi

chmod +x "$BURASI/lockscreen.py" "$BURASI/run.sh"

# Sistem geneli autostart - belirli bir kullanıcıya bağlı değil, o tahtada
# kim oturum açarsa açsın devreye giriyor.
cat > /etc/xdg/autostart/tahtakilit.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Tahta Kilit
Exec=$BURASI/run.sh
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "Kurulum tamamlandı."
echo "Tahta, hangi kullanıcıyla oturum açılırsa açılsın otomatik kilitlenecek."
echo "Test etmek için: $BURASI/run.sh"
