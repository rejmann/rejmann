#!/usr/bin/env bash
# Gera ascii.svg a partir de ascii.txt. So isso.
#
#   ascii.txt -> a arte (troque so este arquivo)
#   ascii.svg -> gerado; e o que o README.md embute via <img>
#
# O SVG tem fundo transparente (so os glifos do ascii) e cor adaptavel
# ao tema (claro/escuro). Ajuste o tamanho pelo width do <img> no README.md.
#
# Uso: ./cli/build-ascii-to-svg.sh
set -euo pipefail

cd "$(dirname "$0")/.."

ART="ascii.txt"
SVG="ascii.svg"

[ -f "$ART" ] || { echo "erro: $ART nao encontrado" >&2; exit 1; }

# Metrica de fonte monospace: ~7.226px de largura e 13px de altura por linha.
awk '
  {
    line = $0
    sub(/[ \t]+$/, "", line)               # tira espaco a direita
    if (length(line) > maxc) maxc = length(line)
    gsub(/&/, "\\&amp;", line)
    gsub(/</, "\\&lt;",  line)
    gsub(/>/, "\\&gt;",  line)
    n++
    rows[n] = line
  }
  END {
    cw = 7.226; lh = 13
    w = int(maxc * cw + 0.999)
    h = n * lh
    print "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 " w " " h "\" width=\"" w "\" height=\"" h "\">"
    print "<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;white-space:pre;fill:#1f2328}@media(prefers-color-scheme:dark){text{fill:#e6edf3}}</style>"
    print "<text xml:space=\"preserve\">"
    for (i = 1; i <= n; i++)
      printf "<tspan x=\"0\" y=\"%d\">%s</tspan>\n", i * lh - 3, rows[i]
    print "</text>"
    print "</svg>"
    printf "ok: %s (%dx%d)\n", "'"$SVG"'", w, h > "/dev/stderr"
  }
' "$ART" > "$SVG.tmp"
mv "$SVG.tmp" "$SVG"
