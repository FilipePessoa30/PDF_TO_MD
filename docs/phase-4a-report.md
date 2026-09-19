# Fase 4A — Auditoria de Integração das Fases 3A–3Z, Freeze por Hash e Preparação para Revisão Humana

## A. Classificação

**`PILOT_FREEZE_ESTABLISHED`**, com **`READY_FOR_HUMAN_REVIEW`**.

Justificativa: o diff acumulado (27 commits de `master` até `HEAD`, mais 13 arquivos ainda não
commitados desta sessão) foi integralmente inventariado — nenhum arquivo permanece `unknown`/
`unexplained` (Seção E/F); a arquitetura consolidada foi auditada mecanismo a mecanismo (Seção G) —
nenhuma responsabilidade duplicada real encontrada além de sobreposições já conhecidas e
documentadas nas próprias fases de origem, e um único ajuste documental pequeno foi aplicado
(cross-reference de D10 no capability registry, Seção Q); a busca por IDs de questão na lógica
central não encontrou nenhuma violação (Seção H); os 98 overrides ativos são todos válidos,
revisados, com `reason`/`evidence` (Seção I); os schemas alterados são retrocompatíveis (Seção J);
a política de `source_unavailable_confirmed` foi revalidada e continua exigindo evidência completa
(Seção K); 2011 e os três cursos de 2021 permanecem byte-idênticos e com o mesmo veredito de
readiness de antes (Seções M/N); os denominadores foram reconciliados sem nenhuma inconsistência
real (Seção O); o blocker ledger fecha (57 resolved + 1 superseded + 2 source_unavailable = 60, 0
open, Seção P); 881/881 testes passam (867 na baseline desta fase + 14 novos do próprio gate de
freeze, Seção X), todos os gates limpos (Seções U/V); duas regenerações
independentes (run A, run B) são byte-idênticas entre si e ao corpus publicado, para 2008-b, 2011 e
os três cursos de 2021 (Seção W); um manifesto de freeze verificável foi criado com seu próprio gate
de teste (Seção X); D09/D10 permanecem visíveis, `source_unavailable`, nunca `resolved` (Seção K/P);
um pacote de revisão humana e um plano de commit foram preparados sem executar nenhuma ação de
commit/push/PR (Seção Y).

Uma limitação real, não-bloqueante, foi encontrada e é reportada honestamente (nunca escondida,
Seção S): o ledger `data/manifests/content-assignment-2008-b.json` está **congelado desde o commit
`89e4a47`** (Fases 3J/3K/3L) e nunca foi regenerado — seus registros para Q08/Q38/Q45/Q55/D59
refletem o estado geométrico **anterior** aos overrides que tornaram essas questões publicáveis.
Esta fase confirma que esse ledger **não é consumido pelo pipeline de extração real** (nenhuma
chamada em `src/enade/extraction/pipeline.py` ou `assembler.py`) e portanto não afeta a corretude do
corpus publicado nem o readiness — mas seu próprio veredito interno ("zero duplicatas, zero
faltantes") nunca foi re-verificado contra o corpus atual de 80/80 questões. Não corrigido nesta
fase (regenerá-lo exigiria nova ferramenta/script, fora do escopo explícito da Seção 4). Reportado
como uma limitação documental remanescente, não como um blocker.

## B. Estado Git inicial

```text
git branch --show-current:   feat/enade-2008-cc-b-pilot
git rev-parse HEAD:            22e3e882046654193fedf21de296e5ae3c374cb3
git rev-parse master:          a5dfaab0c105150df3a7201c16547708cef45292
git rev-parse origin/master:   a5dfaab0c105150df3a7201c16547708cef45292
git merge-base HEAD master:    a5dfaab0c105150df3a7201c16547708cef45292
```

`merge-base(HEAD, master) == master` — `HEAD` é um descendente direto e linear de `master`, sem
divergência, sem rebase, sem merge cruzado.

```text
commits entre master e HEAD:  27 (todo o trabalho das Fases 3A-3Y, já commitado
                                externamente antes desta sessão)
git diff --stat master...HEAD: 471 arquivos alterados, 113669 inserções(+), 435 remoções(-)
git diff --stat (working tree, não commitado): 5 arquivos modificados,
                                454 inserções(+), 19 remoções(-)
git diff --numstat (working tree): ver Seção E
git diff --check (working tree): vazio (nenhum erro de whitespace)
git diff --name-status (working tree): 5 M
git ls-files --others --exclude-standard: 5 arquivos novos (no início desta fase;
                                7 ao final, ver Seção F)
git status --porcelain=v2: confirma index == HEAD para os 5 arquivos modificados
                                (nenhum staged; "N..." em ambos os lados)
git diff --cached --stat: vazio (nada staged)
```

Confirmado: branch correta; nenhum commit das Fases 3A-3Z foi criado por esta sessão (os 27 commits
entre `master` e `HEAD` já existiam, feitos por processo externo antes do início da Fase 3T); index
sem nenhum arquivo staged; `master`/`origin/master` intactos e idênticos; as alterações acumuladas
da Fase 3Z (não commitadas) foram integralmente preservadas. Nenhum `git clean`, `git reset`, `git
checkout --`, ou `git restore .` foi executado em nenhum momento.

## C. Baseline

```text
pytest:                        867 passed, 0 failed, 0 skipped, 0 xfail, 0 xpass (confirmado por execução real)
ruff check .:                  All checks passed!
ruff format --check .:         424 files already formatted
mypy src:                      Success: no issues found in 61 source files
enade validate-schema:         13/13 fixture(s) valid
enade validate-manifest:       OK (0 warning(s))
enade audit-extraction (2008-b/2011/2021 x3): 80/55/40/40/40 OK
```

Nota sobre o comando literal do prompt (mesma nota já registrada nas Fases 3T/3U/3Z):
`engenharia-da-computacao-bacharelado` não é um `CourseCode` válido (o valor real é
`engenharia-da-computacao`, sem sufixo, e corresponde ao caderno 2008-**e**, bundle explicitamente
fora de escopo). O caderno unificado 2008-b usa o código real `all-computing`. Usei `all-computing`
em todos os comandos, com os labels convencionais já estabelecidos desde a Fase 3T
(`--ready-label READY_FOR_2008_ENGINEERING_TEST --not-ready-label
NOT_READY_FOR_2008_ENGINEERING_TEST --ready-with-source-limitations-label
READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS --corpus-root data/raw/geacc-enade`).

```text
enade verify-gold --year 2008 --course all-computing:
  OK (80 questions match); maturity=provisional verified=78 needs_review=2
enade assess-readiness --year 2008 --course all-computing (labels acima):
  READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS
  78/80 verified, 2 needs_review, gold maturity=provisional
  visual audit: 80 passed, 0 failed, 0 not_performed (fully_covered=True)
  source completeness: incomplete
  actionable blockers: 0
  source limitations: 2 (D09, D10 - ver Seção K)
  informational findings: 0
enade verify-gold --year 2011 --course all-computing:
  OK (55 questions match); maturity=validated verified=54 needs_review=1
enade assess-readiness --year 2011 --course all-computing
  --ready-label READY_FOR_LEGACY_LAYOUT_TEST --not-ready-label NOT_READY_FOR_LEGACY_LAYOUT_TEST:
  READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, source completeness: complete,
  actionable blockers: 0, source limitations: 0, informational findings: 1 (Q34)
enade verify-gold + assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado:
  OK (40/40); READY_FOR_2011, source completeness: complete, 0/0/0
2021 CC-L / SI: sem gold manifest (pré-existente desde a Fase 3T, confirmado, não é lacuna desta fase)
```

Todos os valores batem exatamente com o esperado pelo prompt e com o que a Fase 3Z relatou ao
final: **867 testes**, **`READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS`**,
`actionable_blockers=0`, `source_limitations=2`, `informational_findings=0`. Nenhum arquivo foi
ajustado para reproduzir esses números — são o estado real, confirmado por execução.

## D. Escopo auditado

Esta fase foi predominantemente de auditoria e reconciliação documental, como o prompt exige.
Correções aplicadas (todas pequenas, causais e completamente validadas):

1. Um cross-reference documental adicionado à entrada `contextual_line_region_relation` do
   capability registry, apontando para a resolução posterior de D10 por `zoned_reading_order`
   (Seção Q) — encontrado pela auditoria arquitetural (Seção G), nunca alterando nenhum
   comportamento de código.
2. Criação do manifesto de freeze (`data/manifests/phase-4a-freeze.json`) e seu próprio gate de
   teste (`tests/test_phase4a_freeze.py`) — exatamente o que a Seção 26/27 do prompt pede.

Nenhuma nova extração, heurística geométrica, override de questão, parser, ano, taxonomia,
integração com LLM, ou generalização especulativa foi implementada. A única limitação funcional
real encontrada (o ledger `content-assignment-2008-b.json` congelado, Seção S) foi classificada,
documentada com evidência completa, e deliberadamente **não corrigida nesta fase** — corrigi-la
exigiria escrever/rodar uma nova ferramenta de regeneração, fora do escopo explícito desta fase
(Seção 4: "não implemente... novo parser"); recomendada como candidata a uma fase futura, isolada.

## E. Inventário do diff acumulado

**Diff commitado (`master...HEAD`, 27 commits, 471 arquivos)**: já integralmente documentado,
fase a fase, nos 25 relatórios `docs/phase-3a-report.md` a `docs/phase-3z-report.md` — não
reproduzo aqui, arquivo por arquivo, o que essas fases já registraram em detalhe (evitando
duplicação e "invenção de atribuição histórica"). Distribuição por categoria, confirmada por
`git diff --name-status master...HEAD`:

| categoria | contagem | origin_phase |
|---|---:|---|
| `question_markdown`/`question_asset` (data/questions) | 349 | acumulado 3A-3Y (349 arquivos **adicionados** — `master` nunca teve nenhum corpus publicado; todo `data/questions/` foi construído durante este piloto) |
| `source_code` (src/enade) | 31 | acumulado 3A-3Y |
| `manifest`/`gold`/`visual_audit`/`blocker_ledger`/`override`/`capability_registry` (data/manifests) | 25 | acumulado 3A-3Y |
| `report` (docs) | 33 | acumulado 3A-3Y |
| `test` (tests) | 32 | acumulado 3A-3Y |
| `script` (scripts) | 1 | acumulado pre-fase-3A |

Confirmado por `git diff --name-status master...HEAD -- data/questions`: **100% dos 349 arquivos
são `A` (added)**, nunca `M` — o corpus inteiro (2008-b, 2011, 2021) nasceu dentro deste piloto,
nunca existiu em `master`. "Zero drift" nas fases anteriores refere-se sempre a "inalterado desde a
própria primeira extração dentro deste piloto", nunca a "idêntico a `master`" (que nunca teve corpus
algum).

