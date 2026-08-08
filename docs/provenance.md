# Provenance policy

**No Markdown question, asset, or manifest entry may exist without a way to
trace it back to an exact PDF, page, and byte-for-byte content hash.** This
page describes how that's enforced structurally, not just as a convention.

## Levels of provenance

1. **Corpus snapshot** (`SourceRepository`, `src/enade/models/provenance.py`):
   `repository_url` + `ref` (branch) + `commit_sha`. Recorded once per
   manifest run (`SourceManifest.repository`), and printed by both
   `enade doctor` and `enade inventory`. This is what makes "which corpus
   was this generated from" answerable months later even if `geacc/enade`
   changes upstream.

2. **Per-PDF** (`PdfProvenance` / manifest `DocumentRecord`): for every
   physical PDF file - `source_path` (relative to the corpus root),
   `sha256`, `file_size_bytes`, `page_count`, `exam_year`, `document_type`,
   and `course_codes` when applicable. This is what `enade inventory`
   actually computes and writes to `data/manifests/source-exams.yaml`.

3. **Per-question-occurrence** (`SourceOccurrence`): `exam_id` (manifest
   bundle id) + `pdf_sha256` + `source_path` + `pages` + `question_number`
   + `section`. This is what a future Markdown question's front matter
   uses to point back at exactly which PDF/page(s) it was extracted from -
   see [markdown-format.md](markdown-format.md) and
   `Question.source_occurrences` in [data-contract.md](data-contract.md).

4. **Per-asset** (`Asset.source_page` + `Asset.sha256`): once an image/
   figure/table is extracted, it carries its own page number and content
   hash, independent of the question's hash.

## Why SHA-256 everywhere

Hashing every PDF (and, later, every extracted asset) means:

- `enade validate-manifest --corpus-root <path>` can detect **silent
  corpus drift** - a PDF that changed on disk since the manifest was
  generated - by re-hashing and comparing
  (`check_manifest_matches_filesystem` in
  `src/enade/validation/manifest_checks.py`).
- Two documents that are byte-identical (e.g. accidentally duplicated
  files) are flagged as a `duplicate_document` issue at the manifest level,
  or surfaced as a warning by `validate_manifest` if they show up in
  different bundle slots without being an outright naming collision.
- A future `Question.source_occurrences[i].pdf_sha256` pins the occurrence
  to an exact byte-for-byte version of a PDF, not just "the file that
  happened to be at that path" - if the corpus is ever re-fetched and a
  file has silently changed, the mismatch is detectable.

## What is *not* covered yet

Provenance down to the *pixel/region* of a page for a specific asset crop,
and down to the *exact character offsets* of a statement within a page's
text layer, are both out of scope for Phase 0 - those only matter once
real extraction (Phase 1) exists. The contract fields to carry that
information already exist (`Asset.source_page`, `SourceOccurrence.pages`),
they are just not populated by any code yet.
