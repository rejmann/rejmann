# Renderização dos SVGs

Três módulos, sem acesso à rede:

- `cli/build_svg.py` — ponto de entrada; monta o SVG e grava os arquivos.
- `cli/panel_to_svg.py` — markup do painel (lado direito).
- `cli/ascii_to_svg.py` — markup da arte ASCII (lado esquerdo).

```bash
python3 cli/build_svg.py      # ou: make svg
# ok: dark_mode.svg recreated (1005x530, 62 cols)
# ok: light_mode.svg recreated (1005x530, 62 cols)
```

## Estrutura do SVG gerado

```xml
<svg font-family="ConsolasFallback,Consolas,monospace" width="…px" height="…px" font-size="16px">
  <style>
    @font-face { src: local('Consolas'); font-family: 'ConsolasFallback'; size-adjust: 109%; }
    .key {…} .value {…} .addColor {…} .delColor {…} .cc {…}
    .ascii {font-size: 6px;}
    text, tspan {white-space: pre;}
  </style>
  <rect … fill="{background}" rx="15"/>             <!-- cartão com cantos arredondados -->
  <text x="15"  y="30" fill="{text}" class="ascii">  <!-- arte: um <tspan> por linha -->
  <text x="390" y="30" fill="{text}">                <!-- painel: um <tspan> por linha -->
</svg>
```

- Fonte monoespaçada: usa a Consolas local quando existe, com `size-adjust:
  109%` para aproximar a métrica dela à do fallback `monospace`.
- `white-space: pre` preserva os espaços do alinhamento.
- As cores vêm de `themes.<modo>` no `panel.yaml`; o CSS usa classes, então o
  mesmo markup do painel serve para todos os temas.

## `build_svg.py`

Fluxo de `main()`:

1. Lê o `panel.yaml`; aborta se não houver `themes:`.
2. `effective_cols(doc)` → número de colunas do painel.
3. `build_panel(doc, cols)` → markup do painel e `y` da última linha (igual para
   todos os temas).
4. Calcula a largura do canvas.
5. Para cada tema, `render_svg()` valida as 7 cores, lê `<modo>_mode.txt`,
   calcula a altura e preenche o `TEMPLATE`. **Tudo em memória.**
6. Só então, para cada tema: apaga o `.svg` antigo e grava o novo.

A etapa 5 antes da 6 garante que uma falha no meio não deixe SVGs apagados.

### Geometria do canvas

O desenho base tem **985×530 px** para um painel de **60 colunas** começando em
`x=390`, com ~15 px de margem direita. Daí a largura de uma coluna:

```
CHAR_W = (985 - 390 - 15) / 60 ≈ 9.667 px
```

| Dimensão | Fórmula |
|----------|---------|
| Largura | `max(985, ceil(985 + (cols - 60) * CHAR_W))` |
| Altura | `max(530, y_última_linha_painel + 20, y_última_linha_arte + 36)` |

Exemplo atual: a linha `Languages.Real` tem 58 caracteres de conteúdo + 4 de
pontilhado mínimo = 62 colunas → largura `ceil(985 + 2 × 9.667) = 1005`. O
painel termina em `y=490` (+20 = 510) e a arte em `y=494` (+36 = 530) → altura
530.

O canvas cresce, mas nunca encolhe abaixo de 985×530.

## `panel_to_svg.py`

### Constantes

| Constante | Valor | Significado |
|-----------|------:|-------------|
| `PANEL_X` | 390 | `x` do painel |
| `Y_START` | 30 | `y` da primeira linha (régua do `header`) |
| `LINE_HEIGHT` | 20 | espaço vertical entre linhas |
| `MIN_DOTS` | 4 | pontilhado mínimo numa linha chave/valor |
| `FIXED_CHARS` | 5 | `". "` + `":"` + os dois espaços em volta do pontilhado |
| `BASE_COLS` | 60 | colunas do desenho original |

### Largura efetiva — `effective_cols(doc)`

O maior entre:

- `width` do YAML (padrão 60);
- `len(header) + 8`;
- `len("- " + title) + 8` de cada seção com título;
- `5 + len(key) + len(value) + 4` de cada linha chave/valor;
- `2 + ` o comprimento visível de cada template de stats expandido com o
  pontilhado mínimo.