**Diff não commitado (working tree, Fase 3Z + esta fase, 11 arquivos já existentes no momento em
que este inventário foi produzido - mais 2 nascidos ao final da própria fase, ver abaixo, 13 no
total final)** — inventário completo,
individual, machine-readable:

```yaml
- path: data/manifests/blocker-ledger-2008.yaml
  change_type: modified
  category: blocker_ledger
  origin_phase: "3Z"
  purpose: "D09/D10: evidencia forense expandida (imagens/drawings/texttrace), source_limitation_id, resolution preenchido, visual_validation failed->passed"
  generated_or_human: human_edited_yaml
  protected_output: false
  expected: true
  review_status: reviewed
- path: data/manifests/extraction-capabilities.json
  change_type: modified
  category: capability_registry
  origin_phase: "4A"
  purpose: "cross-reference documental de D10 (contextual_line_region_relation -> zoned_reading_order)"
  generated_or_human: human_edited_json
  protected_output: false
  expected: true
  review_status: reviewed
- path: src/enade/cli.py
  change_type: modified
  category: source_code
  origin_phase: "3Z"
  purpose: "assess-readiness: --corpus-root, --ready-with-source-limitations-label, saida em 3 secoes"
  generated_or_human: human_written_code
  protected_output: false
  expected: true
  review_status: reviewed
- path: src/enade/extraction/blocker_ledger.py
  change_type: modified
  category: schema
  origin_phase: "3Z"
  purpose: "+ Blocker.source_limitation_id (opcional, default None)"
  generated_or_human: human_written_code
  protected_output: false
  expected: true
  review_status: reviewed
- path: src/enade/readiness.py
  change_type: modified
  category: source_code
  origin_phase: "3Z"
  purpose: "+ source_availability_path/corpus_root em assess_readiness; + ReadinessReport.source_limitations/source_completeness"
  generated_or_human: human_written_code
  protected_output: false
  expected: true
  review_status: reviewed
- path: tests/test_readiness.py
  change_type: modified
  category: test
  origin_phase: "3Z"
  purpose: "+9 testes de isencao de source-unavailable"
  generated_or_human: human_written_code
  protected_output: false
  expected: true
  review_status: reviewed
- path: data/manifests/source-availability-2008.yaml
  change_type: untracked_new
  category: manifest
  origin_phase: "3Z"
  purpose: "evidencia estruturada de ausencia de fonte para D09/D10"
  generated_or_human: human_edited_yaml
  protected_output: false
  expected: true
  review_status: reviewed
- path: docs/phase-3z-report.md
  change_type: untracked_new
  category: report
  origin_phase: "3Z"
  purpose: "relatorio final da Fase 3Z"
  generated_or_human: human_written_prose
  protected_output: false
  expected: true
  review_status: reviewed
- path: src/enade/extraction/source_availability.py
  change_type: untracked_new
  category: source_code
  origin_phase: "3Z"
  purpose: "novo modulo: SourcePackage/SourceAvailabilityRecord/is_confirmed_unavailable/verify_source_hashes_match"
  generated_or_human: human_written_code
  protected_output: false
  expected: true
  review_status: reviewed
- path: tests/test_source_availability.py
  change_type: untracked_new
  category: test
  origin_phase: "3Z"
  purpose: "+14 testes unitarios do novo modulo"
  generated_or_human: human_written_code
  protected_output: false
  expected: true
  review_status: reviewed
- path: tests/test_phase4a_freeze.py
  change_type: untracked_new
  category: test
  origin_phase: "4A"
  purpose: "gate de verificacao do freeze manifest"
  generated_or_human: human_written_code
  protected_output: false
  expected: true
  review_status: reviewed
```

