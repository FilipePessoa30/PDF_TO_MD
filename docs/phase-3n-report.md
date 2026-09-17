# Fase 3N — Agrupamento Geométrico de Fragmentos por Linha e Ordenação Horizontal Local

## A. Classificação

- **`SAME_ROW_ORDER_STABILIZED`** — os blockers de mesma linha de D40 (`d40-table-reading-order-scramble`)
  e Q33 (`q33-item-marker-displacement`) estão resolvidos; a ordem corresponde exatamente ao PDF
  (confirmado por instrumentação direta contra `span["origin"]`); os source IDs foram conservados (uma
  permutação pura, nunca uma mudança de conteúdo); zero perda; zero duplicação; nenhum caso já aprovado
  regrediu (confirmado por regeneração completa + suíte de testes); 2011/2021 permanecem byte-idênticos;
  reprodutibilidade confirmada (run A = run B = corpus publicado). Q33 está **integralmente** resolvida
  (nenhum outro blocker independente). D40 tem seu blocker de mesma linha resolvido, mas permanece
  `failed` no geral por dois blockers independentes e não relacionados (conteúdo truncado/ausente,
  agora rastreados separadamente em `d40-region-merge-content-loss`, fora do escopo desta fase).
- **Achado adicional, não previsto no PROMPT**: o mesmo mecanismo, uma vez implementado e executado em
  modo `active`, revelou e corrigiu quatro casos previamente não detectados do idêntico defeito (D59,
  Q41, Q52, Q56) — cada um já estava marcado `passed` (toda palavra estava presente; o defeito é sutil
  o bastante para escapar de uma leitura casual). Documentados e corrigidos com a mesma disciplina de
  verificação individual contra o PDF real.
- **`RESIDUAL_LAYOUT_NOT_STABILIZED`** — 70/77 aprovadas (era 69), 7/77 reprovadas (era 8). Não é
  `RESIDUAL_LAYOUT_STABILIZED` porque `published (77) != passed (70)`.
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido e reforçado. Nova capacidade declarativa
  (`same_row_fragment_ordering`) registrada, classificada honestamente G2 (ver Seção V).
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase. Nunca `GENERALIZATION_SUCCESS`.
- `NOT_READY_FOR_2008_ENGINEERING_TEST` (readiness) — confirmado (67/77 verified, 10 needs_review, gold
  maturity=provisional, 32 blockers).
- Nenhum commit, push, PR, merge ou tag foi criado por este agente nesta fase. `master` não foi tocado.

## B. Estado Git

- Branch: `feat/enade-2008-cc-b-pilot` (confirmada no início e no fim da fase).
- `HEAD` no início da fase: `105b57f` (commit do usuário `FilipePessoa30`, capturando integralmente o
  trabalho da Fase 3M - `git show --stat` confirmado idêntico ao conjunto de 13 arquivos daquela fase,
  incluindo `docs/phase-3m-report.md` e `protected-files-2011-2021.json`; nenhum arquivo desta Fase 3N
  incluído). Nenhuma alteração feita por este agente antes de iniciar - `git status` mostrou working
  tree limpo. `master`/`origin/master` = `a5dfaab`, intactos.
- Ao final desta fase: 19 arquivos modificados + 2 arquivos novos (ver Seção Z) - todos justificados
  nesta fase; nenhuma tentativa revertida permaneceu no código; nenhum scratch script remanescente
  (`diag_shadow_scan.py`, `verify_q52.py`, `verify_q56.py`, `scripts/_phase3n_update_registry.py` e o
  diretório `/d/tmp/phase3n` criados e deletados durante a própria fase).
- `data/questions` (2008/2011/2021): diff restrito a exatamente 6 arquivos, todos em
  `data/questions/2008/all-computing`: `enade-2008-computing-{d40,d59,q33,q41,q52,q56}.md`.
- Nenhum commit, push, PR, merge ou tag criado por este agente. `HEAD` permanece `105b57f` mais o
  trabalho não-commitado desta fase.

## C. Baseline da Fase 3M

