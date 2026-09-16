"""Declarative exam structure profiles for booklets that do not fit the
single-(course, ExamStructure) shape ``declared_structure.py`` models.

PROMPT Phase 2A section 10: the 2011 unified "COMPUTACAO" caderno has
question ranges shared by four courses at once, plus four disjoint
course-specific ranges within the *same* PDF - not representable as one
course + four fixed part boundaries. Rather than branching the extractor on
``if year == 2011``, the shape of the booklet is data
(``data/manifests/exam-structure-2011.yaml``), loaded and validated here;
``pipeline.extract_exam`` stays agnostic to how many sections or courses a
given booklet has by consulting whatever profile it is handed.

Every range in the shipped 2011 profile was confirmed against the real PDF
text (see the YAML file's own header comment and docs/corpus.md) - this
module additionally cross-checks the *loaded* profile against the PDF at
run time (``verify_declared_profile``), the same "confirm, do not silently
assume" discipline ``declared_structure.py`` already applies to 2021.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import pymupdf
import yaml
from pydantic import BaseModel, Field, model_validator

from enade.extraction.boundaries import QuestionKind
from enade.models.enums import CourseCode


class SectionRange(BaseModel):
    """One contiguous run of question numbers sharing a section id and applicability."""

    id: str
    kind: QuestionKind
    #: ``range`` in the YAML source - aliased because a field named ``range``
    #: would shadow the builtin ``range`` type used by the ``numbers`` property below.
    number_range: tuple[int, int] = Field(..., alias="range")
    applicable_courses: list[CourseCode] = Field(..., min_length=1)

    @property
    def numbers(self) -> range:
        start, end = self.number_range
        return range(start, end + 1)

    @model_validator(mode="after")
    def _validate_range_order(self) -> SectionRange:
        start, end = self.number_range
        if start > end:
            raise ValueError(f"section {self.id!r}: range start {start} > end {end}")
        return self


class ExamStructureProfile(BaseModel):
    """A whole booklet's declarative part boundaries, independent of any one course."""

    year: int
    exam_type: str
    exam_id: str
    id_shorthand: str
    sections: list[SectionRange] = Field(..., min_length=1)
    #: The single-character course-letter prefix this unified booklet's own
    #: source filenames carry (PROMPT Phase 3A), e.g. "b" for 2008's
    #: ``b1_prova.pdf``/``b2_gabarito.pdf``/``b3_padrao.pdf``. 2011's own
    #: unified booklet has no letter at all (plain ``1_prova.pdf``), hence
    #: the default of ``None`` - not every unified booklet is named the same
    #: way, and nothing here should have to guess which convention applies.
    source_letter: str | None = None
    #: True when this booklet's discursive markers reuse the same printed
    #: number stream as its objectives, interleaved among them (2008-b's
    #: "QUESTAO 39 - DISCURSIVA" sits between objectives 38 and 41) rather
    #: than each kind having its own independent 1..N run (2011's "QUESTAO
    #: DISCURSIVA 1".."5", entirely separate from objectives 1..50 - the
    #: default, unchanged, ``False`` case). See
    #: ``boundaries.detect_question_boundaries``'s own ``combined_numbering``
    #: parameter, which this value is threaded into.
    combined_numbering: bool = False
    #: Opt-in cap (points) on how far apart two large visual-content
    #: candidates may sit in X and still be merged into one region during
    #: figure detection (PROMPT Phase 3C - see
    #: ``figures.MERGE_X_TOLERANCE``/``UNBOUNDED_MERGE_X_TOLERANCE``).
    #: ``None`` (default) means unbounded - the exact, unchanged behavior
    #: every booklet without this field set already has. Set only for a
    #: booklet whose own layout is confirmed (by direct instrumentation) to
    #: need it - never a blanket default, since a finite value was found by
    #: full regeneration to alter 2011's own Q23/Q38 and would very likely
    #: alter other already-validated corpora too if applied unconditionally.
    region_merge_x_tolerance: float | None = None
    #: Opt-in requirement (PROMPT Phase 3D section 6-7) that a label/caption
    #: absorption candidate have a font size strictly smaller than the
    #: page's own dominant body-prose font size (see
    #: ``figures._dominant_body_font_size``). ``False`` (default) means
    #: exactly the original, unchanged behavior every booklet without this
    #: field set already has. Set only for a booklet whose own layout is
    #: confirmed (by direct instrumentation) to need it - never a blanket
    #: default, since enabling it unconditionally was found by full
    #: regeneration to alter 2011's own Q05/Q33/Q34/Q35.
    caption_font_size_gate: bool = False
    #: Opt-in requirement (PROMPT Phase 3F) that a visual region explicitly
    #: owned by a *different* question (``VisualRegion.owner_key``, computed
    #: by ``figures.py`` from the same ``QuestionRegion`` geometry - see
    #: ownership.py) is never admitted into a span's own candidate set,
    #: even when it satisfies the older, ownership-agnostic y/x bounding-box
    #: tolerance in ``assembler.assemble_question``. Only ever *removes* a
    #: previously wrongly-admitted region - it can never add one, since it
    #: is purely an additional restriction layered on top of the existing
    #: tolerance, so it can only fix a false cross-question attribution,
    #: never miss a genuine one. ``False`` (default) means exactly the
    #: original, unchanged behavior every booklet without this field set
    #: already has. Set only for a booklet confirmed (by direct
    #: instrumentation) to need it - enabling it unconditionally was found
    #: by full regeneration to change 2011's own Q34 (a region genuinely
    #: unowned by either Q34 or its neighbor Q35 was, before this gate,
    #: geometrically counted as Q34's own candidate purely by y/x
    #: proximity, tripping a conservative "region fell after the
    #: alternatives cutoff" structural warning that already has a
    #: documented false-positive precedent for this exact question - see
    #: ``blocker_ledger.py``'s own ``accepted_non_material_difference``
    #: docstring - but a byte-for-byte change to a protected corpus is
    #: never accepted regardless of how the change is characterized).
    owner_exclusion_gate: bool = False
    #: Opt-in (PROMPT Phase 3G) replacement of ``assembler._line_in_region``'s
    #: original fixed-padding touch test and blanket alternative-marker
    #: exemption with a richer, contextual relation
    #: (``assembler.LineRegionRelation``/``compute_line_region_relation``):
    #: text consumption now requires geometric containment, genuine overlap
    #: against the region's own raw (pre-growth) extent, or a match against
    #: growth's own authoritative absorbed-label record - never mere
    #: touching or partial overlap - and an alternative-shaped line is only
    #: protected from region membership when it also sits at the page's
    #: own established body-text margin (``figures._is_marker_at_margin``),
    #: closing the class of defect where a diagram-internal label (an
    #: automaton input, an ER-diagram entity name) shares that exact shape.
    #: ``False`` (default) keeps the exact, original behavior every
    #: booklet without this field set already has. Set only for a booklet
    #: confirmed (by full regeneration) to need it: enabling it
    #: unconditionally was found to change 2011's own Q9/Q12/Q23/Q38 and
    #: several 2021 questions (own growth/reading-order shapes not yet
    #: characterized with the same precision as the 2008-b cases this was
    #: built for - see docs/phase-3g-report.md).
    contextual_relation_gate: bool = False
    #: Opt-in (PROMPT Phase 3H, "Cluster D") geometric rejoining of a
    #: physical line PyMuPDF's own ``get_text("dict")`` reported as several
    #: separate "line" entries sharing the exact same baseline - see
    #: ``layout.fragment_reconstruction``/``layout._raw_lines``. Two
    #: independent, documentary signals (never a dictionary/language
    #: model) are required together: a literal trailing space in the
    #: earlier fragment's own raw glyph stream, and a horizontal gap
    #: within a font-size-relative safety ceiling; a detected column
    #: boundary is never crossed regardless. ``False`` (default) keeps the
    #: exact, original per-dict-line behavior every booklet without this
    #: field set already has. Confirmed by full regeneration that this
    #: mechanism DOES fix a real, already-documented defect in 2021's own
    #: corpus (page 19's own "B Escalonamento por taxas monotonicas" split
    #: into four fragments, see layout.py's own MIN_LINES_PER_COLUMN
    #: docstring) - gated regardless, since any change to a protected
    #: corpus is reverted on principle (PROMPT: "nao aceite equivalencia
    #: semantica"), not only when it is wrong.
    fragment_reconstruction_gate: bool = False
    #: Opt-in (PROMPT Phase 3K/3L, "topologia de colunas") activation of a
    #: zone-aware, question-local reordering (see ``reading_zones.py``)
    #: for a page whose column topology changes partway down - a
    #: photo-and-article zone, then full-width prose, then a two-column
    #: bulleted list, all on the same page (2008-b's own D10, "Formação
    #: Geral Discursiva 10"). ``"disabled"`` (default) keeps the exact,
    #: original page-wide split every booklet without this field set
    #: already has - confirmed by full regeneration that 2011/2021 are
    #: byte-identical, since neither profile sets it. This field only ever
    #: *enables the capability for a booklet* - it never selects which
    #: page(s) actually activate (PROMPT Phase 3L, section 13: "o profile
    #: pode habilitar a capacidade, mas não selecionar páginas
    #: específicas"). Which question spans actually get reordered is
    #: decided per span, from structural evidence alone (see
    #: ``reading_zones.assess_eligibility`` and
    #: ``assembler._canonical_content_lines``) - never by a question ID,
    #: page number, or page hash consulted as an operational selector.
    #: ``"shadow"``: compute zones/eligibility/candidate order and record
    #: them in the transformation log for every eligible span, but always
    #: publish the original, stable order (diagnostic only - used to build
    #: the Phase 3L confusion matrix against 2008-b/2011/2021 without any
    #: risk of publishing a wrong reorder). ``"active"``: publish the
    #: candidate order instead of the stable one, but only for a span that
    #: is both structurally eligible *and* passes the differential safety
    #: oracle (word-multiset/source-id/owner conservation) - a span that
    #: fails either check keeps the original, stable order and records why.
    zoned_reading_order_mode: Literal["disabled", "shadow", "active"] = "disabled"

    @model_validator(mode="after")
    def _validate_sections(self) -> ExamStructureProfile:
        for kind in (QuestionKind.OBJECTIVE, QuestionKind.DISCURSIVE):
            claimed: set[int] = set()
            for section in self.sections:
                if section.kind != kind:
                    continue
                numbers = set(section.numbers)
                overlap = claimed & numbers
                if overlap:
                    raise ValueError(
                        f"{kind.value}: question number(s) {sorted(overlap)} claimed by "
                        "more than one section"
                    )
                claimed |= numbers
        for section in self.sections:
            if (
                CourseCode.ALL_COMPUTING in section.applicable_courses
                and len(section.applicable_courses) > 1
            ):
                raise ValueError(
                    f"section {section.id!r} range {section.number_range}: 'all-computing' "
                    "cannot be combined with an explicit course code"
                )
        return self

    def resolve(self, kind: QuestionKind, number: int) -> SectionRange | None:
        """Return the section owning ``(kind, number)``, or None if no section claims it."""
        for section in self.sections:
            if section.kind == kind and number in section.numbers:
                return section
        return None


