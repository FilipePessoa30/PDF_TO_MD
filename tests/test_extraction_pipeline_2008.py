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
from enade.extraction.layout_overrides import load_layout_overrides
from enade.extraction.pipeline import extract_exam
from enade.models.enums import QuestionType

CORPUS_ROOT = Path(__file__).parent.parent / "data" / "raw" / "geacc-enade"
PROVA_PATH = CORPUS_ROOT / "2008" / "b1_prova.pdf"
GABARITO_PATH = CORPUS_ROOT / "2008" / "b2_gabarito.pdf"
PADRAO_PATH = CORPUS_ROOT / "2008" / "b3_padrao.pdf"
PROFILE_PATH = Path(__file__).parent.parent / "data" / "manifests" / "exam-structure-2008.yaml"
OVERRIDES_PATH = Path(__file__).parent.parent / "data" / "manifests" / "layout-overrides.yaml"

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
        layout_overrides=load_layout_overrides(OVERRIDES_PATH),
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


def test_q29_no_longer_has_sidebar_fragment_inserted_mid_sentence(extraction_result):
    """Regression test for ``q29-inline-sidebar-fragment`` (RESOLVED Phase
    3G): the grammar diagram's own 'A'/'B' production labels, previously
    blanket-protected by the old fixed alternative-marker regex regardless
    of position, must no longer bleed into the statement - contextual_relation_gate's
    margin-aware exemption (``_is_marker_at_margin``) correctly absorbs them
    into figure-01 instead.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q29 = questions_by_number[29]
    assert q29.statement.endswith(
        "Considere a gramática G definida pelas regras de produção ao lado, em que os "
        "símbolos não-terminais são S, A e B, e os símbolos terminais são a e b. Com "
        "relação a essa gramática, é correto afirmar que"
    )
    assert "A ÷ a" not in q29.statement
    assert "B ÷ b" not in q29.statement


def test_q75_statement_is_now_complete(extraction_result):
    """Regression test for ``q75-region-merge-content-loss`` (RESOLVED
    Phase 3G): the NAPT statement, previously entirely empty, must now be
    complete and match the source verbatim. The separate, pre-existing
    alternative-D diagram-label contamination
    (``q75-alternative-d-diagram-label-bleed``) is intentionally not
    asserted against here - it remains open.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q75 = questions_by_number[75]
    assert q75.statement.startswith(
        "Considere que a figura ao lado ilustre o cenário de NAPT em uma empresa"
    )
    assert q75.statement.endswith(
        "quais deverão ser os endereços IP de origem contidos nos pacotes de A e B, "
        "respectivamente, que chegarão a esse servidor?"
    )
    assert "cujos equipamentos de rede interna (LAN) usam endereços IP privados" in q75.statement


def test_q12_statement_is_now_complete(extraction_result):
    """Regression test for ``q12-partial-content-loss`` (RESOLVED Phase
    3H, Cluster D): 'base', 'na', 'complexidade', 'ciclomatica.' were four
    separate same-baseline PyMuPDF dict-mode line fragments, individually
    swallowed as figure-label candidates. fragment_reconstruction_gate
    rejoins them into one physical line.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q12 = questions_by_number[12]
    assert (
        "cujo número de caminhos pode ser determinado com base na complexidade ciclomática."
        in q12.statement
    )


def test_q63_statement_is_now_complete(extraction_result):
    """Regression test for ``q63-region-merge-content-loss`` (RESOLVED
    Phase 3H, Cluster D): 'a seguinte representação de' was its own
    fragmented run of same-baseline line entries, individually swallowed
    as figure-label candidates.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q63 = questions_by_number[63]
    assert q63.statement.startswith(
        "Considere a seguinte representação de abstração de generalização/especialização,"
    )


