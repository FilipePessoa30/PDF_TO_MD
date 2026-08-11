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

import pymupdf
import pytest

from enade.extraction.layout import extract_page_lines
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


# --- Phase 1C: D3 (table) and D5 (two-column code) regression tests ----------


def _question(extraction_result, question_id: str):
    result, _ = extraction_result
    return next(q for q in result.questions if q.id == question_id)


def test_d3_truth_table_is_structured_with_a_mandatory_visual_fallback(extraction_result):
    d3 = _question(extraction_result, "enade-2021-cc-b-d03")
    assert d3.content_blocks is not None
    table_blocks = [b for b in d3.content_blocks if b.type == "table"]
    asset_blocks = [b for b in d3.content_blocks if b.type == "asset"]
    assert len(table_blocks) == 1
    assert len(asset_blocks) == 1  # mandatory visual fallback, regardless of validation status
    table = table_blocks[0]
    assert table.headers == ["", "", "1", "2", "3", "4", "5", "6"]
    assert len(table.rows) == 5  # variable/formula-label row + 4 F/V data rows
    assert table.rows[0] == ["a", "b", "a → ¬ b", "b ∧ a", "¬ b ∨ b", "a ∨ b", "b → a", "¬ b → a"]
    # Every data row is exactly 8 cells of V/F, never fabricated.
    for row in table.rows[1:]:
        assert len(row) == 8
        assert all(cell in ("V", "F") for cell in row)
    # The asset referenced by the AssetBlock must be a real, declared asset.
    asset_ids = {a.id for a in d3.assets}
    assert asset_blocks[0].asset_id in asset_ids


def test_d5_heapify_code_is_complete_and_correctly_ordered(extraction_result):
    d5 = _question(extraction_result, "enade-2021-cc-b-d05")
    assert d5.content_blocks is not None
    code_blocks = [b for b in d5.content_blocks if b.type == "code"]
    assert len(code_blocks) == 1
    code = code_blocks[0].text
    # Every real construct from the source listing must survive, in order -
    # this is the exact function body that used to be silently dropped
    # (see docs/decisions.md, "Phase 1C" ADR).
    for marker in (
        "int left(int i) { return (2 * i + 1); }",
        "int right(int i) { return (2 * i + 2); }",
        "void heapify (int *a, int n, int i)",
        "e = left(i);",
        "d = right(i);",
        "if (e < n && a[e] > a[i])",
        "if (max != i)",
        "heapify(a, n, max);",
        "void buildHeap(int *a, int n)",
        "for (i = (n-1)/2; i >= 0; i--)",
    ):
        assert marker in code
    assert code.index("void heapify") < code.index("void buildHeap")
    assert code.index("e = left(i);") < code.index("heapify(a, n, max);")
    # The genuine blank line between "int e, d, max, aux;" and "e = left(i);".
    assert "int e, d, max, aux;\n\n   e = left(i);" in code


def test_d5_statement_prose_is_not_swallowed_by_the_tree_diagram_region(extraction_result):
    d5 = _question(extraction_result, "enade-2021-cc-b-d05")
    assert "heap máximo" in d5.statement
    assert "CORMEN" in d5.statement


# --- Phase 1C: Q20 (line-number gutter, l/1 glyph) regression tests ----------


def test_q20_code_has_no_line_number_gutter_leaked_into_it(extraction_result):
    q20 = _question(extraction_result, "enade-2021-cc-b-q20")
    assert q20.content_blocks is not None
    code_blocks = [b for b in q20.content_blocks if b.type == "code"]
    assert len(code_blocks) == 1
    code = code_blocks[0].text
    # None of the printed line numbers 1-26 leaked into the code text as a
    # token (PROMPT Phase 1C section 8.1) - checked structurally (no line
    # starts with a bare integer followed by whitespace and more code),
    # not by a blind substring search for any occurrence of a digit.
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        first_token = stripped.split()[0] if stripped.split() else ""
        assert not first_token.isdigit(), f"line-number gutter leaked into code line: {line!r}"
    assert "int funcao2(int vetor[], int v, int i, int f){" in code
    assert code.index("int funcaol") < code.index("int funcao2")


def test_q20_preserves_the_documented_l_glyph_verbatim_no_semantic_correction(extraction_result):
    """Forensic finding (PROMPT Phase 1C section 8.2, see docs/decisions.md):
    direct glyph-outline comparison (16x zoom crops) shows the character in
    both "funcaol" (function definition) and "m+l" (line 18) matches the
    unambiguous 'l' reference shape (flat top serif + base serif, e.g. the
    'l' in "#include") and is visibly distinct from the '1' reference shape
    (diagonal top flag, e.g. in "TAM 10" and both other "funcao1"
    occurrences - the printf call and the alternatives prose). This is a
    genuine inconsistency in the source PDF's own typesetting (the
    definition and its two call sites are not spelled identically), not an
    extraction defect - the pipeline must keep transcribing exactly what
    each occurrence's glyph shows, never "fixing" it to make the code
    compile or read as if the function were consistently named.
    """
    q20 = _question(extraction_result, "enade-2021-cc-b-q20")
    code_blocks = [b for b in q20.content_blocks if b.type == "code"]
    code = code_blocks[0].text
    assert (
        "int funcaol(int vetor[], int v){" in code
    )  # definition: lowercase L, confirmed by glyph shape
    assert (
        "return funcao2(vetor, v, m+l, f);" in code
    )  # recursive call: lowercase L, confirmed by glyph shape
    assert "funcao1(vetor, 15)" in code  # unrelated call site: digit 1, confirmed by glyph shape
    assert "m+1" not in code  # never silently "corrected" without typographic evidence
    assert "funcao1(int vetor" not in code  # the definition itself must not be silently renamed


