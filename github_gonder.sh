#!/bin/bash
cd "$(dirname "$0")" || exit 1

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git init -b main
fi

if ! git remote | grep -q '^origin$'; then
    git remote add origin https://github.com/mstogluk/tahta-kilit-program.git
fi

git add -A
read -rp "Commit mesaji (bos birakip Enter'a basabilirsin): " msg
if [ -z "$msg" ]; then
    msg="guncelleme"
fi
git commit -m "$msg"
git push -u origin main
