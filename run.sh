#!/bin/bash
# ec=0 (dogru PIN ile normal kapanis) -> tekrar acma
# ec!=0 (cokme/beklenmedik kapanis) -> 1sn sonra tekrar ac
while true; do
  python3 /opt/tahtakilit/lockscreen.py
  ec=$?
  if [ "$ec" -eq 0 ]; then
    break
  fi
  sleep 1
done
