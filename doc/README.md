# Documentação — `rejmann/rejmann`

Repositório de perfil do GitHub. O `README.md` da raiz exibe um cartão em SVG
(estilo *neofetch*: arte ASCII à esquerda, painel de informações à direita) que
é regenerado automaticamente todo dia com estatísticas reais da conta no GitHub.

```
panel.yaml ─┐                                   ┌─> dark_mode.svg
            ├─> cli/build_svg.py ───────────────┤
*_mode.txt ─┘        ▲                          └─> light_mode.svg
                     │
GitHub GraphQL ─> cli/today.py ─> panel.yaml (reescreve os números)
```

## Índice

| Documento | Conteúdo |
|-----------|----------|
| [arquitetura.md](arquitetura.md) | Visão geral, fluxo de dados, papel de cada arquivo e decisões de projeto |
| [painel.md](painel.md) | Referência completa do `panel.yaml` e da arte ASCII (`*_mode.txt`) |
| [renderizacao.md](renderizacao.md) | Como os SVGs são montados: geometria, alinhamento, temas (`build_svg.py`, `panel_to_svg.py`, `ascii_to_svg.py`) |
| [coleta.md](coleta.md) | Coleta de estatísticas no GitHub, cache de linhas de código e escrita no YAML (`today.py`, `fetch_stats.py`, `panel_stats.py`) |
| [operacao.md](operacao.md) | Uso no dia a dia: Makefile, Docker, GitHub Actions, variáveis de ambiente e solução de problemas |

## Início rápido

```bash
make setup      # cria o .env (1ª vez), builda a imagem Docker, busca stats e gera os SVGs
make svg        # só regenera os SVGs a partir do panel.yaml (não acessa a rede)
make publish    # setup + commit dos arquivos gerados (não faz push)
make help       # lista os alvos
```

Na primeira execução o `make setup` copia `.env.dist` para `.env` e para;
preencha `ACCESS_TOKEN` e `USER_NAME` e rode de novo. Detalhes em
[operacao.md](operacao.md).

## Regras de ouro

1. **`panel.yaml` é a fonte da verdade.** Os SVGs são saída de build — nunca
   edite `dark_mode.svg` / `light_mode.svg` à mão; a próxima geração descarta.
2. **Conflito de merge nos SVGs?** Resolva o `panel.yaml` e rode `make svg`.
3. **Os números do GitHub são sobrescritos.** Os `value:` dos campos em
   `fields:` e da linha `Uptime` são reescritos pelo `today.py`; o resto do
   `panel.yaml` é editado à mão.

## Estrutura do repositório

```
.
├── README.md                 # perfil exibido no GitHub (usa os SVGs via raw.githubusercontent)
├── panel.yaml                # conteúdo do painel + cores dos temas
├── dark_mode.txt             # arte ASCII do tema escuro
├── light_mode.txt            # arte ASCII do tema claro
├── dark_mode.svg             # GERADO
├── light_mode.svg            # GERADO
├── cli/
│   ├── today.py              # coleta no GitHub → panel.yaml → SVGs (entrada do CI)
│   ├── fetch_stats.py        # mesma coleta, ponto de entrada manual (--no-render)
│   ├── panel_stats.py        # escreve valores no panel.yaml e dispara a renderização
│   ├── build_svg.py          # monta e grava os dois SVGs
│   ├── panel_to_svg.py       # markup do painel (lado direito)
│   └── ascii_to_svg.py       # markup da arte ASCII (lado esquerdo)
├── cache/
│   ├── requirements.txt      # dependências Python
│   └── <sha256>.txt          # cache de LOC/commits por repositório (GERADO)
├── Makefile                  # install / svg / setup / publish
├── .env.dist                 # modelo do .env (ACCESS_TOKEN, USER_NAME)
├── docker-compose.yml        # serviços app / fetch / debug (o Makefile usa o app)
├── .dockerignore             # mantém .git, .venv e .env fora da imagem
├── devops/Dockerfile         # imagem python:3.12-slim com as deps
├── .github/workflows/build.yaml  # CI diário que atualiza e commita os SVGs
└── doc/                      # esta documentação
```

## Limitações conhecidas

Pontos encontrados na leitura do código que valem ter em mente (nenhum quebra
o fluxo atual):

- **`add_archive()` nunca roda para esta conta.** O `today.py` e o
  `fetch_stats.py` só somam repositórios arquivados quando o ID do dono é
  `MDQ6VXNlcjU3MzMxMTM0` (`04:User57331134`), herdado do projeto original. O ID
  de `rejmann` é `MDQ6VXNlcjcyMDk3NzI3`. Além disso,
  `cache/repository_archive.txt` não existe — se o ID algum dia batesse, a
  execução quebraria com `FileNotFoundError`.
- **Estrelas contam só os 100 primeiros repositórios.** `graph_repos_stars`
  pede `first: 100` e não pagina; para `stars`, repositórios além do 100º são
  ignorados. (Para `repos` o `totalCount` já é o total real.)
- **Default mutável em `loc_query(..., edges=[])`.** A lista acumula entre
  chamadas no mesmo processo. Hoje `loc_query` é chamado uma vez por execução,
  então não há efeito.
- **Resumo de tempo no terminal do `today.py`.** A linha "Total function time"
  sobe o cursor 8 linhas com ANSI para sobrescrever "Calculation times:", mas
  a saída hoje tem mais linhas que isso (logs do scan e da renderização), então
  ela cai no lugar errado. O total também não inclui o tempo de
  `follower_getter`. Puramente cosmético.
