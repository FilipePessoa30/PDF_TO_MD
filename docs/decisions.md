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

## Phase 1C

### 12. `Question.content_blocks`: optional ordered representation for mixed prose/table/code content

**PROBLEMA**: `statement` is one flat string. For 38 of this corpus's 40
questions that is sufficient - inline Markdown (`![...]()` for figures,
` ```...``` ` for a code listing) already preserves reading order within a
single string, and every question that mixes text with a figure or a code
block already renders and round-trips correctly this way. It stops being
sufficient for exactly the content shape D3 and D5 have: a *table* with no
native Markdown-fenced representation in the extractor at all (so its text
collapsed into unordered prose - see EXEMPLO below), and, for D5, a
two-column layout where the code column's reading order was computed
wrong (a bug in `layout.py`'s column classification, not a schema gap).

**EXEMPLO NO CORPUS**: D3 (`data/raw/geacc-enade/2021/b1_prova.pdf`, page
14) has a 6-formula x 4-row truth table with no vector-drawn grid lines.
Read in raw token order it produces `"a -> not b b ^ a ... F F V F V F
..."` - a real, confirmed content-fidelity failure, not a hypothetical one.

**LIMITACAO DO MODELO ATUAL**: `assembler.py`'s `StatementSegment` union
(`TextSegment | CodeSegment | FigureSegment`) has no table variant, so a
detected table region has only two possible outcomes: fall into
`TextSegment` (D3's actual bug) or `FigureSegment` (loses searchable
text/accessibility entirely). Neither is correct.

**ALTERACAO MINIMA CONSIDERADA E REJEITADA**: a wholesale ordered
"content_blocks first" rendering pipeline, replacing `statement` as the
body's source of truth for every question. Rejected: it would touch all 40
files' rendering path to fix a shape that only 2 of them have, and
`statement` (with inline Markdown) already correctly handles the
text+figure+code ordering case - only *tables* were missing a segment
type. Migrating everything to re-derive risked regressing the 37 already
`verified` questions for no corpus-evidenced benefit (PROMPT section 12:
"nenhum arquivo anteriormente verificado pode mudar silenciosamente").

**ALTERACAO MINIMA**: (1) added `TableSegment` to `assembler.py`'s segment
union, populated by a new geometric table detector
(`extraction/tables.py`) that clusters `get_text("words")` tokens by Y then
X - never by the logical/mathematical meaning of a cell. `statement`
rendering gained one case: a `TableSegment` renders as a real Markdown
table when `validation_status == verified`, otherwise as a short notice
plus the mandatory visual-fallback asset reference (PROMPT section 5.2)
- so the existing single-string `statement` body remains the ordered,
human-readable "corpo Markdown canônico ordenado" the prompt itself names
as an acceptable answer to section 4's investigation. (2) added
`content_blocks: list[ContentBlock] | None = None` to `Question`
(`models/content_block.py`) as a **strictly additive**, mechanically
derived projection of the same segments already computed for
`statement` - populated only for a question whose extracted content
actually contains a `TableSegment` or `CodeSegment` (a content-shape rule,
not a hardcoded question id list; it will apply unprompted to whichever
2011/future questions have the same shape). It is never the only source of
truth: round-trips through YAML front matter exactly like `assets` already
does, no re-parsing of rendered Markdown involved. The 38 unaffected
questions' Markdown files are byte-identical after this change (confirmed
- see the Phase 1C non-regression diff).

**TESTE DE REGRESSAO**: `tests/test_extraction_tables.py` (geometric
clustering: header/data rows, ragged rows, non-rectangular region ->
conservative failure, never inventing a missing cell),
`tests/test_schema_content_block.py` (round-trip, discriminated union,
undeclared-asset-id rejection, non-verified `TableBlock` without a visual
fallback asset rejection), and the Phase 1C pipeline-integration diff
against the pre-1C gold manifest confirming zero unexpected byte
differences across the 37 previously-verified questions.

### 13. D5: three compounding region-segmentation bugs on a genuine two-column page

**PROBLEMA**: D5's page (17) is a real two-column layout - a tree/array
diagram in the left column, the complete `heapify`/`buildHeap` C listing in
the right column, at overlapping Y-ranges. The pre-Phase-1C statement was
severely broken: missing opening paragraph, missing almost the entire
`heapify()` body, wrong/inflated code indentation.

**EXEMPLO NO CORPUS**: this is the only two-column, figure-plus-code page
in the 2021 CC bacharelado booklet - a genuinely rare shape, but not
unique to D5 by construction (any future 2011/other-course page with a
diagram beside a code listing has the same shape).