def load_exam_structure_profile(path: Path) -> ExamStructureProfile:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ExamStructureProfile.model_validate(data)


#: Range-pair patterns cross-checked against the 2011 instructions-page
#: table (page 1). Each is a literal "<n> a <m>" substring as printed -
#: ``\s*`` absorbs the table-cell line breaks PyMuPDF's plain text
#: extraction leaves in place (e.g. "Discursiva 3 \na Discursiva 5").
_RANGE_PATTERNS: dict[str, re.Pattern[str]] = {
    "Formacao Geral objetivas (1 a 8)": re.compile(r"\b1\s*a\s*8\b"),
    "Formacao Geral discursivas (Discursiva 1 e Discursiva 2)": re.compile(
        r"(?i)discursiva\s*1\s*e\s*discursiva\s*2"
    ),
    "Componente Especifico Comum objetivas (9 a 30)": re.compile(r"\b9\s*a\s*30\b"),
    "Componente Especifico Comum discursivas (Discursiva 3 a Discursiva 5)": re.compile(
        r"(?i)discursiva\s*3\s*a\s*discursiva\s*5"
    ),
    "Licenciatura (31 a 35)": re.compile(r"\b31\s*a\s*35\b"),
    "Ciencia da Computacao (36 a 40)": re.compile(r"\b36\s*a\s*40\b"),
    "Engenharia de Computacao (41 a 45)": re.compile(r"\b41\s*a\s*45\b"),
    "Sistemas de Informacao (46 a 50)": re.compile(r"\b46\s*a\s*50\b"),
    "Questionario de percepcao (1 a 9)": re.compile(r"\b1\s*a\s*9\b"),
}


