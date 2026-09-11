# Operação

## Requisitos

- Python 3 com `venv` (o CI usa 3.12)
- `make`, `git`
- Opcional: Docker + Docker Compose
- Para a coleta: um token do GitHub (ver [coleta.md](coleta.md#permissões-do-token))

Dependências Python (`cache/requirements.txt`): `python-dateutil`, `requests`,
`PyYAML`.

## Configuração local

```bash
make setup
# criei o .env a partir do .env.dist: preencha ACCESS_TOKEN e USER_NAME e rode o make de novo
```

Edite o `.env` (está no `.gitignore`):

```dotenv
ACCESS_TOKEN=github_pat_...
USER_NAME=rejmann
```

Opcionalmente, acrescente `LOC_AFFILIATIONS=OWNER` para uma execução bem mais
rápida só com os seus repositórios (usa um arquivo de cache separado), ou
`HTTP_TIMEOUT=60`.

## Makefile

| Alvo | Faz |
|------|-----|
| `make` / `make help` | Lista os alvos (auto-documentados pelos comentários `##`). |
| `make install` | Cria o `.venv` e instala as dependências. Só refaz quando `cache/requirements.txt` muda (arquivo-carimbo `.venv/.installed`). |
| `make svg` | Recria os dois SVGs a partir do `panel.yaml` e dos `*_mode.txt`. Não acessa a rede. |
| `make setup` | Garante `.env` e deps, carrega o `.env`, roda `cli/today.py` e depois `cli/build_svg.py`. |
| `make publish` | `setup` + `git add` e `git commit -m "docs: Updated README"` dos arquivos gerados. **Não faz push.** |

Detalhes:

- **Venv local vs. CI.** Localmente o Python usado é `.venv/bin/python` (o
  Python do sistema costuma recusar `pip install`). Quando `GITHUB_ACTIONS`
  está definida, o Makefile usa `python` direto, sem venv, porque o workflow
  já instalou as dependências.
- **`setup` renderiza mesmo se a coleta falhar**, como o CI, e sai com o
  código de erro da coleta.
- **`publish` só commita os arquivos gerados**: `panel.yaml`,
  `dark_mode.svg`, `light_mode.svg` e `cache/`. Outras alterações do working
  tree ficam de fora. Se nada mudou, imprime `No changes to commit`.

## Docker

`docker-compose.yml` define três serviços sobre a mesma imagem
(`devops/Dockerfile`, `python:3.12-slim` com as dependências). Todos montam o
repositório em `/app` — o que for gerado aparece no diretório local — e leem o
`.env`.

| Serviço | Comando |
|---------|---------|
| `app` | `python3 cli/today.py` |
| `fetch` | `python3 cli/fetch_stats.py` |
| `debug` | `bash` interativo |

```bash
docker compose run --rm app      # coleta completa + SVGs
docker compose run --rm fetch    # idem, pelo fetch_stats.py
docker compose run --rm debug    # shell no container
```

## GitHub Actions — `.github/workflows/build.yaml`

**Gatilhos:** push em `main` e diariamente às 06:00 UTC (03:00 em São Paulo).

**Job `build`** (`ubuntu-latest`, timeout de 10 minutos, permissão
`contents: write`):

1. Checkout (`fetch-depth: 1`).
2. Python 3.12 com cache de pip baseado em `cache/requirements.txt`.
3. `pip install -r cache/requirements.txt`.
4. **Update README file** — `python cli/today.py` com os secrets
   `ACCESS_TOKEN` e `USER_NAME`.
5. **Render SVGs** — `make svg`, com `if: !cancelled()`: roda mesmo se o passo
   anterior falhar, para que mudanças de layout sempre cheguem aos SVGs.
6. **Commit** — `git add .`, commit `docs: Updated README` como
   `Rejman/GitHub-Actions-Bot` e `git push`. Sem mudanças, imprime
   `No changes to commit`.

O `today.py` já renderiza no fim; o `make svg` seguinte é redundante no caso
de sucesso e existe para cobrir o caso de falha.

### Secrets necessários

Em *Settings → Secrets and variables → Actions*:

- `ACCESS_TOKEN` — o token fine-grained
- `USER_NAME` — `rejmann`

## Tarefas comuns

**Mudar um texto do painel** (ex.: IDE, linguagens): edite o `panel.yaml` →
`make svg` → commit do YAML e dos SVGs.

**Adicionar uma linha:** acrescente `- { key: "Nova", value: "..." }` em
`rows:`. O alinhamento se ajusta sozinho; se a linha for longa, o canvas
alarga.

**Mudar cores:** edite `themes.dark` / `themes.light` → `make svg`.

**Trocar a arte ASCII:** substitua `dark_mode.txt` / `light_mode.txt` →
`make svg`.

**Atualizar os números agora:** `make setup` (ou `make publish` para já
commitar), ou dispare o workflow com um push em `main`.

**Validar só o layout, sem rede:** `make svg` e abra os SVGs no navegador.

**Resolver conflito de merge nos SVGs:** resolva o `panel.yaml` (se houver
conflito nele), aceite qualquer versão dos SVGs e rode `make svg`.

## Solução de problemas

| Sintoma | Causa provável / solução |
|---------|--------------------------|
| `criei o .env a partir do .env.dist...` | Primeira execução: preencha o `.env`. |
| `RuntimeError: Missing required environment variables` | `ACCESS_TOKEN`/`USER_NAME` não definidos (fora do `make`, exporte-os ou use `set -a; . ./.env; set +a`). |
| `... has failed with a 401` | Token inválido ou expirado. |
| `Too many requests in a short amount of time!` | Limite anti-abuso (403) durante o scan de LOC. O progresso já foi salvo no cache; espere e rode de novo. |
| Execução "parada" por minutos | Scan de LOC sem cache; acompanhe as linhas `owner/repo: N of my commits to scan`. Para testar rápido, use `LOC_AFFILIATIONS=OWNER`. |
| `error: themes.<modo> in panel.yaml is missing: ...` | Falta alguma das 7 cores do tema. Os SVGs antigos foram preservados. |
| `error: no \`value:\` to update for <campo>` | A entrada do campo no `panel.yaml` saiu do formato esperado (mapa inline de uma linha, valor entre aspas duplas). Ver [painel.md](painel.md#campos-reescritos-automaticamente). |
| `FileNotFoundError: ... <modo>_mode.txt` | Tema declarado em `themes:` sem o arquivo de arte correspondente. |
| `ModuleNotFoundError: yaml` | Rodando fora do venv: use `make ...` ou `.venv/bin/python`. |
