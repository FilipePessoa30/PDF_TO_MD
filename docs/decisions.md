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

## Phase 2A

### 17. Unified multi-course booklets: declarative `ExamStructureProfile`, not a single fixed course

**PROBLEMA**: the whole extraction pipeline (`build_question`,
`extract_exam`) was built assuming exactly one course per booklet - a
question's `applicable_courses` was always `[course]`, its id shorthand
always `COURSE_ID_SHORTHAND[course]`. The 2011 caderno is a single PDF
shared by 4 courses, with 50 objective + 5 discursive questions each
individually `all-computing` or exactly one specific course.

**ALTERACAO MINIMA**: `build_question`/`extract_exam` now take
already-resolved `applicable_courses`/`section`/`id_shorthand` per
question instead of deriving them internally from a single `course`. The
2021 (and every other per-course year) call path is unchanged byte-for-
byte - it resolves these the same way it always did, just now via an
explicit small resolver instead of an implicit single value. A unified
booklet instead supplies an `ExamStructureProfile` (new module
`exam_profile.py`, loaded from `data/manifests/exam-structure-<year>.yaml`)
that maps each question number to its section/applicability; the profile's
own ranges are cross-checked at runtime against the PDF's own printed
instructions page (`verify_declared_profile`), not hardcoded on faith.

**TESTE DE REGRESSAO**: full 2021 byte-diff after this refactor: 0 diffs.

### 18. New gabarito shape (`ITEM`/`GABARITO` flat table) gets its own parser, not a branch in the old one

**PROBLEMA**: `parse_answer_key` assumes every entry is introduced by a
`QUESTAO [DISCURSIVA] N` marker line - true for every per-course year's
gabarito, but 2011's unified-booklet gabarito is a flat `ITEM` -> `GABARITO`
table with bare item numbers, no marker text at all.

**ALTERACAO MINIMA**: `parse_flat_item_gabarito`, a new function in the
same module, reusing `_classify`'s letter/ANULADA/unrecognized logic but
with its own bare-number marker regex. `parse_answer_key` itself is
untouched.

### 19. Chrome literals for 2011's own running header/transition text

**PROBLEMA**: 2011's running header ("COMPUTACAO"/"2011"/"EXAME NACIONAL
DE DESEMPENHO DOS ESTUDANTES") and a one-time "ATENCAO!" section-transition
notice (between Discursiva 5 and Questao 31) are not covered by any
existing `chrome.py` literal - they leaked into D3, D5 and several
course-block objectives' statement text.

**ALTERACAO MINIMA**: new exact-match literals added to
`_EXACT_CHROME_LINES` (the bare year "2011", the header phrase's
occasionally-unspaced form, every distinct line of the "ATENCAO!" block,
and the four course-block page headers) - same risk profile and precedent
as the existing 2021 literals (e.g. "bacharelado"), not a new mechanism.

### 20. Geometric layout bugs found and fixed generally (never 2011-specific)

**PROBLEMA**: 2011's denser two-objective-per-page, two-column layout
exercised three latent bugs in `layout.py` that 2021's own page layouts
never triggered: (1) `detect_column_margins` picked the two most
*frequent* x0 buckets rather than the two most *separated* ones, so a
column with two indentation levels could be paired against itself; (2)
`_merge_orphan_markers` compared candidates by Y only, letting a
right-column marker merge into an unrelated left-column fragment merely
because it was closer in Y; (3) `MIN_LINES_PER_COLUMN=4` was too strict
for a genuinely two-column page with one short column, and page-furniture
header lines were being counted as column evidence.

**ALTERACAO MINIMA**: (1) split candidate margins at the single widest gap
between qualifying buckets, not the top-2 by raw count; (2) require
`_merge_orphan_markers` candidates to be in the same detected column; (3)
lowered the threshold to 3 and excluded chrome lines from the "substantial
line" evidence pool. All three are general geometric rules with no
reference to 2011 or any specific question id.

**TESTE DE REGRESSAO**: full 2021 byte-diff after each of the three
changes, individually: 0 diffs each time.

## Phase 2B

### 21. Q22's truth-table header: two general fixes tried and rejected, Level-3 override used instead

**PROBLEMA**: `_ORPHAN_MARKER_RE` (`^[A-E]\t*$`) matches any bare A-E
letter regardless of why it is alone on its own line - both a genuinely
split circled-letter alternative marker (its intended purpose) and an
unrelated bare-letter table-header cell or diagram-node label. 2011 Q22's
truth-table header ("A B C D S") was being merged into nonsense fragments
("A\tS", "C\t0") through this path, which then fell outside
`detect_tables()`'s own row/column geometry - dropping the header *and*
the true first data row from both the structured Markdown table and its
own mandatory visual-fallback crop.

**INVESTIGACAO (duas tentativas gerais rejeitadas)**:
1. A minimum-bounding-box-width filter (real pictograph markers measure
   ~17.5-20pt wide vs ~7.2pt for a plain glyph) fixed Q22 but, on full 2021
   regression, changed 3 already-certified files (Q23, Q34, D4): each has
   its own bare A-E letter merge from a diagram label, at a similarly
   narrow width, that Phase 1C's own visual audit never flagged as wrong.