def test_q71_statement_is_now_complete(extraction_result):
    """Regression test for ``q71-region-merge-content-loss`` (RESOLVED
    Phase 3H, Cluster D): 'e acoplamento são dois conceitos' and 'conceito
    de ocultação de informação.' were their own fragmented same-baseline
    line entries.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q71 = questions_by_number[71]
    assert (
        "Coesão e acoplamento são dois conceitos fundamentais para a qualidade do projeto modular"
        in q71.statement
    )
    assert "relacionada ao conceito de ocultação de informação." in q71.statement


def test_q71_alternative_b_c_boundary_is_now_correct(extraction_result):
    """Regression test for ``q71-alternative-b-c-cross-contamination``
    (RESOLVED Phase 3I): assembler._find_alternative_starts's own purely
    textual, right-to-left search had no margin awareness, so a genuine
    line-wrap of alternative B's own prose ("...dos módulos B e" / "C é
    maior e o acoplamento do projeto é maior.") that happened to match the
    marker shape for 'C' was mistaken for the real C marker, swallowing
    C's own real opening lines into B. alternative_groups.find_alternative_group
    prefers the on-margin candidate (the real marker) over the off-margin
    one (the wrapped continuation line).
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q71 = questions_by_number[71]
    alternative_b = next(a for a in q71.alternatives if a.letter == "B")
    alternative_c = next(a for a in q71.alternatives if a.letter == "C")
    assert alternative_b.text == (
        "Em relação à alternativa 1, na alternativa 2, a coesão do módulo A é menor, "
        "a dos módulos B e C é maior e o acoplamento do projeto é maior."
    )
    assert alternative_c.text == (
        "Em relação à alternativa 1, na alternativa 2, a coesão do módulo A é maior, "
        "a dos módulos B e C é menor e o acoplamento do projeto é maior."
    )


