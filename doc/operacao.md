# Operação

## Requisitos

- Docker + Docker Compose (v2.24 ou mais novo, por causa do `env_file` com
  `required: false`)
- `make`, `git`
- Para a coleta: um token do GitHub (ver [coleta.md](coleta.md#permissões-do-token))

Não é preciso ter Python na máquina: localmente, os scripts rodam no container
(`python:3.12-slim`). As dependências Python (`cache/requirements.txt`:
`python-dateutil`, `requests`, `PyYAML`) são instaladas na imagem.

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
| `make install` | Builda a imagem do serviço `app` (`docker compose build app`). Só refaz quando `cache/requirements.txt` ou `devops/Dockerfile` mudam (arquivo-carimbo `.docker-built`). |
| `make svg` | Recria os dois SVGs a partir do `panel.yaml` e dos `*_mode.txt`. Não acessa a rede e não precisa do `.env`. |
| `make setup` | Garante `.env` e imagem, roda `cli/today.py` e depois `cli/build_svg.py` no container. |
| `make publish` | `setup` + `git add` e `git commit -m "docs: Updated README"` dos arquivos gerados. **Não faz push** (o git roda na máquina, não no container). |

Detalhes:

- **Docker local vs. CI.** Localmente cada script roda com
  `docker compose run --rm --user <uid>:<gid> app python3 ...`: o repositório
  é montado em `/app`, então o que o script gera aparece no diretório local; o
  `--user` faz esses arquivos saírem com o seu usuário como dono, e não root;
  o `.env` chega ao container pelo `env_file` do serviço. Quando
  `GITHUB_ACTIONS` está definida, o Makefile usa o `python` do runner direto,
  sem Docker, porque o workflow já instalou as dependências.
- **Imagem desatualizada.** O `docker compose run` builda a imagem sozinho se
  ela não existir, mas não a atualiza quando o `requirements.txt` muda — é
  para isso que existe o carimbo do `make install`. Para forçar um rebuild:
  `rm .docker-built && make install`.
- **`setup` renderiza mesmo se a coleta falhar**, como o CI, e sai com o
  código de erro da coleta.
- **`publish` só commita os arquivos gerados**: `panel.yaml`,
  `dark_mode.svg`, `light_mode.svg` e `cache/`. Outras alterações do working
  tree ficam de fora. Se nada mudou, imprime `No changes to commit`.

## Docker

`docker-compose.yml` define três serviços sobre a mesma imagem
(`devops/Dockerfile`, `python:3.12-slim` com as dependências). Todos montam o
repositório em `/app` — o que for gerado aparece no diretório local — e leem o
`.env` (no `app` ele é opcional, para o `make svg` rodar sem credenciais). O
`.dockerignore` mantém `.git`, `.venv` e o `.env` fora da imagem; as
credenciais só entram em tempo de execução.

O Makefile usa só o serviço `app`, trocando o comando. Chamando o Compose
direto, sem `--user`, os arquivos gerados saem com root como dono:

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
| `ModuleNotFoundError: yaml` | Rodando o script com o Python da máquina: use `make ...` ou `docker compose run --rm app python3 cli/<script>.py`. |
| `ModuleNotFoundError` depois de mudar o `requirements.txt` | Imagem antiga: `make install` (o carimbo detecta a mudança) ou `rm .docker-built && make install`. |
| `permission denied` ao editar `panel.yaml`, SVGs ou `cache/` | Foram gerados como root por um `docker compose run` sem `--user`. Corrija com `sudo chown -R $(id -u):$(id -g) .` e prefira os alvos do `make`. |
| `unable to get image` / `Cannot connect to the Docker daemon` | Docker parado ou usuário fora do grupo `docker`. |