2. A "3+ short cells share this y0" geometric row heuristic (motivated by
   Q22's header cells all sharing y0=119.83 almost exactly) still changed
   2021 Q23: that question's own binary-tree figure happens to have 3
   independent node labels ("R", "L", "A") sharing a y0 by diagram-layout
   coincidence, not because they form a table row.

Both are, in a real sense, *correct* general fixes - they likely also fix
genuine (if minor, previously undetected) defects already latent in the
certified 2021 corpus. But PROMPT Phase 2B section 5 forbids updating any
2021 gold hash in this phase merely to accommodate an extractor change,
and section 24 requires an explicit, visually-revalidated migration before
any 2021 output may change at all - neither condition is met here, so
neither general fix was kept.

**DECISAO (Level 3 - override)**: `layout_overrides.py`, a small,
independent module (no dependency from `layout.py` on `tables.py`, so no
circular import) providing a `LayoutOverrideSet` loaded from
`data/manifests/layout-overrides.yaml`, keyed by the source PDF's own
SHA-256 + page number + a tightly-scoped bbox. `_merge_orphan_markers`
consults it (via `_is_orphan_marker`) before treating a bare letter as an
orphan candidate. One entry ships, covering exactly Q22's header row on
page 14 of the 2011 prova. The override silently stops matching (and must
be re-reviewed) if that PDF is ever replaced, since the hash would no
longer match.

**TESTE DE REGRESSAO**: full 2021 byte-diff after adding the override
mechanism (with the 2011-only override entry in place): 0 diffs. Q22's
structured table and visual-fallback crop both now match the source PDF
exactly, cell-by-cell (verified by direct visual inspection of the
rendered crop against the source page).

### 22. Q13's spurious figure region: same override mechanism, extended to region suppression

**PROBLEMA**: 2011 Q13's interval-scheduling pseudocode was split in two
around a spurious `figure-01.png`. The crop showed no real figure - a
wrongly-bounded region spanning Q11's own alternatives D/E, all of Q12,
and part of Q13's own code.

**INVESTIGACAO**: `detect_visual_regions` (figures.py) seeds candidate
regions from `page.get_drawings()` + `page.get_images()`, then grows each
via `_expand_with_labels`'s iterative nearby-text absorption. Page 10 has
7 tiny raster images (8-13pt wide, y0 404-549) - almost certainly inline
math/logic glyphs inside Questao 12's grammar productions (e.g. an arrow
or epsilon symbol embedded as a raster image rather than a font glyph),
not a real figure. The decorative-baseline mechanism correctly excludes
the page's own full-page border rectangle (confirmed directly: it *is* in
the computed baseline), so that was not the cause. The absorption chain
itself - the same general mechanism three separate compounding bugs were
already found and fixed in during Phase 1C (2021, Discursiva 5's own
region: monospace-label absorption, missing X-overlap check, two-column
protection) - is what grows a ~145pt-tall image cluster into a 315pt-tall
region reaching across three questions.

**DECISAO**: rather than attempt a fourth general tightening of an
already three-times-patched, cross-year-sensitive mechanism (the Q22
investigation had just demonstrated, twice, that plausible-looking general
fixes to this exact code area can regress already-certified 2021 content
in non-obvious ways), `layout_overrides.py` was extended with a second
rule, `suppress_visual_region`: hash+page+bbox-locked, matched by the
candidate region's own center point (looser than
`exclude_from_orphan_marker_merge`'s tight containment, since a
chain-grown region's exact bounds are not a stable target to lock onto
byte-for-byte). One entry ships, covering Q13's page.

**TESTE DE REGRESSAO**: full 2021 byte-diff after adding the region-
suppression rule and the 2011-only override entry: 0 diffs. Q11, Q12 and
Q13 all now render as complete, uninterrupted text with `assets: []` -
including a side-effect fix to a spurious "figure region fell after the
alternatives cutoff" warning that had also been on Q11 (the same wrongly-
grown region overlapped Q11's own alternatives).

### 23. Q23's missing inline math notation: two more override rules, one disclosed residual left open

**PROBLEMA**: 2011 Q23's statement was truncated mid-sentence
("...um autômato que" then straight to the diagram images), and
alternatives D/E were grammatically broken, because the alphabet/
epsilon/regular-expression notation ("Σ={a,b,c}", "Σ*", "λ") is set as
small inline raster images (~10-13pt tall), not font glyphs.

**INVESTIGACAO**: two independent, compounding causes, both in
figures.py's region-detection pipeline: (1) the text fragments trailing
each symbol mid-sentence ("e", ", em que", "representa o string vazio.")
start at an x0 matching neither of page 14's two detected column margins
(they are sentence continuations, not line starts), so
`_is_two_column_body_text` never protected them, leaving them eligible for
absorption as figure labels; (2) independent of (1), the three tiny symbol
images themselves chain-merge (`_merge_by_vertical_proximity`'s 18pt
tolerance) into the same candidate cluster as the automaton diagram below
them, re-anchoring the whole region's top edge into the statement text
regardless of label absorption - each cause alone would have hidden the
same text, so both needed fixing.

**DECISAO**: two new override rules on the same hash+bbox-locked
mechanism as ADR 21/22: `protect_from_label_absorption` (stops a specific
text fragment from ever being treated as a label candidate) and
`exclude_from_region_candidates` (stops a specific image/drawing from
ever entering the initial clustering pass at all - the only point that
actually prevents the chain-merge, since a candidate this small would
never form a region on its own once excluded). Three entries of each
ship, one per affected symbol/fragment pair on Q23's page.

**RESULTADO (parcial, divulgado)**: the statement is now a single,
grammatically complete sentence with correctly-scoped diagram assets - a
major improvement from the prior fully-truncated statement. The three
symbols themselves, and the equivalent ones in alternatives D/E, are
**not** individually preserved as inline Markdown or as their own asset -
recorded as a disclosed residual limitation (`visual-audit-2011-
computing.json`), not silently hidden, and out of scope for a full fix
this phase (would require either true inline-image rendering in
`render_statement_markdown` or a dedicated small-symbol asset mechanism -
a bigger feature than a bug fix, deferred).

**TESTE DE REGRESSAO**: full 2021 byte-diff after adding both new rules
and the six 2011-only override entries: 0 diffs.

### 24. Q1/Q2: an indented poem block misdetected as a genuine second column

**PROBLEMA** (found during the full 55-question audit, not the initial
sample): Questao 1's own statement - a 14-line indented poem, all sharing
one consistent x0=173.0 offset from the page's body margin (x0=28.5) -
was entirely missing from Q1's rendered statement, and instead appeared,
completely out of place, appended after Questao 2's own alternatives.

**INVESTIGACAO**: `detect_column_margins` found two qualifying x0 buckets
on page 2 (28.5 and 173.0) separated by more than `MIN_COLUMN_SEPARATION`
- correctly geometric, but wrong in this case: the poem is not a second
column running in parallel with the body text, it is an indented block
*nested inside* a genuinely single-column page. `extract_page_lines` then
sorted the entire poem block (14 lines) and its citation line to the very
end of the page's own line sequence, after Q2's content, instead of
leaving them in their true position between Q1's marker and Q1's own
"No poema, a autora sugere que" prompt line.

**DECISAO**: a fourth override rule, `force_single_column_page`, bypasses
`detect_column_margins` for the one page it is declared for and falls
back to the plain (y0, x0) sort the whole module already uses for
genuinely single-column pages. A real geometric discriminator likely
exists (a genuine two-column layout's two "columns" run in parallel
across roughly the same Y-range; this poem's Y-range sits nested inside
the surrounding flow instead) but was not implemented as a general Level 1
fix here, given the session's repeated experience that column-detection
changes have non-obvious effects elsewhere in a two-year corpus.

