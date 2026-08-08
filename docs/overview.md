# Overview

## Vision

An open-source study platform for the Brazilian **ENADE** exam, starting
with the Computing area (Ciência da Computação, Engenharia da Computação,
Sistemas de Informação). The end state: a student can practice with real,
correctly-attributed past questions, get automatic grading on objective
questions, receive a diagnosis of *which concept* they got wrong (not just
*that* they got it wrong), and be pointed at study material - offline by
default, with optional LLM-backed explanations when available.

None of that exists yet. Building it on top of unverified, ad-hoc-extracted
questions would make every later feature untrustworthy. So Phase 0 does not
build any of it.

## What Phase 0 actually is

Phase 0 is the foundation: a reproducible way to obtain the source PDFs, an
automated (not hand-typed) inventory of what is actually in them, and the
canonical data contracts every future question/asset/taxonomy/material
record must satisfy. It intentionally stops short of extracting real
questions - see [decisions.md](decisions.md) for why extraction is
sequenced after the contract, not before.

Concretely, this phase delivers:

1. A pinned, reproducible reference to the source corpus
   ([geacc/enade](https://github.com/geacc/enade)) - exact commit, not just
   "the latest version" (see [corpus.md](corpus.md)).
2. Code that *discovers* the corpus structure (years, courses, document
   triples) rather than hard-coding it, and *compares* what it found
   against what was expected going in, documenting any divergence.
3. A provenance model so that any future Markdown question can be traced
   back to an exact PDF, page, and SHA-256 ([provenance.md](provenance.md)).
4. Pydantic + JSON Schema contracts for a Question, an Asset, a Taxonomy, a
   Misconception, and a Material - with explicit `pending`/`unknown`
   states everywhere real data isn't known yet
   ([data-contract.md](data-contract.md)).
5. A documented per-question Markdown format for future authoring/extraction
   ([markdown-format.md](markdown-format.md)).
6. A minimal CLI (`enade doctor|inventory|validate-manifest|validate-schema`)
   and a test suite that exercises all of the above against small,
   synthetic fixtures - never by asserting on hard-coded corpus numbers.

## What Phase 0 is not

No frontend, no login, no database of users, no LLM integration, no OCR
pass, no bulk question extraction, no finished taxonomy, no invented
answers. See [decisions.md](decisions.md) for the reasoning and
`README.md`'s scope note for the literal list.

## Where to go next

- New to the corpus? Start with [corpus.md](corpus.md).
- Want the exact shape of a Question record? [data-contract.md](data-contract.md).
- Reproducing the inventory yourself? [reproduce.md](reproduce.md).
