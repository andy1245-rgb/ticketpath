#!/usr/bin/env bash
# Section 8.5 of the brief: these counts must all be zero.
# Scoped to the source we wrote, never the fixture JSON or the build output.
set -uo pipefail
cd "$(dirname "$0")/.."

SRC=(app components lib)
fail=0

check() {
  local label="$1" pattern="$2"
  local n
  n=$(grep -rnE "$pattern" "${SRC[@]}" --include='*.tsx' --include='*.ts' --include='*.css' 2>/dev/null | wc -l)
  printf '%-28s %s\n' "$label" "$n"
  [ "$n" -eq 0 ] || fail=$((fail + 1))
}

echo "=== 8.5 forbidden strings ==="
check 'cdn.tailwindcss.com' 'cdn\.tailwindcss\.com'
check 'fonts.googleapis.com' 'fonts\.googleapis\.com'
check 'material-symbols' 'material-symbols'
check 'transition-all' 'transition-all'
check 'user-scalable' 'user-scalable'
check 'maximum-scale' 'maximum-scale'
check 'href="#"' 'href="#"'
check 'text-[11px]' 'text-\[11px\]'
check 'border-dashed' 'border-dashed'

echo
echo "=== colour values outside app/theme.css ==="
n=$(grep -rnE '#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(' app components lib \
      --include='*.tsx' --include='*.ts' --include='*.css' 2>/dev/null \
    | grep -v '^app/theme.css:' \
    | grep -v '^lib/mock/' \
    | grep -v '\.test\.ts:' | wc -l)
printf '%-28s %s\n' 'hex / rgb() / hsl()' "$n"
[ "$n" -eq 0 ] || { fail=$((fail + 1)); grep -rnE '#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(' app components lib --include='*.tsx' --include='*.ts' --include='*.css' 2>/dev/null | grep -v '^app/theme.css:' | grep -v '^lib/mock/' | grep -v '\.test\.ts:' | head -8; }

echo
echo "=== data-in-component and encoding checks ==="
printf '%-28s %s\n' 'fetch( in components' "$(grep -rn 'fetch(' components --include='*.tsx' 2>/dev/null | wc -l)"
printf '%-28s %s\n' 'as any / @ts-ignore' "$(grep -rnE 'as any|@ts-ignore|@ts-expect-error' app components lib --include='*.tsx' --include='*.ts' 2>/dev/null | wc -l)"
printf '%-28s %s\n' 'iframe' "$(grep -rn '<iframe' app components --include='*.tsx' 2>/dev/null | wc -l)"
printf '%-28s %s\n' 'em dashes in JSX copy' "$(grep -rn '—' app components --include='*.tsx' 2>/dev/null | grep -v 'formatLamports\|// ' | wc -l)"

echo
if [ "$fail" -eq 0 ]; then echo "8.5 GREPS: ALL ZERO"; else echo "8.5 GREPS: $fail GROUP(S) NON-ZERO"; fi
exit "$fail"
