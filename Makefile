.PHONY: help setup install svg publish
all: help
SHELL := /bin/bash

VENV  := .venv
STAMP := $(VENV)/.installed
# arquivos que o fluxo reescreve — é só isso que `make publish` commita
GENERATED := panel.yaml dark_mode.svg light_mode.svg cache

# Localmente tudo roda num venv (o python do sistema recusa `pip install`); no
# GitHub Actions o setup-python + "Install dependencies" do build.yaml já entregam
# o interpretador com as deps, então `make svg` lá não cria venv nenhum.
ifdef GITHUB_ACTIONS
PYTHON := python
DEPS   :=
else
PYTHON := $(VENV)/bin/python
DEPS   := $(STAMP)
endif

# Absolutely awesome: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-10s\033[0m %s\n", $$1, $$2}'

.env:
	@cp .env.dist .env
	@echo "criei o .env a partir do .env.dist: preencha ACCESS_TOKEN e USER_NAME e rode o make de novo"; exit 1

$(STAMP): cache/requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -r cache/requirements.txt
	@touch $@

install: $(DEPS) ## cria o .venv e instala cache/requirements.txt (só refaz se o requirements mudar)

svg: $(DEPS) ## apaga e recria os dois SVGs do zero (panel.yaml + dark_mode.txt / light_mode.txt)
	$(PYTHON) cli/build_svg.py

# mesmos passos do build.yaml: stats do GitHub -> panel.yaml -> SVGs; como no CI,
# os SVGs são recriados mesmo se a coleta falhar (e o make sai com o erro dela)
setup: .env install ## build inicial: cria o .env, instala as deps, busca as stats e gera os SVGs
	@set -a; . ./.env; set +a; \
	status=0; $(PYTHON) cli/today.py || status=$$?; \
	$(PYTHON) cli/build_svg.py && exit $$status

publish: setup ## fluxo completo do build.yaml + commit dos arquivos gerados (sem push)
	git add -- $(GENERATED)
	@git diff --cached --quiet -- $(GENERATED) \
		&& echo "No changes to commit" \
		|| git commit -m "docs: Updated README" -- $(GENERATED)
