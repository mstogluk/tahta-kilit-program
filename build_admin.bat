@echo off
cd /d "%~dp0"
python -m pip install --quiet pyinstaller PySide6 qrcode Pillow cryptography
python -m PyInstaller --onefile --windowed --icon=anka.ico --name=ANKA --add-data "anka.ico;." --add-data "anka_ikon.png;." admin_gui.py
echo.
echo Bitti: dist\ANKA.exe
pause
