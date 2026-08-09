"""Correct known math/logic symbols extracted with the wrong Unicode
codepoint because their PDF font is a "Symbol"-style font whose character
codes get decoded using the wrong (Latin) meaning, absent a working
ToUnicode CMap for that specific glyph.

## Evidence

D3's propositional-logic operators are set in font "EuclidSymbol-BoldItalic".
PyMuPDF extracts:

  - the implication arrow as "®" (Latin "registered trademark" sign)
  - conjunction (AND, "wedge") as "Ù"
  - disjunction (OR, "vee") as "Ú"
  - negation (NOT) as "Ø"

Confirmed by directly rendering the glyphs at high zoom and reading them
(see docs/decisions.md, Phase 1B): page 14's own formulas render
unambiguously as "a -> not b", "b and a", "not b or b" - the exact symbols
a logic textbook would use for implication/conjunction/disjunction/negation.
This is direct visual/glyph identity evidence, not a linguistic guess -
the same evidentiary standard as spacing.py's ligature-space fix and
label_normalization.py's case-mangled labels.

This is a closed, per-font character table, extended only after visually
confirming a new instance the same way - never a general "Symbol font"
decoder (a different PDF could map the same font name's code points to
different glyphs; this module keys off both the font name and the
specific codepoint observed here, nothing else).
"""

from __future__ import annotations

#: Font names (case-insensitive) known to need this substitution.
_SYMBOL_FONT_NAMES = frozenset({"euclidsymbol-bolditalic", "euclidsymbol"})

#: Wrongly-decoded character -> its confirmed correct Unicode symbol.
_KNOWN_SYMBOL_SUBSTITUTIONS: dict[str, str] = {
    "®": "→",  # (R) -> -> (implication)
    "Ù": "∧",  # U-grave -> ^ (and / conjunction)
    "Ú": "∨",  # U-acute -> v (or / disjunction)
    "Ø": "¬",  # O-slash -> not (negation)
}


def is_symbol_font(font_name: str) -> bool:
    return font_name.lower() in _SYMBOL_FONT_NAMES


def substitute_symbol_font_text(text: str) -> str:
    """Replace any known mis-decoded symbol-font character in ``text``.

    Caller is responsible for only invoking this on text known to come
    from a line that actually uses one of ``_SYMBOL_FONT_NAMES`` (see
    ``is_symbol_font``) - this function does not itself gate on font,
    since by the time text reaches here (post geometric-spacing
    reconstruction) it is no longer associated with per-character font
    metadata.
    """
    for wrong, right in _KNOWN_SYMBOL_SUBSTITUTIONS.items():
        text = text.replace(wrong, right)
    return text