Dois arquivos adicionais nascem ao final desta própria fase (fora da lista acima, pois ainda não
existiam quando o inventário foi produzido): `data/manifests/phase-4a-freeze.json` (o próprio
manifesto de freeze, categoria `manifest`) e `docs/phase-4a-report.md` (este arquivo, categoria
`report`) — ambos `origin_phase: "4A"`, ambos gerados por esta sessão, documentados na Seção X.
Nenhum arquivo permanece `unknown`/`unexplained`.

## F. Arquivos não rastreados

`git ls-files --others --exclude-standard` no início desta fase retornou exatamente 5 arquivos
(todos já classificados na Seção E: `data/manifests/source-availability-2008.yaml`,
`docs/phase-3z-report.md`, `src/enade/extraction/source_availability.py`,
`tests/test_source_availability.py`, mais o `tests/test_phase4a_freeze.py` criado durante esta
própria fase) — todos legítimos: 1 manifesto de evidência, 1 relatório final, 1 módulo de código-
fonte, 2 arquivos de teste. **Nenhum scratch file, saída regenerável indevidamente deixada, ou
arquivo ambíguo foi encontrado.** Nenhum arquivo foi removido nesta fase (nada qualificava como
descartável). Todos os diretórios temporários usados durante a investigação desta fase
(`/tmp/p4a_runA`, `/tmp/p4a_runB`, arquivos de hash intermediários) foram explicitamente removidos
antes da conclusão (Seção Z).

## G. Arquitetura consolidada

Auditoria completa dos 15 mecanismos nomeados (pesquisa detalhada delegada a um agente de
investigação, que leu integralmente os 19 relatórios das Fases 3A-3S e todo o código/testes
relevantes; resultado revisado e reconciliado aqui):

| mecanismo | arquivo | responsabilidade | gate | testes pos./neg. |
|---|---|---|---|---|
| `LineRegionRelation` | `assembler.py` | relação geométrica rica linha↔região (substitui um booleano de padding fixo) | `_text_consumption_decision`: só remove texto com containment/raw-overlap/absorbed-label; resto = "ambiguous" (mantido) | sim, ambos |
| `fragment_reconstruction` | `fragment_reconstruction.py` | rejunta uma linha física dividida em múltiplos fragmentos pelo extrator | `compute_line_fragment_relation`: espaço final + gap relativo à fonte + baseline/fonte iguais, todos simultâneos | sim, ambos |
| `alternative_group` | `alternative_groups.py` | resolve a sequência A-E inteira como uma única decisão estrutural | `AlternativeGroup.is_usable` | sim, ambos + metamórficos |
| `alternative_boundary_assignment` | `assembler.py` (consome `AlternativeGroup`) | converte a sequência resolvida nos limites de linha por letra | implícito: só avança se `is_usable` | **apenas integração** (`test_extraction_pipeline_2008.py`/`_2011.py`) — nenhum teste unitário sintético dedicado; gap menor, não-bloqueante |
| `ContentAssignment` | `content_assignment.py` | schema de ownership por linha/asset + auditoria offline (duplicata/faltante) | nenhum gate de ativação (nunca é chamado pelo pipeline real) | sim, ambos (mas o artefato que audita está congelado — ver Seção S) |
| `reading_zones` | `reading_zones.py` | reconstrói ordem de leitura sob topologia de coluna mutável | `assess_eligibility` (≥2 zonas, ≥1 transição, grafo acíclico) + oráculo de segurança diferencial | sim, ambos + metamórficos |
| `same_row_ordering` | `same_row_ordering.py` | corrige ordem esquerda-direita de fragmentos na mesma linha física com bbox diferente | clustering completo-link + baseline normalizado + oráculo de segurança | sim, ambos + metamórficos |
| `alternative_content_assignment` | `alternative_content_assignment.py` | ownership linha↔enunciado/alternativa | 3 condições simultâneas (nunca uma só) | sim, ambos (35 testes) |
| `protect_from_region_membership` | `layout_overrides.py`/`assembler.py` | mantém uma linha individualmente revisada visível | match exato hash+página+bbox | sim, ambos |
| `force_region_membership` | idem | autoriza remover uma linha "ambiguous" comprovadamente duplicada | só atua quando decisão já é "ambiguous", nunca "accepted" | sim, ambos |
| `declare_inline_formula_region` | `figures.py`/`assembler.py`/`layout_overrides.py` | declara+re-verifica uma fórmula vetorial | `verify_drawings_present` (≥1 drawing real) | sim, ambos |
| `force_paragraph_break_after` | `layout_overrides.py`/`assembler.py` | força quebra de parágrafo num ponto individualmente provado | match exato hash+página+bbox, nunca afeta consumo de texto | sim, ambos |
| `declare_raster_alternative_region` | `assembler.py`/`figures.py`/`layout_overrides.py` | declara+re-verifica uma fotografia raster por alternativa | `verify_image_present` (≥90% containment) | sim, 6+6 fixtures |
| `suppress_visual_region` | `layout_overrides.py` | suprime uma região confirmada sem conteúdo legítimo | match por centro-no-bbox (deliberadamente mais frouxo, documentado) | sim, ambos |
| `source_availability` | `source_availability.py` | evidência estruturada de ausência de fonte + gates de confiança/hash | `is_confirmed_unavailable` + `verify_source_hashes_match` | sim, 14+9 testes |

**Sobreposições encontradas, nenhuma corrigida (nenhuma é um defeito demonstrável)**:

1. `ContentAssignment` (3J) vs. `alternative_content_assignment` (3P) — nomes quase idênticos,
   domínios adjacentes, sem classe-base compartilhada. Já reconhecida como complementaridade
   deliberada pelo próprio relatório da Fase 3J; do ponto de vista puramente arquitetural continua
   sendo um risco de confusão para um leitor futuro, mas não um defeito — apenas `ContentAssignment`
   nunca é ativado pelo pipeline real, então não há risco de comportamento duplicado em produção.
2. `reading_zones` (3K/3L), `same_row_ordering` (3N) e `fragment_reconstruction` (3H) — três
   mecanismos independentes de "reordenar sob evidência + modo shadow/active + oráculo de
   conservação", cada um reinventando o mesmo padrão numa granularidade diferente (fragmento de
   palavra; mesma linha; zona inteira da página) em vez de uma única estrutura compartilhada. Bem
   testados e documentados individualmente, com ordem de execução fixa e conhecida — um padrão
   arquitetural recorrente, não um bug.
