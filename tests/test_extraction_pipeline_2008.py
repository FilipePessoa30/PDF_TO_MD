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
from enade.extraction.layout_overrides import LayoutOverrideSet, load_layout_overrides
from enade.extraction.pipeline import extract_exam
from enade.models.enums import AssetType, QuestionType

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


@pytest.fixture(scope="module")
def extraction_result_no_layout_overrides(tmp_path_factory: pytest.TempPathFactory):
    """Same extraction, but with an *empty* ``LayoutOverrideSet`` - no
    entries loaded at all, not even D10's own now-superseded
    ``force_zoned_reading_order_page`` rule. PROMPT Phase 3L section 14:
    proves D10's own reordering is selected by structural eligibility
    alone, with literally no override of any kind available to consult.
    """
    out_dir = tmp_path_factory.mktemp("pipeline_2008_no_overrides")
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
        layout_overrides=LayoutOverrideSet(overrides=[]),
    )
    return result, out_dir


def test_all_80_academic_questions_are_accounted_for(extraction_result):
    """80 published, 0 excluded - never silently fewer.

    Was 77 published + 3 excluded until PROMPT Fase 3W (Q55's own
    alternatives re-diagnosed as 100% vector-drawn formulas, never raster
    images, published via the declared-inline-formula mechanism Fase 3S
    already built for Q45), 78 published + 2 excluded until PROMPT Fase
    3X (Q38's own circuit pin labels and output-label annotation,
    previously leaking as loose statement text, excluded via
    force_region_membership), and 79 published + 1 excluded until PROMPT
    Fase 3Y, which closed the last gap: Q8's own 5 fine-art photographs -
    a genuinely different, real-photograph/two-row-horizontal-layout
    shape, requiring a new `declare_raster_alternative_region` mechanism
    (see q08-unstructured-image-alternatives (RESOLVED) in
    blocker-ledger-2008.yaml) - are now individually published, one per
    alternative.
    """
    result, _ = extraction_result
    published_ids = {q.id for q in result.questions}
    assert len(published_ids) == 80
    assert not result.structural_warnings


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


def test_d40_opening_sentence_word_order_is_no_longer_scrambled(extraction_result):
    """Regression test for ``d40-table-reading-order-scramble`` (RESOLVED
    Phase 3N): "Cliente," is set in a Courier/monospace font run inline in
    otherwise-regular prose - PyMuPDF reports it as a separate dict-mode
    "line" entry whose own bounding-box top sits 0.39pt above its own
    neighbors, even though its true glyph baseline (span origin[1]) is
    identical to them. ``layout.py``'s own bbox-based line sort inverted
    the correct left-to-right order, scrambling "SGBD relacional possui a
    relacao Cliente, com as informacoes" into "SGBD relacional Cliente,
    possui a relacao com as informacoes". ``same_row_ordering.py`` fixes
    this generally (never a question ID, page, or specific text as a
    selector) by grouping fragments that share a true baseline, normalized
    by font size, and sorting them by x0 - this test pins the exact,
    corrected word order; a plain substring check would not catch a
    silent re-scramble that still contains every word.
    """
    result, _ = extraction_result
    d40 = _discursive_by_number(result)[40]
    statement = d40.statement
    assert statement.startswith(
        "O banco de dados de um sistema de controle bancário implementado por meio de "
        "um SGBD relacional possui a relação Cliente, com as informações apresentadas "
        "a seguir, em que a chave primária da relação é grifada."
    )
    assert "SGBD relacional Cliente, possui a relação" not in statement


