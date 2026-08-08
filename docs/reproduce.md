# Reproducing the Phase 0 verification

All commands assume PowerShell or Git Bash on Windows, from the project
root (`C:\Users\Filip\Downloads\PDF_TO_MD`), Python 3.11+, and `git` on
PATH. Commands are given for Git Bash (`./.venv/Scripts/python.exe`); on
Linux/macOS use `.venv/bin/python` / `.venv/bin/activate` instead.

## 1. Environment setup

```bash
python3 -m venv .venv
./.venv/Scripts/python.exe -m pip install --upgrade pip
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

## 2. Fetch the source corpus (gitignored, local only)

```bash
./.venv/Scripts/python.exe scripts/fetch_corpus.py
# -> clones/updates https://github.com/geacc/enade.git (branch master)
#    into data/raw/geacc-enade, prints the exact commit SHA fetched.
```

## 3. Environment check

```bash
./.venv/Scripts/python.exe -m enade.cli doctor
# or, after `pip install -e .`, simply: enade doctor
```

## 4. Build the inventory manifest

```bash
./.venv/Scripts/python.exe -m enade.cli inventory
# writes data/manifests/source-exams.yaml
# prints a summary and compares it against the previously-observed
# corpus shape (see docs/corpus.md), calling out any divergence.
```

## 5. Validate the manifest

```bash
./.venv/Scripts/python.exe -m enade.cli validate-manifest --corpus-root data/raw/geacc-enade
# --corpus-root is optional; without it, only internal manifest
# consistency is checked (not filesystem drift).
```

## 6. Validate the data-contract fixtures + demo taxonomy

```bash
./.venv/Scripts/python.exe -m enade.cli validate-schema
```

## 7. Export JSON Schemas (only needed after editing a model)

```bash
./.venv/Scripts/python.exe scripts/export_schemas.py
```

## 8. Run the full verification suite

```bash
./.venv/Scripts/python.exe -m pytest tests/ -v
./.venv/Scripts/python.exe -m ruff check .
./.venv/Scripts/python.exe -m ruff format --check .
./.venv/Scripts/python.exe -m mypy src
```

Expected result at the time this phase was completed: 96 tests passing,
zero ruff findings, zero mypy findings, and an inventory/validate-manifest
run against the pinned corpus commit
(`a657632b72b97468c8a5eb3b433d1abb4a5511c5`) reporting 0 errors / 0
warnings and an exact match against the previously-observed corpus shape.

## Determinism check (manual)

```bash
./.venv/Scripts/python.exe -m enade.cli inventory --output /tmp/run1.yaml
./.venv/Scripts/python.exe -m enade.cli inventory --output /tmp/run2.yaml
diff <(grep -v generated_at /tmp/run1.yaml) <(grep -v generated_at /tmp/run2.yaml)
# expected: no differences other than generated_at itself
```

(`tests/test_scanner.py::test_scanner_is_deterministic` automates the same
check with `manifest_to_yaml_dict(..., include_generated_at=False)`.)
