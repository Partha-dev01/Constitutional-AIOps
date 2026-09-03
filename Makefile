# Constitutional AIOps - lite self-host convenience targets.
#
# These wrap the canonical lite command so a self-hoster runs one short verb.
# The raw `docker compose ... --env-file .env ...` command stays the portable
# fallback (see docs/DEPLOYMENT.md section 1) for hosts without `make`, e.g.
# Windows.
#
# --env-file .env is REQUIRED: Compose reads the interpolation .env from the
# compose file's own directory (docker/), not the repo root, so a bare
# `-f docker/docker-compose.lite.yml` invocation does not auto-load the root
# .env. (A flagless bare `docker compose up` was considered and rejected: it
# would need a root compose.yaml, which Compose's default-file discovery
# prefers over the existing full-stack docker-compose.yml and would hijack it.)

COMPOSE ?= docker compose
LITE := $(COMPOSE) -f docker/docker-compose.lite.yml --env-file .env

.PHONY: help lite-up lite-edge lite-build lite-down lite-logs lite-ps

help:               ## List the lite targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

lite-up:            ## Start the lite stack (localhost: :3000 frontend, :8000 backend)
	$(LITE) up -d

lite-edge:          ## Start the lite stack behind Caddy TLS (needs APP_DOMAIN + ACME_EMAIL)
	$(LITE) --profile edge up -d

lite-build:         ## Rebuild images, then start
	$(LITE) up -d --build

lite-down:          ## Stop and remove the lite stack
	$(LITE) down

lite-logs:          ## Follow backend + frontend logs
	$(LITE) logs -f

lite-ps:            ## Show lite container status
	$(LITE) ps