**TESTE DE REGRESSAO**: full 2021 byte-diff after adding the rule and the
2011-only override entry: 0 diffs. Q1 now renders its complete poem
statement; Q2 no longer has any orphaned content appended to it.

**SUPERSEDED (see ADR 25)**: the general Y-range-overlap discriminator
predicted above was found and implemented later in the same phase, after
an *independent* instance of this exact defect class turned up on
Discursiva 4 (page 19 - a different indented block, a different page, not
caught by this page-2-only override). Because a validated general fix now
covers both cases, the `force_single_column_page` override entry for Q1
was removed from `data/manifests/layout-overrides.yaml` as redundant (the
`force_single_column_page` rule kind and its test remain as generic,
available infrastructure, but nothing currently depends on it). This is
the fix-hierarchy working as intended: a Level-3 override bought safety
immediately, and was later replaced by a Level-1 fix once a second
occurrence made the general shape of the bug undeniable.

### 25. `detect_column_margins` requires Y-range overlap between candidate columns

**PROBLEMA** (found during the full 55-question audit): Discursiva 4's own
statement opens, in the source PDF, with a centered epigraph block
("Listas ordenadas implementadas com vetores sao estruturas...", 7 lines,
x0=141.9, y0 95.1-205.5, page 19) immediately followed by the question's
real prompt paragraph ("Considerando essas informacoes...", x0=28.5, y0
229.6+). The rendered Markdown had the epigraph appended at the very end
of D4's text, after "Observacao: Qualquer notacao..." - the same defect
shape as ADR 24's Q1 poem, on a different page, that the Q1-only override
did not cover.

**INVESTIGACAO**: confirmed via `extract_page_lines` on the raw page-19
lines that the epigraph block was sorted to the very end of the page's
entire line sequence - after the RASCUNHO ruler and even the footer
barcode caption - exactly like Q1's poem before ADR 24's fix. Comparing
the two cases' geometry: in both, the "second column" bucket's Y-range
(page 2's poem: nested inside the surrounding flow; page 19's epigraph:
y0 95.1-205.5) never overlaps the body-margin bucket's own Y-range (page
19's body text: y0 229.6-412.2) at all. Checked this against every known
genuine two-column page in both years' corpora (2011 Q9/Q10, 2011 D5's
pseudocode column, 2021 D5's own two-column split): in every real case,
the two columns' Y-ranges overlap substantially, because both columns
start near the top of the same content area and run down the page in
parallel.

**DECISAO**: `detect_column_margins` now computes the full Y-range (min
y0, max y1) of the lines belonging to the left-side bucket(s) and the
right-side bucket(s) separately, and rejects the split (returns `None`,
falling back to the plain (y0, x0) sort) if the two ranges do not overlap
at all. This is a genuine Level-1 general fix, not a page- or document-
specific rule: it encodes an actual property that distinguishes real
parallel columns from a sequential indented block, and required no
hash-locked override for either page it fixes.

