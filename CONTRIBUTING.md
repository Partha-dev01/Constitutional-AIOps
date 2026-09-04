# Contributing to Constitutional AIOps

Thanks for your interest in improving Constitutional AIOps. This project is
licensed under the [AGPL-3.0](LICENSE); by contributing you agree that your
contributions are licensed under the same terms.

Please also read the [Code of Conduct](CODE_OF_CONDUCT.md). For anything that
looks like a security issue, do not open a public issue. Follow
[SECURITY.md](SECURITY.md) instead.

## Ways to contribute

- Report a bug or a rough edge (see below).
- Improve the docs, including the in-app guide and `docs/`.
- Fix a bug or add a small, self-contained feature.
- Discuss a larger change in an issue first, so the design is agreed before code.

For anything beyond a small fix, open an issue before you start. It saves you
from building something that then needs a rethink in review.

## Development setup

The recommended stack is the **lite** profile: backend plus frontend plus your
own OpenAI-compatible LLM endpoint. No GPU, no bundled models, no Neo4j. The full
guide is in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Backend (Python 3.11+)

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # set your LLM endpoint + key
```

### Frontend (Node 18+)

```bash
cd frontend
npm install
```

### Run it with Docker

```bash
cp .env.example .env
docker compose -f docker/docker-compose.lite.yml --env-file .env --profile edge up -d --build
```

## Before you open a pull request

Keep the gates green. A change is not ready until these pass:

```bash
# Backend
pytest -q
black --check src/ && isort --check-only src/

# Frontend (from frontend/)
npm run build
npm run lint
```

Guidelines that make review quick:

- **Keep pull requests small and focused.** One logical change per PR.
- **Add or update tests** for behavior you change. New backend routes and helpers
  should ship with unit tests; see `tests/` for the direct-call style used here
  (routes are tested by calling the async functions, not by importing the whole
  app).
- **Match the surrounding code.** Python is `snake_case`, React components are
  `PascalCase`, and the TypeScript is strict, so avoid `any`.
- **Do not add new runtime dependencies** without discussing it first. Much of the
  project deliberately uses only the standard library plus what is already pinned.
- **Never commit secrets or personal data** (`.env`, API keys, tokens, private
  infrastructure identifiers). The history is meant to be publishable.
- **Write a clear PR description**: what changed, why, and how you verified it.

## Reporting bugs

Open an issue with:

- What you did and what you expected.
- What actually happened, with the exact error text or a screenshot.
- Your deployment profile (lite / full), and the model endpoint type if relevant.

Thanks again. Small, well-tested contributions are the easiest to accept.