def test_q13_statement_no_longer_duplicates_alternative_e(extraction_result):
    """Regression test for ``q13-duplicated-alternative-text`` (RESOLVED
    Phase 3J): alternative E's own text genuinely overflows into the top
    of the next printed column on page 8 (it did not fit below D in Q13's
    own left-column position), so its own reading-order position is
    *after* D even though its raw y0 is smaller than every earlier
    alternative's own y0 on that page. The old ``(page, y0)`` cutoff
    comparison in assembler.assemble_question re-admitted it into the
    statement it had already correctly left for the alternatives, on top
    of it being correctly assembled as alternative E - the same source
    line published in two destinations. assembler._reading_order_index
    slices the statement using the cutoff line's own reading-order
    position within ``content_lines``, not its raw geometric position.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q13 = questions_by_number[13]
    assert q13.statement == (
        "Considerando o conjunto A = {1, 2, 3, 4, 5, 6}, qual opção corresponde a uma "
        "partição desse conjunto?"
    )
    alternative_e = next(a for a in q13.alternatives if a.letter == "E")
    assert alternative_e.text == "{{1, 2}, {2, 3}, {3, 4}, {4, 5}, {5, 6}}"


def test_d60_value_annotations_are_attached_to_their_own_item(extraction_result):
    """Regression test for ``d60-valor-annotation-misattachment`` (RESOLVED
    Phase 3J): the three "(valor: X pontos)" annotations for items A, B, C
    are typeset in their own narrow column, which extract_page_lines's own
    column-major reading order sorts after every other column on the
    page - detaching them from the items they belong to and, worse, gluing
    the first one onto item C's own trailing text (item C published with
    A's own 3,0-point value instead of its real 4,0).
    annotations.reattach_value_annotations reattaches each one by real
    geometric interval containment against each item's own position.
    """
    result, _ = extraction_result
    d60 = _discursive_by_number(result)[60]
    assert (
        "Apresente os cálculos necessários. (valor: 3,0 pontos)\n\n"
        "B Na presença de ruído térmico" in d60.statement
    )
    assert "considere que log10 (1.023) = 3,01. (valor: 3,0 pontos)" in d60.statement
    assert d60.statement.rstrip().endswith(
        "é possível adotar mais de 16 níveis de sinalização no referido canal? "
        "Justifique. (valor: 4,0 pontos)"
    )
    # The old, wrong shape must not survive: two orphaned annotation
    # paragraphs trailing after item C's own text.
    assert "\n\n(valor: 3,0 pontos)\n\n(valor: 4,0 pontos)" not in d60.statement


def test_d10_reading_order_is_no_longer_scrambled(extraction_result):
    """Regression test for ``d10-newspaper-collage-reading-order-scramble``
    (RESOLVED Phase 3K): D10's own page opens with a photo beside a
    two-column newspaper article, continues as full-width single-column
    prose for two more motivating fragments, then closes with a genuine
    two-column bulleted "Observações" box - detect_column_margins's own
    single, page-wide (left_margin, right_margin) split pushed the entire
    right-side article (and the entire right half of the bulleted box) to
    after every left-side line on the page, scrambling three distinct
    articles' own text together out of order. reading_zones.
    zoned_reading_order (activated only for this one page, via a
    hash-locked layout override - see data/manifests/layout-overrides.yaml)
    requires genuine, concurrent two-sided evidence within each specific
    vertical window rather than one page-wide split. This test would have
    failed against the pre-Phase-3K output (each assertion below reflects
    an ordering that literally did not hold before this fix).
    """
    result, _ = extraction_result
    d10 = _discursive_by_number(result)[10]
    statement = d10.statement

    # Each article's own body stays with its own headline and its own
    # citation, in the correct relative order - never split across the
    # old algorithm's own left/right halves.
    assert statement.index("Alunos dão nota 7,1 para ensino médio") < statement.index(
        "GOIS, Antonio. Folha de S.Paulo, 11 jun. 2008"
    )
    assert statement.index("GOIS, Antonio. Folha de S.Paulo, 11 jun. 2008") < statement.index(
        "Entre os piores também em matemática e leitura"
    )
    assert statement.index("Entre os piores também em matemática e leitura") < statement.index(
        "WEBER, Demétrio. Jornal O Globo, 5 dez. 2007"
    )
    assert statement.index("WEBER, Demétrio. Jornal O Globo, 5 dez. 2007") < statement.index(
        "Ensino fundamental atinge meta de 2009"
    )
    assert statement.index("Ensino fundamental atinge meta de 2009") < statement.index(
        "GOIS, Antonio; PINHO, Angela. Folha de S.Paulo, 12 jun. 2008"
    )
    # The main task prompt comes after all three motivating fragments, and
    # the bulleted "Observações" box comes last, ending on its own value.
    assert statement.index(
        "GOIS, Antonio; PINHO, Angela. Folha de S.Paulo, 12 jun. 2008"
    ) < statement.index("A partir da leitura dos fragmentos motivadores")
    assert statement.index("A partir da leitura dos fragmentos motivadores") < statement.index(
        "Observações"
    )
    assert statement.rstrip().endswith("motivadores. (valor: 10,0 pontos)")
    # Never absorbed into or contaminated by any neighboring question.
    assert "QUESTÃO 11" not in statement


def test_q25_alternative_b_is_no_longer_word_order_scrambled(extraction_result):
    """Regression test for ``q25-alternative-b-word-order-scramble``
    (RESOLVED Phase 3H, Cluster D): PyMuPDF's own content-stream traversal
    order for two same-baseline fragments ('A' and 'transformada') did not
    match their own visual x-order - group_line_fragments always sorts by
    x0 before merging, resolving this as a side effect of the general
    mechanism (not a per-question fix).
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q25 = questions_by_number[25]
    alternative_b = next(a for a in q25.alternatives if a.letter == "B")
    assert alternative_b.text.startswith("A transformada de Hadamard da imagem apresentada")


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


def test_q13_no_longer_receives_q12_own_diagram(extraction_result):
    """Regression test for ``q13-cross-question-image-contamination``
    (RESOLVED Phase 3F, ``owner_exclusion_gate``): Q13's own alternative E
    overflows into the top of the next page column (page 8), widening
    Q13's own coarse bounding box enough to previously satisfy the
    ownership-agnostic y/x tolerance for Q12's own control-flow-graph
    diagram. Q13 is a pure set-partition question with no diagram of its
    own; Q12 must keep its own asset unaffected.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q12 = questions_by_number[12]
    q13 = questions_by_number[13]
    assert not q13.assets
    assert len(q12.assets) == 1
    assert q12.assets[0].sha256 != (q13.assets[0].sha256 if q13.assets else None)