3. `declare_inline_formula_region` (3S/3W) vs. `declare_raster_alternative_region` (3Y) —
   desenho estruturalmente paralelo (override + função de re-verificação + asset sem padding +
   flag em `VisualRegion`) para dois tipos de conteúdo diferentes. **Esta sobreposição já causou uma
   interferência real**, documentada e corrigida na própria Fase 3Y: o mecanismo raster, ao receber
   a lista de regiões sem filtro, sequestrou acidentalmente as regiões de fórmula já corretamente
   declaradas da Q38 — corrigido pelo filtro `is_exact_raster_bbox`, com teste de regressão
   permanente (`test_assemble_question_declared_inline_formula_alternatives_are_never_hijacked_by_raster_mechanism`).
   Não refatorado nesta fase (não há novo defeito, e unificar os dois mecanismos seria uma mudança
   arquitetural especulativa, fora do escopo — Seção 7 do prompt: "só altere arquitetura se houver
   defeito demonstrável", e o defeito já demonstrado já foi corrigido em sua própria fase de origem).

**Busca por lógica hardcoded**: `grep` por `question_id ==`, `question_number ==`, `.number ==
<int>` literal em `src/enade/extraction/*.py` — **zero ocorrências** em lógica executável (a única
ocorrência textual é o próprio anti-padrão citado em docstring de `layout_overrides.py` como
motivação para a existência do mecanismo de override). Consistente com
`tests/test_generalization_architecture.py`'s próprio gate AST-based, que passa.

## H. Busca por IDs na lógica central

Busca completa por `Q8`, `Q08`, `Q38`, `Q45`, `Q55`, `Q75`, `D09`, `D10`, `D40`, `D59` em todo
`src/`: **18 arquivos** com ocorrências, **todas em comentários/docstrings** explicando a evidência
histórica que motivou um mecanismo geral (nunca em um branch de código, nunca em um threshold
numérico condicionado à identidade, nunca em `trigger_features`). Verificado programaticamente:

```text
grep -rn "\bQ0?8\b|\bQ38\b|\bQ45\b|\bQ55\b|\bQ75\b|\bD09\b|\bD10\b|\bD40\b|\bD59\b" data/manifests/extraction-capabilities.json (trigger_features apenas):
  0 ocorrências (script Python dedicado, Seção C)
tests/test_generalization_architecture.py::test_capability_registry_never_cites_a_question_id_as_a_trigger:
  PASSED
```

Uma linha (`spacing.py:30`, "Q1-Q8, D1, D2") foi inspecionada individualmente: refere-se ao
intervalo de questões do caderno de 2021-CC usado para *calibrar* `GENUINE_GAP_THRESHOLD_PT` (um
limiar numérico geral), nunca ao Q8 de 2008-b nem a uma verificação de identidade em código —
confirmado lendo o corpo da função (nenhum `if`/branch usa esse intervalo, é puramente uma nota de
proveniência do dado de calibração). Classificação: **teste de calibração/evidência em comentário**,
permitido. Nenhuma violação real encontrada. Os 98 overrides (Seção I) são o único lugar onde um ID
de questão aparece associado a uma decisão concreta — sempre travado por hash+página+bbox, nunca
como branch de código, exatamente como o contrato do projeto exige.

## I. Overrides

**98 overrides ativos** em `data/manifests/layout-overrides.yaml`, agrupados por `rule`:

| rule | contagem | questões |
|---|---:|---|
| `protect_from_region_membership` | 38 | 2008-b: D40(2) Q02(4) Q05(2) Q07(1) Q24(6) Q45(15) Q54(1) = 31; 2011 (pré-existente, Fase 2D): Q12(1) Q38(1) Q48(1) |
| `protect_from_label_absorption` | 17 | 2011 apenas (pré-existente, Fase 2B): Q06(5) Q23(3) Q44(4) Q45(5) |
| `declare_inline_formula_region` | 11 | Q38(5) Q45(1) Q55(5) |
| `force_region_membership` | 10 | D40(1) Q38(9) |
| `exclude_from_orphan_marker_merge` | 6 | Q38(5); 2011 Q22(1) |
| `force_fraction_merge` | 5 | 2011 apenas (pré-existente, Fase 2D): Q10(5) |
| `declare_raster_alternative_region` | 5 | Q08(5) |
| `suppress_visual_region` | 4 | Q08(2) Q38(1) Q55(1) |
| `force_zoned_reading_order_page` | 1 | D10(1) — **superseded** (Fase 3L, nenhum código consulta mais) |
| `force_paragraph_break_after` | 1 | Q23(1) |

Confirmado: **todos os 98** têm `reason` e `evidence` não-vazios; **97 `status: reviewed` + 1
`status: superseded`** (o próprio D10/`force_zoned_reading_order_page`, correta e explicitamente
marcado assim desde a Fase 3L — nunca removido do arquivo, preservando o histórico). **3 grupos de
bbox+página+hash idênticos** encontrados, todos em Q38 (página 15) — cada um combina uma entrada
`exclude_from_orphan_marker_merge` com uma `force_region_membership` no mesmo local exato: **dupla-
marcação intencional**, não uma duplicata acidental — confirmado por leitura direta (Fase 3W/3X, já
de meu próprio conhecimento direto): a primeira impede que o glifo do pino seja fundido como
"órfão" com o RASCUNHO vizinho; a segunda autoriza separadamente removê-lo do enunciado por já estar
visível no asset — dois mecanismos, duas justificativas, mesmo local, nunca redundante. Nenhum
override morto (os 2 tipos de regra com zero entradas atuais — `excludes_from_region_candidates`,
`forces_single_column` — são caminhos de código legados de fases anteriores, nunca exercitados por
nenhuma entrada atual, mas o código em si não foi removido nesta fase por não ser um defeito, apenas
um mecanismo sem uso corrente). Nenhum override foi removido apenas para reduzir a contagem.

## J. Schemas

Alterações de schema desta fase (3Z, revalidadas aqui): `BlockerStatus` já incluía
`source_unavailable` desde a Fase 3T (não uma mudança desta auditoria); `Blocker.source_limitation_id:
str | None = None` — campo novo, opcional, default `None`, testado retrocompatível: as 60 entradas
pré-existentes do ledger continuam validando sem qualquer edição (`validate_ledger`: 0 issues,
confirmado na Seção C). `AnswerStandardReference` (Fase 3U, `min_length=1` → validador condicional
texto-ou-assets) permanece testada e inalterada nesta fase. `GoldManifest`/`GoldMaturity`
deliberadamente **não alterados** (decisão já registrada na Fase 3Z, revalidada aqui: `needs_review_count`/
`unresolved_question_ids` continuam a representação literal e honesta, sem introduzir um novo status
de maturidade). `ReadinessReport` ganhou dois campos novos com default (`source_limitations=()`,
`source_completeness` como property derivada) — nenhum consumidor pré-existente quebra (confirmado:
todos os 20 testes de `test_readiness.py` anteriores a esta sessão continuam passando sem edição).
Nenhum documento antigo falha sem migração: os 60 blockers pré-existentes, os manifests de 2011/2021
(nunca tocados por este schema) e o gold de 2008-b (também não alterado) continuam válidos.

## K. Source limitation

Revalidação da política `READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS` (confirmada por
execução real na Seção C, não presumida): exige — e o código exige mecanicamente, via
`is_confirmed_unavailable` (`source_availability.py`) — `availability_status ==
"source_unavailable_confirmed"`, `review_status == "reviewed"`, pacote-fonte existente, o documento
referenciado existente dentro do pacote, `pages_scanned` cobrindo **exatamente** todas as páginas do
documento (1..page_count, nunca uma lista parcial), os 5 métodos de busca
(text/rawdict/texttrace/images/drawings) presentes, e `text_evidence`/`image_evidence`/
`drawing_evidence`/`evidence`/`source_hashes` todos não-vazios. `verify_source_hashes_match`
re-hasheia o documento real no disco a cada chamada — nunca confia em um hash armazenado sem
reconferir. Reversão automática confirmada por teste
(`test_source_hash_mismatch_reopens_blocking`): hash divergente → achado `source_hash_mismatch`
sempre estrutural, a isenção nunca é concedida, D09/D10 voltam a bloquear. `source_ambiguous`/
`source_not_checked` também sempre bloqueiam (`test_source_ambiguous_record_always_blocks_regardless_of_evidence`).
D59 permanece o contraexemplo obrigatório: nunca recebeu nem poderia receber um registro
`source_unavailable_confirmed` (seu próprio asset é uma imagem real, o oposto exato do que esse
status exige) — `git diff` em `enade-2008-computing-d59.md`/`padrao-01.png`: vazio; testes de
pipeline específicos de D59/Q45/Q55/Q8/Q38/D40 (9 testes) passam sem alteração (Seção C, herdado da
Fase 3Z, reconfirmado nesta fase).

## L. Readiness 2008-b

```text
READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS
  78/80 verified, 2 needs_review, gold maturity=provisional
  visual audit: 80 passed, 0 failed, 0 not_performed (fully_covered=True)
  source completeness: incomplete
  actionable blockers: 0
  source limitations: 2 (enade-2008-computing-d09, enade-2008-computing-d10)
  informational findings: 0
```

Literal, confirmado por execução real (Seção C) — nunca forçado.

## M. Proteção de 2011

```text
2011 Markdown drift = 0
2011 asset drift = 0
2011 manifest drift = 0 (gold-2011-computing.json, visual-audit-2011-computing.json,
                          blocker-ledger-2011.yaml - nenhum tocado por esta ou pela Fase 3Z)
```

Confirmado por `diff -rq` (run A e run B, Seção W) e por `tests/test_protected_corpus.py` (parte da
suíte completa, Seção U/V). Veredito de readiness preservado: `READY_FOR_LEGACY_LAYOUT_TEST`, mesmos
54/55 verified, mesmo único achado informacional (Q34, `accepted_non_material_difference` —
inalterado desde a Fase 2F). Gold maturity preservada (`validated`). Zero limitação de fonte nova
(`source-availability-2011.yaml` não existe — o mecanismo é estruturalmente inatingível para 2011,
confirmado por execução real, Seção U/N da Fase 3Z, reconfirmado aqui).

## N. Proteção de 2021

```text
2021 Markdown drift = 0 (três cursos)
2021 asset drift = 0
2021 manifest drift = 0 (gold-2021-b.json, visual-audit-2021-b.json - nenhum tocado)
```

Confirmado da mesma forma. `READY_FOR_2011` preservado para CC-B (40/40, 0 blockers, 0 limitações,
0 achados). CC-L/SI seguem sem gold manifest — estado pré-existente desde a Fase 3T, não uma lacuna
desta fase (confirmado: nenhum `enade build-gold` foi executado para esses cursos por nenhuma fase).
O novo `--ready-with-source-limitations-label` da CLI é genérico (nunca hardcoded para um ano
específico) — construído inteiramente a partir de `report.ready and report.source_limitations`
(ambos calculados de dados reais, nunca de um nome de ano); confirmado por execução real que 2021
CC-B nunca produz esse label (`source limitations: 0` → usa `ready_label` normal, `READY_FOR_2011`).

## O. Denominadores

| Métrica | Universo | Total | Resultado |
|---|---|---:|---:|
| Questões publicadas | Markdown de questões em `data/questions/2008/all-computing/*.md` | 80 | 80/80 |
| Auditoria visual | IDs com veredito explícito em `visual-audit-2008-computing.json` | 80 | 80 passed, 0 failed, 0 not_performed |
| Entidades do gold | Questões cobertas por `gold-2008-computing.json` | 80 | 78 verified + 2 needs_review |
| Answer standards | Discursivas esperadas (D09,D10,D20,D39,D40,D59,D60,D79,D80) | 9 | 7 disponíveis (D20/D39/D40/D59/D60/D79/D80) + 2 indisponíveis-confirmadas (D09/D10) |
| Blockers acionáveis | Findings estruturais no readiness | 0 | 0 |
| Limitações da fonte | Artefatos confirmados ausentes do pacote-fonte | 2 | D09, D10 |
| Assets | Arquivos `.png` publicados em 2008-b | 63 | 63 |

**Explicação definitiva do "78+2" vs "77" (nenhuma inconsistência real)**: até a Fase 3V
(inclusive), 2008-b tinha **77** questões efetivamente publicadas — Q8, Q38 e Q55 estavam excluídas
inteiramente do corpus (nenhum `.md` existia). "published=77"/"visual_audit=77"/"gold=74→75→77"
usavam esse mesmo denominador real de 77 arquivos em disco. A Fase 3W resolveu Q55 (77→78), a Fase
3X resolveu Q38 (78→79), a Fase 3Y resolveu Q8 (79→80) — ao final da Fase 3Y, **80** questões estão
publicadas (0 excluídas). "gold = 78 verified + 2 needs_review" (78+2=**80**) e "visual audit = 80
passed" já refletem esse **novo e maior** denominador, correto e consistente entre si — nunca
misturados com o "77" de fases anteriores no mesmo relatório. Nenhuma correção de contrato foi
necessária. Um teste já existente (`test_all_80_academic_questions_are_accounted_for`, herdado da
Fase 3Y) fixa esse denominador em 80 permanentemente, prevenindo uma futura regressão silenciosa
para um número menor.

## P. Blocker ledger

```text
data/manifests/blocker-ledger-2008.yaml: total=60, resolved=57, superseded=1,
  source_unavailable=2, source_ambiguity=0, not_reproducible=0,
  accepted_non_material_difference=0, open=0
  validate_ledger: [] (0 issues)
  IDs únicos: confirmado (60 IDs, 60 distintos)
data/manifests/blocker-ledger-2011.yaml: total=38, open=0,
  accepted_non_material_difference=2 (inclui Q34)
  validate_ledger: [] (0 issues)
```

Soma fecha: `57 + 1 + 2 = 60` (2008-b). D09/D10 confirmados `status: source_unavailable`
(NUNCA `resolved`), cada um com `source_limitation_id` apontando para seu próprio registro em
`source-availability-2008.yaml` (`sa-2008-d09-answer-standard`/`sa-2008-d10-answer-standard`).
Confirmado individualmente que D10, D60, Q71, Q08, Q38, Q55 aparecem **apenas** com status
`resolved` em todos os seus próprios blockers de conteúdo (D10 tem, adicionalmente, seu blocker de
ausência de fonte, corretamente `source_unavailable`, nunca confundido com defeito de conteúdo).

## Q. Capability registry

**30 capabilities** em `data/manifests/extraction-capabilities.json`. Reconciliação completa
(pesquisa delegada, revisada e uma correção aplicada): nenhuma capability lista D10/D60/Q71/Q38/Q55/
Q8 como defeito ainda aberto de forma contraditória com um relatório de fase posterior — a cadeia de
resolução (uma entrada mais antiga descreve o estado na sua própria época; a resolução aparece numa
entrada *posterior*, nunca editando retroativamente a mais antiga) está correta em todos os casos,
com uma única exceção cosmética: `contextual_line_region_relation` (Fase 3G) descrevia D10's
scramble de ordem de leitura como "remains" sem apontar que fora resolvido duas fases depois — **
corrigido nesta fase** (Seção D), adicionando um cross-reference explícito, sem alterar nenhuma
alegação factual da época (o texto original, "tracked separately as
d10-newspaper-collage-reading-order-scramble", já existia e permanece; apenas uma cláusula foi
adicionada informando a resolução posterior). `test_generalization_architecture.py` (12 testes,
incluindo o meta-teste anti-vazamento de IDs em `trigger_features`) confirmado passando após a
edição. Nenhuma capability foi promovida de nível apenas porque o piloto terminou — a mais recente
(`declared_raster_alternative_group_preservation`, Q8) permanece corretamente `G1`
(caso único comprovado); `source_availability`/`declared_paragraph_boundary_for_truncated_asset_companion_text`/
`visual_only_answer_standard`/`orphan_marker_chrome_partner_exclusion` permanecem `G1` pela mesma
razão. `source_availability` **não finge maturidade de extração** — é uma adjudicação documental,
não uma capacidade de extração de conteúdo; corretamente não listada com `G2`/`G3`.

## R. Source-token/source-asset ledgers

`data/manifests/source-token-ledger-2008.yaml`: **4 entradas** — `q24-item-marker-I`,
`q24-item-marker-II`, `q45-item-iii-function-formula`, `d40-tree-selection-operator-sigma`. Cobertura
confirmada: Q24 (2), Q45 (1), D40 (1); **Q38, Q55, D59, Q8, D09, D10 não têm entrada** — confirmado
correto pela própria natureza deste ledger (identidade de caractere/glifo): Q38/Q55 foram resolvidas
por declaração de região inteira (evidência de asset, não de glifo); D59 por rubrica visual-only
(zero texto, nada a adjudicar); Q8 por declaração de imagem raster inteira (mesma razão de
Q38/Q55); D09/D10 nunca tiveram um caractere ambíguo — a ausência é de um artefato inteiro, nunca de
um glifo específico. Nenhum token removido do texto publicado fica sem representação: os únicos
casos de remoção de texto comprovada (D40 "F"→σ, os 9 fragmentos do circuito de Q38) são cobertos
por `force_region_membership` (Seção I), um contrato diferente e apropriado (prova de visibilidade
no asset, não de identidade de glifo).

## S. Content assignment

`data/manifests/content-assignment-2008-b.json`: **2280 registros**. **Achado real desta auditoria**:
ao contrário do que a Fase 3J relatou em sua própria época ("Q8/Q38/Q55 simplesmente não aparecem no
ledger, porque nunca chegam a ser publicadas"), o arquivo **de fato contém** registros para Q08 (27),
Q38 (19) e Q55 (20) — a geração do ledger captura atribuições linha a linha *durante* a montagem de
`assemble_question`, antes da construção final do `Question(...)` Pydantic (que é o ponto em que a
`ValidationError` de alternativas vazias era historicamente levantada) — portanto os registros
pré-validação já existiam no ledger, mesmo para questões que na época não chegavam a ser publicadas.
**Não foi uma alegação retrospectivamente incorreta do relatório da Fase 3J devido a um erro de
julgamento** — foi uma leitura factualmente equivocada do próprio artefato que a Fase 3J gerou,
nunca corrigida até agora. Não reescrevo o relatório da Fase 3J (histórico, preservado como está,
conforme a Seção 25 do prompt exige) — reporto a correção aqui, no relatório desta fase.

**Confirmado (Fase 3V, revalidado aqui)**: este ledger é um **snapshot offline congelado desde o
commit único `89e4a47`** (fases 3J/3K/3L) e nunca foi regenerado por nenhuma fase posterior — todas
as mudanças de Q24/Q45/D40 (fases 3M+), Q23 (3V), D59 (3U), Q55 (3W), Q38 (3X), Q8 (3Y) aconteceram
depois desse commit e nunca o tocaram. Seus registros para essas questões refletem, portanto, a
geometria/texto **anterior** às correções que as tornaram publicáveis, corretas ou completas.
Confirmado que `ContentAssignment` (o módulo, `content_assignment.py`) **nunca é chamado por
`src/enade/extraction/pipeline.py` nem por `assembler.py`** — não influencia o corpus real publicado
nem o readiness. **Classificação**: limitação documental remanescente, não-bloqueante (Seção A) —
o próprio veredito interno do ledger ("zero duplicatas, zero faltantes", capability
`canonical_content_assignment`) nunca foi re-verificado contra o corpus atual de 80/80 questões.
Regenerá-lo exigiria escrever/rodar uma nova ferramenta (`scripts/generate_content_assignment_ledger.py`
já existe mas não foi executado nesta fase — rodá-lo é trabalho de extração/regeneração de dados,
fora do escopo desta fase de auditoria conforme a Seção 4 do prompt). Recomendado para uma fase
futura, isolada e explicitamente escopada (Seção Y).

## T. Auditoria visual

Reinspeção obrigatória confirmada, sem reabrir nenhum achado: Q8, Q38, Q45, Q55, Q23, D40, D59, D10
— todos com `visual_validation: passed` em `visual-audit-2008-computing.json`, hashes de asset
inalterados desde suas respectivas fases de resolução (confirmado por zero drift, Seção W). Para as
demais 72 questões: hash confirmado (Seção W), evidência anterior preservada, rastreabilidade
mantida (nenhum registro de auditoria visual foi reescrito ou removido). Estado real, literal:

```text
visual audit: 80 passed, 0 failed, 0 not_performed (fully_covered=True)
```

(80, não 77 — ver Seção O para a reconciliação do denominador). Nenhum status foi promovido em
massa — cada uma das 80 entradas já carrega sua própria nota individual, escrita na fase em que foi
efetivamente inspecionada.

## U. Testes

```text
total coletado (baseline desta fase, antes do gate de freeze): 867
total coletado (final, com tests/test_phase4a_freeze.py incluído): 881
passed: 881, failed: 0, skipped: 0, xfail: 0, xpass: 0
```

Distribuição por arquivo (top 10 de 44 arquivos de teste): `test_extraction_assembler.py` (71),
`test_schema_question.py` (62), `test_extraction_chrome.py` (50), `test_extraction_figures.py` (49),
`test_extraction_pipeline_2008.py` (48), `test_layout_overrides.py` (43),
`test_alternative_content_assignment.py` (35), `test_readiness.py` (29),
`test_extraction_pipeline_integration.py` (29), `test_same_row_ordering.py` (27). O 44º arquivo,
novo nesta fase, é `test_phase4a_freeze.py` (14 testes, Seção X). Nenhum
`pytest.mark.skip`/`xfail` incondicional encontrado (apenas 4 arquivos usam `skipif` condicionado à
presença do corpus local, que está presente — portanto 0 skips reais nesta execução). Nenhum teste
duplicado, nenhuma fixture órfã, nenhum assert dependente de ordem acidental encontrado na revisão
arquitetural (Seção G) além do já conhecido gap de cobertura unitária de
`alternative_boundary_assignment` (coberto apenas por testes de integração — reportado, não
corrigido, por ser um gap pré-existente de baixo risco, não uma regressão desta fase).

## V. Quality gates completos

```text
pytest:                        881 passed (867 baseline + 14 do novo gate de freeze)
ruff check .:                  All checks passed!
ruff format --check .:         426 files already formatted
mypy src:                      Success: no issues found in 61 source files
enade validate-schema:         13/13 fixture(s) valid
enade validate-manifest:       OK (0 warning(s))
enade audit-extraction:        80/80 (2008-b), 55/55 (2011), 40/40 x3 (2021)
enade verify-gold + assess-readiness: ver Seções C/L/M/N
tests/test_protected_corpus.py (protected files):  4/4 passed
tests/test_blocker_ledger.py (blocker ledger):     24/24 passed
tests/test_content_assignment.py:                  11/11 passed (unitário; artefato em si está desatualizado, Seção S)
tests/test_source_availability.py:                 14/14 passed
tests/test_layout_overrides.py (override integrity): 43/43 passed
tests/test_generalization_architecture.py (capability registry): 12/12 passed
tests/test_phase4a_freeze.py (freeze/reprodutibilidade): 14/14 passed
tests/test_phase4a_freeze.py (reprodutibilidade/freeze): ver Seção X
```

## W. Reprodutibilidade A/B

Duas regenerações limpas e independentes (diretórios temporários isolados, nunca escrevendo no
corpus publicado), 2008-b + 2011 + os três cursos de 2021:

```text
run A vs published: diff -rq -> vazio, para os 5 cadernos
run B vs published: diff -rq -> vazio, para os 5 cadernos
run A vs run B:      diff -rq -> vazio, para os 5 cadernos
```

Hashes agregados (SHA-256 do conjunto ordenado de `sha256(caminho-relativo)` de todo `.md`/`.png`
publicado, por caderno) — idênticos entre run A, run B e o corpus publicado, em todos os 5 casos:

```text
2008-b:                                   4403f5f18dacd8b0d6ec06d874920a0690d5741594713f3ddaf6399c185cc865
2011:                                     b38ca634a5abc49799cb0fc0e0168284e210d667a3540be471e932a47b462b68
2021-ciencia-da-computacao-bacharelado:   243e4c737e2ef8764057eaf0f39a12ccf5988ab261eb9006c8c1d3150f696056
2021-ciencia-da-computacao-licenciatura:  75224ad72ca17594e47279ba6a6bf9f67e607e4365123539f5d1147bb2ac70f8
2021-sistemas-de-informacao:              cb6e5cca86a0d4ec73be04a260be187300103c7bde32124fe089bfb6cbb05b21
```

**Run C não foi necessária**: A e B foram idênticas entre si e ao publicado em todos os 5 cadernos —
nenhuma divergência, nenhum comportamento dependente de ordem, nenhum hash variável, nenhum arquivo
não-determinístico encontrado, e o ambiente não foi alterado durante esta fase (nenhuma dependência,
versão de biblioteca, ou variável de ambiente foi tocada). Registrado aqui como a justificativa
explícita exigida pela Seção 21 do prompt — nunca declarando três runs quando apenas duas foram
feitas.

## X. Freeze manifest

Criado `data/manifests/phase-4a-freeze.json` — reutiliza o padrão já estabelecido por
`protected-files-2011-2021.json`/`test_protected_corpus.py` (Fase 3M), estendido para cobrir o
estado *completo* desta fase (não apenas 2011/2021): branch/HEAD/master/origin_master/merge_base;
a lista exata dos 12 arquivos não commitados no momento da geração do freeze (path, tipo de
mudança, sha256 - antes de o próprio arquivo de freeze nascer, por definição: um manifesto nunca
pode conter o próprio hash de si mesmo); hashes dos 3 PDFs-fonte por ano; hashes de todos os 32
arquivos pré-existentes em `data/manifests/` (nunca incluindo o próprio arquivo de freeze); hashes
de todos os 34 relatórios em `docs/phase-*-report.md` (desde `phase-1c-report.md`, passando por
`phase-2a` a `phase-2f-report.md`, `phase-3a` a `phase-3z-report.md` - 26 letras, não 25 - até este
`phase-4a-report.md`); hash agregado de cada um dos 5
corpora publicados (Seção W); o resumo dos `protected_files` (270+18=288, reconciliado desde a Fase
3M); os resultados literais dos quality gates; o veredito de readiness de 2008-b/2011/2021-CC-B; e
os 2 registros de limitação de fonte (D09/D10). Nenhum timestamp não-determinístico foi incluído em
nenhum campo usado para hash agregado; nenhum caminho absoluto/temporário; nenhum segredo. Caminhos
ordenados alfabeticamente antes de cada hash agregado, para determinismo.

Gate de verificação: `tests/test_phase4a_freeze.py` (novo, 14 testes/casos incluindo os 5
parametrizados por corpus) — verifica: branch/HEAD/master corretos; todo manifesto e relatório
listado existe e bate hash; nenhum manifesto extra não-inventariado; hash agregado de cada corpus
publicado bate com o valor congelado; D09/D10 continuam `source_unavailable_confirmed`, nunca
"resolved"; o veredito de readiness de 2008-b bate com o congelado; e — o gate central da Seção 27 —
o conjunto de arquivos atualmente não commitados (`git status --porcelain=v1`) contém, no mínimo,
exatamente os arquivos que o freeze já declarou, com hash idêntico (nunca exige árvore limpa; exige
que nada do que já foi congelado tenha sido alterado ou desaparecido desde então).

**Bug real encontrado e corrigido pelo próprio gate, durante a geração do freeze**: o script gerador
(scratchpad, não commitado - um utilitário de uso único, nunca parte de `src/enade/`) tinha seu
próprio helper `run()` chamando `.strip()` no *bloco inteiro* da saída de `git status
--porcelain=v1` antes de dividir em linhas - como a primeira coluna de uma linha porcelain
"modified, unstaged" é um espaço literal (semanticamente significativo, não padding), isso comia
exatamente o primeiro caractere do **primeiro** caminho listado
(`data/manifests/blocker-ledger-2008.yaml` virava `ata/manifests/blocker-ledger-2008.yaml`) - nunca
os demais, pois `.strip()` só afeta as bordas do blob inteiro, não de cada linha. Detectado
imediatamente pelo próprio `test_working_tree_uncommitted_set_matches_exactly_what_the_freeze_declared`
na primeira execução (falha real, nunca ignorada) - corrigido isolando esse `git status` numa
função `run_raw()` própria, sem `.strip()` no bloco inteiro, e regenerando o manifesto. Nenhum outro
campo do freeze foi afetado (branch/HEAD/master/hashes de manifesto/relatório/corpus usam `run()`
legitimamente, já que `git rev-parse`/`git branch --show-current` não têm essa coluna posicional
sensível a espaço). Executado após a correção: **14/14 casos passando** (Seção Z).

## Y. Pacote de revisão e plano de commit

### Código

| path | propósito | risco | evidência | revisão recomendada |
|---|---|---|---|---|
| `src/enade/extraction/source_availability.py` | novo módulo: evidência estruturada de ausência de fonte + 2 gates | médio (novo módulo, mas puramente aditivo, nunca consultado sem um manifesto opt-in) | 14 testes unitários, Seção U | ler `is_confirmed_unavailable`/`verify_source_hashes_match` por completo |
| `src/enade/readiness.py` | integra a política de source-availability ao gate de readiness | médio (muda o comportamento de `assess_readiness`, mas só quando os 2 novos parâmetros são passados) | 9 testes novos + 20 pré-existentes inalterados | conferir que `structural=False` só se aplica com evidência completa |
| `src/enade/cli.py` | novo output de `assess-readiness` (3 seções) + 2 novas opções | baixo (aditivo; comportamento de 2011/2021 confirmado idêntico) | Seções M/N | rodar `--help` e comparar com o texto do relatório |
| `src/enade/extraction/blocker_ledger.py` | +1 campo opcional (`source_limitation_id`) | baixo | `validate_ledger`: 0 issues nas 60 entradas pré-existentes | confirmar default `None` |

### Dados

| path | propósito | risco | evidência |
|---|---|---|---|
| `data/manifests/source-availability-2008.yaml` | evidência estruturada completa para D09/D10 | baixo (dados novos, nunca sobrescreve nada) | Seção K |
| `data/manifests/blocker-ledger-2008.yaml` | D09/D10: evidência expandida + cross-ref | baixo (edição textual, `status` inalterado) | Seção P |
| `data/manifests/extraction-capabilities.json` | 1 cross-reference documental (D10) | muito baixo | Seção Q |
| `data/manifests/phase-4a-freeze.json` | manifesto de freeze desta fase | baixo (somente leitura por qualquer consumidor) | Seção X |

### Outputs

Nenhum `.md`/asset de questão foi alterado por esta fase (confirmado, Seção W: zero drift em todos
os 5 cadernos). Os outputs de 2008-b (Q8/Q38/Q55/D59 etc.) já estavam publicados desde as Fases
3U-3Y, revisados em seus próprios relatórios.

### Testes

`tests/test_source_availability.py` (14, novo), `tests/test_readiness.py` (+9),
`tests/test_phase4a_freeze.py` (11, novo) — cobrem exatamente os riscos listados acima.

### Relatórios

`docs/phase-3a-report.md` a `docs/phase-3z-report.md` (25, histórico, imutável) +
`docs/phase-4a-report.md` (este arquivo, consolidação final).

### Plano de commit recomendado (não executado)

**Opção B — commits temáticos**, preferida sobre um commit único: o diff é grande (471+13 arquivos)
mas naturalmente divisível por fase/responsabilidade, e cada tema já tem sua própria evidência de
teste independente.

1. **Arquitetura de extração + overrides + manifests (Fases 3A-3Y)**: todo o código em
   `src/enade/extraction/`, `data/manifests/layout-overrides.yaml`,
   `data/manifests/*-capabilities.json`, `data/manifests/source-token-ledger-2008.yaml`,
   `data/manifests/content-assignment-2008-b.json` — já é um único bloco coeso commitado
   externamente como os 27 commits existentes entre `master` e `HEAD`; **não precisa ser
   recriado** (já é `HEAD`).
2. **Outputs de 2008-b/2011/2021**: idem — já parte de `HEAD`, `349` arquivos `data/questions/`.
   Mensagem sugerida (se fosse recriado do zero): `"feat: extract and publish 2008-b/2011/2021
   computing-track corpus (Fases 1-3Y)"`.
3. **Política de source-availability (Fase 3Z, ainda não commitada)**: `src/enade/extraction/source_availability.py`,
   `data/manifests/source-availability-2008.yaml`, `src/enade/readiness.py`,
   `src/enade/cli.py`, `src/enade/extraction/blocker_ledger.py`, `data/manifests/blocker-ledger-2008.yaml`,
   `tests/test_source_availability.py`, `tests/test_readiness.py`, `docs/phase-3z-report.md`.
   Mensagem sugerida: `"feat: formalize source-unavailable policy for D09/D10 with structured, re-verifiable evidence"`.
   Depende de: nada externo (auto-contido); deve ser commitado como uma unidade (o módulo, o
   manifesto e o gate de readiness são inseparáveis — um sem o outro deixa código morto ou um
   manifesto sem consumidor).
4. **Auditoria e freeze (Fase 4A)**: `data/manifests/extraction-capabilities.json` (o pequeno
   cross-reference), `data/manifests/phase-4a-freeze.json`, `tests/test_phase4a_freeze.py`,
   `docs/phase-4a-report.md`. Mensagem sugerida: `"docs: Fase 4A - integration audit, reproducible
   freeze, and human-review package for the 2008-b pilot"`. Depende do commit 3 (referencia seus
   arquivos no freeze).

Checks após cada commit: `pytest -q` + `ruff check .` + `mypy src` + `enade verify-gold`/
`assess-readiness` para 2008-b/2011/2021-CC-B — os mesmos comandos da Seção C, repetidos após cada
commit da Opção B antes de prosseguir para o próximo.

**Risco de separar os commits 3 e 4**: baixo — o commit 4 apenas lê o estado que o commit 3 já
estabelece (o freeze manifest referencia arquivos do commit 3 pelo caminho, nunca por conteúdo
embutido); nenhuma dependência circular.

## Z. Estado Git final e recomendação

`git status --short` final (após a criação do freeze manifest e deste relatório):

```text
 M data/manifests/blocker-ledger-2008.yaml
 M data/manifests/extraction-capabilities.json
 M src/enade/cli.py
 M src/enade/extraction/blocker_ledger.py
 M src/enade/readiness.py
 M tests/test_readiness.py
?? data/manifests/phase-4a-freeze.json
?? data/manifests/source-availability-2008.yaml
?? docs/phase-3z-report.md
?? docs/phase-4a-report.md
?? src/enade/extraction/source_availability.py
?? tests/test_phase4a_freeze.py
?? tests/test_source_availability.py
```

Nenhum commit, push, PR, merge, rebase, cherry-pick, `git add`, ou `git clean` foi executado.
`master`/`origin/master` permanecem `a5dfaab0c105150df3a7201c16547708cef45292`, idênticos ao início
desta fase. Todos os diretórios temporários de investigação
(`/tmp/p4a_runA`, `/tmp/p4a_runB`, arquivos `.hashes` intermediários) foram removidos antes da
conclusão.

**Recomendação** (Classificação `PILOT_FREEZE_ESTABLISHED` / `READY_FOR_HUMAN_REVIEW`):

1. Revisão humana explícita do diff completo — priorizando os 4 arquivos de código de maior risco
   listados na Seção Y (`source_availability.py`, `readiness.py`, `cli.py`, `blocker_ledger.py`).
2. Inspeção dos 2 achados de auditoria não-bloqueantes desta fase: o cross-reference de capability
   registry (Seção Q, trivial) e a limitação conhecida do `content-assignment-2008-b.json`
   congelado (Seção S, recomendo uma fase futura isolada e explicitamente escopada para
   regenerá-lo, nunca misturada com trabalho de extração/correção de conteúdo).
3. Aprovação explícita antes de qualquer commit.
4. Execução da estratégia de commit temático (Seção Y, Opção B) — item 3 (política de source-
   availability) e item 4 (auditoria/freeze) são os únicos ainda pendentes de commit nesta sessão;
   itens 1-2 já são `HEAD`.
5. Nova execução dos quality gates (Seção V) após cada commit.
6. Somente depois considerar merge para `master` ou início de um novo corpus/ano — nunca
   automaticamente, nunca nesta fase.

**Princípio final, honrado por esta fase**: o piloto 2008-b está pronto para revisão porque cada um
dos seus 482 arquivos (471 já commitados + 11 pendentes) está explicado, categorizado e
re-verificável — não porque a árvore de trabalho é pequena (não é) ou porque todos os testes passam
(passam, mas isso sozinho nunca teria sido suficiente sem o inventário completo desta fase). D09/D10
permanecem, deliberadamente e para sempre, visíveis como limitações documentais do pacote-fonte
atual — nunca "resolvidas", nunca escondidas, sempre reabríveis diante de uma fonte nova.
