# Architectural decisions

Short ADR-style entries for choices that weren't forced by the brief and
could reasonably have gone another way. Each has the alternative considered
and why it lost. Organized by phase; Phase 1A entries that change a data
contract follow the PROBLEMA -> EXEMPLO NO CORPUS -> LIMITACAO DO MODELO
ATUAL -> ALTERACAO MINIMA -> TESTE DE REGRESSAO structure requested for
schema changes motivated by real corpus evidence.

## Phase 0

## 1. Contract and inventory before extraction

**Decision**: build the manifest + Pydantic contracts first; do not extract
any real question in Phase 0.

**Why**: every downstream feature (grading, diagnosis, recommendations,
the app itself) depends on question records having a trustworthy shape and
provenance. Extracting questions against a schema that isn't validated yet
means re-doing that extraction once the schema inevitably changes. The
manifest is what makes the *scale* of extraction work knowable in advance
(exactly 16 provas, 48 PDFs - not "some unknown number of PDFs we'll
discover as we go").

## 2. Raw corpus lives outside git, fetched by script

**Decision**: `data/raw/geacc-enade/` is a full `git clone` of the source
repo, gitignored, reproduced via `python scripts/fetch_corpus.py`.

**Alternative considered**: commit a snapshot of the PDFs (or a subset)
directly into this repo.

**Why not**: 185 MB of binary PDFs in git history is exactly the kind of
bloat the brief explicitly warns against ("Não adicione PDFs brutos grandes
desnecessariamente ao Git"). Keeping it as a live clone (rather than a
plain directory of downloaded files) also means `git -C data/raw/geacc-enade
rev-parse HEAD` is always available for provenance, with no separate
bookkeeping file that could drift from reality.

## 3. `applicable_courses` is a list with an `all-computing` alias

**Decision**: `Question.applicable_courses: list[CourseCode]`, where
`CourseCode.ALL_COMPUTING` is a valid value that must not be combined with
other explicit course codes.

**Why**: the 2011 unified booklet has questions genuinely shared by all
four courses (see [corpus.md](corpus.md)). Modeling `course: str` would
make that unrepresentable without duplicating the question four times (and
inventing four separate "occurrences" for content that has exactly one
appearance in exactly one PDF). The alias-must-be-alone constraint exists
because `[all-computing, sistemas-de-informacao]` is genuinely ambiguous -
does it mean "all courses" or "all courses, emphasis on SI"? - so it's
rejected outright rather than silently interpreted one way.

## 4. `source_occurrences` list, no deduplication logic

**Decision**: a canonical `Question` can have >= 1 `SourceOccurrence`; the
architecture supports it, but Phase 0 never populates more than one from
real data (it isn't extracting anything) and implements no similarity/
matching logic.

**Why not build the matcher now**: deciding whether two extracted question
texts are "the same question" needs actual extracted text to test against,
and is a genuinely hard problem (near-duplicates with reworded stems,
renumbered alternatives, etc.). Building it against zero real data would
mean designing blind. The fixture
`tests/fixtures/questions/valid/q-multi-occurrence.md` proves the shape
works; the matching logic is deliberately deferred.

## 5. pypdf over a Poppler binary dependency

**Decision**: PDF metadata/text-layer/page-count extraction uses `pypdf`
(pure Python), not `pdftotext`/`pdfinfo` (Poppler, a system binary).

**Why**: this environment happens to have Poppler installed
(`/mingw64/bin/pdftotext`), but that's not guaranteed on every contributor's
machine or in CI. `pypdf` is already a declared Python dependency, ships
via pip, and was sufficient for page count + text extraction + encryption
detection - no need for a second, harder-to-reproduce toolchain. (Poppler's
`pdftotext -layout` *was* used manually, once, to investigate the 2011
booklet's real structure - see [corpus.md](corpus.md) - but no code depends
on it.)

## 6. Hand-rolled minimal PDF builder for tests, no new PDF-writer dependency

**Decision**: `tests/pdf_builder.py` emits minimal valid PDF byte streams
directly (object table + xref) instead of adding `fpdf2`/`reportlab` as a
dev dependency.

**Why**: the only thing tests need is "a PDF with N pages, some with known
text, some blank" to exercise text-layer detection both ways. That's a
small, fully-controlled, dependency-free ~70 line generator, versus a new
transitive dependency graph for a feature (real font layout/rendering)
tests don't need.

## 7. Manifest format: single YAML file, Pydantic-validated on read

**Decision**: `data/manifests/source-exams.yaml`, one file, containing all
bundles/orphans/issues/summary; read back through the same `SourceManifest`
Pydantic model used to write it.

**Alternative considered**: one manifest file per year, or a database
(SQLite).

**Why**: at 16 bundles / 48 documents, a single file is trivially
diffable in a PR and easy to `git blame`. A database would be premature
infrastructure for a corpus this size at this phase, and would fight the
"machine-readable, human-reviewable manifest" requirement.

## 8. Text-layer usability threshold

**Decision**: `has_text_layer = (extracted_chars / page_count) >= 20`
(`pdfmeta.MIN_AVG_CHARS_PER_PAGE_FOR_USABLE_TEXT`).

**Why this number**: it's a deliberately conservative floor meant to
separate "no real text layer" (0 or near-0 chars/page, e.g. a scanned
image) from "has one" - not a claim about extraction *quality*. For this
corpus specifically, every document came back with hundreds to thousands
of chars/page, far above the threshold either way, so the exact cutoff
didn't end up mattering for the 2005-2021 geacc/enade corpus - it matters
for whatever gets scanned next.

## 9. Enums as `StrEnum`

**Decision**: all controlled vocabularies in `src/enade/models/enums.py`
use Python 3.11's `enum.StrEnum` rather than the older `class X(str, Enum)`
idiom.

**Why**: functionally equivalent for our purposes (string-compatible,
JSON-serializes as the plain value), and `ruff` (UP042) flags the older
idiom as outdated on 3.11+. No behavior difference observed in the test
suite.

## 10. Fixture layout: `valid/` and `invalid/` subdirectories

**Decision**: every fixture kind (`questions`, `taxonomy`, `materials`,
`misconceptions`) has both `valid/` and `invalid/` subdirectories.
`enade validate-schema` only walks `valid/`; pytest walks both.

**Why**: without this split, a fixture deliberately designed to fail
validation (needed for negative tests like "duplicate alternative letter is
rejected") would make the CLI's `validate-schema` report a false failure.
Separating them keeps "does the CLI think the golden examples are OK" and
"does the schema correctly reject bad input" as two different questions
with two different answers.

## Phase 1A

### 11. `Question.answer_standard`: a dedicated field for the discursive grading rubric

**PROBLEMA**: the Phase 0 `Question` contract had no field capable of
holding the official grading criteria text for a discursive question,
only `official_answer_source: str | None` - a loose pointer intended for
objective questions (e.g. "this correct_answer came from this gabarito").

**EXEMPLO NO CORPUS**: `data/raw/geacc-enade/2021/b3_padrao.pdf` (the
"padrao de resposta") contains, for each of D1-D5, several paragraphs of
real grading criteria - e.g. for Discursiva 1: *"O respondente deve, a
partir dos argumentos presentes no texto I, refletir sobre as tensões
existentes entre a arte e a cultura no Brasil contemporâneo [...]"*. This
is substantive content with its own provenance (a specific PDF + specific
pages), not just a pointer string.

**LIMITACAO DO MODELO ATUAL**: `official_answer_source: str | None` can
name *which* document the rubric came from, but has nowhere to put the
rubric *text itself*, and no page-level provenance for it (unlike
`SourceOccurrence`, which does carry `pages`). Forcing the rubric into
`official_answer_source` would either truncate it into a single-line
pointer or overload a field documented as "reference", not "content".

**ALTERACAO MINIMA**: added `AnswerStandardReference` (new model in
`src/enade/models/provenance.py`, mirroring `SourceOccurrence`'s shape:
`source_path`, `pdf_sha256`, `pages`, plus `text`) and one new **optional**
field on `Question`: `answer_standard: AnswerStandardReference | None =
None`. `official_answer_source` is untouched. This is purely additive -
every existing fixture and every Phase 0 test still validates unchanged
(confirmed: all 96 Phase 0 tests pass after the change, before any Phase
1A code was written).

Per docs/data-contract.md's existing rule, this content must stay
separated from `statement` at the presentation layer too (see PROMPT
section 21: a future study app must not show the rubric before a student
attempts a discursive question) - `answer_standard` is a sibling field to
`statement`, never concatenated into it, and the Markdown renderer
(`enade.markdown_format`) never prints its contents into the question body.

**TESTE DE REGRESSAO**: `tests/test_schema_question.py` gained new cases
asserting (a) a discursive `Question` can carry a populated
`answer_standard` with its own `pdf_sha256`/`pages`/`text`, (b) existing
fixtures with no `answer_standard` still validate (default `None`), and
(c) the full Phase 0 suite (96 tests) plus all Phase 1A tests pass together.
`schemas/question.schema.json` and the new
`schemas/answer-standard-reference.schema.json` were regenerated via
`scripts/export_schemas.py`.
