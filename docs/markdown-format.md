# Per-question Markdown format

Implemented and round-trip tested in
[`src/enade/markdown_format.py`](../src/enade/markdown_format.py) (see
`tests/test_markdown_format.py`). This is the format future extraction
tooling should write, and the format `enade validate-schema` checks.

## Design

YAML front matter carries **every `Question` field except `statement` and
`alternatives`**. Those two are authored as plain Markdown in the body,
because that's what a human editor (or reviewer) actually wants to read and
diff - not two more YAML strings/lists. A loader reassembles the two halves
into one validated `Question`; a renderer does the inverse (used to prove
the round-trip in tests).

```markdown
---
id: enade-2021-cc-b-q12
exam_year: 2021
source_occurrences:
  - exam_id: enade-2021-b
    pdf_sha256: <64-hex-char sha256 of the exact PDF>
    source_path: 2021/b1_prova.pdf
    pages: [14]
    question_number: 12
    section: componente-especifico
applicable_courses:
  - ciencia-da-computacao-bacharelado
section: componente-especifico
question_number: 12
question_type: multiple_choice
correct_answer: null
official_answer_source: null
answer_validation_status: pending
assets: []
subjects: [estruturas-de-dados]
topics: [arvores]
concepts: [arvore-binaria]
keywords: [arvore, percurso]
competencies: []
prerequisites: []
difficulty: null
alternative_diagnostics: {}
extraction_method: pending
ocr_confidence: null
extraction_status: pending
taxonomy_review_status: pending
---

# Questão 12

<statement text goes here, one or more paragraphs>

## Alternativas

A. <text of alternative A>
B. <text of alternative B>
C. <text of alternative C>
D. <text of alternative D>
E. <text of alternative E>
```

Rules the parser enforces (`enade.markdown_format.parse_question_markdown`):

- The file must start with `---`, and the front matter must be closed with
  a second `---` - otherwise it raises `MarkdownFormatError` rather than
  guessing.
- `statement` and `alternatives` must **not** appear in the front matter -
  that would create two conflicting sources of truth for the same field.
- The first non-blank body line may be a `# Questão N` heading (purely
  informational for a human reader); everything up to (but not including)
  a `## Alternativas` heading is the `statement`.
- Under `## Alternativas`, lines matching `<A-E>. text` or `<A-E>) text`
  start a new alternative; continuation lines (no leading letter) are
  appended to the current alternative's text. This only runs for
  `multiple_choice` questions - discursive/perception questions simply omit
  the `## Alternativas` section, and the body is the statement in full (see
  `tests/fixtures/questions/valid/q-discursive.md`).

Once assembled, the merged data is validated against the full `Question`
Pydantic model - so a Markdown file that violates any contract invariant
(e.g. duplicate alternative letters, `all-computing` combined with another
course) fails the same way a directly-constructed `Question(...)` would.

## Images

Referenced through the `assets` list in front matter (see
[data-contract.md](data-contract.md), "Assets"), with **relative, portable**
paths (no leading `/`, no `..` segments) - e.g.
`2021-s-q20/figure-01.png`, resolved relative to
`data/assets/questions/<question-id>/`. No image files are committed by
Phase 0; only the contract and a couple of small fixtures exist.

## Duplicate ids

`enade.markdown_format.load_questions_directory(dir)` loads every `*.md` in
a directory and raises if two files declare the same `id`. This is the
mechanism `tests/test_markdown_format.py::test_load_questions_directory_detects_duplicate_id`
exercises (fixtures in `tests/fixtures/questions/duplicate_id/`), and the
mechanism any future bulk-loading code should reuse rather than
reimplementing duplicate detection.