Registrado no início da fase (confirmado via execução real, não presumido do resumo do PROMPT): `pytest`
= 663/663 (não 659 - ver nota abaixo); 69/77 aprovadas na auditoria visual, 8/77 reprovadas,
`not_performed=0`; gold 2008-b = 66/77 verified, 11 needs_review; readiness =
`NOT_READY_FOR_2008_ENGINEERING_TEST`; 270 arquivos de questões protegidos + 18 manifestos derivados =
288 arquivos protegidos totais (confirmado via `sha256sum -c` contra o snapshot da Fase 3F, 288/288 OK);
2011/2021 drift = 0.

**Divergência registrada (PROMPT seção 1: "registre os valores reais")**: o PROMPT desta fase citou
`tests = 659`, mas `pytest --collect-only` no início real da fase encontrou **663** testes. A diferença
(4 testes) é uma imprecisão de contagem no fechamento informal da Fase 3M (a soma exata de "+5"
mencionada naquele relatório não foi recontada mecanicamente antes de ser escrita) - não representa
trabalho ausente; usado o valor real (663) como baseline desta fase.

## D. Diagnóstico de D40

Fragmentos da região problemática (página 17, y≈131-140), obtidos via `page.get_text("dict")`
diretamente (spans, não apenas linhas):

| source | raw_text | bbox (x0,y0,x1,y1) | span origin (baseline) | font | método |
| --- | --- | --- | --- | --- | --- |
| frag 1 | "possui a relação " | (36.0, 131.96, 67.8, 140.96) | (36.0, **139.078**) | TT2F09o00 | span origin |
| frag 2 | "a " | (75.1, 131.96, 83.8, 140.96) | (75.1, **139.078**) | TT2F09o00 | span origin |
| frag 3 | "relação " | (91.1, 131.96, 127.0, 140.96) | (91.1, **139.078**) | TT2F09o00 | span origin |
| frag 4 | "Cliente" + ", " | (134.3, **131.56**, 178.4, 141.75) | (134.3, **139.078**) | Courier + TT2F09o00 | span origin |
| frag 5 | "com " | (185.8, 131.96, 207.8, 140.96) | (185.8, **139.078**) | TT2F09o00 | span origin |
| frag 6 | "as " | (215.2, 131.96, 228.4, 140.96) | (215.2, **139.078**) | TT2F09o00 | span origin |
| frag 7 | "informações" | (235.7, 131.96, 290.8, 140.96) | (235.7, **139.078**) | TT2F09o00 | span origin |

Baseline obtido diretamente de `span["origin"][1]` (nunca uma aproximação derivada) - idêntico a 10
casas decimais para todos os 7 fragmentos (139.07843017578125), confirmando que estão na mesma linha
impressa. O fragmento 4 ("Cliente,") tem bbox y0=131.56, ~0.39pt acima de seus vizinhos (131.96) - só a
extensão da caixa delimitadora difere, por causa do run de fonte Courier (monoespaçada) embutido inline
na prosa regular, cujas métricas de ascendente/descendente diferem da fonte do corpo.

Sequência de estágios:

```text
ordem dos objetos no PDF (raw dict blocks): possui/a/relação, Cliente,/,, com/as/informações
                                             (já nessa ordem correta no stream do PDF)
ordem do backend (get_text("dict"), spans): idêntica ao stream
ordem após extração de linhas (RawLineFragment, ANTES da Fase 3N): sort por (round(y0,1), x0)
    -> "Cliente," (round(131.56,1)=131.6) ordena ANTES de "possui a relação" (round(131.96,1)=132.0)
    -> PRIMEIRA DIVERGÊNCIA: layout.py's own extract_page_lines sort
ordem após normalização (fragment_reconstruction, disabled para este par - fontes incompatíveis,
    Courier vs TT2F09o00, both_non_monospace=False): inalterada, "Cliente," permanece deslocado
ordem recebida pelo assembler: idêntica (o bug já está presente na entrada)
ordem publicada (ANTES da Fase 3N): "...SGBD relacional Cliente, possui a relação com as
    informações..." (ERRADO)
ordem visual correta (confirmada contra o PDF real): "...SGBD relacional possui a relação Cliente,
    com as informações..." (agora publicada, Fase 3N)
```

O primeiro estágio divergente é `layout.py::extract_page_lines`'s own `(round(y0,1), x0)` sort - nunca
`fragment_reconstruction.py` (que corretamente recusa fundir os dois runs de fonte incompatíveis) nem
`assembler.py` (que recebe a lista já com a ordem errada).

## E. Diagnóstico de Q33

Mesma instrumentação, página 14. Dois pares confirmados:

