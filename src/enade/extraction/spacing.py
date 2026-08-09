"""Geometry-based reconstruction of spurious intra-word spaces ("faux spaces").

## Root cause (investigated in Phase 1B, see docs/decisions.md)

Words like "ati ngissem" (should read "atingissem") and "esti mati va"
(should read "estimativa") were observed concentrated in the Formacao
Geral section's body text. Inspecting the raw glyph stream with
``page.get_text("rawdict")`` at the character level showed the mechanism
precisely: the body font renders certain letter pairs ("ti" in particular)
as a single ligature glyph, and that glyph's ToUnicode CMap entry - the
table a PDF font uses to say "this glyph represents this Unicode text" -
maps to the letter sequence *plus a trailing space* (e.g. the "ti"
ligature glyph decodes to "t", "i", " " instead of just "t", "i"). The
injected space character's own bounding box is degenerate: it does not
advance forward from the preceding glyph the way a real inter-word space
does - it sits at or behind the previous glyph's right edge (observed
literally overlapping backward in one case). PyMuPDF's word tokenizer
honors that embedded space as a genuine word boundary, splitting one
visual word into two "words" in ``get_text("words")`` output.

This is a defect in the embedded font's character-decoding table, not a
misreading of a real space - so it can be detected and corrected using
*only* glyph geometry already present in the PDF, never by consulting a
Portuguese dictionary, spellchecker, or language model (PROMPT section 4:
"e proibido corrigir por conhecimento linguistico").

## The geometric signal

Measured across every word-gap in the Formacao Geral pages of the 2021 CC
booklet (Q1-Q8, D1, D2): genuine inter-word gaps are >= 1.26pt (median
~3pt, this corpus's body font varies in size across sections); every
injected-ligature-space gap measured <= 0.18pt. The two populations are
separated by roughly an order of magnitude with a wide empty margin
in between - see ``tests/test_extraction_spacing.py`` for the recorded
sample. ``GENUINE_GAP_THRESHOLD_PT`` sits in that margin.

## What this does NOT do

- It never merges two words separated by a real (even if small) gap.
- It never inserts a hyphen or guesses at word boundaries from context.
- If a gap is ambiguous (this corpus never produced one, but a future
  corpus might), the words are left unmerged and unmodified - no
  correction is silently applied outside the geometric evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf

#: A gap (points) below this is geometrically inconsistent with a real
#: inter-word space in this corpus (see module docstring for the measured
#: distributions) and is treated as an injected-ligature artifact.
GENUINE_GAP_THRESHOLD_PT = 1.0


@dataclass(frozen=True)
class SpacingCorrection:
    """One instance of two 'words' merged because their gap was geometrically spurious."""

    page_number: int
    left: str
    right: str
    gap_pt: float
    merged: str

    def describe(self) -> str:
        return f"'{self.left}'+'{self.right}' -> '{self.merged}' (gap={self.gap_pt:.3f}pt, p.{self.page_number})"


def reconstruct_line_text(
    page: pymupdf.Page,
    page_number: int,
    bbox: tuple[float, float, float, float],
    *,
    y_tolerance: float = 1.0,
) -> tuple[str | None, list[SpacingCorrection]]:
    """Reconstruct the text within ``bbox`` from word geometry, merging spurious gaps.

    Returns ``(None, [])`` if no words fall in the bbox (caller should keep
    whatever text it already had - this function only ever *replaces* text
    with a geometrically-justified equivalent, never invents content).
    """
    words = [
        w
        for w in page.get_text("words")
        if w[1] >= bbox[1] - y_tolerance
        and w[3] <= bbox[3] + y_tolerance
        and w[0] >= bbox[0] - y_tolerance
        and w[2] <= bbox[2] + y_tolerance
    ]
    if not words:
        return None, []

    words.sort(key=lambda w: w[0])

    corrections: list[SpacingCorrection] = []
    pieces: list[str] = [words[0][4]]
    for previous, current in zip(words, words[1:], strict=False):
        gap = current[0] - previous[2]
        if gap < GENUINE_GAP_THRESHOLD_PT:
            merged = pieces[-1] + current[4]
            corrections.append(
                SpacingCorrection(
                    page_number=page_number,
                    left=pieces[-1],
                    right=current[4],
                    gap_pt=gap,
                    merged=merged,
                )
            )
            pieces[-1] = merged
        else:
            pieces.append(current[4])

    return " ".join(pieces), corrections
