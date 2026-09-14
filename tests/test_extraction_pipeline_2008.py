"""End-to-end integration tests against the real 2008-b unified booklet
(PROMPT Phase 3A/3B).

Same rationale as test_extraction_pipeline_integration.py's own docstring:
runs the real pipeline against the real, locally-cached corpus rather than a
synthetic fixture, and is skipped (not failed) when that corpus is not
present. This suite's own reason for existing is narrower and more
pointed - it is the regression test for the Phase 3B ownership/chrome fixes
that resolved the Q21/Q22/Q23 cross-question contamination (see
docs/phase-3b-report.md, section G): a single question that the data
contract refuses to build (Q8/Q38/Q55's own unstructured image
alternatives) must not derail the whole extraction, and a region that only
looks close to Q21 or Q23 must never be attributed to them just because it
sits nearby.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from enade.extraction.answer_key import parse_flat_item_gabarito
from enade.extraction.exam_profile import _RANGE_PATTERNS_2008_B, load_exam_structure_profile
from enade.extraction.pipeline import extract_exam
from enade.models.enums import QuestionType

CORPUS_ROOT = Path(__file__).parent.parent / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2008" / "b1_prova.pdf"
GABARITO_PATH = CORPUS_ROOT / "2008" / "b2_gabarito.pdf"
PADRAO_PATH = CORPUS_ROOT / "2008" / "b3_padrao.pdf"
PROFILE_PATH = Path(__file__).parent.parent / "data" / "manifests" / "exam-structure-2008.yaml"

pytestmark = pytest.mark.skipif(
    not PROVA_PATH.exists(),
    reason="geacc/enade corpus not cloned locally (run scripts/fetch_corpus.py)",
)


@pytest.fixture(scope="module")
def extraction_result(tmp_path_factory: pytest.TempPathFactory):
    out_dir = tmp_path_factory.mktemp("pipeline_2008_integration")
    profile = load_exam_structure_profile(PROFILE_PATH)
    result = extract_exam(
        prova_path=PROVA_PATH,
        gabarito_path=GABARITO_PATH,
        padrao_path=PADRAO_PATH,
        corpus_root=CORPUS_ROOT,
        exam_year=2008,
        exam_id=profile.exam_id,
        questions_output_dir=out_dir / "questions",
        structure_profile=profile,
        structure_verification_page=11,
        structure_verification_patterns=_RANGE_PATTERNS_2008_B,
        output_dir_name="all-computing",
        answer_key_parser=parse_flat_item_gabarito,
    )
    return result, out_dir


def test_all_80_academic_questions_are_accounted_for(extraction_result):
    """77 published + 3 explicitly excluded (unstructured image
    alternatives, PROMPT Phase 3A) = 80 - never silently fewer.
    """
    result, _ = extraction_result
    published_ids = {q.id for q in result.questions}
    assert len(published_ids) == 77
    for excluded_number in (8, 38, 55):
        exclusion_note = f"objective {excluded_number}: could not build a valid Question"
        assert any(exclusion_note in w for w in result.structural_warnings), (
            f"objective {excluded_number} must be loudly excluded, not silently missing"
        )


def test_q21_statement_is_complete_and_uncontaminated(extraction_result):
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q21 = questions_by_number[21]
    assert "EMPREGADO" in q21.statement
    assert "sobrenome" in q21.statement
    assert "Árvore-B+" in q21.statement
    # Never contains Q22's or Q23's own real content (PROMPT Phase 3B
    # section 12 - the exact bug this test exists to catch: Q21's own
    # rendered figure/statement previously included the entirety of Q22
    # and part of Q23).
    assert "tradutor" not in q21.statement  # Q22's own statement
    assert "EMPREGADO" not in q21.statement or "Pessoa" not in q21.statement  # Q23 uses "Pessoa"
    assert "banco de dados relacional" not in q21.statement  # Q23's own opening


def test_q22_statement_is_complete_and_not_lost(extraction_result):
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q22 = questions_by_number[22]
    assert "software tradutor" in q22.statement
    assert "velocidade de execução" in q22.statement
    # Never contaminated by the page-11 instructions table this bug used to
    # leak (PROMPT Phase 3B section D/M).
    assert "Número das Questões" not in q22.statement
    assert "21 a 38" not in q22.statement


def test_q23_statement_is_complete_and_uncontaminated(extraction_result):
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q23 = questions_by_number[23]
    assert "banco de dados relacional" in q23.statement
    assert "Pessoa" in q23.statement
    # Never contains Q21's own content.
    assert "EMPREGADO" not in q23.statement
    assert "sobrenome" not in q23.statement


def _discursive_by_number(result):
    return {
        q.question_number: q for q in result.questions if q.question_type == QuestionType.DISCURSIVE
    }


def test_d09_statement_is_now_complete(extraction_result):
    """PROMPT Phase 3C, region-merge X-axis fix: D09's own page-6 RASCUNHO
    ruled grid was collapsing (via a Y-only merge) into a nearly-full-page-
    width region, absorbing the entire statement (blocker
    d09-region-merge-content-loss). That alone only stopped the statement
    from being empty (see docs/phase-3c-report.md section E) - the real
    article headline ("DIREITOS HUMANOS EM QUESTAO", 11pt) was still being
    absorbed into the photo's own region on the first label-absorption
    pass, geometrically indistinguishable from a legitimate diagram label
    by proximity/width alone. PROMPT Phase 3D's own font-size gate
    (caption_font_size_gate, ExamStructureProfile) fixes this: a candidate
    must be strictly smaller than the page's own dominant body font size
    (10pt here) to be eligible for absorption - the 11pt headline no longer
    qualifies, and the statement is now genuinely complete, matching the
    real source (page 6) word for word.
    """
    result, _ = extraction_result
    d09 = _discursive_by_number(result)[9]
    assert "DIREITOS HUMANOS EM QUESTÃO" in d09.statement
    assert "François JULIEN, filósofo e sociólogo." in d09.statement
    assert "Neste ano, em que são comemorados os 60 anos da Declaração Universal" in d09.statement
    assert "a habitação como moradia digna" in d09.statement
    assert "a segurança como bem-estar" in d09.statement
    assert "o trabalho como ação para a vida" in d09.statement
    assert "Tendo em vista o exposto acima" in d09.statement
    assert "Seu texto deve ter entre 8 e 10 linhas." in d09.statement


def test_d40_sql_code_block_is_now_preserved_verbatim(extraction_result):
    """PROMPT Phase 3D, caption_font_size_gate: combined with the Phase 3C
    region-merge fix, D40's own statement is now built via content_blocks
    (paragraph/code/asset/paragraph/asset/paragraph) with a full, verbatim
    fenced SQL code block, instead of the severely scrambled single blob
    documented in docs/phase-3c-report.md section E. One residual defect
    remains (a diagram label bleeding in as loose text - not asserted
    against here, see docs/phase-3d-report.md).
    """
    result, _ = extraction_result
    d40 = _discursive_by_number(result)[40]
    assert d40.content_blocks is not None
    code_blocks = [b for b in d40.content_blocks if b.type == "code"]
    assert any("SELECT nome, endereco" in b.text for b in code_blocks)
    assert any("WHERE idade < 40 OR renda > 30000;" in b.text for b in code_blocks)


def test_d10_no_longer_loses_its_own_newspaper_fragments(extraction_result):
    """PROMPT Phase 3D: D10's own three newspaper fragments (each with a
    headline+body+citation) were previously missing 2 of 3 headlines/bodies
    almost entirely (docs/phase-3c-report.md section L). The font-size gate
    recovers all three headline titles and all three citations - asserted
    here. It does NOT recover every body paragraph in full: a Phase 3E
    re-audit against page 7's own raw text found headline 1's own entire
    body paragraph, and headline 2's own opening clause, still missing -
    genuine content loss, not merely a reading-order defect as Phase 3D's
    own note had claimed (see docs/phase-3e-report.md,
    d10-label-absorption-newspaper-fragments). Not re-asserted as missing
    here (this suite documents confirmed-present content, not open
    defects) - see the blocker ledger for the corrected, complete picture.
    """
    result, _ = extraction_result
    d10 = _discursive_by_number(result)[10]
    assert "Alunos dão nota 7,1 para ensino médio" in d10.statement
    assert "Entre os piores também em matemática e leitura" in d10.statement
    assert "Ensino fundamental atinge meta de 2009" in d10.statement
    assert "GOIS, Antonio. Folha de S.Paulo, 11 jun. 2008" in d10.statement
    assert "WEBER, Demétrio. Jornal O Globo, 5 dez. 2007" in d10.statement
    assert "GOIS, Antonio; PINHO, Angela. Folha de S.Paulo, 12 jun. 2008" in d10.statement


def test_q01_multi_caption_page_is_not_regressed_by_font_size_gate(extraction_result):
    """PROMPT Phase 3D regression guard: Q1's own page has 5 small portrait
    images, each with its own multi-line caption - together outnumbering
    Q1's own real body paragraph. An early, flat-mode version of
    ``figures._dominant_body_font_size`` picked the captions' own (6pt)
    font size as "the page's body size", which then wrongly excluded a
    same-size roman-numeral index label ("IV") from absorption, stranding
    it and fragmenting the region into a spurious extra asset (confirmed by
    direct regeneration before this was fixed to also require the page's
    own dominant left margin as evidence). Q1 was already ``passed`` before
    Phase 3D and must not regress.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q01 = questions_by_number[1]
    assert len(q01.assets) == 2
    assert "Disponível em" not in q01.statement
    assert "Ermakoff" not in q01.statement
    assert "reflete o clima político-social vivido naquela época." in q01.statement


