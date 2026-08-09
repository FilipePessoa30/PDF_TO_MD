"""Correct known, font-mangled structural labels to their canonical form.

The 2021 booklet's "TEXTO N" section labels (introducing a reading excerpt
within a Formacao Geral question's statement) are set in the same bold,
pseudo-small-caps-style font already documented for "QUESTAO N" headings
(see boundaries.py's module docstring): the font's ToUnicode table maps
certain glyphs to a case-scrambled codepoint sequence (e.g. "TEXTO I"
extracts as " tEXtO i") even though the *visual* rendering is unambiguous
bold full-caps - confirmed by rendering the page and reading it directly
(PROMPT Phase 1B section 3: "aquilo que um leitor humano efetivamente ve").

Unlike the ligature-space fix (spacing.py), this is not solved by glyph
geometry - it is a case-only defect with otherwise-correct codepoints, so
the only mechanical, non-linguistic evidence available is byte-for-byte
identity: every one of the 12 "TEXTO I"/"TEXTO II" occurrences across this
booklet decodes to one of exactly two fixed strings (whitespace/case-
normalized), plus "Capitulo I" (the Constituicao Federal excerpt's own
section heading on page 2) and "PORQUE" (the asserção-razão connector
heading, mangled on 3 Formacao Geral pages, already clean on 2 Componente
Especifico pages) - a closed, evidence-based list in the same spirit as
chrome.py's `_EXACT_CHROME_LINES` - never a general "fix case" heuristic,
and never applied to text outside this exact set. Matching requires the
*entire* line to be nothing but the label (see layout.py, ``_raw_lines``),
so it cannot fire on an incidental lowercase mention of "texto I", or the
ordinary lowercase conjunction "porque", inside a longer sentence.

A related, smaller defect was found but deliberately NOT fixed here: the
same page's book-title citation ("direito, arte e liberdade", correctly
"Direito, arte e liberdade") is mangled mid-line, not as a whole line, so
it cannot be matched by this module's whole-line mechanism without a
riskier substring-replacement approach for a single occurrence - see
docs/decisions.md for why this was left as a disclosed, non-structural
residual rather than engineering a one-off substring rule.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Exact (whitespace-normalized, case-folded) known-mangled label text ->
#: its correct canonical rendering, as confirmed by directly reading the
#: rendered PDF page (see .scratch/pdf-pages/page-02.png at the time of
#: this investigation). Closed list: only extend after visually confirming
#: a new instance the same way - never guess a pattern to generalize this.
_KNOWN_MANGLED_LABELS: dict[str, str] = {
    "texto i": "TEXTO I",
    "texto ii": "TEXTO II",
    "capítulo i": "Capítulo I",
    # The asserção-razão connector heading ("afirmação I / PORQUE /
    # afirmação II") - mangled on Formacao Geral pages (7, 9, 11) exactly
    # like TEXTO I/II, already clean uppercase on Componente Especifico
    # pages (23, 27), confirming the same font/section pattern documented
    # in boundaries.py. Whole-line matching (see normalize_known_label)
    # keeps this from ever touching the ordinary lowercase conjunction
    # "porque" used mid-sentence elsewhere on these same pages.
    "porque": "PORQUE",
}


@dataclass(frozen=True)
class LabelCorrection:
    """One instance of a known font-mangled label replaced by its canonical form."""

    page_number: int
    original: str
    corrected: str

    def describe(self) -> str:
        return f"'{self.original}' -> '{self.corrected}' (p.{self.page_number})"


def normalize_known_label(text: str) -> str | None:
    """Return the canonical form of ``text`` if it exactly matches a known
    font-mangled structural label (whole line, nothing else), else None.
    """
    key = " ".join(text.strip().lower().split())
    return _KNOWN_MANGLED_LABELS.get(key)
