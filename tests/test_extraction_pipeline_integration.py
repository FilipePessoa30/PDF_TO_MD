"""End-to-end integration tests against the real 2021 CC bacharelado booklet.

Building a full synthetic 40-question exam booklet (two-column pages,
monospace code, embedded images, multi-page questions, a real gabarito/
padrao trio) to exercise the pipeline end-to-end would not meaningfully
test anything the unit tests in tests/test_extraction_*.py don't already
cover in isolation, and risks testing the fixture instead of reality. This
suite instead runs the real pipeline against the real, locally-cached
corpus (see PROMPT section 28: "Use questoes reais somente quando
necessario e mantenha rastreabilidade") and asserts the structural
invariants Phase 1A's acceptance criteria actually depend on. It is
skipped (not failed) when the corpus cache is not present, so the rest of
the suite still runs in an environment that hasn't fetched it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enade.extraction.pipeline import extract_exam
from enade.markdown_format import load_questions_directory
from enade.models.enums import (
    AutomaticValidationStatus,
    CourseCode,
    ExtractionStatus,
    VisualValidationStatus,
)

CORPUS_ROOT = Path(__file__).parent.parent / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2021" / "b1_prova.pdf"
GABARITO_PATH = CORPUS_ROOT / "2021" / "b2_gabarito.pdf"
PADRAO_PATH = CORPUS_ROOT / "2021" / "b3_padrao.pdf"

pytestmark = pytest.mark.skipif(
    not PROVA_PATH.exists(),
    reason="geacc/enade corpus not cloned locally (run scripts/fetch_corpus.py)",
)


@pytest.fixture(scope="module")
def extraction_result(tmp_path_factory: pytest.TempPathFactory):
    out_dir = tmp_path_factory.mktemp("pipeline_integration")
    return extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2021,
        course=CourseCode.CC_BACHARELADO,
        exam_id="enade-2021-b",
        questions_output_dir=out_dir / "questions",
    ), out_dir


def test_finds_exactly_the_documented_structure(extraction_result):
    result, _ = extraction_result
    m = result.metrics
    assert m.objectives_found == 35
    assert m.discursives_found == 5
    assert m.questions_found == 40
    assert result.excluded_perception_pages == [44]


def test_no_section_heading_leaks_into_statement_or_alternatives(extraction_result):
    """Regression test: "COMPONENTE ESPECIFICO" (the section-transition
    heading at the top of Discursiva 3's page) leaked into Q8's alternative
    E before chrome.py recognized it - no question's rendered text should
    ever contain a section-heading string (Phase 1B audit finding).
    """
    result, _ = extraction_result
    leaking_terms = ("COMPONENTE ESPECÍFICO", "FORMAÇÃO GERAL")
    for q in result.questions:
        for term in leaking_terms:
            assert term not in q.statement.upper(), f"{q.id}: statement contains {term!r}"
            for alt in q.alternatives:
                assert term not in alt.text.upper(), (
                    f"{q.id}: alternative {alt.letter} contains {term!r}"
                )


def test_no_cross_column_word_bleed_between_q09_and_q10(extraction_result):
    """Regression test: PyMuPDF's dict-mode text extraction occasionally
    splits one continuous visual line into several separate "line" entries
    with unusually wide gaps between them - on Q9/Q10's shared two-column
    page, "B Escalonamento por taxas monotonicas" (Q9's own alternative B)
    split into 4 fragments, and a midpoint-based column split let the tail
    fragments ("taxas", "monotonicas") cross into Q10's line range,
    corrupting Q10's statement into "...as estruturas de taxas monotonicas
    dados implementadas..." (Phase 1B audit finding, see docs/decisions.md).
    """
    result, _ = extraction_result
    q9 = next(q for q in result.questions if q.id == "enade-2021-cc-b-q09")
    q10 = next(q for q in result.questions if q.id == "enade-2021-cc-b-q10")

    assert "taxas monot" not in q10.statement.lower()
    assert "as estruturas de dados implementadas pelas classes a, b, c e d" in q10.statement.lower()
    assert any(alt.letter == "B" and "taxas monot" in alt.text.lower() for alt in q9.alternatives)


def test_multiline_alternative_is_not_swallowed_by_a_nearby_figure_region(extraction_result):
    """Regression test: Q22's DER-diagram figure region grew (via label
    absorption) far enough to overlap the start of the alternatives
    section below it. ``_line_in_region`` only ever protected an
    alternative's own marker line, not its continuation lines, so
    alternative A's own middle lines (TIPO_PET/PET table definitions and
    a foreign-key reference line) were silently dropped, leaving only the
    first and last line of a 5-line alternative (Phase 1B audit finding,
    see docs/decisions.md).
    """
    result, _ = extraction_result
    q22 = next(q for q in result.questions if q.id == "enade-2021-cc-b-q22")
    alt_a = next(alt for alt in q22.alternatives if alt.letter == "A")
    for expected in (
        "PESSOA(cpf: texto, nome: texto)",
        "TIPO_PET(codigo: inteiro, descricao: texto)",
        "codigo_tipo_pet referencia TIPO_PET(codigo)",
        "adotante referencia PESSOA(cpf)",
    ):
        assert expected in alt_a.text, f"alternative A is missing {expected!r}"


def test_no_duplicate_question_ids(extraction_result):
    result, _ = extraction_result
    ids = [q.id for q in result.questions]
    assert len(ids) == len(set(ids))


def test_every_question_id_follows_the_documented_convention(extraction_result):
    result, _ = extraction_result
    for q in result.questions:
        assert q.id.startswith("enade-2021-cc-b-")
        assert q.id[-2:].isdigit()


def test_all_objective_answers_are_linked_from_the_real_gabarito(extraction_result):
    result, _ = extraction_result
    objectives = [q for q in result.questions if q.question_type.value == "multiple_choice"]
    assert len(objectives) == 35
    for q in objectives:
        assert q.answer_validation_status.value in ("validated", "annulled")
        if q.answer_validation_status.value == "validated":
            assert q.correct_answer in {"A", "B", "C", "D", "E"}


def test_annulled_questions_29_and_33_have_no_correct_answer(extraction_result):
    result, _ = extraction_result
    by_number = {
        q.question_number: q for q in result.questions if q.question_type.value == "multiple_choice"
    }
    for number in (29, 33):
        assert by_number[number].answer_validation_status.value == "annulled"
        assert by_number[number].correct_answer is None


def test_every_gabarito_answer_matches_the_real_answer_key_exhaustively(extraction_result):
    """PROMPT section 19: revalidate Q1-Q35 against the real gabarito, not
    just aggregate counts. Every letter below was cross-checked by directly
    rendering data/raw/geacc-enade/2021/b2_gabarito.pdf (a single-page
    table) and reading it (see docs/decisions.md, Phase 1B). Q29/Q33 are
    "ANULADA" in that table - confirmed there is no letter, never modeled
    as `correct_answer="ANULADA"`, only as `answer_validation_status=annulled`
    with `correct_answer=None` (section 19's design check).
    """
    expected_letters = {
        1: "E", 2: "C", 3: "B", 4: "B", 5: "A", 6: "A", 7: "C", 8: "D",
        9: "E", 10: "B", 11: "D", 12: "B", 13: "E", 14: "C", 15: "C",
        16: "B", 17: "C", 18: "E", 19: "D", 20: "A", 21: "E", 22: "A",
        23: "C", 24: "E", 25: "B", 26: "A", 27: "D", 28: "B",
        30: "E", 31: "E", 32: "A", 34: "C", 35: "D",
    }  # fmt: skip
    annulled_numbers = {29, 33}

    result, _ = extraction_result
    by_number = {
        q.question_number: q for q in result.questions if q.question_type.value == "multiple_choice"
    }
    assert set(by_number) == set(expected_letters) | annulled_numbers

    for number, letter in expected_letters.items():
        q = by_number[number]
        assert q.correct_answer == letter, (
            f"Q{number}: expected {letter!r}, got {q.correct_answer!r}"
        )
        assert q.answer_validation_status.value == "validated"

    for number in annulled_numbers:
        q = by_number[number]
        assert q.correct_answer is None
        assert q.answer_validation_status.value == "annulled"
        # never modeled as a fake "answer" - annulled is a distinct status,
        # not a special correct_answer value.
        assert q.correct_answer != "ANULADA"


def test_all_discursive_questions_have_an_answer_standard_linked(extraction_result):
    result, _ = extraction_result
    discursives = [q for q in result.questions if q.question_type.value == "discursive"]
    assert len(discursives) == 5
    for q in discursives:
        assert q.answer_standard is not None
        assert q.answer_standard.text.strip()
        assert q.answer_standard.source_path == "2021/b3_padrao.pdf"


def test_every_answer_standard_matches_the_real_padrao_pdf_exhaustively(extraction_result):
    """PROMPT section 20: revalidate D1-D5's padrao linkage - correct
    question_id, correct pages, correct text, correct source PDF. Every
    expected substring below was cross-checked by directly rendering
    data/raw/geacc-enade/2021/b3_padrao.pdf page by page and reading it
    (see docs/decisions.md, Phase 1B) - not a placeholder "is non-empty"
    check. Also confirms the conceptual separation PROMPT section 20
    requires: the padrao is never merged into `statement` or exposed as
    `correct_answer` - it only ever lives in its own dedicated field.
    """
    expected = {
        1: {
            "pages": [2],
            "starts_with": "O respondente deve, a partir dos argumentos presentes no texto I",
            "contains": "duas ações educativas",
        },
        2: {
            "pages": [2, 3],
            "starts_with": "a) O respondente deve mencionar que as cidades inteligentes",
            "contains": "impacto social e contribua",
        },
        3: {
            "pages": [4],
            "starts_with": "a) O respondente deve dizer que a fórmula 3 contém uma tautologia",
            "contains": "consequência lógica de Q",
        },
        4: {
            "pages": [5, 6],
            "starts_with": "O respondente deve descrever a tabela verdade e desenhar o diagrama",
            "contains": "IEC 60617-12",
        },
        5: {
            "pages": [8],
            "starts_with": "a) O respondente deve mostrar que após a execução da função",
            "contains": "O(log n)",
        },
    }

    result, _ = extraction_result
    discursives_by_number = {
        q.question_number: q for q in result.questions if q.question_type.value == "discursive"
    }
    assert set(discursives_by_number) == set(expected)

    for number, exp in expected.items():
        q = discursives_by_number[number]
        standard = q.answer_standard
        assert standard is not None
        assert standard.pages == exp["pages"], (
            f"D{number}: pages {standard.pages} != {exp['pages']}"
        )
        assert standard.text.startswith(exp["starts_with"]), f"D{number}: {standard.text[:80]!r}"
        assert exp["contains"] in standard.text, f"D{number}: missing {exp['contains']!r}"
        assert standard.source_path == "2021/b3_padrao.pdf"
        assert len(standard.pdf_sha256) == 64

        # Conceptual separation (section 20): the padrao must never leak
        # into the student-facing statement or masquerade as the answer.
        assert exp["starts_with"] not in q.statement
        assert q.correct_answer is None  # discursive questions have no letter answer


def test_source_pages_are_within_the_prova_page_range(extraction_result):
    result, _ = extraction_result
    for q in result.questions:
        occurrence = q.source_occurrences[0]
        assert occurrence.source_path == "2021/b1_prova.pdf"
        assert all(1 <= p <= 48 for p in occurrence.pages)
        assert occurrence.pdf_sha256 == result.questions[0].source_occurrences[0].pdf_sha256


def test_asset_files_exist_and_hashes_match(extraction_result):
    """Resolve ``asset.path`` exactly the way a real Markdown viewer (VS
    Code, GitHub, a browser) resolves ``![...](asset.path)`` inside the
    question's own .md file: relative to that file's own directory - *not*
    against some separate "assets root" only this project's tooling knows
    about. An earlier version of this test resolved against a bespoke
    ``out_dir / "assets"`` root that matched the pipeline's own (buggy)
    output layout instead of real Markdown resolution semantics, so it kept
    passing while every image link in the generated Markdown was actually
    broken when opened normally (Phase 1B regression, caught by manually
    opening a generated question file - see docs/decisions.md).
    """
    import hashlib

    result, out_dir = extraction_result
    course_dir = out_dir / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    any_assets = False
    for q in result.questions:
        md_path = course_dir / f"{q.id}.md"
        for asset in q.assets:
            any_assets = True
            asset_path = md_path.parent / asset.path
            assert asset_path.exists(), f"{q.id}: {asset.path} does not resolve from {md_path}"
            assert hashlib.sha256(asset_path.read_bytes()).hexdigest() == asset.sha256
    assert any_assets  # sanity: this booklet does have figures


def test_written_markdown_round_trips_through_the_loader(extraction_result):
    result, out_dir = extraction_result
    questions_dir = out_dir / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    loaded = load_questions_directory(questions_dir)
    assert len(loaded) == 40
    for q in result.questions:
        assert loaded[q.id].statement == q.statement
        assert loaded[q.id].correct_answer == q.correct_answer


def test_transformation_log_records_every_spacing_correction_with_evidence(extraction_result):
    """PROMPT section 15: whenever canonical text diverges from the raw
    library text, that divergence must be auditable - tagged with a type,
    the page it came from, and a mechanical justification, not just applied
    silently. This booklet's Formacao Geral pages are known (see
    spacing.py) to carry many ligature-injected faux spaces, so the log
    must be non-empty and every entry must carry real evidence, not a
    placeholder. Different transformation mechanisms (spacing vs. label-case
    vs. symbol-font substitution) must stay distinguishable by `type`.
    """
    result, _ = extraction_result
    assert result.transformation_log, "expected at least one spacing correction to be logged"
    known_question_ids = {q.id for q in result.questions}
    known_types = {
        "glyph_spacing_reconstruction": "character_geometry",
        "label_case_normalization": "known_font_label_lookup",
        "symbol_font_substitution": "known_symbol_font_char_map",
    }
    seen_types: set[str] = set()
    for entry in result.transformation_log:
        assert entry.type in known_types
        assert entry.method == known_types[entry.type]
        assert entry.automatic is True
        assert entry.question in known_question_ids
        assert entry.source_page >= 1
        assert "->" in entry.detail  # e.g. "'ati'+'ngissem' -> 'atingissem' (gap=...pt, p.N)"
        seen_types.add(entry.type)
    assert seen_types == set(known_types), "expected all known transformation types to occur"


def test_needs_review_never_silently_becomes_verified(extraction_result):
    """A question with mechanical warnings is always needs_review. A clean
    question is only ever "extracted" from the pipeline alone - never
    "verified" without a real visual audit entry (none is supplied to this
    fixture's `extract_exam` call, see PROMPT section 12/14).
    """
    result, _ = extraction_result
    for q in result.questions:
        warnings = result.per_question_warnings.get(q.id, [])
        if warnings:
            assert q.extraction_status == ExtractionStatus.NEEDS_REVIEW
            assert q.automatic_validation == AutomaticValidationStatus.FAILED
        else:
            assert q.extraction_status == ExtractionStatus.EXTRACTED
            assert q.automatic_validation == AutomaticValidationStatus.PASSED
        assert q.visual_validation == VisualValidationStatus.NOT_PERFORMED


def test_pipeline_is_idempotent_on_a_second_run_over_unchanged_source(extraction_result, tmp_path):
    _, out_dir = extraction_result
    # Re-run into the SAME output directories used by the module-scoped fixture.
    second = extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2021,
        course=CourseCode.CC_BACHARELADO,
        exam_id="enade-2021-b",
        questions_output_dir=out_dir / "questions",
    )
    assert second.metrics.files_written == 0
    assert second.metrics.files_unchanged == 40


def test_rerun_removes_stale_asset_files_no_longer_produced(extraction_result):
    """A region-detection fix (or any other change) can make a later run
    produce fewer/different asset files for a question than an earlier run
    did. A leftover file from the earlier run that nothing in the current
    Markdown references is exactly the "final file isn't referenced by any
    question when it should be" failure PROMPT section 10 requires this
    suite to catch - a stale asset must not silently keep existing on disk.
    """
    result, out_dir = extraction_result
    course_dir = out_dir / "questions" / "2021" / "ciencia-da-computacao-bacharelado"
    question_with_assets = next(q for q in result.questions if q.assets)
    asset_dir = course_dir / question_with_assets.id
    stale_file = asset_dir / "figure-99.png"
    stale_file.write_bytes(b"not a real png, just a leftover from a previous run")
    assert stale_file.exists()

    extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2021,
        course=CourseCode.CC_BACHARELADO,
        exam_id="enade-2021-b",
        questions_output_dir=out_dir / "questions",
    )

    assert not stale_file.exists()
    remaining = {p.name for p in asset_dir.iterdir()}
    expected = {f"{asset.id}.png" for asset in question_with_assets.assets}
    assert remaining == expected