def test_d20_statement_is_complete_and_has_no_spurious_figure(extraction_result):
    """PROMPT Phase 3C: D20's own page-10 RASCUNHO grid was previously
    producing a spurious figure that split the statement mid-word
    ('Tabelas de dispersao (tabelas' / [image] / 'hash) armazenam...') -
    not caught by Phase 3B's own re-inspection, which had claimed this
    question was already fully resolved. Regression test for the corrected
    claim: the statement must be one coherent, unsplit passage with no
    figure asset at all.
    """
    result, _ = extraction_result
    d20 = _discursive_by_number(result)[20]
    assert "Tabelas de dispersão (tabelas hash) armazenam" in d20.statement
    assert not d20.assets


def test_d39_statement_is_complete_and_has_no_spurious_figure(extraction_result):
    """Same RASCUNHO-grid-figure-split defect as D20 (see
    test_d20_statement_is_complete_and_has_no_spurious_figure), found for
    the first time in Phase 3C on D39's own item B."""
    result, _ = extraction_result
    d39 = _discursive_by_number(result)[39]
    assert "gramática acima é ambígua" in d39.statement
    assert not d39.assets


def test_q68_where_clause_is_no_longer_split(extraction_result):
    """PROMPT Phase 3D, 'Classe B': Q68's own page 29 has a 3-line
    nested-SQL-subquery continuation (query II's own WHERE clause) that
    ``layout.detect_column_margins`` was mistaking for a genuine second
    page column (font size 9pt against the page's own 10pt body, short
    relative to the rest of the page), scrambling query II across two
    disconnected fragments (blocker q68-sql-code-block-reordering). Fixed
    by requiring both a short column AND an off-body-size font before
    rejecting a candidate split (layout.py, MIN_COLUMN_HEIGHT_RATIO/
    _is_short_off_size_column) - confirmed safe for Q49/Q50's own genuine
    two-column page and 2011's own D5 by full regeneration (zero drift).
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q68 = questions_by_number[68]
    assert (
        "WHERE D.IdDep=E.IdDep and E.salario >10000 and E.IdDep IN "
        "(SELECT IdDep FROM Empregado GROUP BY IdDep HAVING count(*) > 5) GROUP BY NomeDep;"
        in q68.statement
    )


def test_q61_gains_its_own_itil_diagram(extraction_result):
    """PROMPT Phase 3E: Q61's own ITIL service-lifecycle diagram is printed
    on page 27 *before* Q61's own "QUESTAO 61" marker (D60's own discursive
    text fills the space above it, with an explicit "Figura para a questao
    61" caption documenting the diagram's real owner) - marker-position-based
    span-slicing therefore attributed it to D60/Q62 instead (see
    q62-cross-question-diagram-label-bleed / d60-cross-question-diagram-
    label-bleed). The forward-reference-caption mechanism
    (reference_captions.py) now moves the caption and its anchored diagram
    labels to Q61's own span before any region detection/merge runs. Q61 was
    already ``passed`` before this phase (its own statement text was never
    truncated) but had no figure of its own at all.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q61 = questions_by_number[61]
    assert len(q61.assets) == 1
    assert q61.assets[0].type == "image"
    assert "A figura acima, adaptada do documento" in q61.statement
    assert q61.statement.index("![Figura") < q61.statement.index("A figura acima")
    assert "QUESTÃO 61" not in q61.statement
    assert "Estágios do ciclo de vida" not in q61.statement  # moved into the figure, not loose text


