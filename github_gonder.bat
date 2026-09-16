@echo off
cd /d "%~dp0"
git add -A
set /p msg="Commit mesaji (bos birakip Enter'a basabilirsin): "
if "%msg%"=="" set msg=guncelleme
git commit -m "%msg%"
git push -u origin main
pause
