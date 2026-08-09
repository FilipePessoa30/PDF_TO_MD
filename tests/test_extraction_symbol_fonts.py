from __future__ import annotations

from enade.extraction.symbol_fonts import is_symbol_font, substitute_symbol_font_text


def test_is_symbol_font_matches_known_font_case_insensitively():
    assert is_symbol_font("EuclidSymbol-BoldItalic") is True
    assert is_symbol_font("euclidsymbol-bolditalic") is True
    assert is_symbol_font("Calibri") is False
    assert is_symbol_font("Calibri-Bold") is False


def test_substitute_replaces_all_known_symbols():
    assert substitute_symbol_font_text("a ® ¬ b") == "a → ¬ b"
    assert substitute_symbol_font_text("b Ù a") == "b ∧ a"
    assert substitute_symbol_font_text("Ø b Ú b") == "¬ b ∨ b"


def test_substitute_leaves_unrelated_text_unchanged():
    assert substitute_symbol_font_text("Enunciado normal sem símbolos.") == (
        "Enunciado normal sem símbolos."
    )


def test_substitute_is_idempotent_on_already_correct_text():
    assert substitute_symbol_font_text("a → ¬ b") == "a → ¬ b"