def test_q62_no_longer_contaminated_by_q61_diagram(extraction_result):
    """Regression test for ``q62-cross-question-diagram-label-bleed``
    (RESOLVED Phase 3E): Q62's own real statement (INTOSAI audit ethics
    question) must be complete, uncontaminated by Q61's own ITIL diagram
    labels, and carry no spurious figure of its own.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q62 = questions_by_number[62]
    assert not q62.assets
    assert q62.statement.endswith(
        "qual valor ou princípio um auditor estaria primariamente falhando em atender?"
    )
    assert "Suporte a serviços" not in q62.statement
    assert "Gerenciamento de infra-estrutura de TIC" not in q62.statement
    alternative_e = next(a for a in q62.alternatives if a.letter == "E")
    assert alternative_e.text == "competência"


def test_d60_no_longer_contaminated_by_q61_diagram(extraction_result):
    """Regression test for ``d60-cross-question-diagram-label-bleed``
    (RESOLVED Phase 3E): D60's own Nyquist/Shannon statement must end at
    its own real content (page 26), never spilling onto page 27's own Q61
    diagram caption/labels.
    """
    result, _ = extraction_result
    d60 = _discursive_by_number(result)[60]
    assert "Figura para a questão 61" not in d60.statement
    assert "Estágios do ciclo de vida" not in d60.statement
    assert d60.statement.rstrip().endswith("(valor: 4,0 pontos)")
