#!/usr/bin/env bash
# 사용: build.sh deck.html (작업 폴더는 /tmp 쪽) -> deck.pdf + deck-preview-N.png, 넘침·쪽수 검사. 통과하면 PDF 를 현재 pwd 로 복사
set -euo pipefail
f=$(realpath "$1"); out="${f%.html}"
skill=$(dirname "$(dirname "$(realpath "$0")")")
tmp="${out}.build.html"; trap 'rm -f "$tmp"' EXIT
sed "s|{{SKILL}}|$skill|g" "$f" > "$tmp"
chrome=$(command -v google-chrome || command -v chromium || command -v chromium-browser)
n=$("$chrome" --headless=new --no-sandbox --virtual-time-budget=2000 --allow-file-access-from-files --dump-dom "file://$tmp" 2>/dev/null | { grep -o 'data-overflow=""' || true; } | wc -l)
"$chrome" --headless=new --no-sandbox --no-pdf-header-footer --allow-file-access-from-files --print-to-pdf="$out.pdf" "file://$tmp" 2>/dev/null
pages=$(pdfinfo "$out.pdf" | awk '/^Pages/{print $2}')
slides=$(grep -c 'class="slide' "$f")
rm -f "$out"-preview-*.png
pdftoppm -png -r 50 "$out.pdf" "$out-preview"
echo "pdf: $out.pdf  pages=$pages slides=$slides overflow=$n"
[ "$n" = 0 ] && [ "$pages" = "$slides" ] || { echo "FAIL: 넘침 또는 쪽수 불일치"; exit 1; }
if [ "$(dirname "$out")" != "$PWD" ]; then cp "$out.pdf" "$PWD/"; echo "final: $PWD/$(basename "$out").pdf"; fi