**LIMITACAO DO MODELO ATUAL (causas, todas geométricas)**: (1)
`figures.py`'s label-absorption candidate list never excluded monospace
lines, so individual code lines got absorbed into the diagram region's
bbox, growing it ~110pt into the code column. (2) `assembler.py`'s
`_line_in_region` tested only Y-overlap against a region's bbox, never
X-overlap, so even after fixing (1) it still treated same-Y-band code in
the *other* column as "inside" the (correctly-sized) diagram region. (3)
`MAX_LABEL_LINE_WIDTH` (300pt) was calibrated for single-column body text
(~500pt wide); a two-column page's own column is only ~245pt wide, so
*every* prose line there - including a paragraph's own first line - looked
"label-width" and was absorption-eligible.

**ALTERACAO MINIMA**: (1) exclude `Line.is_monospace` lines from
`figures.py`'s label candidates - code is its own content class, never a
diagram annotation. (2) require real horizontal overlap (not just Y) in
`_line_in_region`, with a small `REGION_X_PADDING` (5pt, well under any
observed inter-column gutter). (3) reuse `layout.detect_column_margins`
(promoted from private to public, since two call sites now need it) to
protect genuine two-column body text - a line starting flush with either
detected column margin - from absorption, regardless of its own width.
(4) `assembler._render_code_lines` now detects and preserves genuine blank
lines within a code listing from the run's own modal line pitch (a gap of
~2x the modal pitch is exactly one blank line), rather than collapsing
every line together.

All four are content-shape rules keyed on geometry (monospace-ness,
X-overlap, column margins, line pitch), none reference D5's question id.

**TESTE DE REGRESSAO**: `test_extraction_figures.py` (`_is_two_column_body_text`),
`test_extraction_assembler.py` (`_line_in_region` X-overlap,
`_render_code_lines` blank-line preservation), and
`test_extraction_pipeline_integration.py`'s D5-specific tests asserting
every real construct in the heapify/buildHeap listing survives, in order,
with the genuine blank line intact, and that the opening paragraph is no
longer swallowed. Confirmed zero regression across the other 39 questions
via the same pre/post-1C gold diff as ADR 12.

### 14. Q20: geometric line-number gutter removal; `l`/`1` resolved by glyph-width evidence

**PROBLEMA**: Q20's printed line-number gutter ("1".."26") leaked into the
code (`"\t11 \t int funcao2(...)"`), and a `return funcao2(vetor, v, m+l,
f);` line carried a character that reads as either `l` or `1` depending on
the font.

**LIMITACAO/CAUSA**: for 25 of 26 rows, PyMuPDF already emits the gutter
number as its own `Line`, already correctly stripped by chrome.py's
existing bare-1-3-digit rule. For exactly row 11, PyMuPDF instead fused
the gutter number into the *same* line as the code, which chrome.py's
whole-line check cannot catch (the merged line is not purely numeric).

**ALTERACAO MINIMA**: `assembler._strip_line_number_gutter` drops a
purely-numeric gutter line outright, and for a merged line strips a
leading `[whitespace]*digits[whitespace]+` prefix - a shape no real C
statement has - then reconstructs the remainder's indentation from the
run's *other*, unaffected lines (never from the corrupted merged line's
own x0). A lone bare-digit line requires >=2 recurring instances before
being trusted (still ambiguous alone); the merged-prefix shape is trusted
on its own, since it is syntactically unambiguous.

**l/1 investigation (section 8.2)**: resolved, not left ambiguous. Both
`funcaol` (definition) and `m+l` decode as `l` via PyMuPDF's own font
cmap, matching direct 16x-zoom visual comparison against unambiguous `l`
references (flat top serif + base serif, no diagonal flag - e.g. the `l`
in `#include`) and clearly unlike the `1` reference shape (diagonal top
flag - e.g. in `TAM 10`). Cross-checked against the function's own two
*other* occurrences (`funcao1`, printf call and alternatives prose), both
independently confirmed `1` by the same method - a genuine inconsistency
in the source PDF's own typesetting (the definition and its call sites are
literally spelled differently), not an extraction defect. No second
official source was needed (internal evidence was already decisive).

**Consequence for `evaluate_extraction`**: Phase 1B's blanket "code
spanning >1 page needs manual confirmation" rule (`validator.py`) could
never be satisfied by *any* question matching that shape, regardless of
correctness - a permanent block on `verified` that pre-dated a working
two-column/code reconstruction. Removed now that the reconstruction it
distrusted is fixed and tested (D5, ADR 13); per-question trust is enforced
the same way as everywhere else - a real, disclosed `visual_validation`
entry, not a structural distrust rule keyed on content shape alone.