### Montagem — `build_panel(doc, cols)`

Percorre as seções acumulando `y`:

- Primeira linha: régua do `header` em `y=30`.
- Seção com título: `y += 40` (uma linha em branco) e régua `- <title>`.
- Cada linha: `y += 20` e prefixo `<tspan x="390" y="…" class="cc">. </tspan>`,
  seguido de:
  - nada, se for `spacer`;
  - o conteúdo de `raw`, sem escape;
  - `render_stats_row()`, se a seção tiver `fields` e a linha for string;
  - `content_row()`, caso contrário.

Retorna o markup (linhas unidas por `\n`) e o `y` final, usado no cálculo da
altura.

### Régua — `divider_line(y, prefix, cols)`

```
rejman@root -——————————————————————————————————————————-—-
```

`prefix` + `" -"` + `"—" × max(3, cols − len(prefix) − 5)` + `"-—-"`. O
traço longo é o travessão (U+2014). Só o prefixo fica dentro de um `<tspan>`;
os traços são texto solto do `<text>`, na cor `text`.

### Linha chave/valor — `content_row(row, cols)`

```
. OS: .......................... Windows 11, Android 16, Linux
```

- pontilhado = `max(MIN_DOTS, cols − (5 + len(key) + len(value)))` pontos,
  entre dois espaços, classe `cc`;
- valor na classe `value`;
- se a linha tiver `id`, os `<tspan>` recebem `id="<id>_dots"` e `id="<id>"`.

`key_markup()` transforma `"A.B"` em dois `<tspan class="key">` unidos por um
ponto literal.

### Templates de stats — `render_stats_row(template, fields, cols)`

```
. Diff: ............................. 3,735,641++, 2,218,088--
```

Três substituições por regex, nesta ordem:

1. `{k:Texto}` → `key_markup(Texto)`
2. `{Rótulo:campo}` → `key_markup(Rótulo) + ":"` + pontilhado +
   `value_markup(campo)`, se o campo existir
3. `{campo}` → `field_markup(campo)`, se o campo existir

No primeiro `{Rótulo:campo}` da linha o pontilhado é **elástico**: entra um
marcador (`FLEX`), a linha é expandida por inteiro, mede-se a largura visível
(`visible_len`: sem tags e com entidades decodificadas) e o marcador vira
`<tspan class="cc" id="<campo>_dots"> …… </tspan>` com
`max(MIN_DOTS, cols − len(". ") − largura − 2)` pontos. Assim a linha termina
na coluna `cols`, como as linhas chave/valor, qualquer que seja o tamanho dos
números. Com `cols=0` sai o pontilhado mínimo, o que dá a largura natural da
linha — é assim que `effective_cols` mede as linhas de stats.

Os demais `{Rótulo:campo}` da linha e os `{campo}` usam `field_markup()`:
pontilhado fixo (`stats_dots`, se `dots: true`, com `id="<campo>_dots"`),
prefixo, valor (`id="<campo>"`) e sufixo — os três na classe `class`, via
`value_markup()`. A regra do pontilhado fixo
está em [painel.md](painel.md#campos). Linhas sem `{Rótulo:campo}` não são
esticadas.

### Escape

`esc()` escapa `&`, `<`, `>` em rótulos e valores. Aspas não são escapadas
(o texto nunca vai para atributos). `raw` não é escapado de propósito.

## `ascii_to_svg.py`

| Constante | Valor |
|-----------|------:|
| `ASCII_X` | 15 |
| `Y_START` | 30 |
| `LINE_HEIGHT` | 8 |

| Função | Descrição |
|--------|-----------|
| `art_lines(art)` | Divide em linhas e descarta a vazia final (newline do arquivo). |
| `last_y(lines)` | `y` da última linha: `30 + (n − 1) × 8`, ou 0 sem arte. |
| `build_tspans(lines, x)` | Um `<tspan x=… y=…>` por linha, com `rstrip()` e `escape()`. |
| `escape(text)` | Troca U+00A0 por espaço e escapa `&`, `<`, `>`. |

O tamanho de fonte de 6 px vem da classe `.ascii` no CSS do template.
