from __future__ import annotations

from enade.extraction.label_normalization import normalize_known_label


def test_recognizes_known_mangled_texto_labels():
    assert normalize_known_label("tEXtO i") == "TEXTO I"
    assert normalize_known_label("tEXtO ii") == "TEXTO II"


def test_recognizes_known_mangled_capitulo_label():
    assert normalize_known_label("Capítulo i") == "Capítulo I"


def test_recognizes_known_mangled_porque_label():
    assert normalize_known_label("pORQuE") == "PORQUE"
    assert normalize_known_label("PORQUE") == "PORQUE"  # already-clean form is idempotent


def test_does_not_match_porque_used_as_an_ordinary_conjunction():
    assert normalize_known_label("aparência, porque há hortaliças ruins") is None


def test_normalizes_whitespace_and_case_before_matching():
    assert normalize_known_label("  TeXtO   I  ") == "TEXTO I"
    assert normalize_known_label("texto ii") == "TEXTO II"


def test_does_not_match_incidental_mention_inside_a_sentence():
    # Real prose mentioning "texto I" as part of a longer sentence must
    # never be rewritten - only a line that IS exactly the label matches
    # (enforced by the caller passing whole-line text, not by this
    # function inspecting context it doesn't have).
    assert normalize_known_label("o texto I apresenta um caso") is None


def test_does_not_match_unrelated_or_unknown_text():
    assert normalize_known_label("texto iii") is None
    assert normalize_known_label("texto") is None
    assert normalize_known_label("questao 01") is None
    assert normalize_known_label("") is None
