.PHONY: svg help
all: help
SHELL=bash

# Absolutely awesome: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

svg: ## regenera o bloco ASCII dos SVGs a partir de dark_mode.txt / light_mode.txt
	python3 cli/ascii_to_svg.py $(MODE)
