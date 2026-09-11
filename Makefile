.PHONY: help setup install svg publish
all: help
SHELL := /bin/bash

STAMP := .docker-built
# arquivos que o fluxo reescreve — é só isso que `make publish` commita
GENERATED := panel.yaml dark_mode.svg light_mode.svg cache

# Localmente os scripts rodam no container do serviço `app` do docker-compose.yml
# (o repositório é montado em /app e o .env entra via env_file), então o que eles
# geram cai direto aqui; o --user faz esses arquivos saírem com o seu dono, e não
# como root. No GitHub Actions o setup-python + "Install dependencies" do
# build.yaml já entregam o interpretador com as deps, então `make svg` lá roda o
# python do runner, sem buildar imagem.
ifdef GITHUB_ACTIONS
PYTHON := python
DEPS   :=
else
PYTHON := docker compose run --rm --user $(shell id -u):$(shell id -g) app python3
DEPS   := $(STAMP)
endif

# Absolutely awesome: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-10s\033[0m %s\n", $$1, $$2}'

.env:
	@cp .env.dist .env
	@echo "criei o .env a partir do .env.dist: preencha ACCESS_TOKEN e USER_NAME e rode o make de novo"; exit 1

$(STAMP): cache/requirements.txt devops/Dockerfile
	docker compose build app
	@touch $@

install: $(DEPS) ## builda a imagem Docker com cache/requirements.txt (só refaz se ele ou o Dockerfile mudarem)

svg: $(DEPS) ## apaga e recria os dois SVGs do zero (panel.yaml + dark_mode.txt / light_mode.txt)
	$(PYTHON) cli/build_svg.py

# mesmos passos do build.yaml: stats do GitHub -> panel.yaml -> SVGs; como no CI,
# os SVGs são recriados mesmo se a coleta falhar (e o make sai com o erro dela)
setup: .env install ## build inicial: cria o .env, builda a imagem, busca as stats e gera os SVGs
	@status=0; $(PYTHON) cli/today.py || status=$$?; \
	$(PYTHON) cli/build_svg.py && exit $$status

publish: setup ## fluxo completo do build.yaml + commit dos arquivos gerados (sem push)
	git add -- $(GENERATED)
	@git diff --cached --quiet -- $(GENERATED) \
		&& echo "No changes to commit" \
		|| git commit -m "docs: Updated README" -- $(GENERATED)
