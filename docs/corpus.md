# Source corpus

## Origin

- **Repository**: <https://github.com/geacc/enade>
- **Branch used**: `master`
- **Commit pinned for this phase's inventory run**: `a657632b72b97468c8a5eb3b433d1abb4a5511c5`
- **License of the repository's code/structure**: MIT (see its `LICENSE`).

The repository is treated **strictly as a read-only data source**. Nothing
in this project writes to it, and it is never assumed to stay the same in
the future - which is exactly why the commit is pinned and recorded in
every generated manifest (`repository.commit_sha`), not just written down
once in this document.

> **Licensing note.** The MIT license in `geacc/enade` covers that
> repository's own contents as redistributed there. It does **not**
> obviously extend copyright permissions over the underlying ENADE exam
> PDFs themselves, which are official documents published by INEP/MEC
> (Brazil). Before any derived content (Markdown questions, images, text)
> is published or redistributed outside this project, the licensing/usage
> terms of the original INEP documents must be checked explicitly. This
> project does not assume that hosting the PDFs in an MIT-licensed repo
> settles that question. See also the note in `LICENSE` at the project root.

## What the corpus's own README says

Quoting `geacc/enade`'s `README.md` (read before writing any parsing code,
per this phase's instructions): provas/gabaritos are grouped in directories
named by application year, and filenames are prefixed by a letter
identifying the course:

- `b` = Ciência da Computação, **bacharelado**
- `l` = Ciência da Computação, **licenciatura**
- `e` = **Engenharia** da Computação
- `s` = **Sistemas** de Informação

This convention is implemented in [`src/enade/inventory/filenames.py`](../src/enade/inventory/filenames.py)
(`COURSE_LETTER_MAP`), and is exercised by [`tests/test_filenames.py`](../tests/test_filenames.py).

## Filename convention (as discovered, not just as documented)

Every real file in the corpus matches `<letter?><seq>_<doctype>.pdf`:

| doctype     | seq | meaning                                     |
|-------------|-----|----------------------------------------------|
| `prova`     | 1   | the exam booklet (questions)                 |
| `gabarito`  | 2   | the official answer key (objective questions)|
| `padrao`    | 3   | the "padrao de resposta" - grading rubric for discursive questions |

`letter` is one of `b`/`l`/`e`/`s` above, or **absent** for the 2011
unified booklet (see below). The scanner treats a letter/sequence mismatch
as a warning, not a hard failure - and treats any filename that doesn't
match this pattern at all as an "unexpected filename" / orphan, never as a
silently-ignored file.

## Structure actually found (automated inventory, not hand-counted)

Running `enade inventory` against the pinned commit (see
[reproduce.md](reproduce.md) for the exact command) produced:

```
years: 7            (2005, 2008, 2011, 2014, 2017, 2019, 2021)
bundles: 16          (one per year+course "sitting")
exams: 16
answer_keys: 16
answer_standards: 16
total_pdfs: 48
orphan_files: 0
errors: 0
warnings: 0
```

Per-year course letters found:

| year | course letters found | matches the Phase 0 brief? |
|------|-----------------------|------------------------------|
| 2005 | b, e                  | yes |
| 2008 | b, e                  | yes |
| 2011 | (none - unified booklet) | yes |
| 2014 | b, e, l               | yes |
| 2017 | b, e, l, s            | yes |
| 2019 | e                     | yes |
| 2021 | b, l, s               | yes |

This **exactly matches** the structure described going into this phase (16
provas / 16 gabaritos / 16 padroes / 48 PDFs total, with the year-by-year
course breakdown given in the brief). That match is a *result*, produced by
[`enade.inventory.expected_corpus.compare_with_expected`](../src/enade/inventory/expected_corpus.py)
diffing the *discovered* manifest against the previously-observed shape -
it is not hard-coded into the scanner itself. If a future corpus update
adds/removes a booklet, `enade inventory` will print the divergence instead
of silently agreeing or silently failing.

All 48 PDFs were found to have a **usable text layer** (not scanned
images) - i.e. `pdfmeta.extract_pdf_metadata` extracted a non-trivial
amount of text from every page of every document. This means Phase 1
extraction can start from `extraction_method: text_layer` for the whole
corpus; no OCR pass is currently required for this specific corpus
snapshot. This is worth re-checking if the corpus is ever refreshed from a
different source.