#: 2008-b's own equivalent (PROMPT Phase 3A). Unlike 2011, this booklet's
#: page 1 cover is a single embedded raster image with *zero* extractable
#: text (confirmed empirically: ``page[0].get_text()`` returns ""), so its
#: printed range table cannot be cross-checked there at all - not a defect
#: in this verification, just a limitation of what the source PDF actually
#: offers. Its Componente Especifico transition page (11) does repeat the
#: three course-specific ranges in real, selectable text ("Bacharelado em
#: Ciencia da Computacao | 21 a 38 | 39 e 40", etc. - confirmed against the
#: real PDF), so only those three are checked; Formacao Geral and Nucleo
#: Comum are not independently re-printed anywhere else in this PDF's own
#: text layer and are therefore not claimed as machine-confirmed here (see
#: docs/phase-3a-report.md for how those two were instead confirmed by
#: direct visual reading of the cover image).
_RANGE_PATTERNS_2008_B: dict[str, re.Pattern[str]] = {
    "Bacharelado em Ciencia da Computacao objetivas (21 a 38)": re.compile(r"\b21\s*a\s*38\b"),
    "Bacharelado em Ciencia da Computacao discursivas (39 e 40)": re.compile(r"\b39\s*e\s*40\b"),
    "Engenharia de Computacao objetivas (41 a 58)": re.compile(r"\b41\s*a\s*58\b"),
    "Engenharia de Computacao discursivas (59 e 60)": re.compile(r"\b59\s*e\s*60\b"),
    "Sistemas de Informacao objetivas (61 a 78)": re.compile(r"\b61\s*a\s*78\b"),
    "Sistemas de Informacao discursivas (79 e 80)": re.compile(r"\b79\s*e\s*80\b"),
}


def verify_declared_profile(
    doc: pymupdf.Document,
    instructions_page: int = 1,
    patterns: dict[str, re.Pattern[str]] | None = None,
) -> list[str]:
    """Confirm the profile's ranges are actually printed on the instructions page.

    Returns a note per pattern that could not be confirmed - never raises,
    matching ``declared_structure.parse_declared_structure``'s
    fail-loud-but-not-blocking discipline (PROMPT: "documente a estrutura
    real" rather than silently trusting the YAML).

    ``patterns`` defaults to the 2011 unified booklet's own set
    (``_RANGE_PATTERNS``) so every existing call site is unaffected; a
    different booklet whose instructions page uses different wording (see
    ``_RANGE_PATTERNS_2008_B``) passes its own set explicitly rather than
    this function guessing a booklet's shape from its year.
    """
    active_patterns = patterns if patterns is not None else _RANGE_PATTERNS
    text = doc[instructions_page - 1].get_text("text")
    return [
        f"could not confirm '{label}' in the printed instructions on page {instructions_page}"
        for label, pattern in active_patterns.items()
        if not pattern.search(text)
    ]
