# Data contracts

All contracts are Pydantic v2 models under [`src/enade/models/`](../src/enade/models/),
each with an exported JSON Schema under [`schemas/`](../schemas/) (regenerate
with `python scripts/export_schemas.py` after any model change). Pydantic is
the source of truth at runtime; the JSON Schema exports exist for
non-Python consumers (e.g. a future web app, editor tooling, or a static
validator).

None of these contracts are populated at corpus scale in Phase 0. They are
exercised only against the small fixtures in
[`tests/fixtures/`](../tests/fixtures/), on purpose (see
[decisions.md](decisions.md)).

## Question (`src/enade/models/question.py`)

The canonical, courseless-of-any-one-PDF representation of a single ENADE
question. Every field either has real, known data, or an explicit
`pending`/`unknown`/`null` state - nothing is a placeholder value dressed
up as real data.

| field | type | notes |
|---|---|---|
| `id` | `str` (kebab-case) | Stable id, unique across the corpus. See "ID convention" below. |
| `exam_year` | `int` | |
| `source_occurrences` | `list[SourceOccurrence]`, >= 1 | Where this question physically appears; see "Source occurrences" below. |
| `applicable_courses` | `list[CourseCode]`, >= 1 | **List**, not a single course - see the 2011 case in [corpus.md](corpus.md). `all-computing` is a course-count alias and must appear alone if used. |
| `section` | `str` (kebab-case) | e.g. `componente-especifico-comum`, free-form but slug-shaped; see the vocabulary observed for 2011 in corpus.md. |
| `question_number` | `int` | Number as printed in the *first* source occurrence's booklet. |
| `question_type` | `multiple_choice \| discursive \| perception_survey` | Perception-survey questions exist (2011's "Questionario de percepcao") and are explicitly not scored - modeled, not extracted, in Phase 0. |
| `statement` | `str` | Question text. Authored in the Markdown body, not front matter - see [markdown-format.md](markdown-format.md). |
| `alternatives` | `list[Alternative]` | Required (>= 2, unique letters) for `multiple_choice`; must be empty otherwise. |
| `correct_answer` | `str \| None` (`A`-`E`) | Must reference a declared alternative; required when `answer_validation_status = validated`. |
| `official_answer_source` | `str \| None` | Pointer (e.g. gabarito path) backing `correct_answer`. |
| `answer_validation_status` | enum | `pending \| validated \| annulled \| conflicting_sources \| not_applicable \| unknown`. `annulled` exists because real ENADE gabaritos contain `ANULADA` entries (see 2011). `not_applicable` is for discursive/perception questions. |
| `assets` | `list[Asset]` | Visual elements the question depends on - see below. |
| `subjects` / `topics` / `concepts` / `keywords` / `competencies` / `prerequisites` | `list[str]` | Taxonomy references (ids), all optional/empty in Phase 0. |
| `difficulty` | `easy \| medium \| hard \| None` | Never invented; `None` unless a real source exists. |
| `alternative_diagnostics` | `dict[letter, AlternativeDiagnostic]` | Wrong-answer -> misconception mapping; keys must be declared, non-correct alternatives. |
| `extraction_method` | enum | `manual \| text_layer \| ocr \| hybrid \| unknown \| pending`. |
| `ocr_confidence` | `float \| None` (0-1) | Only settable when `extraction_method` is `ocr`/`hybrid`. |
| `extraction_status` | enum | `pending \| extracted \| needs_review \| verified`. |
| `taxonomy_review_status` | enum | `pending \| draft \| reviewed`. |

Validated invariants (see the `@model_validator`s in `question.py`, and
their negative-test fixtures in `tests/fixtures/questions/invalid/` +
`tests/test_schema_question.py`):

- `id`/`section` must be kebab-case.
- `all-computing` cannot be combined with an explicit course code.
- `applicable_courses` has no duplicates and is non-empty.
- `multiple_choice` needs >= 2 alternatives with unique letters; other
  question types must have none.
- `correct_answer`, when set, must name a declared alternative letter.
- `answer_validation_status = validated` requires `correct_answer` to be set.
- `ocr_confidence` requires an OCR-involving `extraction_method`.
- `alternative_diagnostics` keys must be declared alternative letters and
  must not be the correct answer.
- Asset ids are unique within a question.

### ID convention

`id` is a stable slug, e.g. `enade-2021-cc-b-q12`. It is **not** derived
automatically by the Phase 0 tooling (no extraction happens yet), but the
convention it must follow going into Phase 1 is:

```
enade-<year>-<course-shorthand>-<section-shorthand>-q<question_number>
```

`<course-shorthand>` should be readable (`cc-b`, `cc-l`, `ec`, `si`, or
`comum`/`geral` for questions applicable to more than one course), not the
raw filename letter, since the id is meant to be human-legible. The
important *hard* constraint - enforced by
[`enade.markdown_format.load_questions_directory`](../src/enade/markdown_format.py)
and tested in `tests/test_markdown_format.py` - is that **ids must be
globally unique**; two files declaring the same id is a hard error.

### Source occurrences and duplicates

`source_occurrences` is a list because the *same* question can be printed
in more than one booklet/year (ENADE reuses some items across editions).
Phase 0 only builds the architecture for this - it does **not** attempt to
detect which occurrences are "the same question" (no text-similarity or
hashing pass). See `tests/fixtures/questions/valid/q-multi-occurrence.md`
for the shape a canonical question with two occurrences takes. Future
phases can use normalized-text hashing, embeddings/similarity, and/or human
review to *merge* what are currently always treated as separate extracted
records into one canonical `Question`.

### Assets (visual elements)

```
assets:
  - id: figure-01
    type: diagram            # image | diagram | graph | table | equation | page_crop
    path: 2021-s-q20/figure-01.png   # relative, portable, no leading '/' or '..'
    source_page: 22
    extraction_method: pending       # manual | raster_crop | vector_export | ocr | unknown | pending
    sha256: null                     # filled once the asset is actually extracted
    alt_text: ...
    caption: ...
```

**Rule this exists to enforce** (not yet automated as a check anywhere,
this is a rule for Phase 1+ tooling to enforce before promoting a question
to `verified`): a question cannot be `extraction_status: verified` if it
visually depends on the source PDF (a figure, graph, table, or equation
required to answer it) and that element is not preserved as an `Asset`
with a real `sha256`.

### Misconceptions / alternative diagnostics

Two related but distinct things:

- `MisconceptionDefinition` (`src/enade/models/misconception.py`): a small,
  reusable catalog entry (e.g. `assumes-tree-is-balanced`). See
  `data/taxonomy/demo-misconceptions.yaml` for a demo catalog.
- `AlternativeDiagnostic`: the link from *one wrong alternative on one
  question* to a `misconception_id` + the concepts it implicates:

```yaml
alternative_diagnostics:
  B:
    misconception_id: assumes-tree-is-balanced
    concepts: [binary-search-tree, complexity]
    explanation: "..."
```

This is the architecture for the future pipeline: wrong answer ->
misconception -> concept -> prerequisite -> material -> new practice
question. Phase 0 does not run this pipeline against the corpus; see
`tests/fixtures/questions/valid/q-with-misconceptions.md` for a fixture
exercising the shape end-to-end.

## Taxonomy (`src/enade/models/taxonomy.py`)

Hierarchical: `Subject -> Topic -> Concept`, where each `Concept` carries
its own `aliases`, `keywords`, and `prerequisites` (ids of other concepts,
anywhere in the taxonomy - not just the same topic). See
[taxonomy.md](taxonomy.md) for the demo instance and why it is explicitly
marked non-definitive.

Validated invariants: all subject/topic/concept ids are unique across the
whole document; every `prerequisites` entry must resolve to a real concept
id elsewhere in the same taxonomy (no dangling references, no
self-reference).

## Material (`src/enade/models/material.py`)

Contract for a future study-material catalog entry (`id`, `title`, `type`,
`url`, `language`, `subjects`/`topics`/`concepts`/`prerequisites`,
`source`, `verification_status`). No real material URLs exist in this
repository yet - the one fixture under `tests/fixtures/materials/valid/`
deliberately sets `url: null` and `source: test-fixture`.

## Manifest / provenance contracts

See [provenance.md](provenance.md) for `PdfProvenance`, `SourceOccurrence`,
and the manifest-level `DocumentRecord`/`ExamBundle`/`SourceManifest`
models in `src/enade/inventory/manifest.py`.