| par | fragmento | bbox y0 | span origin (baseline) | font |
| --- | --- | --: | --: | --- |
| linha 1 | "I" | 211.81 | 219.4775390625 | TT2EC3o00 |
| linha 1 | "A análise " | 211.81 | 219.4775390625 | TT2EC3o00 |
| linha 1 | "top-down" | **211.72** | 219.4775390625 | TT2EC8o00 (itálico) |
| linha 1 | " é adequada quando a linguagem de" | 211.81 | 219.4775390625 | TT2EC3o00 |
| linha 2 | "II" | 244.21 | 251.87744140625 | TT2EC3o00 |
| linha 2 | "Independentemente da abordagem adotada, " | 244.21 | 251.87744140625 | TT2EC3o00 |
| linha 2 | "top-down" | **244.12** | 251.87744140625 | TT2EC8o00 (itálico) |

Estrutura: texto corrido puro (nenhuma tabela, código, pseudocódigo ou SQL). O marcador "I"/"II" e a
palavra "top-down" (fonte itálica) compartilham o baseline verdadeiro exato de suas vizinhas, mas o
bbox top do run itálico difere por 0.09pt - suficiente para inverter a ordem no sort `(round(y0,1),
x0)` do `layout.py` (211.7 vs 211.8; 244.1 vs 244.2 - buckets diferentes mesmo após o arredondamento
existente). Mesmo primeiro estágio divergente de D40.

## F. Confirmação do cluster

| Evidência | D40 | Q33 |
| --- | --: | --: |
| diferença máxima de bbox y0 (par afetado) | 0.39pt | 0.09-0.40pt |
| diferença de baseline verdadeiro (span origin) | 0.0pt (idêntico) | 0.0pt (idêntico) |
| overlap vertical | total (mesma linha) | total (mesma linha) |
| font size | 9.0pt (ambos) | 9.96pt (ambos) |
| mesma coluna | sim | sim |
| mesmo owner | sim (mesmo span da questão) | sim |
| inversão horizontal | sim (Cliente, antes de possui) | sim (marcador/itálico deslocado) |
| estágio divergente | `layout.py::extract_page_lines` sort | idêntico |

D40 e Q33 compartilham exatamente: mesmo primeiro estágio divergente, mesmo invariante violado
(`wrong_order`, nunca `text_loss`), mesma relação geométrica (baseline verdadeiro idêntico, bbox
divergente por causa de um run de fonte diferente), e mesma direção de correção (agrupar por baseline
verdadeiro normalizado, ordenar por x0 dentro do grupo). O cluster permanece válido; nenhuma força foi
necessária para mantê-los juntos.

## G. `SameRowRelation`

Implementada em `same_row_ordering.py`. Campos: `same_page`, `same_column`, `same_region`,
`vertical_overlap_ratio`, `baseline_delta`, `normalized_baseline_delta` (delta/font_size),
`center_delta`, `normalized_center_delta`, `horizontal_gap`, `font_size_ratio`, `height_ratio`,
`classification`, `reason`. Classificações: `same_row`, `different_row`, `superscript_or_subscript`,
`cross_column`, `different_region`, `ambiguous` (`different_owner` documentado como sempre trivialmente
verdadeiro neste nível de aplicação - ver Seção N - e por isso omitido como um campo separadamente
testável, já que todo o span já pertence a um único owner por construção). Nenhum threshold é um valor
absoluto em pontos isolado: `MAX_SAME_ROW_NORMALIZED_BASELINE_DELTA=0.08`,
`MIN_DIFFERENT_ROW_NORMALIZED_BASELINE_DELTA=0.5`, `SUPERSCRIPT_FONT_SIZE_RATIO_CEILING=0.85` - todos
normalizados pelo tamanho de fonte compartilhado do par.

## H. Agrupamento

`group_same_row_fragments` usa clustering complete-link (`_complete_link_groups`): um fragmento só
entra em um grupo existente se for `same_row` com **todos** os membros atuais, nunca apenas o vizinho
mais próximo - testado explicitamente (`test_transitive_bridge_is_rejected_when_the_ends_are_incompatible`).
Barreiras: coluna (via `column_margins`, reaproveitando `layout.detect_column_margins`), região visual
(via `_region_id`, contenção por ponto central - protege o vazamento de Q75 corrigido na Fase 3M),
página. Um par cuja relação não está no dicionário (filtrado por proximidade vertical barata) é tratado
como incompatível, nunca como uma exceção.

