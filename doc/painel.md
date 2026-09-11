# Configuração do painel (`panel.yaml` e arte ASCII)

O `panel.yaml` define tudo o que aparece no lado direito dos SVGs e as cores de
cada tema. A arte ASCII do lado esquerdo vem de `<modo>_mode.txt`.

Depois de editar qualquer um desses arquivos, rode `make svg`.

## Chaves de topo

```yaml
header: "rejman@root"     # título da primeira régua
birthday: "1998-08-21"    # YYYY-MM-DD; base da linha "Uptime"
width: 60                 # largura mínima do painel, em colunas
themes: { ... }           # um SVG por tema
sections: [ ... ]         # blocos do painel, de cima para baixo
```

| Chave | Obrigatória | Descrição |
|-------|:---:|-----------|
| `header` | sim | Texto antes da régua tracejada do topo (`rejman@root -————…-—-`). |
| `birthday` | para a coleta | Data `YYYY-MM-DD`. O `today.py` calcula "`X years, Y months, Z days`" a partir dela (com 🎂 no aniversário). Não é usada pelo `build_svg.py`. |
| `width` | não (padrão 60) | Largura **mínima** do alinhamento. Se algum conteúdo for maior, o painel e o canvas crescem automaticamente. |
| `themes` | sim | Mapa `nome → cores`. Precisa ter ao menos um tema. |
| `sections` | não | Lista de seções. |

## Temas

Cada chave em `themes:` gera `<nome>_mode.svg` e exige o arquivo
`<nome>_mode.txt` com a arte ASCII. Hoje existem `dark` e `light`.

```yaml
themes:
  dark:
    background: "#161b22"   # fundo do cartão (retângulo com cantos arredondados)
    text:       "#c9d1d9"   # arte ASCII e texto sem classe (réguas, ':' e '{ }')
    key:        "#ffa657"   # rótulos (classe .key)
    value:      "#a5d6ff"   # valores (classe .value)
    addColor:   "#3fb950"   # linhas adicionadas (classe .addColor)
    delColor:   "#f85149"   # linhas removidas (classe .delColor)
    cc:         "#616e7f"   # pontilhado e o prefixo ". " de cada linha (classe .cc)
```

As sete cores são obrigatórias; faltando alguma, o build aborta com
`error: themes.<modo> in panel.yaml is missing: ...` **sem apagar** os SVGs
existentes.

Para criar um tema novo (ex.: `sepia`), adicione `themes.sepia` com as sete
cores e crie `sepia_mode.txt`. O build passará a gerar `sepia_mode.svg`.

## Seções

Cada item de `sections:` tem:

| Chave | Descrição |
|-------|-----------|
| `title` | Cabeçalho da seção (`- Contact -————…`). `null` = sem cabeçalho (usado na primeira). Uma seção com título ganha uma linha em branco antes. |
| `rows` | Lista de linhas. |
| `fields` | (opcional) Campos com valores vindos do GitHub. Quando presente, as linhas do tipo string viram **templates** (ver abaixo). |

### Tipos de linha em `rows`

Todas as linhas começam com o prefixo `. ` na cor `cc`.

**Chave/valor** — o caso comum:

```yaml
- { key: "OS", value: "Windows 11, Android 16, Linux" }
```

Renderiza `OS:` + pontilhado + valor, com o pontilhado calculado para que todos
os valores terminem na mesma coluna. Um ponto na chave cria subníveis:
`key: "Languages.Programming"` exibe `Languages` e `Programming` como dois
rótulos coloridos ligados por um `.` na cor do texto.

Opcional: `id: <campo>` liga a linha a um campo reescrito pelo `today.py`
(hoje só `age_data`, na linha "Uptime") e adiciona `id="<campo>"` /
`id="<campo>_dots"` aos `<tspan>` do SVG.

**Linha em branco:**

```yaml
- spacer            # ou: - { spacer: true }
```

**SVG cru** (escape hatch, raramente necessário) — o conteúdo é inserido
literalmente depois do prefixo `. `, sem escape:

```yaml
- { raw: '<tspan class="key">Algo</tspan> especial' }
```

**Template de stats** — só em seções com `fields:`; ver a próxima seção.

## Seções com `fields:` (GitHub Stats)

Os valores do GitHub têm alinhamento próprio, que replica o `justify_format`
do projeto original. Por isso a seção "GitHub Stats" usa campos declarados em
`fields:` e linhas escritas como templates.

### Campos