# --- Phase 1C: answer-standard-only assets (D4 + D1-D5 audit) ----------------


def test_d4_answer_standard_has_its_own_four_diagrams(extraction_result):
    """D4's padrao text references 4 genuinely new diagrams ('conforme
    abaixo', the notation legend, and the 'S'/'Cout' worked examples) - see
    docs/decisions.md, "Phase 1C" ADR. All 4 verified by direct visual
    inspection of the rendered crops.
    """
    d4 = _question(extraction_result, "enade-2021-cc-b-d04")
    assert d4.answer_standard is not None
    assert len(d4.answer_standard.assets) == 4
    ids = {a.id for a in d4.answer_standard.assets}
    assert ids == {"padrao-01", "padrao-02", "padrao-03", "padrao-04"}
    for asset in d4.answer_standard.assets:
        assert asset.path.startswith("enade-2021-cc-b-d04/answer-standard/")
        assert asset.sha256 is not None and len(asset.sha256) == 64


def test_d4_answer_standard_assets_are_never_mixed_with_question_assets(extraction_result):
    d4 = _question(extraction_result, "enade-2021-cc-b-d04")
    question_paths = {a.path for a in d4.assets}
    padrao_paths = {a.path for a in d4.answer_standard.assets}
    assert question_paths.isdisjoint(padrao_paths)
    assert all("answer-standard/" not in p for p in question_paths)
    assert all("answer-standard/" in p for p in padrao_paths)


def test_d4_padrao_diagram_does_not_duplicate_the_reprinted_question_figure(extraction_result):
    """D4's own figure ("Somador Completo de 1-bit") is reprinted a second
    time inside the padrao PDF (page 4), immediately before the rubric
    heading - that reprint must never become a *second* copy of an asset
    already captured from the prova (see docs/decisions.md)."""
    d4 = _question(extraction_result, "enade-2021-cc-b-d04")
    assert len(d4.assets) == 1  # only the prova's own figure-01
    assert d4.answer_standard.assets[0].source_page == 5  # first padrao asset, not page 4


def test_only_d4_has_answer_standard_assets_among_d1_through_d5(extraction_result):
    """PROMPT Phase 1C section 9.2: re-audited D1-D5's padrao text and every
    embedded image on padrao pages 1-8 - only D4's rubric section
    references (and contains) genuinely new diagrams. D3's and D5's own
    padrao pages (4 and 7 respectively) also contain images, but those are
    reprints of the question's own already-captured figure/table, not new
    answer-standard content, and must not be captured here.
    """
    result, _ = extraction_result
    discursives = {
        q.question_number: q for q in result.questions if q.question_type.value == "discursive"
    }
    assert set(discursives) == {1, 2, 3, 4, 5}
    for number, q in discursives.items():
        assert q.answer_standard is not None
        if number == 4:
            assert len(q.answer_standard.assets) == 4
        else:
            assert q.answer_standard.assets == [], f"D{number} unexpectedly has padrao assets"


# --- Phase 1C section 18: monospace region detection, no prose normalization -


def test_monospace_region_is_correctly_detected_on_a_real_two_column_page():
    """Direct, explicit test of layout.py's monospace detection (PROMPT
    Phase 1C section 18) - D5's page 17 is real, verified ground truth: the
    left column (prose) must never be flagged monospace, the right column
    (the heapify/buildHeap listing) must always be.
    """
    doc = pymupdf.open(PROVA_PATH)
    try:
        lines = extract_page_lines(doc[16], page_number=17)
    finally:
        doc.close()

    prose_lines = [ln for ln in lines if ln.x0 < 280 and "heap" in ln.text.lower()]
    code_lines = [ln for ln in lines if ln.x0 >= 290 and "void" in ln.text]

    assert prose_lines, "expected to find left-column prose lines"
    assert code_lines, "expected to find right-column code lines"
    assert all(not ln.is_monospace for ln in prose_lines)
    assert all(ln.is_monospace for ln in code_lines)


def test_code_lines_never_go_through_prose_spacing_reconstruction():
    """PROMPT Phase 1C section 7.3/18: code must never be run through the
    ligature/faux-space reconstruction built for prose (spacing.py) - a
    monospace ``Line`` must always have empty ``spacing_corrections``,
    verified directly against D5's real code lines.
    """
    doc = pymupdf.open(PROVA_PATH)
    try:
        lines = extract_page_lines(doc[16], page_number=17)
    finally:
        doc.close()

    code_lines = [ln for ln in lines if ln.is_monospace]
    assert code_lines
    assert all(ln.spacing_corrections == () for ln in code_lines)