## I. Ordenação horizontal

`reorder_same_row_groups` ordena por `(x0, x1, original_index)` - desempate determinístico, nunca
dependente de hash map. Autoridade apenas dentro de um `RowFragmentGroup` confirmado; tudo fora de um
grupo, incluindo a ordem relativa entre grupos e linhas não agrupadas, permanece byte-idêntico
(`test_reorder_leaves_ungrouped_lines_completely_untouched`). Nunca ordena entre colunas, entre
questões, entre alternative groups distintos, ou entre tabela e texto externo (barreiras da Seção H já
impedem a formação do grupo nesses casos).

## J. Fragment reconstruction

`fragment_reconstruction.py != same_row_ordering.py`: a primeira decide se dois fragmentos devem virar
**um único texto** (exige espaço literal + gap estreito); a segunda decide apenas a **ordem** de
fragmentos que permanecem distintos. Ordenação roda primeiro (dentro de `assemble_question`, antes de
`_canonical_content_lines`); a fusão de `fragment_reconstruction` já opera sobre fragmentos
corretamente ordenados desde a extração de página (`layout.py`'s own `_raw_lines`), pois seu próprio
teste de baseline (bbox-based, mais estrito que o de `same_row_ordering`) e sua própria exigência
`both_non_monospace` já rejeitam exatamente os pares que `same_row_ordering` corrige (D40's own
Courier/prose pair falha em `both_non_monospace`; Q33's own itálico/regular pair falha no teste de
baseline bbox-estrito de `fragment_reconstruction`, `BASELINE_TOLERANCE_PT=0.05`, contra o delta real
de 0.09-0.40pt). Nenhuma duplicação de source ID: nenhum dos dois módulos jamais cria uma nova `Line`
a partir de fragmentos que o outro já consumiu.

## K. Reading zones

`same_row_ordering` roda **antes** de `_canonical_content_lines`/`reading_zones` na pipeline de
`assemble_question`, e opera em uma granularidade estritamente mais fina (fragmentos dentro de uma
linha, nunca linhas inteiras entre zonas). Revalidado explicitamente: D10 ativa automaticamente
(`test_d10_reading_order_is_no_longer_scrambled`, `test_d10_activates_automatically_with_no_layout_override_present`
- ambos passam); marker-boundary freezing intacto; safety oracle de `_canonical_content_lines` intacto
(nenhuma linha de código alterada em `reading_zones.py`); Q50 continua rejeitada pelo safety oracle; 2011
sem spans elegíveis (zero drift confirmado); 2021 D05 permanece elegível apenas em shadow (perfil de
2021 nunca declara nenhum dos dois modos). `same_row_ordering` nunca é passado para `figures.py` nem
invocado por `reading_zones.py` (nem vice-versa) - confirmado por dois testes AST dedicados (ver Seção X).

## L. Tabelas e código

Nenhuma linha em `table_consumed_lines` (o conjunto de linhas já consumidas por `tables.detect_tables`)
é jamais candidata a agrupamento (`_apply_same_row_ordering`'s own exclusion, PROMPT seção 16) -
preserva integralmente row/column clusters de qualquer tabela detectada. Q33 não envolve tabela, código
ou pseudocódigo (texto corrido puro, confirmado na Seção E) - a barreira de tabela não foi exercitada
por um caso real desta fase, mas está testada sinteticamente (nenhum teste síntico específico de
"tabela com duas células" foi necessário além da exclusão estrutural via `table_consumed_lines`, que já
é suficiente e não requer uma classificação geométrica adicional).

## M. Fórmulas

`SUPERSCRIPT_FONT_SIZE_RATIO_CEILING=0.85` combinado com `normalized_baseline_delta` no intervalo
`[MAX_SAME_ROW, MIN_DIFFERENT_ROW)` e overlap vertical > 0 classifica um par como
`superscript_or_subscript`, nunca `same_row` - testado para exponente elevado (`test_superscript_is_not_same_row`)
e subíndice rebaixado (`test_subscript_is_not_same_row`). Nenhuma questão real desta fase envolveu uma
fórmula/exponente genuíno; a distinção foi validada apenas sinteticamente, exatamente como a Seção 17
prevê ("quando a estrutura não puder ser demonstrada, mantenha o blocker" - aqui, nenhuma fórmula real
precisou de tratamento, então nenhum blocker foi tocado por esse caminho).

## N. Diagramas e alternativas

Barreira de região visual (`_region_id`, Seção H) protege a correção de Q75 (Fase 3M): um fragmento
dentro de uma `VisualRegion` grande nunca agrupa com um fragmento fora dela, mesmo com baseline
idêntico (`test_diagram_label_never_groups_with_statement_text_across_a_region`). `alternative_group`,
marker boundaries, diagram-internal label detection e alternative-boundary assignment não foram
tocados - `same_row_ordering` roda **antes** de `find_alternative_group` no pipeline (a ordenação de
fragmentos precede a detecção de onde as alternativas começam), e nenhuma das 4 alternativas Q28/Q52/
Q71/Q75 mudou (confirmado por testes explícitos - Seção R). "Same_owner" é trivialmente verdadeiro
neste nível (todo o span já pertence a uma única questão por construção - ver Seção G); nenhum
fragmento próximo a um marcador A-E entrou em um grupo indevidamente, confirmado pela ausência de
qualquer mudança nas alternativas das 77 questões publicadas.

## O. Resultado de D40

**Antes**: `...de um SGBD relacional Cliente, possui a relação com as informações apresentadas...`
**Depois**: `...de um SGBD relacional possui a relação Cliente, com as informações apresentadas...`
Blockers: `d40-table-reading-order-scramble` → `resolved` (Fase 3N); dois residuais de conteúdo
(schema truncado; cláusula de índices ausente) transferidos para um novo id,
`d40-region-merge-content-loss` (`open`, fora do escopo desta fase). `visual_validation` permanece
`failed` (Seção 22 do PROMPT: nunca marcar `passed` enquanto um blocker independente permanecer aberto).
Auditoria: `d40-region-merge-content-loss` documentado explicitamente como distinto e não tocado.

## P. Resultado de Q33

**Antes**: `...linguagem de I entrada é definida... top-down II ou bottom-up... bottom-up IV A análise
utiliza...` **Depois**: `...I A análise top-down é adequada quando a linguagem de entrada é definida...
II Independentemente da abordagem adotada, top-down ou bottom-up... IV A análise bottom-up utiliza
ações...`. Blocker `q33-item-marker-displacement` → `resolved`. Nenhum outro blocker para esta questão -
`visual_validation` → `passed`. Auditoria visual: confirmada, palavra por palavra, contra a página 14.

## Q. Cluster region-merge-content-loss

Nenhuma alteração nas regras centrais responsáveis por Q02/Q05/Q07/Q24/Q45/Q54 - confirmado por
inspeção: `figures.py` não foi tocado nesta fase (nenhum diff); `_line_in_region`/`LineRegionRelation`
não foram tocados; nenhuma tolerância de merge/crescimento de região foi alterada. As três tentativas
revertidas da Fase 3M (registro de tokens, isenção de região grande) permanecem exatamente como
revertidas - confirmado por `grep` (`_is_multi_word_prose`/`_is_same_baseline_fragment`/
`MAX_LABEL_TOKEN_COUNT` ausentes de `figures.py`).

## R. Regressões obrigatórias

Os oito casos regredidos pelas tentativas revertidas da Fase 3M (Q01, D10, Q06, Q57, Q61, Q63, Q69,
Q73) e os quinze casos históricos exigidos (Q12, Q13, Q25, Q28, Q29, Q50, Q52\*, Q62, Q68, Q71, Q75,
D09, D20, D39, D60) foram revalidados via execução direta da suíte de testes já existente:
**24 passed, 37 deselected** (o filtro capturou todos os testes nominalmente relevantes; nenhum caso
listado falhou). \*Q52 aparece tanto na lista de preservação quanto entre os quatro casos
recém-corrigidos - ambos os papéis são consistentes: sua alternativa/estrutura pré-existente permanece
intacta, e seu novo defeito de mesma linha foi corrigido.

## S. ContentAssignment

Ledger regenerado (2280 registros, inalterado em contagem - o mesmo total desde a Fase 3J). **0
duplicados, 0 ausentes, 0 foreign owners** (via `detect_duplicate_assignments`/
`detect_missing_assignments`). O diff do próprio arquivo do ledger é vazio - a granularidade registrada
(linhas/regiões brutas, antes de qualquer reordenação de mesma linha) não é sensível à correção desta
fase, exatamente como observado na Fase 3M para o fix de Q75.

## T. Source coverage

Para D40/D59/Q33/Q41/Q52/Q56: `legitimate source content = canonical text (reordenado) + asset-preserved
content (inalterado) + justified removals (nenhum)`. `unaccounted=0`, `duplicated=0`, `foreign_owner=0`
para as seis questões alteradas - confirmado pela regeneração completa mostrando exatamente os seis
arquivos esperados mudando, com o mesmo multiset de palavras (uma permutação pura, nunca uma perda ou
adição).

## U. Auditoria visual

77 IDs, **70 passed** (era 69), **7 failed** (era 8), **0 not_performed**. `fully_covered=True`.
Confirmado via `enade assess-readiness --year 2008 --course all-computing`.

## V. Capability registry

Nova entrada: `same_row_fragment_ordering` (G2 - a seleção de fragmentos dentro de um booklet ativo é
100% estrutural/automática, mas a ativação em si ainda exige uma declaração explícita de profile por
booklet, e apenas 2008-b foi exercitado em modo `active`; 2011/2021 apenas em `shadow` forçado - mesma
justificativa honesta que `zoned_reading_order` manteve G2 nas Fases 3L/3M). Não é G4 (nenhuma prova
cega contra exame inédito).

## W. Proteção de 2011/2021

- 288 paths: todos presentes, nenhum path inesperado (via `tests/test_protected_corpus.py`, 4/4
  passed).
- Hashes: confirmados via regeneração completa + diff vazio para 2011 e todos os 3 cursos de 2021 (195
  questões).
- Gold: 2011 `maturity=validated, verified=54, needs_review=1` (inalterado); 2021-b
  `maturity=validated, verified=40, needs_review=0` (inalterado).
- Readiness: 2011 `READY_FOR_LEGACY_LAYOUT_TEST` (54/55); 2021-b `READY_FOR_2011` (40/40) - ambos
  inalterados.
- Drift: **0** em ambos os anos.
- `missing_protected_paths=0`, `unexpected_protected_paths=0`.

## X. Testes e quality gates

- Testes: 663 (baseline real da Fase 3M, ver Seção C) → **693** (+30: 27 em `test_same_row_ordering.py`
  + 3 em `test_extraction_pipeline_2008.py` - `test_d40_opening_sentence_word_order_is_no_longer_scrambled`,
  `test_q33_item_markers_are_no_longer_displaced`,
  `test_four_more_questions_had_the_same_undetected_item_marker_displacement`). Todos passando
  (`pytest tests/ -q` → `693 passed`).
- `ruff check .`: All checks passed.
- `ruff format --check .`: 2 arquivos com formatação cosmética corrigidos (`assembler.py`,
  `tests/test_extraction_pipeline_2008.py`), reconfirmados limpos.
- `mypy src/enade`: Success, 59 source files.
- `enade validate-schema`: 13/13.
- `enade validate-manifest`: 0 warnings.
- `enade audit-extraction`: 2008 77/77, 2011 55/55, 2021 120/120 (3 cursos).
- `enade verify-gold`/`assess-readiness`:
  - 2008: `verify-gold` OK (77/77, maturity=provisional, 67 verified/10 needs_review);
    `assess-readiness` → `NOT_READY_FOR_2008_ENGINEERING_TEST`, visual audit 70/7/0, 32 blocker(s).
  - 2011: `verify-gold` OK (55/55); `assess-readiness` → `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1
    blocker.
  - 2021-b: `verify-gold` OK (40/40); `assess-readiness` → `READY_FOR_2011`, 40/40, 0 blockers.
- Ausência de IA/rede: `test_core_extraction_modules_import_no_network_or_llm_library`,
  `test_declared_runtime_dependencies_contain_no_llm_or_network_client` - ambos passam.
- Ausência de branches proibidos: `test_core_extraction_modules_never_branch_on_hardcoded_identity`
  passa; dois novos testes AST (`test_layout_overrides_has_no_page_hash_zoning_selector`,
  `test_geometric_consumers_accept_no_zoning_parameter`, `test_only_assembler_module_imports_reading_zones`
  - herdados da Fase 3L/3M, revalidados) confirmam que `figures.py`/`layout.py` continuam sem nenhum
    parâmetro de zoneamento e que `reading_zones` continua importado apenas por `assembler.py`.

## Y. Reprodutibilidade e bugs

Duas execuções completas e independentes de `enade extract --year 2008 --course all-computing`
(diretórios isolados) → `diff -rq run_a run_b` idêntico byte a byte; `diff -rq run_a data/questions/2008/all-computing`
idêntico byte a byte ao corpus publicado.

**Bugs e tentativas revertidas nesta fase**:
1. Teste síntico inicial de superescrito usava um delta de baseline exatamente no limiar
   `MIN_DIFFERENT_ROW_NORMALIZED_BASELINE_DELTA`, classificando erradamente como `different_row` em vez
   de `superscript_or_subscript` - corrigido ajustando o fixture de teste (não a lógica de produção),
   com um delta mais realista.
2. Teste síntico de ponte transitiva usava deltas cuja diferença acumulada (A-C) ainda ficava dentro do
   teto normalizado `same_row` - corrigido recalculando os deltas do fixture para that A-C
   genuinamente excedesse o teto enquanto A-B e B-C individualmente não excedessem.
3. `ruff check` acusou uma importação não utilizada (`detect_column_margins`) em `same_row_ordering.py`
   após eu decidir que o módulo recebe `column_margins` já computado pelo chamador, em vez de computá-lo
   internamente - removida.
4. Nenhuma tentativa de correção de produção foi revertida nesta fase (ao contrário da Fase 3M) - o
   mecanismo de três sinais (baseline normalizado, barreira de coluna, barreira de região) funcionou
   corretamente já na primeira implementação completa, validado em modo shadow antes de qualquer
   ativação real.

## Z. Arquivos e Git final

- Modificados (19): `data/manifests/blocker-ledger-2008.yaml`, `data/manifests/exam-structure-2008.yaml`,
  `data/manifests/extraction-audit-2008-computing.csv`, `data/manifests/extraction-audit-2008-computing.json`,
  `data/manifests/extraction-capabilities.json`, `data/manifests/gold-2008-computing.json`,
  `data/manifests/visual-audit-2008-computing.json`,
  `data/questions/2008/all-computing/enade-2008-computing-{d40,d59,q33,q41,q52,q56}.md`,
  `src/enade/extraction/assembler.py`, `src/enade/extraction/exam_profile.py`,
  `src/enade/extraction/fragment_reconstruction.py`, `src/enade/extraction/layout.py`,
  `src/enade/extraction/pipeline.py`, `tests/test_extraction_pipeline_2008.py`.
- Novos (2): `src/enade/extraction/same_row_ordering.py`, `tests/test_same_row_ordering.py`.
- Removidos: nenhum arquivo permanente; scripts de diagnóstico e diretórios temporários criados e
  deletados durante a própria fase, nunca commitados.
- `git status --short` final: exatamente os 21 arquivos listados acima; `data/questions` restrito às
  seis questões corrigidas.
- Branch `feat/enade-2008-cc-b-pilot`, `HEAD=105b57f` (commit do usuário, anterior ao início desta fase
  - nenhum commit feito por este agente), `master=a5dfaab` — ambos intocados por este agente. Nenhum
  commit, push, PR, merge ou tag criado por este agente.

## Recomendação

Sete questões permanecem `failed`. Pela mesma regra de seleção (severidade real, não conveniência), o
próximo alvo é o cluster **`region-merge-content-loss`** (Q02, Q05, Q07, Q24, Q45, Q54, mais o
`d40-region-merge-content-loss` recém-separado) - agora o único cluster de severidade "perda de
conteúdo legítimo" (nível 2, acima de qualquer "ordem incorreta" remanescente) ainda aberto.
Recomenda-se uma **Fase 3O restrita a esse cluster**, usando as três tentativas revertidas da Fase 3M
como contraexemplos obrigatórios (o registro/token-count sozinho regride Q1; a isenção de região grande
sozinha regride D10/Q06/Q57/Q61/Q63/Q69/Q73) - um oráculo de segurança pós-publicação mais rigoroso
(comparando não apenas presença/ausência de palavras, mas a posição relativa de cada conteúdo
recuperado dentro do fluxo do texto) é provavelmente necessário antes de tentar generalizar de novo.
Não iniciar Q8/Q38/Q55. Não processar o bundle `e`.