```yaml
fields:
  repo_data:     { value: "46",        length: 6,  dots: true }
  contrib_data:  { value: "46" }
  loc_add:       { value: "3,735,641", class: addColor, suffix: "++" }
  loc_del:       { value: "2,218,088", class: delColor, suffix: "--", length: 7, dots: true, dots_class: "" }
```

| Atributo | Padrão | Descrição |
|----------|--------|-----------|
| `value` | `"0"` | Texto exibido. Reescrito pelo `today.py`. |
| `class` | `value` | Classe CSS do valor (e do sufixo): `value`, `addColor`, `delColor`, `key`, `cc`. |
| `dots` | `false` | Se `true`, insere um pontilhado antes do valor. |
| `length` | `0` | Coluna-alvo do pontilhado: o pontilhado preenche `length - len(value)` posições. |
| `dots_class` | `cc` | Classe do pontilhado. `""` = sem classe (herda a cor `text`). |
| `suffix` | — | Texto logo após o valor, na mesma classe (ex.: `++`, `--`). |

Regra do pontilhado (`stats_dots`), com `just = max(0, length - len(value))`:

| `just` | Saída |
|:---:|-------|
| 0 | *(nada)* |
| 1 | `" "` |
| 2 | `". "` |
| ≥ 3 | `" " + "." * just + " "` |

### Sintaxe dos templates

| Token | Resultado |
|-------|-----------|
| `{k:Texto}` | `Texto` como rótulo colorido (classe `key`) |
| `{Rótulo:campo}` | rótulo + `:` + pontilhado (se `dots`) + valor do `campo` |
| `{campo}` | só o valor do `campo` (com pontilhado se `dots: true`) |

Tokens com campo desconhecido e chaves soltas ficam como texto literal. É isso
que permite `{{k:Contributed}: {contrib_data}}` — o par externo de chaves
aparece no SVG:

```yaml
rows:
  - "{Repos:repo_data} {{k:Contributed}: {contrib_data}}"
  # . Repos: .... 46 {Contributed: 46}
  - "{k:Diff}: {loc_add}, {loc_del}"
  # . Diff: 3,735,641++, 2,218,088--
```

## Campos reescritos automaticamente

`panel_stats.set_values` só pode escrever nestes identificadores
(`WRITABLE_FIELDS`):

| Campo | Onde fica | Origem |
|-------|-----------|--------|
| `age_data` | linha em `rows` com `id: age_data` | idade a partir de `birthday` |
| `repo_data` | `fields` | repositórios próprios (`OWNER`) |
| `contrib_data` | `fields` | repositórios nas afiliações de `LOC_AFFILIATIONS` |
| `star_data` | `fields` | estrelas nos repositórios próprios |
| `commit_data` | `fields` | commits seus, somados do cache |
| `follower_data` | `fields` | seguidores |
| `loc_data` | `fields` | linhas adicionadas − removidas |
| `loc_add` | `fields` | linhas adicionadas |
| `loc_del` | `fields` | linhas removidas |

A reescrita é feita por regex para preservar comentários. **Contrato de
formato** para que ela encontre o alvo:

- a entrada precisa ser um mapa inline **numa única linha** (`{ ... }`);
- o valor precisa estar entre **aspas duplas**: `value: "123"`;
- em `fields:`, a linha começa com o nome do campo: `star_data: { value: "4", ... }`;
- em `rows:`, a linha é `- { ... id: age_data ... }`.

Se algum campo pedido não for encontrado, o script aborta com
`error: no \`value:\` to update for <campo> in panel.yaml` sem gravar nada.

Pode-se mudar livremente rótulos, ordem das linhas, separadores, `length`,
classes e sufixos — só não quebre o formato acima nem renomeie os campos.

## Arte ASCII (`<modo>_mode.txt`)

- Um arquivo por tema, lido como UTF-8.
- Cada linha vira um `<tspan>` de 6 px de fonte, com 8 px entre linhas,
  começando em `x=15, y=30`.
- Espaços à direita são removidos; espaços não quebráveis (U+00A0) viram
  espaços comuns; `&`, `<` e `>` são escapados.
- Uma quebra de linha final no arquivo é ignorada.
- A cor é a `text` do tema. As duas artes atuais têm 59 linhas (última em
  `y=494`); uma arte maior aumenta a altura do canvas automaticamente.

Para trocar a arte, gere o texto (qualquer conversor imagem→ASCII serve),
salve em `dark_mode.txt` / `light_mode.txt` e rode `make svg`. Costuma-se usar
artes com densidade invertida para cada tema, já que no escuro os caracteres
"acendem" sobre o fundo.