**TESTE DE REGRESSAO**: all 12 pre-existing `test_extraction_layout.py`
cases pass unchanged. Full 2011 all-computing regen: only
`enade-2011-computing-d04.md` and `enade-2011-computing-q01.md` changed
(both now correct - epigraph/poem restored to their true position; Q2 no
longer carries Q1's orphaned poem tail). Full 2021 regen for all three
locally-available, previously-committed courses
(ciencia-da-computacao-bacharelado, ciencia-da-computacao-licenciatura,
sistemas-de-informacao): `git status` shows zero diff for
ciencia-da-computacao-bacharelado (the corpus's own tracked 2021 gold
baseline) - byte-identical. Real two-column pages in both years
(2011 Q9/Q10, 2011 D5, 2021 D5) were spot-checked post-fix and still
detect two columns correctly, confirming the overlap requirement does not
reject genuine cases. The Q1-only `force_single_column_page` override
(ADR 24) is now redundant and was removed; see that ADR's "SUPERSEDED"
note.

### 26. Q6's statement-truncation chain: five `protect_from_label_absorption` overrides

**PROBLEMA** (found during the full 55-question audit, page 5): Questao
6's own statement was truncated mid-sentence ("usada no titulo do",
missing "infografico diz respeito") and its own caption ("Disponivel em:
<http://ead.uepb.edu.br/noticias,82>...") was missing entirely from the
rendered Markdown.

**INVESTIGACAO**: the page-5 infographic (a vector "X" chart) has a true
extent ending around y=366.3 (confirmed via `detect_visual_regions`'s own
pre-label-expansion candidate bbox). `_expand_with_labels`
(figures.py) then chain-absorbed, in order: the caption 16pt below the
chart; Q6's own two-line statement tail immediately below that; and,
independently, alternative A's and B's own wrapped continuation lines
("garantir um emprego estavel...", "que aumenta o nivel..."), each within
`TEXT_ABSORPTION_PADDING` (90pt) of the chart's true edge even without the
caption/statement-tail bridge, growing the region to y=476.3 - exactly
366.3 + `MAX_ABSORPTION_GROWTH`'s 110pt cap. Protecting only the
caption/statement-tail (the first, most obviously-broken symptom) did not
stop the growth: the two alternative-continuation lines independently
re-triggered the same chain, since each candidate is tested against the
current bbox on its own merits, not in a fixed sequence blocked by
protecting one bridge alone.

**DECISAO**: five `protect_from_label_absorption` Level-3 overrides
(the caption, both statement-tail lines, and both alternative-continuation
bridge lines - see `data/manifests/layout-overrides.yaml`). No general fix
was attempted for the underlying `TEXT_ABSORPTION_PADDING`/
`MAX_ABSORPTION_GROWTH` values themselves, given the demonstrated
regression risk of touching this shared mechanism (ADR 21) and that the
same generous padding is likely load-bearing for genuinely large figures
elsewhere in the two-year corpus.

**TESTE DE REGRESSAO**: full 2021 byte-diff after adding all five
overrides: zero diff for the tracked `ciencia-da-computacao-bacharelado`
baseline. Re-inspected Q6 directly: statement and caption fully restored;
figure-01.png crop now shows only the true chart, ending well above the
alternatives.

### 27. `assembler.py` region-attachment X-tolerance reduced from 15pt to 5pt

**PROBLEMA** (found while investigating ADR 26's Q6 fix): even after Q6's
own region bbox was corrected to its true extent (x1=284.7), the same
region was still being attached to Questao 7 as well (page 5's right
column, x0=296.7) - Q7 has no figure of its own, but its rendered
statement carried a spurious `![Figura da questao]` reference mid-sentence
and a duplicate copy of Q6's own figure-01.png asset.

**INVESTIGACAO**: this corpus's real column gaps run narrow - 9.3pt on
page 14 (Q22/Q23's own columns), 12pt on page 5 (Q6/Q7) - consistently
narrower than the 15pt `x_tolerance` `assemble_question` (assembler.py)
used when deciding whether a detected region's X-range overlaps a
question span's own X-range (the general fix from earlier this phase that
resolved Q16/Q15's cross-column figure leak, see the module's own
docstring). A tolerance wider than the corpus's own column gaps
systematically bridges every real column boundary a region happens to sit
close to, not just the "figure sitting just outside its nearest text
line" case the tolerance was meant for.

**DECISAO**: reduced `x_tolerance` to 5pt - comfortably under every
observed real column gap in the corpus, while still large enough to
absorb minor rendering slack for a figure whose own bbox sits just
outside its span's text lines (the case the tolerance exists for).

**TESTE DE REGRESSAO**: full `pytest` suite (352 tests) passes unchanged.
Full 2011 all-computing regen: in addition to Q7 (now correctly
figure-less), this also fixed Q15's own long-standing, previously
undiagnosed defect (Questao 14's Venn diagram was wrongly attached to
Questao 15 - see visual-audit-2011-computing.json's Q15 entry) as a side
effect, since it is the exact same cross-column-adjacency mechanism.
Q16 (the fix's original motivating case) re-verified still correct: no
figure attached. Full 2021 regen for all three locally-available,
previously-committed courses: `git status` shows zero diff for
`ciencia-da-computacao-bacharelado` - byte-identical.

### 28. Two systemic defect classes found during the exhaustive audit, not fixed this phase

**PROBLEMA**: the full, non-sampling 55-question re-audit (PROMPT Phase
2B section 10) found two recurring defect classes well beyond the three
originally documented in Phase 2A, affecting at least 15 questions.
Neither is a one-off; both are disclosed here as confirmed, unresolved,
and requiring dedicated future investigation, rather than being fixed
under this phase's time constraints or hidden behind an optimistic status.

**Classe A - inline math/logic notation is not extractable text.**
Several questions embed set-builder notation, modular-arithmetic symbols,
stacked fractions, BNF-with-symbol grammars, or boolean-algebra formulas
as small embedded glyph sequences distinct from the body font, which this
pipeline's text layer does not expose as text (the same underlying
phenomenon as Q23's disclosed residual, ADR 23, but at a much larger
scale). Confirmed affected: Q9 (equivalence-relation properties, quotient
set, canonical projection, roman-numeral items II-IV all lost), Q10 (all
5 alternative fractions lose their numerators), Q12 (symbol names and the
entire BNF grammar block missing), Q14 (all 5 alternatives render empty),
Q38 (grammar production scrambling), D3 (Fibonacci recurrence formula
missing). A proper fix needs either a font-aware glyph-to-text mapping
for this corpus's specific math-typesetting fonts, or a mandatory visual
fallback for any statement/alternative segment identified as
non-extractable - both larger undertakings than a Level 1-3 fix.

**Classe B - page-content-width rendering lets a chain-absorbed region's
crop straddle unrelated, sometimes distant, questions.** `assets.py`'s
`_render_bbox` deliberately widens every crop horizontally to the page's
own content width (``PAGE_CONTENT_MARGIN``, documented rationale: avoid
clipping full-width paragraph lines that share a figure's vertical band).
On a two-column page, "full content width" spans *both* columns; combined
with `_expand_with_labels`'s vertical chain-absorption (already the root
cause behind ADR 22's Q13 and ADR 26's Q6), a single region's crop can
grow tall enough, and wide enough, to visually capture real content
belonging to an entirely different, sometimes non-adjacent question -
without that content being reflected in the correct question's own
Markdown. Confirmed instances: Q25's figure-01.png contains Q24's own
roman-numeral items I-IV (in full, legible form) plus Q26's own 5-card
poker image plus the "QUESTAO 26" header, spanning three consecutive
questions in one crop; Q40's figure-01.png contains Q38's own missing
LR-automaton item-set states and assertion block from two questions
earlier. In both cases the "recipient" question's own content is
undamaged, but the true owner question loses real content (Q24, Q26,
Q38) that is not lost from extraction - only misattached, unlabeled, and
rendered under the wrong heading. Q43/Q44/Q45/Q48/Q20's shorter,
same-question lead-in-sentence losses (see their own visual-audit
entries) are the same absorption mechanism at smaller scale, without the
cross-question misattachment.

**DECISAO**: not fixed this phase. Both classes were investigated deeply
enough to identify root cause with confidence (verified by directly
opening the offending asset files and visually locating the "lost" text
inside them, in Classe B's case), but a general, corpus-safe fix for
either was judged too large an undertaking for this phase's remaining
time without risking the same kind of 2021 regression already
demonstrated three times this session for narrower changes to this same
shared machinery (ADR 21, ADR 22, the rejected row/width orphan-marker
heuristics). Documented in full in
`data/manifests/visual-audit-2011-computing.json` (per-question) and
`docs/phase-2b-report.md` (aggregate) instead of silently left as
`passed`/`extracted` - the exact failure mode Classe A's own Q9 entry
had fallen into before this audit (see that entry's "CORRECTION" note).

**TESTE DE REGRESSAO**: not applicable - no code changed for this entry.

## Phase 2C

### 29. Spatial ownership model for figure regions (`ownership.py`)

**PROBLEMA**: ADR 28's Classe B (cross-question crop contamination: Q24's
own roman-numeral items I-IV, plus Q26's own card image, ending up inside
Q25's own `figure-01.png`; Q38's own missing LR-automaton states ending up
inside Q40's own crop) and much of Classe A (Q9/Q10/Q12/Q14/D3's own
missing paragraphs/alternatives) shared one underlying cause never before
addressed directly: `detect_visual_regions` (figures.py) had no concept of
*whose* content a candidate region actually was before growing or
rendering it - any region within Y/X tolerance of a question's own lines
was accepted, and growth via `_expand_with_labels` had no hard boundary
tied to a specific owner, only the generic `MAX_ABSORPTION_GROWTH` cap
(110pt - large enough to reach a genuinely different, several-questions-away
block of content).

**INVESTIGACAO**: opening the offending crops directly (not just comparing
rendered Markdown to the PDF) showed the "lost" text in Classe A/B's cases
was never actually lost from extraction - it was present, legible, and
complete, just captured inside the wrong region, attached to the wrong
question, or excluded from a question's own statement as if it were figure
content. This reframed both classes as one architectural gap (no spatial
ownership), not two separate content-extraction failures, and one
principled fix could address most of both at once.

**DECISAO**: a new module, `ownership.py`, computes one `QuestionRegion`
per (question span, page) - the tight bbox of that question's own
non-chrome lines on that page, derived only from `QuestionSpan.lines`
(never guessed from a neighbor's boundary). `detect_visual_regions` gained
an optional `question_regions` parameter (page-scoped); when given, every
raw candidate (drawing/image) and every label candidate is assigned an
owner *before* any merging (`find_owner`, containment first, then nearest
region in the same column - a point can never resolve to a different
column's question just because its own Y-range happens to be numerically
closer). Merging and label-absorption run independently per owner group,
and every region's final bbox is hard-clipped to `owner.clip(bbox,
margin=20pt)` - a fixed, small margin, not the old 110pt growth cap - so a
region can no longer reach into a neighboring question's own territory no
matter how close/absorbable its labels look. `pipeline.py` computes the
full-document ownership map once (`compute_question_regions(boundary_result.spans)`)
and threads it through `assemble_question` -> `detect_visual_regions` for
every span. A `detect_contamination` gate (geometry-only, not OCR of the
rendered PNG) is available to check a final asset's bbox against every
other question's own claimed region on the same page.

A second, related change: small embedded raster images
(`SMALL_IMAGE_MAX_WIDTH`=250pt, `SMALL_IMAGE_MAX_HEIGHT`=40pt - this
corpus's own inline math notation is 15-31pt tall, its smallest genuine
diagram ~250pt tall) are classified *before* merging and routed through a
separate, much tighter merge (`SMALL_IMAGE_Y_MERGE_TOLERANCE`=16pt vs.
the general pipeline's 18pt cluster tolerance plus 90pt label-absorption
padding) and **never** participate in label absorption at all - a
formula's own sub-parts (numerator/bar/denominator, a multi-line stacked
relation) merge into one small asset without pulling in the surrounding
prose paragraph, closing the other half of Classe A.

**RESULTADO** (re-verified by direct visual inspection of the regenerated
Markdown/assets, not assumed from the mechanism alone):
- Q24: its own roman-numeral items I-IV are now complete, correct text in
  its own statement (previously fragments; the full text was trapped
  inside Q25's own crop).
- Q25: no longer carries any figure reference (it never had a real figure).
- Q26: now has its own, correctly-scoped `figure-01.png` (the 5-card
  image) - previously entirely absent from Q26 (it existed, mis-owned, in
  Q25's own crop).
- Q40: `figure-01.png` is now scoped to only its own maze-grid figure - no
  longer contains Q38's own grammar-automaton content.
- Q38: significantly improved (its own previously entirely-missing e1
  automaton states, and the "PORQUE" assertion block, are now present as
  its own image assets, `figure-01.png` through `figure-05.png`) but not
  fully resolved - some of its own text (the hexadecimal-ambiguity
  paragraph, and the grammar-production block's own scrambling) remains a
  separate, unexplained residual (see Section F below).
- Q9: dramatically improved - property (iii), the quotient-set paragraph,
  and analysis items I/II/III/IV are now present (previously fragments or
  entirely missing); one small residual remains (the canonical-projection
  formula, "A funcao" with nothing after it).
- Q12: dramatically improved - the intro sentence (with symbol names), the
  full grammar productions, and items I-III are now present, all inside
  one correctly-owned, legible visual-fallback image; a residual remains
  (item IV's own text is neither in the image nor in the surviving prose).
- D3 (question statement): the Fibonacci recurrence formula
  (`f_n = f_{n-1} + f_{n-2}`) is now a clean, correctly-cropped, legible
  visual-fallback asset - fully resolved.
- Q20, Q43: also newly fixed as a side effect (their own previously-lost
  lead-in/closing sentences are now present) - the ownership clip
  apparently now stops growth before it reaches as far as these
  sentences, though the exact boundary geometry was not traced further
  given time constraints.
- Q10, Q14, Q44, Q45, Q48, Q23's own residual: **not** resolved by this
  change (see their own ADRs/notes below and the visual-audit entries) -
  their own defect geometry sits entirely within one question's own
  already-generous territory, so ownership clipping alone does not reach
  them.

**TESTE DE REGRESSAO**: all 368 tests pass (14 new, in `tests/test_ownership.py`,
covering `compute_question_regions`, `find_owner` containment/nearest-
column-fallback/empty-input, `QuestionRegion.clip` growth-limiting and
no-op-when-already-inside, and `detect_contamination` real/none/
below-threshold). Full 2011 regen re-inspected question-by-question (see
above). Full 2021 regen for all three locally-available courses: `git
status` shows zero diff for `ciencia-da-computacao-bacharelado` (the
tracked 2021 gold baseline) - byte-identical; `verify-gold` confirms
40/40 hashes match, `maturity=validated` unchanged. The Q13
`suppress_visual_region` override (ADR 22) was removed as redundant
(superseded by ownership) - `enade-2011-computing-q11/-q12/-q13` were all
re-verified directly (Q11/Q13 unchanged and still correct; Q12
significantly recovered) after its removal.

### 30. Stacked two-line fraction reconstruction (Q10): tried and rejected

**PROBLEMA**: Q10's own 5 alternatives are each a stacked two-line
fraction (e.g. "61" above the marker's own baseline, "73" below - never
one line with a slash). The existing marker-merge already attaches the
denominator (closer in Y, in every observed case) to the marker; the
numerator is left as an orphan bare-digit line, which chrome.py's
text-only running-page-number heuristic then strips before the
alternative-building stage ever sees it (chrome.py's own docstring already
flags this exact class of ambiguity as needing geometry it does not have).

**INVESTIGACAO/DECISAO**: a second pass was added to `_merge_orphan_markers`
(layout.py): once a marker's primary partner is itself found to be
bare-digit (i.e. this really is a fraction, not a generic marker+text
merge), search the *opposite* side of the marker's own baseline, same
column, same distance threshold, for another bare-digit line - the
numerator - and merge both into "marker\tnumerator/denominator". This
correctly reconstructed all 5 of Q10's own fractions
("A. 61/73" ... "E. 67/112", byte-for-byte matching the source).

**REJEITADO** after full 2021 regression testing found a real false
positive: 2021's own Q34 (Dijkstra shortest-path algorithm) has a graph
node-label listing rendered the same way this corpus renders any bare
single-letter + adjacent short text (`orphan_marker` shape) - five
independent single-letter-node + single-digit-value pairs set close
together ("C 8", "A 2", "B 5", "E 9", "D 5"). The second pass's own
opposite-side search found each pair's *neighbor's* own bare-digit value
within the same distance/column threshold and spliced unrelated pairs
into spurious fractions ("B 5/1", "D 9/5"), silently dropping node E's
own pair. Tightening the precondition (e.g. requiring the numerator and
denominator to share a near-identical X-center, the way a real fraction's
two halves are horizontally centered on the same fraction bar) was not
attempted and verified safe in the time remaining - unlike Q22's
orphan-marker case (ADR 21), where a Level-3, hash-and-bbox-locked
override was viable, this defect's shape (a marker-merge behavior, not a
region/asset) has no existing override rule kind, and building one for a
single, narrow case was judged a worse trade than reverting.

**RESULTADO**: reverted in full (`_merge_orphan_markers` restored to its
pre-Phase-2C behavior, `_BARE_NUMBER_RE` removed). Q10 remains a
disclosed, unresolved defect (`status: failed` in
visual-audit-2011-computing.json) - a real, narrow, well-understood
residual rather than a false claim of resolution.

**TESTE DE REGRESSAO**: full 2021 regen after the revert: zero diff for
`ciencia-da-computacao-bacharelado` (`git status` clean, `verify-gold`
40/40); `enade-2021-cc-b-q34.md` confirmed restored to its exact prior,
certified text.

## Phase 2D

### 31. Q10's fractions: a hash-and-bbox-locked `force_fraction_merge` override, not a general rule

**PROBLEMA**: ADR 30 rejected a general second-pass merge for Q10's own
stacked fractions after it produced false positives on 2021 Q34. Q10
itself remained unresolved.

**DECISAO**: a new declarative override kind, `force_fraction_merge`,
with a `secondary_bbox` field alongside the existing `bbox`. In
`_merge_orphan_markers` (layout.py), before the general partner search
runs, `overrides.fraction_merge_partner(pdf_sha256, page, marker_bbox)` is
checked for a declared numerator bbox; if present, that candidate is
excluded from the general search (guaranteeing the general search can
only ever find the denominator, even where numerator/denominator
distances from the marker differ by <0.001pt - real Q10 data), and after
the primary partner is found, the exact line matching `secondary_bbox` is
merged in as the numerator: `f"{marker}\t{numerator}/{denominator}"`.
5 overrides were added (`layout-overrides.yaml`), one per alternative,
each hash-locked to `1_prova.pdf`'s own SHA-256 and pinned to both
bboxes' exact coordinates.

**POR QUE NAO UM CROP VISUAL**: the fraction text is real, extractable
text (not a raster image) - a full visual crop would have been a strictly
worse outcome than correctly reconstructing it as text, given a safe,
narrow mechanism was available (PROMPT Phase 2D section 8: "o fallback
visual e preferivel a uma regra geral insegura", not "preferivel a uma
extracao textual segura").

**RESULTADO**: all 5 alternatives now read as complete fractions
("A. 61/73" ... "E. 67/112"), byte-for-byte matching the source.

**TESTE DE REGRESSAO**: `test_merge_orphan_markers_applies_a_matching_fraction_merge_override`
(positive, Q10); `test_merge_orphan_markers_fraction_override_never_matches_unrelated_pairs`
(negative, models 2021 Q34's own Dijkstra shape with a *different*
`pdf_sha256` than the override declares - asserts `["A\t2", "B\t5",
"C\t8"]`, zero cross-contamination). Full 2021 regen: zero diff,
`verify-gold` 40/40.

### 32. `MAX_ABSORPTION_GROWTH` as a growth *cap*, not just candidate exhaustion: `protect_from_region_membership`

**PROBLEMA**: Q12 (item IV), Q44, Q45, and Q48 each lost a text fragment
sitting close to a growing figure region. `protect_from_label_absorption`
(the existing override kind) was tried first on each case, matching the
already-solved Q6/Q20/Q23 precedent - but for Q12 and Q48 specifically,
adding the override changed nothing: recomputing the region's own bbox
with and without the override produced the *identical* final bbox.

**DIAGNOSTICO**: the pre-expansion "large" candidate's own edge, plus
`MAX_ABSORPTION_GROWTH` (110pt) exactly, matched the final region's own
edge in both cases (Q12: `499.29 + 110 = 609.29`; Q48: `334.5 + 110 =
444.5`). This is a different failure mode from every prior
label-absorption case: growth was hitting a *hard cap*, not running out
of absorbable candidates, so protecting any single candidate from
absorption cannot change the outcome - the region grows exactly
`MAX_ABSORPTION_GROWTH` regardless of which candidates exist.

**DECISAO**: a new override kind, `protect_from_region_membership`,
addressing the *symptom* (wrongful text exclusion) directly rather than
the cause (the growth cap itself, a shared, load-bearing general constant
that must not be changed per-question). `assembler.py`'s `_line_in_region`
gained an `overrides`/`pdf_sha256` parameter; a line matching a declared
override bbox is treated as never inside any region, regardless of the
region's own final (capped) extent. Threaded through
`_build_statement_segments` and all 3 call sites in `assemble_question`.

Applied to Q12 (item IV's opening line) and Q48 (the "Da analise do
diagrama..." connecting sentence) - both previously showed zero effect
from `protect_from_label_absorption`. Q44 and Q45's own defects *were*
each resolved by `protect_from_label_absorption` (4 and 5 overrides
respectively) - their own limiting factor was genuine candidate
absorption, not the growth cap, confirmed by the same before/after bbox
diagnostic returning a *changed* bbox in those cases.

**DIAGNOSTIC PROTOCOL** (reusable, established this phase): (1) recompute
the pre-expansion candidate's own edge and check whether `edge +
MAX_ABSORPTION_GROWTH` matches the final region's own edge exactly - if
so, the cap is the limiting factor, not candidate exhaustion; (2) if
`protect_from_label_absorption` on the suspected culprit line does not
change the final region bbox at all when re-tested, this confirms the cap
theory and signals `protect_from_region_membership` is needed instead.

**RESULTADO**: Q12 item IV, Q44's 3 paragraphs + 2 equations, Q45's
opening sentence + items II-V, and Q48's connecting sentence are all now
present, matching the source exactly.

**TESTE DE REGRESSAO**: `tests/test_layout_overrides.py` (5 new tests for
`protect_from_region_membership` - containment/non-containment/
hash-mismatch/distinctness-from-label-absorption); `tests/test_extraction_assembler.py`
(2 new tests for `_line_in_region`'s own override handling). Full 2021
regen: zero diff, `verify-gold` 40/40.

### 33. D3's answer standard: a second `symbol_fonts.py` entry (Wingdings, not Euclid)

**PROBLEMA**: D3's own answer-standard pseudocode (`3_padrao.pdf`) had
every assignment arrow ("<-") corrupted to "A with ring above" (Å)
throughout both the iterative and recursive listings.

**EVIDENCIA**: direct rawdict inspection found `font=Wingdings-Regular,
codepoint=0xC5` at every corrupted position - a dingbat font whose
codepoints are pictures, not letters; PyMuPDF, absent a working
ToUnicode CMap for this specific glyph, decoded the byte as
Windows-1252 text. Confirmed by the pseudocode's own context: every
occurrence sits between a variable name and its assigned value/expression
(e.g. "prevFib [glyph] 0"), matching this corpus's own plain-ASCII "<-"
assignment convention used elsewhere (D4's own CriaABP listing) - a
geometric/font finding, never a value inferred from what the pseudocode
"should" logically do (PROMPT Phase 2D section 5's own prohibition).

**DECISAO**: extended the existing, closed `symbol_fonts.py` substitution
table (the same mechanism already used for D3's own logic-operator
glyphs, ADR from Phase 1B) with `"wingdings-regular"`/`"wingdings"` as
known symbol font names and `"Å"` -> `"←"` as a new substitution - not a
general "any Symbol-style font" decoder (a different PDF could map the
same font name's codepoints to different glyphs; this module keys off
both font name and the specific codepoint observed here).

**RESULTADO**: every "prevFib <- 0", "currFib <- 1", "temp <- prevFib +
currFib" etc. now renders correctly throughout both algorithm listings.

**TESTE DE REGRESSAO**: `test_is_symbol_font_matches_wingdings`,
`test_substitute_replaces_the_wingdings_arrow`. Full 2021 regen: zero
diff (D3's own font substitution table is shared code, but 2021's own
`b3_padrao.pdf` does not use Wingdings anywhere, confirmed by unchanged
output).

### 34. D5's answer-standard tables: a narrower rescue heuristic, not `tables.py`'s `detect_tables`

**PROBLEMA**: D5's own answer standard (`3_padrao.pdf`, pages 4-5) has 3
small bit-width breakdown tables, each just 1 data row (e.g. "Rotulo
Linha Palavra" / "13 17 2"), missing entirely from the extracted text -
the bare row numbers were indistinguishable, on text alone, from a
running page number, and got dropped by chrome.py before
`answer_standard.py`'s own text-assembly ever saw them.

**POR QUE NAO `detect_tables`**: `tables.py`'s own `detect_tables` (used
by `assembler.py` for question statements, e.g. D3's own larger grid)
requires `MIN_TABLE_ROWS = 3` - a deliberate, documented anti-false-
positive threshold. D5's own tables have only 1 data row each; using
`detect_tables` here found zero tables (confirmed: a first fix attempt
using it left D5's numbers still missing).

**DECISAO**: a new, narrower heuristic scoped specifically to
`answer_standard.py`'s own simpler parsing pipeline (which has no
table-detection machinery of its own): `_rescue_table_row_numbers`. A
genuine page footer has exactly one bare-number line; two or more
bare-number lines sharing a Y position (within `_ROW_Y_TOLERANCE`,
mirroring `tables.py`'s own `ROW_Y_TOLERANCE`) can only be a real table's
own data row. Never rescues a lone digit (still indistinguishable from a
page number on text alone). `parse_answer_standard`'s own `flush()` now
tracks every line seen while `in_rubric` (before chrome filtering, in a
`raw_buffer`) and calls the rescue pass against it before building the
final rubric text.

**RESULTADO**: all 3 rows now present in full ("Rotulo Linha Palavra / 13
17 2", "Rotulo Palavra / 30 2", "Rotulo Conjunto Palavra / 15 15 2"),
matching the source exactly.

**TESTE DE REGRESSAO**: `tests/test_extraction_answer_standard.py` (new
file, 4 tests: real-row-recovery, lone-page-number-never-rescued,
already-buffered-numbers-not-double-counted, row-Y-tolerance-respected).
Full 2021 regen: zero diff (2021's own answer standards have no
comparable 1-row tables, confirmed unchanged).

### 35. Cross-column asset contamination: crop-widening had no notion of columns (Q9, Q23)

**PROBLEMA**: found by direct pixel inspection while re-verifying Q9 and
Q23 after their other fixes, *not* previously documented in any prior
phase's audit (which checked text completeness, never asset pixel
purity). Q9's own `figure-01.png` (the canonical-projection formula) also
showed Q10's own alternative fractions bleeding in from the right column.
Q23's own `figure-01.png`/`figure-02.png` also showed the *entirety* of
Q22's own left-column truth table and alternatives bleeding in across the
column boundary.

**ROOT CAUSE**: `assets.py`'s `_render_bbox` unconditionally widens every
crop to the page's own full content width (`PAGE_CONTENT_MARGIN` from
each physical edge) so a figure's own full extent is never truncated - a
rule tuned against 2021's single-column layout (docstring: "observed on
this booklet's Q3, Q5, Q11"), where a shared vertical band can only ever
belong to the same question. On 2011's two-column pages, this same
widening reaches straight across into the *other* column's own unrelated
content, since it has no notion of columns at all - `ownership.py`'s own
clipping (ADR 29) is applied to the *region*, well before this later,
separate render-time widening step re-opens it back to full page width.

**DECISAO**: `VisualRegion` gained an `owner_x_bounds: tuple[float,
float] | None` field - the owning question's own claimed x-range,
expanded by `OWNERSHIP_MARGIN` - populated only when *both* an owner is
known *and* the page is a genuine two-column layout (via the existing
`detect_column_margins`, already computed in `detect_visual_regions` for
an unrelated purpose). The two-column gate matters because
`QuestionRegion` (ownership.py) is built only from a question's own
*text* lines - a full-width single-column diagram's own drawn extent can
legitimately be wider than that text-only bbox (Q17's own circuit: its
"f"/"g" output labels sit at x~550-580, but Q17's own `QuestionRegion.x1`
is only 405.3, since it comes from text alone) - capping unconditionally
first clipped Q17's own real diagram content, a regression caught before
finalizing (`git diff` showed Q17's own figures changed for the first
time in the whole phase; re-inspected, found the circuit's own "f"/"g"
output labels missing). `assets.py`'s `_render_bbox` gained a
`column_bounds` parameter, threaded from `render_region` via
`region.owner_x_bounds`, intersected with (never replacing) the existing
page-content-width bound.

This is Level-1 (an already-proven general mechanism, ownership.py,
extended into a stage it did not previously reach), not a new heuristic -
PROMPT Phase 2D adjudication category 1.

**RESULTADO**: Q9 and Q23's own figures now show only their own content,
at most a 1-2pt sliver at the page edge (the small, expected
`OWNERSHIP_MARGIN` residual). Q17's own full-width circuit diagram
re-verified unaffected (single-column page, no cap applied).

**TESTE DE REGRESSAO**: `tests/test_extraction_assets.py` (new file, 3
tests: widens to page content width without `column_bounds`; caps to
`column_bounds` when supplied; the two caps combine, whichever is
narrower wins). `tests/test_extraction_figures.py` (`owner_x_bounds`
union behavior on same-owner region merges). Full 2021 regen: zero diff,
`verify-gold` 40/40 (2021's own single-column pages never trigger the cap
- `detect_column_margins` returns `None` throughout).

### 36. `_merge_overlapping_regions` had no ownership check at all (Q38/Q40)

**PROBLEMA**: found by direct pixel inspection while re-verifying Q38.
`figure-01.png` showed Q40's own grid-puzzle image (the A* search-cost
question) rendered as if it were part of Q38 - despite ADR 29's own
ownership model, and despite this exact question pair being ADR 29's own
named regression case. This is a *different*, deeper root cause from what
ADR 29 fixed, not a regression of it.

**ROOT CAUSE**: `detect_visual_regions` groups candidates by owner and
clips growth to each owner's own territory (ADR 29) - but its own final
step, `_merge_overlapping_regions`, runs once across the *whole page's*
region list, merging any two regions with substantial Y-overlap purely by
geometry, with no ownership check of its own. Q38's own
end-of-statement region and Q40's own grid-puzzle region, both already
correctly computed and clipped under their own, different owners, sat
close enough in Y (both near the bottom of page 25) to pass this later,
unguarded merge and be blended into one bbox spanning both columns.

**DECISAO**: `VisualRegion` gained an `owner_key: str | None` field
(`ownership.question_key`, populated for every region regardless of
column layout - a plain identity check, not the two-column-gated
`owner_x_bounds`). `_merge_overlapping_regions` now refuses to merge two
regions whose `owner_key` differs; two `None` owners (no owner info
available) still merge, preserving this function's own pre-ownership
behavior exactly. `owner_key` alone was chosen over reusing
`owner_x_bounds` for this check because two *different* owners' bounds
are not guaranteed to differ in a way a numeric comparison would reliably
catch, where identity comparison is exact by construction.

**RESULTADO**: `figure-01.png` now shows only Q38's own LR-parsing-table
fragment; the grid puzzle correctly renders only under Q40's own
`figure-01.png`; two new, correctly-split assets (`figure-06.png`,
`figure-07.png`) recovered grammar-rule fragments previously absorbed
into the contaminated region. Investigating this also surfaced two
distinct, previously-undocumented text-image discrepancies now resolved
in the visual-audit record: the hex-ambiguity paragraph's own missing
symbol is "x" (not a font-substitution case - a genuine, isolated stray
"g" glyph, U+0067, font ArialMT, confirmed by rawdict inspection,
coexisting with a correct image elsewhere on the same page, not a
substitute for it); and the PORQUE/assertion sentence is present as plain
statement text, contradicting Phase 2C's own note that it was "only crop
padding".

**TESTE DE REGRESSAO**: `tests/test_extraction_figures.py` (4 new tests:
same-owner fragments still merge; different owners never merge -
directly modeling the Q38/Q40 page-25 geometry; both-unknown owners still
merge; `owner_x_bounds` unions correctly on a same-owner merge). Full
2021 regen: zero diff, `verify-gold` 40/40.

### 37. Q22's `table-01.png`: same contamination class, found but not fixed this phase

**PROBLEMA**: found by direct pixel inspection while investigating ADR 35
(Q23). `table-01.png` (Q22's own mandatory visual-fallback crop for its
truth table, rendered via `render_table_region`) also shows Q23's own
automaton diagram and grammar bleeding in on the right edge - the same
general root cause as ADR 35, but in the `render_table_region` code path,
which ADR 35's fix did not touch.

**DECISAO**: not fixed this phase (scoped out given time constraints).
Registered as a new, disclosed, open blocker
(`q22-table-asset-contamination`, blocker-ledger-2011.yaml) rather than
silently left undocumented - PROMPT Phase 2D section 16's own "nenhum
blocker pode sumir" applies equally to a newly-found one going
unrecorded. Does not affect Q22's own passed status: the truth table
itself is already fully and correctly reconstructed as Markdown text in
the statement; `table-01.png` is a supplementary fallback asset, not the
primary source of truth for this question.

**MINIMAL FIX** (not implemented, for a future phase): thread the same
`column_bounds` parameter ADR 35 added to `render_region` into
`render_table_region` too - `DetectedTable` would need its own
`owner_x_bounds`-equivalent, computed the same way, from the question's
own `QuestionRegion` and `detect_column_margins` at the `pipeline.py`
call site (`DetectedTable`, unlike `VisualRegion`, is not itself computed
per-owner today).