def test_q33_item_markers_are_no_longer_displaced(extraction_result):
    """Regression test for ``q33-item-marker-displacement`` (RESOLVED
    Phase 3N): the same mechanism as D40's own fix above - each of the
    four judged items' own roman-numeral marker (and, for items II/IV, an
    italicized word sharing its own printed row) was displaced mid-
    sentence by the same bbox-vs-true-baseline mismatch. This test pins
    the exact, fully-corrected statement (not merely "every word present
    somewhere") - Q33 had no other, independent blocker, so it is now
    fully resolved.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q33 = questions_by_number[33]
    statement = q33.statement
    assert (
        "julgue os itens seguintes. I A análise top-down é adequada quando a linguagem "
        "de entrada é definida por uma gramática recursiva à esquerda. II "
        "Independentemente da abordagem adotada, top-down ou bottom-up, o analisador "
        "sintático utiliza informações resultantes da análise léxica. III Se os "
        "programas em uma linguagem podem ser analisados tanto em abordagem top-down "
        "como em bottom-up, a gramática dessa linguagem é ambígua. IV A análise "
        "bottom-up utiliza ações comumente conhecidas como deslocamentos e reduções "
        "sobre as sentenças do programa-fonte."
    ) in statement
    assert "linguagem de I entrada" not in statement
    assert "top-down II ou" not in statement
    assert "bottom-up IV A análise" not in statement


def test_four_more_questions_had_the_same_undetected_item_marker_displacement(
    extraction_result,
):
    """PROMPT Phase 3N: the same mechanism fixing D40/Q33 also corrects
    four previously-undetected cases (D59, Q41, Q52, Q56) - each was
    already marked ``passed`` because every word was present, but a
    marker/word sat one row-fragment out of place. Pins each one's own
    corrected substring; see the blocker ledger for the full before/after.
    """
    result, _ = extraction_result
    d59 = _discursive_by_number(result)[59]
    assert "durante 2 ut finais. II T2 tem prioridade 2" in d59.statement
    assert "A partir de II seu início" not in d59.statement

    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q41 = questions_by_number[41]
    assert "modelo, permitindo que tokens individualizados" in q41.statement
    assert "modelo, tokens permitindo que individualizados" not in q41.statement

    q52 = questions_by_number[52]
    assert "I int: a, b; /* dois pontos após a palavra int */" in q52.statement
    assert "II int a,b; real a; /* declaração dupla da variável a */" in q52.statement

    q56 = questions_by_number[56]
    assert "I Diferentes níveis de tensão no fio, como !5 V e +5 V, e transições" in q56.statement


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
    complete and match the source verbatim.
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


def test_q75_alternative_d_no_longer_bleeds_diagram_labels(extraction_result):
    """Regression test for ``q75-alternative-d-diagram-label-bleed``
    (RESOLVED Phase 3M): the NAPT diagram's own interior labels
    ("Computador A"/"Computador B"/its IP-address annotations) sit at or
    below the first alternative's own y0 (they print alongside
    alternatives D and E, not above the statement), and
    ``assembler._in_alternatives_section``'s own former blanket exemption
    (every line from the first alternative marker onward was exempted from
    all region filtering, regardless of position) let them bleed into
    alternative D's own text as if they were its own trailing words. The
    exemption is now narrowed to a structural test - see
    ``_in_alternatives_section``'s own docstring - that correctly still
    protects a genuine multi-line alternative's own continuation (this
    same test file's own Q22/Q68/D40 regression tests) while no longer
    protecting a large, disjoint diagram region's own interior content.
    """
    result, _ = extraction_result
    questions_by_number = {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }
    q75 = questions_by_number[75]
    alt_d = next(alt for alt in q75.alternatives if alt.letter == "D")
    assert alt_d.text == "138.76.28.1 e 138.76.28.2"
    assert "Computador" not in alt_d.text
    assert "10.0.0" not in alt_d.text


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
    (RESOLVED Phase 3K, generalized Phase 3L): D10's own page opens with a
    photo beside a two-column newspaper article, continues as full-width
    single-column prose for two more motivating fragments, then closes with
    a genuine two-column bulleted "Observações" box - detect_column_margins's
    own single, page-wide (left_margin, right_margin) split pushed the
    entire right-side article (and the entire right half of the bulleted
    box) to after every left-side line on the page, scrambling three
    distinct articles' own text together out of order. reading_zones.
    zoned_reading_order requires genuine, concurrent two-sided evidence
    within each specific vertical window rather than one page-wide split.
    As of Phase 3L this activates through purely structural eligibility
    (assembler._canonical_content_lines / reading_zones.assess_eligibility) -
    the Phase 3K page/hash-locked override this test used to depend on is
    marked ``status: superseded`` in data/manifests/layout-overrides.yaml
    and is no longer consulted by any code path (see
    test_d10_activates_automatically_with_no_layout_override_present below,
    which proves the same ordering holds even with an *empty* override set).
    This test would have failed against the pre-Phase-3K output (each
    assertion below reflects an ordering that literally did not hold before
    that fix).
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


def test_d10_activates_automatically_with_no_layout_override_present(
    extraction_result_no_layout_overrides,
):
    """PROMPT Phase 3L, section 14: the exact same assertions as
    ``test_d10_reading_order_is_no_longer_scrambled`` above, but run
    against an extraction given a completely empty ``LayoutOverrideSet`` -
    no ``force_zoned_reading_order_page`` entry, no override of any kind.
    D10's own reordering must be identical either way, because
    ``LayoutOverrideSet.forces_zoned_reading_order`` was removed from
    layout_overrides.py entirely in Phase 3L and no code path consults it
    any more - the override in data/manifests/layout-overrides.yaml is
    kept only as historical record (``status: superseded``).
    """
    result, _ = extraction_result_no_layout_overrides
    d10 = _discursive_by_number(result)[10]
    statement = d10.statement

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
    assert statement.index(
        "GOIS, Antonio; PINHO, Angela. Folha de S.Paulo, 12 jun. 2008"
    ) < statement.index("A partir da leitura dos fragmentos motivadores")
    assert statement.index("A partir da leitura dos fragmentos motivadores") < statement.index(
        "Observações"
    )
    assert statement.rstrip().endswith("motivadores. (valor: 10,0 pontos)")
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
    # PROMPT Phase 3O regression guard: a `LineRegionRelation.looks_like_body_prose`
    # unconditional veto (font size alone authorizing a line's own
    # consumption decision) was tried and reverted this phase precisely
    # because it let these two bare roman-numeral picture labels ("IV",
    # "V" - each set at the same 9.96pt raw size as this page's own real
    # body prose, a coincidence of rendering, not evidence they are body
    # text) leak into the statement as a stray "IV V" paragraph between
    # the two figures. See docs/phase-3o-report.md, Section 22/T.
    assert "IV V" not in q01.statement
    assert "\nIV\n" not in f"\n{q01.statement}\n"


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


# --- PROMPT Phase 3O: region-merge-content-loss disposition fixes --------
#
# Every question below shares the same root cause: a line was genuinely
# absorbed by a figure/diagram/table region's own growth or raw merge (a
# real, unchanged region/crop), but that absorption never amounted to
# evidence the line's own *canonical text* should be removed - only that it
# happened to end up geometrically inside the region's own final bbox
# (`_line_in_region`/`_text_consumption_decision`, assembler.py). Each fix
# is an individually-verified `protect_from_region_membership` override
# (data/manifests/layout-overrides.yaml), never a change to region
# detection, merge, label growth, or crop generation (Section 23) - so
# every asset/crop below is asserted unchanged alongside the restored text.


def _objective_by_number(result):
    return {
        q.question_number: q
        for q in result.questions
        if q.question_type == QuestionType.MULTIPLE_CHOICE
    }


def test_q02_statement_and_citation_are_now_complete(extraction_result):
    """Regression test for ``q02-region-merge-content-loss`` (RESOLVED
    Phase 3O): the transition sentence into the image and the image's own
    two-line citation were absorbed by figure-01's own region as growth/
    label-absorption side effects, never authorized to be removed from
    canonical text - both are now present, in order, and figure-01 itself
    is unaffected.
    """
    result, _ = extraction_result
    q02 = _objective_by_number(result)[2]
    assert (
        "Essa afirmativa reitera a necessária interação das diferentes espécies, "
        "representadas na imagem a seguir." in q02.statement
    )
    assert (
        "Disponível em http://curiosidades.spaceblog.com.br. Acesso em 10 out. 2008."
        in q02.statement
    )
    assert q02.statement.index("Essa afirmativa reitera") < q02.statement.index("Disponível em")
    assert q02.statement.index("Disponível em") < q02.statement.index("Depreende-se dessa imagem")
    assert len(q02.assets) == 1


def test_q05_citation_is_now_complete(extraction_result):
    """Regression test for ``q05-image-citation-dropped`` (RESOLVED Phase
    3O): the photo's own two-line citation was absorbed by figure-01's own
    region - mechanically identical to 2008-b D10's own "Revista Veja..."
    photo credit, which correctly stays hidden (no general geometric signal
    separates the two cases, see docs/phase-3o-report.md Section 7/13) -
    and is restored via an individually-verified override rather than a
    general rule.
    """
    result, _ = extraction_result
    q05 = _objective_by_number(result)[5]
    assert (
        "STRICKLAND, Carol; BOSWELL, John. Arte Comentada: da pré-história ao "
        "pós-moderno. Rio de Janeiro: Ediouro [s.d.]." in q05.statement
    )
    assert q05.statement.index("STRICKLAND, Carol") < q05.statement.index(
        "Além da preocupação com a perfeita composição"
    )
    assert len(q05.assets) == 1


def test_q07_framing_clause_is_now_complete(extraction_result):
    """Regression test for ``q07-region-merge-content-loss`` (RESOLVED
    Phase 3O for the framing clause; the alternative E contamination this
    test's own earlier version pinned as "pre-existing, unchanged" is now
    itself resolved by Phase 3P - see
    ``test_q07_alternative_e_is_no_longer_contaminated_by_the_chart_citation``
    for the full, current-state assertion).
    """
    result, _ = extraction_result
    q07 = _objective_by_number(result)[7]
    assert (
        "De acordo com o mesmo gráfico, o percentual da renda total correspondente "
        "aos 20% de maior renda foi," in q07.statement
    )
    assert len(q07.assets) == 1


def test_q24_framing_paragraph_is_now_complete(extraction_result):
    """Regression test for ``q24-region-merge-content-loss`` (RESOLVED
    Phase 3O for the framing paragraph): the decoder-block's own 4-line
    framing paragraph, absorbed by the (correct, unchanged) merged region
    spanning the truth table and all 3 item circuits, is present.
    """
    result, _ = extraction_result
    q24 = _objective_by_number(result)[24]
    assert (
        "Considere o bloco decodificador ilustrado acima, o qual opera segundo a "
        "tabela apresentada. Em cada item a seguir, julgue se a função lógica "
        "mostrada corresponde ao circuito lógico a ela associado." in q24.statement
    )
    assert len(q24.assets) == 1


def test_q24_item_markers_i_and_ii_are_now_present(extraction_result):
    """Full regression test for ``q24-item-i-ii-markers-missing`` (RESOLVED
    Phase 3Q): items "I" and "II"'s own bare markers, genuinely present and
    unambiguous in the PDF's own text layer (charcode 73 = "I" in
    WinAnsiEncoding, font PKFJJH+TT2EC3o00 - identical to sibling marker
    "III", which already survived to the published corpus), were excluded
    by a razor-thin geometric coincidence: item III's own wider 3-glyph
    marker run starts far enough left (x0=43.9) to fall *outside* the
    merged region's own grown bbox (x0=45.2), landing in
    ``state=boundary_crossing`` (never accepted for consumption), while
    I/II's own narrower runs (x0=45.2/46.7) stay fully enclosed
    (``state=contained``, accepted and excluded) - confirmed by direct
    instrumentation of `_line_in_region`/`compute_line_region_relation`
    against the real, unchanged region object (see
    docs/phase-3q-report.md, Section G/H, and
    data/manifests/source-token-ledger-2008.yaml for the full low-level
    identity evidence). Two individually-verified
    `protect_from_region_membership` overrides
    (data/manifests/layout-overrides.yaml) resolve this without touching
    region detection, merge, growth or crop - figure-01.png (still showing
    all three item circuits I/II/III) is unaffected.

    Verified beyond substring checks: the exact final statement text, in
    order, and that the alternatives (which already reference "itens I e
    II"/"itens II e III" etc.) are unaffected.
    """
    result, _ = extraction_result
    q24 = _objective_by_number(result)[24]
    assert q24.statement == (
        "![Figura da questão](enade-2008-computing-q24/figure-01.png)\n\n"
        "Considere o bloco decodificador ilustrado acima, o qual opera segundo a "
        "tabela apresentada. Em cada item a seguir, julgue se a função lógica "
        "mostrada corresponde ao circuito lógico a ela associado.\n\n"
        "I\n\n"
        "II\n\n"
        "III\n\n"
        "Assinale a opção correta."
    )
    assert [(a.letter, a.text) for a in q24.alternatives] == [
        ("A", "Apenas um item está certo."),
        ("B", "Apenas os itens I e II estão certos."),
        ("C", "Apenas os itens I e III estão certos."),
        ("D", "Apenas os itens II e III estão certos."),
        ("E", "Todos os itens estão certos."),
    ]
    assert len(q24.assets) == 1


def test_q45_items_i_and_ii_are_now_complete(extraction_result):
    """Regression test for ``q45-region-merge-content-loss`` (RESOLVED
    Phase 3O for items I/II): the intro's own closing clause, the "Com
    base nessas informações..." transition, and items I and II's own full
    body text (all absorbed by the two solid-of-revolution figures' own
    merged regions) are present.
    """
    result, _ = extraction_result
    q45 = _objective_by_number(result)[45]
    assert "como resultado da integral" in q45.statement
    assert "Com base nessas informações, julgue os itens a seguir." in q45.statement
    assert (
        "Cada seção transversal do sólido S obtida quando este é interceptado em "
        "x = c por um plano paralelo ao plano yOz é um círculo centrado no ponto "
        "(c, 0, 0) e de raio medindo f(x)" in q45.statement
    )
    assert "Se P é uma partição uniforme do intervalo [a, b], sendo" in q45.statement
    assert len(q45.assets) == 2  # figure-01 (intro diagrams) + figure-02 (Fase 3S formula)


def test_q45_item_iii_own_three_lines_are_now_complete(extraction_result):
    """Full regression test for the item-III residual of
    ``q45-region-merge-content-loss`` (RESOLVED Phase 3Q for the three
    missing lines). Item III's own continuation - "torno do eixo x da
    região do plano delimitada pelo", "eixo x, o gráfico de" and "e as
    retas x = 0 e x = 2." - was excluded by the exact same oversized-merge
    region (``state=contained`` against the grown bbox, unrelated to
    these lines' own content) as the 12 lines Phase 3O already restored;
    not found during that phase's own investigation, which mis-
    characterized the residual as "one missing character" rather than
    three whole lines. All three are genuinely present, unambiguous text
    (confirmed via rawdict/texttrace - no font/glyph ambiguity) and are
    now protected via three individually-verified
    `protect_from_region_membership` overrides
    (data/manifests/layout-overrides.yaml) - figure-01.png is unaffected.

    The word-order concern Phase 3O itself documented ("entao" reading
    before "para ci...") is confirmed, by this phase's own low-level
    verification (`page.get_text("rawdict")`'s own `origin` field - both
    spans share the identical baseline y=440.04), to be the *correct*
    printed order, not a defect - Phase 3O's own characterization was
    itself mistaken. No same-row reordering was needed or attempted.

    The gap between "o grafico de" and "e as retas" (RESOLVED Phase 3S) is
    now filled by a dedicated inline-formula asset (``figure-02``,
    ``type: equation``) instead of a missing-text gap: item III's own
    "f(x) = sqrt(x)" is 100% vector-drawn artwork (confirmed via
    ``page.get_drawings()`` - never a font character), so it is preserved
    visually, at the correct point in the reading order, rather than
    fabricated as text - see data/manifests/source-token-ledger-2008.yaml,
    token q45-item-iii-function-formula.
    """
    result, _ = extraction_result
    q45 = _objective_by_number(result)[45]
    # The three lines Phase 3Q restored, in the correct order, with the
    # Fase 3S formula asset landing exactly between "o grafico de" and
    # "e as retas" - never fabricated as text (zero literal "f(x)"/"sqrt"/
    # "√" substring anywhere in the published statement).
    assert (
        "III É igual a 2B o volume do sólido gerado pela rotação em torno do eixo "
        "x da região do plano delimitada pelo eixo x, o gráfico de\n\n"
        "![Figura da questão](enade-2008-computing-q45/figure-02.png)\n\n"
        "e as retas x = 0 e x = 2." in q45.statement
    )
    assert "então para ci 0 [ xi, xi ! 1], 1< i < n." in q45.statement
    assert "f(x)" not in q45.statement.split("gráfico de\n\n")[1].split("e as retas")[0]
    assert "sqrt" not in q45.statement.lower()
    assert "√" not in q45.statement
    assert len(q45.assets) == 2
    formula_asset = next(a for a in q45.assets if a.id == "figure-02")
    assert formula_asset.type == AssetType.EQUATION
    assert formula_asset.source_page == 19


def test_q54_opening_clause_is_now_complete(extraction_result):
    """Regression test for ``q54-region-merge-content-loss`` (RESOLVED
    Phase 3O): the statement's own opening clause, previously cut short
    mid-sentence at "nó", is now complete; the routing-table diagram
    (correctly image-only - its own cell contents are never asserted as
    text here) is unaffected.
    """
    result, _ = extraction_result
    q54 = _objective_by_number(result)[54]
    assert (
        "No encaminhamento de pacotes na Internet, cabe a cada nó determinar se é "
        "possível entregar um pacote diretamente ao destino" in q54.statement
    )
    assert not q54.statement.lstrip().startswith("nó determinar")
    assert len(q54.assets) == 1


def test_d40_own_two_region_merge_residuals_are_now_resolved(extraction_result):
    """Regression test for ``d40-region-merge-content-loss`` (RESOLVED
    Phase 3O): the Cliente(...) schema's own second code line and the
    indices paragraph's own opening clause, both absorbed by figure-02's
    own region (widened by a false merge with an unrelated ruled
    "RASCUNHO" grid, not touched this phase), are now present - figure-02
    itself (still showing the schema's own underlined-primary-key
    formatting) is unaffected.
    """
    result, _ = extraction_result
    d40 = _discursive_by_number(result)[40]
    assert d40.content_blocks is not None
    code_blocks = [b for b in d40.content_blocks if b.type == "code"]
    assert any("data_nascimento, renda, idade)" in b.text for b in code_blocks)
    assert (
        "Para essa relação, foram criados dois índices secundários: IndiceIdade, "
        "para o atributo idade" in d40.statement
    )
    asset_ids = [a.id for a in d40.assets]
    assert "figure-02" in asset_ids


# --- PROMPT Fase 3R: D40's own residual cosmetic "F" leak -----------------


def test_d40_cosmetic_sigma_operator_leak_is_resolved(extraction_result):
    """Regression test for the "F" cosmetic leak documented since Phase
    3G (RESOLVED Phase 3R): the query-tree diagram's own selection-
    operator symbol (font PKHEMP+TT2F14o00, charcode 70/glyph_id 2 - a
    custom relational-algebra operator subset font whose declared
    WinAnsiEncoding fallback decodes to Latin "F", but whose own glyph
    program paints sigma, confirmed by rendering figure-01.png) no longer
    publishes as a standalone, contextless paragraph between figure-01 and
    the closing paragraph. figure-01.png (already showing both operator
    symbols in full - "pi_nome,endereco" / "sigma_idade < 40 OR renda <
    30000" / "Cliente") is unaffected; the sibling "B" leak (same font,
    charcode 66/glyph_id 1, appended to the framing sentence as
    "...respectivamente. B\tnome,endereco") is a separate, pre-existing
    artifact explicitly out of this phase's own scope and must remain
    exactly as before.
    """
    result, _ = extraction_result
    d40 = _discursive_by_number(result)[40]
    assert d40.content_blocks is not None
    paragraph_texts = [b.text for b in d40.content_blocks if b.type == "paragraph"]
    assert "F" not in paragraph_texts
    assert not any(text.strip() == "F" for text in paragraph_texts)
    # The sibling "B" leak stays untouched (out of scope this phase).
    assert any(text.rstrip().endswith("B\tnome,endereco") for text in paragraph_texts)
    asset_ids = [a.id for a in d40.assets]
    assert "figure-01" in asset_ids
    # Every other already-restored content survives unchanged.
    code_blocks = [b for b in d40.content_blocks if b.type == "code"]
    assert any("data_nascimento, renda, idade)" in b.text for b in code_blocks)
    assert (
        "Para essa relação, foram criados dois índices secundários: IndiceIdade, "
        "para o atributo idade" in d40.statement
    )


def test_q23_schema_fragment_is_now_its_own_paragraph_not_glued_to_the_next_sentence(
    extraction_result,
):
    """Regression test for ``q23-schema-fragment-duplicate-bleed`` (RESOLVED
    Phase 3V): the schema's own trailing relation fragment
    ("IdRep:integer referencia Republica)") is real, never-to-be-removed
    text (Phase 3T's own forensic proof: figure-01.png's render clip
    truncates this exact line to its top ~2.3pt of ~9pt height - it is not
    a region duplicate, so ``force_region_membership`` is never applied
    here). Its real vertical gap to the next sentence (15.92pt) sits just
    under ``PARAGRAPH_GAP_THRESHOLD`` (19.0pt), so it used to publish glued
    onto "Suponha que existam..." with no separating space. A new
    ``force_paragraph_break_after`` override (data/manifests/
    layout-overrides.yaml) now ends that paragraph run right after this
    one, individually-identified line - the text itself, figure-01.png,
    and every other content block are otherwise unaffected.
    """
    result, _ = extraction_result
    q23 = _objective_by_number(result)[23]
    assert q23.content_blocks is not None
    paragraph_texts = [b.text for b in q23.content_blocks if b.type == "paragraph"]
    assert "IdRep:integer referencia Republica)" in paragraph_texts
    assert "Suponha que existam as seguintes tuplas no banco de dados:" in paragraph_texts
    # The old, glued single paragraph must no longer exist.
    assert not any(
        text.startswith("IdRep:integer referencia Republica) Suponha") for text in paragraph_texts
    )
    # figure-01 and the code block right after it are unaffected.
    asset_ids = [a.id for a in q23.assets]
    assert "figure-01" in asset_ids
    code_blocks = [b for b in q23.content_blocks if b.type == "code"]
    assert any("Pessoa(1, " in b.text for b in code_blocks)


def test_q55_alternatives_are_now_published_as_vector_formula_equations(extraction_result):
    """Regression test for the `q55-unstructured-image-alternatives` blocker
    (RESOLVED Phase 3W): fresh forensics proved this question's own 5
    alternatives are 100% vector-drawn exponential formulas
    (page.get_drawings(), zero real text), never raster images -
    architecturally identical to Q45's own already-solved inline-formula
    gap (Phase 3S). Five new `declare_inline_formula_region` overrides (one
    per alternative, individually re-verified via `verify_drawings_present`)
    plus one `suppress_visual_region` override (dropping the now-redundant
    coarse blob that used to span all 5 alternatives + the "RASCUNHO"
    scratch box) let this question build for the first time ever. Q38's own
    equivalent attempt was tried and reverted this same phase (unrelated,
    pre-existing `_merge_orphan_markers` defect exposed a garbled
    statement) - Q55 has no such defect and remains the sole content
    target of this fix.
    """
    result, _ = extraction_result
    q55 = _objective_by_number(result)[55]
    assert len(q55.alternatives) == 5
    for alt in q55.alternatives:
        assert alt.text == ""
        assert alt.asset is not None
        assert alt.asset.type == AssetType.EQUATION
    asset_ids = [a.id for a in q55.assets]
    assert len(asset_ids) == len(set(asset_ids))  # every alternative got its own, distinct asset
    # This fixture never loads a visual-audit file (see extraction_result
    # above), so extraction_status stays "extracted" (visual_validation
    # pending) for every question here regardless - the real CLI/canonical
    # corpus, which does load data/manifests/visual-audit-2008-computing.json,
    # reaches "verified" (confirmed directly against data/questions/2008/
    # all-computing/enade-2008-computing-q55.md).
    assert q55.automatic_validation.value == "passed"
    assert (
        "Considere que um sistema seja constituído por três componentes montados em paralelo"
        in q55.statement
    )


def test_q38_circuit_and_alternatives_are_now_fully_published(extraction_result):
    """Regression test for the `q38-unstructured-image-alternatives`
    blocker (RESOLVED Phase 3X, closing the Layer 3 gap Phase 3W left
    open). The circuit diagram's own 5 pin labels ("A"-"E") and its own
    output-label annotation ("f(A,B,C,D,E)", reported by PyMuPDF as 5
    separate same-baseline line fragments) used to leak as loose statement
    text because they sit just outside the circuit's own logical region
    bbox - already fully, legibly visible in the same, byte-identical
    figure-01.png the whole time. A general region-growth fix (threading
    layout overrides into figures.py's own internal label-candidate
    extraction) was tried and rejected after it caused the circuit's own
    region and the alternatives' own region to grow toward each other and
    catastrophically merge (see docs/phase-3x-report.md) - fixed instead
    with 9 individually-verified `force_region_membership` overrides
    (the same zero-blast-radius mechanism already used for D40's own "F"
    leak), leaving figures.py's own region-growth/merge code untouched.
    """
    result, _ = extraction_result
    q38 = _objective_by_number(result)[38]
    assert (
        "No circuito acima, que possui cinco entradas — A, B, C, D e E — e uma "
        "saída f (A, B, C, D, E), qual opção apresenta uma expressão lógica "
        "equivalente à função f (A, B, C, D, E)?"
    ) in q38.statement
    # The one real sentence appears exactly once - no duplication, no
    # leaked circuit pin-label/output-label fragments glued onto it.
    assert q38.statement.count("No circuito acima") == 1
    assert "RASCUNHO" not in q38.statement
    asset_ids = [a.id for a in q38.assets]
    assert len(asset_ids) == 6  # 1 circuit diagram + 5 alternative equations
    assert len(asset_ids) == len(set(asset_ids))
    assert len(q38.alternatives) == 5
    for alt in q38.alternatives:
        assert alt.text == ""
        assert alt.asset is not None
        assert alt.asset.type == AssetType.EQUATION
    assert q38.automatic_validation.value == "passed"


def test_q08_horizontal_photograph_alternatives_are_now_fully_published(extraction_result):
    """Regression test for the `q08-unstructured-image-alternatives`
    blocker (RESOLVED Phase 3Y). Q8's own 5 fine-art photographs are laid
    out in two horizontal rows (A/B/C; D/E) sharing near-identical marker
    Y per row - a shape ``_attach_alternative_formula_regions``'s own
    Y-only row-slicing cannot represent (it computes a zero-height "row"
    whenever two markers share a Y). Letting the general per-letter loop
    run at all on this shape does not just leave letters empty - it
    silently concatenates every intervening line, including *other*
    alternatives' own captions, into whichever letter sits immediately
    before the next marker in reading order (confirmed by direct
    instrumentation: "C" absorbed A/B/C's own captions at once, "E"
    absorbed both D's and its own, while A/B/D were left empty). Fixed
    with 5 individually-verified `declare_raster_alternative_region`
    overrides plus 2 `suppress_visual_region` overrides that kill the
    general owner-less merge's own two redundant, coarser per-row blobs
    (see docs/phase-3y-report.md).
    """
    result, _ = extraction_result
    q08 = _objective_by_number(result)[8]
    assert (
        "O filósofo alemão Friedrich Nietzsche (1844-1900), talvez o pensador "
        "moderno mais incômodo e provocativo" in q08.statement
    )
    assert q08.statement.count("Friedrich Nietzsche") == 1
    # No monolithic per-row crop duplicating what the 5 alternatives'
    # own individual assets already show.
    asset_ids = [a.id for a in q08.assets]
    assert len(asset_ids) == 5
    assert len(asset_ids) == len(set(asset_ids))
    assert len(q08.alternatives) == 5
    expected_captions = {
        "A": "Homem idoso na poltrona Rembrandt van Rijn – Louvre, Paris.",
        "B": "Figura e borboleta Milton Dacosta",
        "C": "O grito – Edvard Munch – Museu Munch, Oslo Disponível em: http://members.cox.net",
        "D": "Menino mordido por um lagarto Michelangelo Merisi (Caravaggio)",
        "E": "Abaporu – Tarsila do Amaral Disponível em: http://tarsiladoamaral.com.br",
    }
    for alt in q08.alternatives:
        assert alt.asset is not None
        assert alt.asset.type == AssetType.IMAGE
        assert alt.text == expected_captions[alt.letter]
    assert [alt.letter for alt in q08.alternatives] == ["A", "B", "C", "D", "E"]
    assert q08.correct_answer == "C"
    assert q08.automatic_validation.value == "passed"


def test_q73_neighboring_question_paragraph_is_not_regressed(extraction_result):
    """PROMPT Phase 3O regression guard (mandatory counterexample, Section
    22): a `LineRegionRelation.looks_like_body_prose` unconditional veto was
    tried and reverted this phase precisely because it let a long,
    genuinely body-prose-shaped paragraph - positioned above the raw top
    edge of Q73's own activity-graph diagram, but never Q73's own statement
    - leak into Q73's own text. Q73's own statement must stay exactly the
    self-contained question it already was.
    """
    result, _ = extraction_result
    q73 = _objective_by_number(result)[73]
    assert (
        "Considerando-se o gráfico de atividades acima e a tabela de custo de "
        "aceleração das atividades da rede que podem ser aceleradas" in q73.statement
    )
    assert not q73.statement.lstrip().startswith("Uma das técnicas")
    assert "técnicas que auxiliam na gerência de projetos de software" not in q73.statement
    assert "eventos iniciais e finais de cada atividade" not in q73.statement
    assert len(q73.assets) == 1


# --- PROMPT Phase 3P: alternative ownership / Q07 contamination fix -------


def test_q07_alternative_e_is_no_longer_contaminated_by_the_chart_citation(extraction_result):
    """Full regression test for ``q07-alternative-e-citation-contamination-risk``
    (RESOLVED Phase 3P): the chart's own citation, "Disponivel em
    http://www.ipea.gov.br", lives in page 4's own LEFT column (beneath
    the Curva de Lorenz graph) while the statement/alternatives live
    entirely in the RIGHT column - the page is never detected as a
    genuine two-column page (a single line is not enough evidence for
    ``detect_column_margins``), so ``extract_page_lines`` falls back to a
    flat (y0, x0) sort, placing the citation after alternative E's own
    marker. ``alternative_content_assignment.assign_alternative_content``
    now demonstrates the citation moves *backward* (x0=164.8) relative to
    alternative E's own marker (x0=272.2) and falls inside the chart's own
    region - reflowed to the statement instead of contaminating E.

    Verified beyond substring checks: the exact final alternative E text,
    the exact statement paragraph order, and that nothing else in the
    77-question 2008-b corpus changed (see docs/phase-3p-report.md,
    Section shadow-mode, for the full corpus-wide byte-diff).
    """
    result, _ = extraction_result
    q07 = _objective_by_number(result)[7]

    assert q07.alternatives[0].letter == "A"
    letters_and_text = [(a.letter, a.text) for a in q07.alternatives]
    assert letters_and_text == [
        ("A", "20%."),
        ("B", "40%."),
        ("C", "50%."),
        ("D", "60%."),
        ("E", "80%."),
    ]
    assert "Disponível" not in q07.alternatives[-1].text
    assert "ipea" not in q07.alternatives[-1].text.lower()

    assert q07.statement == (
        "![Figura da questão](enade-2008-computing-q07/figure-01.png)\n\n"
        "De acordo com o mesmo gráfico, o percentual da renda total correspondente "
        "aos 20% de maior renda foi,\n\n"
        "Disponível em http://www.ipea.gov.br"
    )

    assert len(q07.assets) == 1


def test_q28_alternatives_are_not_regressed_by_the_new_alternative_ownership_mechanism(
    extraction_result,
):
    """Mandatory regression (PROMPT Phase 3P section 25): Q28's own
    alternatives are five short, purely numeric strings ("1, 1 e 2", ...)
    that never fail the continuation-margin test and never sit near any
    visual region - confirms the new mechanism is a true no-op here.
    """
    result, _ = extraction_result
    q28 = _objective_by_number(result)[28]
    assert [(a.letter, a.text) for a in q28.alternatives] == [
        ("A", "1, 1 e 2"),
        ("B", "1, 2 e 1"),
        ("C", "2, 1 e 2"),
        ("D", "2, 2 e 1"),
        ("E", "1, 1 e 1"),
    ]


def test_q52_alternatives_are_not_regressed_by_the_new_alternative_ownership_mechanism(
    extraction_result,
):
    """Mandatory regression (PROMPT Phase 3P section 25): Q52's own
    alternative A is the historical false-marker-candidate case
    (alternative_groups.py's own module docstring) that motivated the
    margin-based resolution in Phase 3I - confirms the new ownership
    layer built on top of it does not disturb the already-correct result.
    """
    result, _ = extraction_result
    q52 = _objective_by_number(result)[52]
    assert q52.alternatives[0].letter == "A"
    assert q52.alternatives[0].text == (
        "A identificação e a comunicação do erro em qualquer uma das sentenças "
        "são funções do analisador léxico."
    )
    assert q52.alternatives[-1].letter == "E"
    assert q52.alternatives[-1].text == (
        "A identificação e a comunicação do erro na sentença II são funções da análise semântica."
    )