## The 2011 special case

2011 is the one year with **no course letter** in its filenames
(`2011/1_prova.pdf`, `2_gabarito.pdf`, `3_padrao.pdf`): a single caderno
titled **"COMPUTAÇÃO"** shared by all four courses. This was verified by
extracting and reading the actual PDF text (not assumed from the filename
alone), specifically the instruction table on page 1 of `2011/1_prova.pdf`
and the transition page before the course-specific block (page 21):

```
Partes                                            Questoes    Peso das   Peso dos
                                                                questoes   componentes
Formacao Geral / Objetivas                        1 a 8        60%        25%
Formacao Geral / Discursivas                      Discursiva 1  40%
Componente Especifico Comum / Objetivas           9 a 30        85% (obj.) 75%
Componente Especifico Comum / Discursivas         Discursiva 2  15% (disc.)
  Licenciatura                                    31 a 35 (+ Discursivas 3-5)
Componente Especifico / Objetivas:
  Ciencia da Computacao                           36 a 40
  Engenharia de Computacao                        41 a 45
  Sistemas de Informacao                          46 a 50
Questionario de percepcao da prova                1 a 9         -          -   (not scored)
```

Page 21 (the transition page immediately before question 31) makes the
per-course split explicit for the reader:

> "A seguir serao apresentadas questoes [...] relativas ao Componente
> Especifico dos cursos da area de Computacao [...] Voce devera responder
> APENAS as questoes referentes ao curso no qual voce esta inscrito."
> (Cursos: Licenciatura 31-35, Ciencia da Computacao 36-40, Engenharia de
> Computacao 41-45, Sistemas de Informacao 46-50.)

### Consequence for the data model

A question from this booklet **cannot** be modeled as belonging to exactly
one course. Concretely, in this canonical Question contract
(see [data-contract.md](data-contract.md)):

- Questions 1-8 (Formacao Geral) and 9-30 (Componente Especifico Comum):
  `applicable_courses: [all-computing]` - they apply to all four courses at
  once, using the `CourseCode.ALL_COMPUTING` alias rather than spelling out
  all four course codes by hand.
- Questions 31-35: `applicable_courses: [ciencia-da-computacao-licenciatura]`
  only.
- Questions 36-40 / 41-45 / 46-50: `applicable_courses` naming exactly one
  of `ciencia-da-computacao-bacharelado` / `engenharia-da-computacao` /
  `sistemas-de-informacao` respectively.

This is why `Question.applicable_courses` is a **list**, not a
`course: str` field - see the fixture
[`tests/fixtures/questions/valid/q-all-computing-2011.md`](../tests/fixtures/questions/valid/q-all-computing-2011.md)
and the model validator in
[`src/enade/models/question.py`](../src/enade/models/question.py) that
rejects combining `all-computing` with an explicit course code (redundant/
ambiguous) while allowing any combination of concrete course codes.

At the manifest level, the 2011 bundle is flagged with
`is_unified_booklet: true` and `course_codes: [all-computing]` so this case
is visible without opening the PDF - see
[`ExamBundle`](../src/enade/inventory/manifest.py).

### The 2011 gabarito is also structurally different

`2011/2_gabarito.pdf` is a single flat `ITEM -> GABARITO` table (items 1..50
across all courses in one list) and includes at least one `ANULADA`
(annulled) entry. This is why the canonical Question contract has a
dedicated `answer_validation_status` state (`annulled`) instead of forcing
`correct_answer` to always be a letter - see
[data-contract.md](data-contract.md).

## Known limitations of this inventory

- The manifest records *file-level* facts (hash, page count, text-layer
  presence). It says nothing yet about which pages inside a PDF correspond
  to which question - that is Phase 1 (extraction) work, out of scope here.
- "Usable text layer" is a heuristic (average extractable characters per
  page above a threshold - see `pdfmeta.MIN_AVG_CHARS_PER_PAGE_FOR_USABLE_TEXT`),
  not a guarantee that every individual page's text is complete or correctly
  ordered (multi-column PDFs, as observed in the 2011 booklet, can interleave
  columns when extracted naively with `-layout`-style tools; the raw
  per-page extraction used here does not attempt column reconstruction).