**TESTE DE REGRESSAO**: `test_extraction_assembler.py` (standalone-gutter
removal, merged-line prefix stripping + indentation reconstruction, lone
bare-digit line left untouched, no-op when nothing gutter-shaped),
`test_extraction_pipeline_integration.py` (no gutter token anywhere in
Q20's rendered code; both `l`-glyph occurrences preserved verbatim, never
"corrected" to `1`), `test_extraction_validator.py` (multi-page code no
longer forces `needs_review` by itself).

### 15. `AnswerStandardReference.assets`: the official answer standard's own visual evidence

**PROBLEMA**: D4's `answer_standard.text` references visual content
("conforme abaixo", "Notações possíveis são apresentadas na seguinte
imagem", "Exemplos de resposta possíveis para 'S'/'Cout'") that was never
captured - `AnswerStandardReference` had no asset mechanism at all.

**EXEMPLO NO CORPUS**: `data/raw/geacc-enade/2021/b3_padrao.pdf` pages 5-6
embed 4 real raster images for D4 alone: the worked truth table + circuit,
the IEC 60617-12/ANSI IEEE gate-notation legend, and the alternate 'S'/
'Cout' circuits - none a duplicate of the question's own figure.

**LIMITACAO DO MODELO ATUAL**: no field existed to hold these, and no
extraction step looked for them.

**ALTERACAO MINIMA**: added `AnswerStandardReference.assets: list[Asset]`
(reusing `Asset` directly - same shape already proven for
`Question.assets`), stored under a dedicated `<question-id>/answer-standard/`
subdirectory with its own `padrao-NN` id namespace, confirmed disjoint
from `Question.assets` by both id and path and confirmed not gitignored.
Detection (`answer_standard.find_answer_standard_images`) is scoped to
each rubric's own text Y-bounds (tracked per-page as `AnswerStandardEntry.
page_bounds`), never the *reprinted question text* the padrao PDF also
contains ahead of the rubric heading - critical, since D3/D4/D5's own
reprinted figures/tables also sit on padrao pages with embedded images,
and must never be captured a second time as if they were new
answer-standard content. One refinement: a page a rubric's buffer touches
but that saw no other marker/heading (i.e. the *entire* page is that one
rubric, confirmed by the absence of a next-question or next-heading
marker) is widened to the full page height rather than the rubric text's
own (possibly sparse) extent - needed for D4's page 6, whose only rubric
text is a one-line caption far above its own diagram.

**Re-audit (section 9.2)**: every discursiva's padrao pages (1-8) were
scanned for embedded images, not just D4's declared pages. Found 3 more
(pages 3, 4, 7) - all confirmed by direct visual inspection to be reprints
of the question's own already-captured figure/table (D3's, D4's, D5's
respectively), correctly excluded by the page_bounds scoping. D4 is
confirmed the only discursiva with genuinely new answer-standard-only
visual content.

**TESTE DE REGRESSAO**: `test_schema_question.py` (assets round-trip,
duplicate-id rejection, disjoint from `Question.assets` even under a
colliding id), `test_extraction_pipeline_integration.py` (D4 has exactly
4 padrao assets with the right id set and path prefix; D1/D2/D3/D5 have
zero; the page-4 reprint of D4's own figure never becomes a 5th asset).

### 16. Citation-title capitalization residuals: investigated, evidenced, left undone by design

**PROBLEMA**: 3 known residuals (D1 "direito"->"Direito", D2 "projetos"->
"Projetos", Q7 "a saúde"->"A saúde") in bold Calibri 9pt citation-title
spans, first disclosed in Phase 1B without a root-cause investigation.

**INVESTIGACAO**: PyMuPDF's own rawdict character advance-width is
decisive, non-linguistic evidence. All 3 ambiguous word-initial letters
measure identically to confirmed capital-letter references elsewhere in
the exact same font+size (e.g. D1's 'd' in "direito" = 5.67pt, matching
"Deep Learning"'s capital D exactly, and clearly unlike the same word's
own two genuinely-lowercase d's in "liberdade" at 4.83pt each). This rules
out a font-wide cmap defect (dozens of other capitals in the same
font/size decode correctly) - it is an isolated ToUnicode mis-mapping for
these 3 specific internal glyph codes in the embedded font subset, not a
linguistic/capitalization-rule question.

**DECISAO**: a safe, generalizable fix is technically available (compare
a word-initial lowercase glyph's measured width against a small,
evidence-documented per-letter capital-width reference table), but was
**not implemented**: it would require a new char-level correction pipeline
stage mirroring the full weight of the existing spacing/label/symbol
correction machinery (new `Line` field, new `TransformationLogEntry` type,
new tests, full 40-file non-regression re-verification) to fix 3 known
single-character residuals total - explicitly lower priority per PROMPT
section 10 ("não deixe isso bloquear D3/D5"). Documented in
`visual-audit-2021-b.json` as a well-scoped, evidence-backed candidate for
a future phase, not as an unresolved mystery.
