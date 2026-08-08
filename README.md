# ENADE Study Platform — Phase 0: Foundation

Open-source platform for studying with real **ENADE** (Exame Nacional de
Desempenho dos Estudantes) exam questions, initially scoped to the
Computing area (Ciência da Computação, Engenharia da Computação, Sistemas
de Informação).

This repository is currently in **Phase 0 — Foundation, Corpus Inventory
and Data Contract**. It does **not** yet contain a web/PWA application, an
LLM integration, or a fully extracted question bank. It contains the
auditable groundwork everything else will be built on: a reproducible way
to fetch the source corpus, an automated inventory of what that corpus
actually contains, and the canonical data contracts (question, assets,
taxonomy, misconceptions, materials) that every future extraction must
conform to.

See [docs/overview.md](docs/overview.md) for the full picture, and
[docs/reproduce.md](docs/reproduce.md) to reproduce the inventory and
verification steps yourself.

## Quick start

```bash
python3 -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on Linux/macOS
pip install -e ".[dev]"

python scripts/fetch_corpus.py     # clone/update the source corpus (data/raw/, gitignored)
enade doctor                       # check the environment
enade inventory                    # inventory the corpus -> data/manifests/source-exams.yaml
enade validate-manifest            # audit the manifest for inconsistencies
enade validate-schema              # validate fixtures against the canonical data contracts

pytest
ruff check .
mypy src
```

## Documentation index

- [docs/overview.md](docs/overview.md) — project vision and phase scope
- [docs/corpus.md](docs/corpus.md) — source corpus, provenance, 2011 special case
- [docs/data-contract.md](docs/data-contract.md) — canonical question/asset/taxonomy contracts
- [docs/provenance.md](docs/provenance.md) — provenance policy
- [docs/markdown-format.md](docs/markdown-format.md) — future per-question Markdown format
- [docs/taxonomy.md](docs/taxonomy.md) — taxonomy model and demo fixture
- [docs/decisions.md](docs/decisions.md) — architectural decisions log
- [docs/reproduce.md](docs/reproduce.md) — exact reproduction commands

## License

The code in this repository is MIT licensed (see [LICENSE](LICENSE)). The
**source exam PDFs themselves are not covered by this license** — see
[docs/corpus.md](docs/corpus.md) for the licensing note on official INEP
exam content.
