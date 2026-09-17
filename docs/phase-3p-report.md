# Fase 3P — Ownership por Alternativa e Eliminação da Contaminação de Q07

## A. Classificação

- **Alternative ownership (Q07):** `ALTERNATIVE_OWNERSHIP_STABILIZED`. Q07 está integralmente correta (cinco alternativas presentes e corretas, contaminação eliminada, zero source ID duplicado/ausente/estrangeiro), as regressões obrigatórias de alternativas (Q13/Q28/Q29/Q52/Q71/Q75) permanecem corretas, 2011/2021 permanecem byte-idênticos, e a reprodutibilidade foi confirmada.
- **Residual layout (corpus 2008-b como um todo):** `RESIDUAL_LAYOUT_NOT_STABILIZED` — `published=77, passed=74, failed=3 (Q24, Q45, D40), not_performed=0`. Não é 77/77; três questões permanecem com blockers próprios, documentados, fora do escopo desta fase.
- **Generalização:** `GENERALIZATION_ARCHITECTURE_ESTABLISHED` para o mecanismo específico desta fase (ownership por alternativa, evidência geométrica tripla: margem de continuação, direção de movimento, território de região visual) — confirmado por validação cruzada em 2008-b/2011/2021 e por três regressões reais encontradas e corrigidas durante a própria validação em shadow mode desta fase.
- **Readiness:** `NOT_READY_FOR_2008_ENGINEERING_TEST` — 71/77 verified, gold maturity=provisional, blockers estruturais remanescentes (Q8/Q38/Q55 excluídas, Q24/Q45/D40 com blockers próprios, D09/D10/D59 com padrões de resposta ausentes, Q23 com vazamento cosmético).

Nenhuma dessas classificações usa o rótulo de sucesso global; `RESIDUAL_LAYOUT_STABILIZED` exigiria `passed=77`, o que não é o caso.

## B. Estado Git

Branch `feat/enade-2008-cc-b-pilot` durante toda a fase. HEAD inicial: `2cb80d1` (o trabalho das Fases 3N e 3O, uncommitted ao final da sessão anterior, foi commitado em um único commit por processo externo a esta sessão, entre as duas fases — confirmado via `git log`, não uma ação desta sessão). `master`/`origin/master`: `a5dfaab`, inalterados do início ao fim. Nenhum commit, push, PR, merge ou tag foi criado nesta fase. Working tree ao final: 9 arquivos modificados + 2 novos (ver Seção Z), nenhum scratch script remanescente.

## C. Baseline da Fase 3O (confirmada no estado real, não presumida)

```text
tests = 701 (confirmado por execução real)
published = 77
visual_passed = 73
visual_failed = 4 (Q07, Q24, Q45, D40)
visual_not_performed = 0
protected_question_files = 270
protected_derived_manifests = 18
protected_total = 288
2011_drift = 0
2021_drift = 0
region_membership_overrides = 26 (todos com evidence apontando para docs/phase-3o-report.md)
gold 2008-b: 70/77 verified, maturity=provisional
blockers abertos: 12, incluindo q07-region-merge-content-loss e
  q07-alternative-e-citation-contamination-risk
```

Todos os valores acima foram lidos diretamente dos manifests reais (`visual-audit-2008-computing.json`, `blocker-ledger-2008.yaml`, `gold-2008-computing.json`, `protected-files-2011-2021.json`) e de uma execução real de `pytest`/`enade verify-gold` no início desta fase — nenhum foi copiado do resumo da fase anterior sem confirmação.

## D. Diagnóstico forense de Q07

Página 4 do caderno, layout de duas colunas visuais (gráfico à esquerda, texto à direita) que `layout.detect_column_margins` **não** reconhece como duas colunas genuínas — a "coluna esquerda" tem apenas uma linha de texto real (a citação), abaixo do limiar de evidência mínima da função — de modo que `extract_page_lines` recorre a uma ordenação plana `(y0, x0)` para a página inteira.

| campo | marcador E | linha contaminante |
|---|---|---|
| `raw_text` | "E\t80%." | "Disponível em http://www.ipea.gov.br" |
| `page` | 4 | 4 |
| `bbox` | (272.2, 745.2, 309.0, 755.4) | (164.8, 753.2, 270.7, 759.2) |
| `font_size` | 9.96 | 6.0 |
| `owner` | objective-7 | objective-7 |
| `reading_order_index` (lista plana) | antes | depois (y0 maior) |
| `alternative_group` (accepted) | E | — (nunca um marcador) |
| `current_alternative_owner` (antes da Fase 3P) | E | E (contaminação) |
| `expected_alternative_owner` | E | statement |
| `asset_relation` | — | dentro do bbox de `figure-01`'s own região (36.8–270.6) |

**Sequência de reprodução:**
1. PDF visual: gráfico + citação (coluna esquerda), enunciado + pergunta + alternativas (coluna direita).
2. Raw spans/page lines: `extract_page_lines` produz uma lista plana (página não detectada como 2 colunas).
3. Question slice: o span de Q07 inclui ambas as linhas (mesmo owner).
4. Accepted markers: `alternative_groups.find_alternative_group` aceita A-E corretamente (a citação nunca casa o formato de marcador).
5. Alternative groups: `alt_bounds` calculado por posição de lista — E vai de seu próprio índice até o fim de `text_only_lines`.
6. Boundaries calculados: nenhuma verificação de proximidade X — a citação, por estar depois de E na lista, cai dentro do intervalo de E.
7. Assignment atual (antes desta fase): citação concatenada ao texto de E ("80%. Disponível em...").
8. Markdown publicado (antes): "E. 80%. Disponível em http://www.ipea.gov.br".
9. Assignment correto (depois desta fase): citação reflowed para o statement.

**Primeira divergência:** ocorre exatamente no passo 6 (cálculo do boundary) — não no marker (corretamente aceito), não na ordem de leitura de `extract_page_lines` (correta para o que ela se propõe a fazer, uma ordenação geométrica page-wide, nunca column-aware o suficiente para este caso raro), não em transbordamento de coluna reconhecido (nunca reconhecido, pois a página não é detectada como 2 colunas), não em asset (a região do gráfico está correta), não em fallback textual, não na renderização Markdown. A causa raiz é a ausência de qualquer verificação de pertencimento (ownership) na construção do texto de cada alternativa a partir de `alt_bounds`.

## E. Definição de contaminação usada nesta fase

Uma linha é contaminação quando (a) falha o teste de margem de continuação já estabelecido (`_ALTERNATIVE_CONTINUATION_X_TOLERANCE`, 60pt) **e** (b) move-se para trás (x0 menor que o x0 do próprio marcador) — nunca apenas (a) isoladamente, que produziria falsos positivos reais (ver Seção L). Exemplos de rejeição (não-contaminação, mesmo falhando o teste de margem): 2008-b Q64's própria continuação "gerentes" (mesma linha física, fragmento de fonte separado, posicionado à *direita* do marcador); 2011 Q23's "em que"/"." (mesmo padrão, após uma imagem de símbolo inline). Nenhuma quebra de linha simples é contada como contaminação; apenas o caso duplo confirmado (falha de margem + movimento para trás + evidência de região) é.

## F. `AlternativeContentAssignment`

Novo módulo `src/enade/extraction/alternative_content_assignment.py`. Estrutura `AlternativeContentAssignment` (frozen dataclass) com os campos: `source_id` (page+bbox, estável entre execuções), `question_owner`, `alternative_owner` (`statement` | `alternative_A`..`E` | `ambiguous` | outros valores do enum declarados para extensibilidade futura, nunca produzidos ainda), `content_type` (`marker`|`continuation`), `marker_source_id`, `group_id`, `boundary_start`/`boundary_end`, `reading_order_index`, `assignment_method`, `confidence`, `status` (`assigned`|`reflowed`|`ambiguous`). Função `assign_alternative_content` produz, para cada linha após o primeiro marcador aceito, exatamente um registro. Integra com `ContentAssignment` (Fase 3J) por complementaridade, não substituição — nenhuma mudança em `content_assignment.py`; ambos os módulos descrevem facetas diferentes (posse geral de conteúdo vs. posse especificamente entre statement/alternativas).

## G. Markers

Nenhuma reimplementação do reconhecimento de marcadores — `alternative_groups.find_alternative_group` (Fase 3I) já resolve isso com evidência estrutural (margem + ordem de leitura), incluindo a rejeição de rótulos internos de diagrama (Cluster C, `figures.py`), variáveis matemáticas e itens romanos (nunca casam `_ALTERNATIVE_LINE_RE`, que exige exatamente uma letra A-E). Esta fase apenas **confia** em um `AlternativeGroup.is_usable` já resolvido; testado explicitamente (`test_diagram_internal_label_never_becomes_a_marker`, `test_roman_numeral_item_marker_is_never_treated_as_an_alternative`, `test_table_cell_letter_and_math_variable_never_match_marker_shape`, `test_code_identifier_never_matches_marker_shape`).

## H. Sequência A–E

Validação do grafo/sequência é responsabilidade de `alternative_groups.find_alternative_group`, já testada (Fase 3I): rejeita duas letras A sem explicação (resolve por margem+ordem, nunca duas aceitas simultaneamente), nunca retrocede silenciosamente (construção estritamente decrescente do limite superior, letra a letra, de E para A), marcador de outra questão é uma barreira estrutural (span já fatiado por questão antes de chegar aqui), ausência de marcador produz `status="incomplete"` (nunca deslocamento automático), e não há noção de "ciclo" possível dado que a busca é sempre unidirecional (E para A, limite superior estritamente decrescente).

## I. Boundaries em ordem de leitura

`alt_bounds` continua exatamente como antes (posição de lista dentro de `text_only_lines`, que por sua vez usa `extract_page_lines`'s own ordem geométrica estável mais a reordenação de zona/mesma-linha já ativas). Esta fase não substitui esse cálculo — adiciona uma segunda camada de verificação, por linha, dentro de cada intervalo já calculado (ver Seção E/F). `E` continua se estendendo até o fim real de `text_only_lines` (fim da questão).

## J. Transbordamento entre colunas

Q13's própria alternativa E (transbordamento legítimo para a coluna seguinte, documentado desde fases anteriores) foi revalidada: `test_q13_statement_no_longer_duplicates_alternative_e` passa sem modificação. O mecanismo desta fase nunca reclassifica uma continuação legítima como contaminação, porque a condição dupla (falha de margem + movimento para trás) nunca é satisfeita por um transbordamento de coluna genuíno (que sempre se move para frente, na direção de leitura, nunca para trás).

## K. Territórios

Não implementado como uma estrutura de segmentos por página/coluna explícita (Seção 13 do prompt) — não havia um segundo caso real, além de Q07, que a exigisse (nenhuma alternativa no corpus real atravessa página ou múltiplos blocos de forma que o mecanismo atual não já cubra). O "território" de cada alternativa, nesta fase, permanece implícito no intervalo `alt_bounds` já existente; apenas o *conteúdo* dentro desse intervalo passou a ser verificado linha a linha. Construir a estrutura completa sem um segundo caso real violaria o mesmo princípio de generalização já citado na Fase 3O (docs/generalization-contract.md, seção 1.1).

## L. Detector de contaminação e as três regressões reais encontradas

`detect_ambiguous_published_assignments` é o gate automático: reporta toda linha retida por falta de evidência estrutural suficiente, nunca resolve silenciosamente. Durante a validação desta fase, duas versões mais simples do mecanismo foram tentadas e rejeitadas por regeneração completa do corpus (2008-b + 2011 + todos os 3 cursos de 2021):

1. **Somente "falha de margem" → reflow se região explica:** corrigia Q07, mas quebrava 2008-b Q64 (a palavra "gerentes", fragmento de mesma linha física da alternativa D, movida para o statement, perdendo a palavra da alternativa), 2011 Q23 (fragmentos "em que"/"." de uma alternativa após uma imagem de símbolo inline, movidos incorretamente) e 2021 SI Q33 (uma questão anulada, com conteúdo "NULO" repetido, teve praticamente todo o texto de suas alternativas A-E esvaziado).
2. **Adição da condição "move-se para trás" (x0 do candidato < x0 do próprio marcador):** eliminou as três regressões acima simultaneamente, mantendo a correção de Q07 - confirmado por regeneração completa e diff byte a byte, zero mismatches restantes.

As três regressões descobertas tornaram-se testes de regressão permanentes (`test_same_row_far_right_continuation_is_never_reflowed_even_with_a_matching_region`, mais os testes reais de Q64/Q23/SI-Q33 implícitos na exigência de "zero drift" do shadow scan, Seção X).

## M. Q07 depois da correção

- **Alternativas:** A="20%.", B="40%.", C="50%.", D="60%.", E="80%." — todas corretas, nenhuma contaminação.
- **Statement:** ganha um novo parágrafo final, "Disponível em http://www.ipea.gov.br", imediatamente após a cláusula de enquadramento restaurada na Fase 3O.
- **Owners:** a citação passa de `alternative_E` (errado) para `statement` (correto), única mudança de posse nesta fase.
- **Visual audit:** reinspecionado diretamente contra `figure-01.png` (o gráfico da Curva de Lorenz) - a citação imprime exatamente como legenda do gráfico na página real, confirmando visualmente a correção. Promovido para `passed`; `extraction_status` promovido para `verified`.

## N. Q24 (contraexemplo, intocado)

`test_q24_framing_paragraph_is_now_complete` (Fase 3O) revalidado sem modificação. Os marcadores romanos "I"/"II" continuam ausentes (blocker `q24-item-i-ii-markers-missing`, Fase 3O, ainda aberto) - confirmado que o novo mecanismo de ownership por alternativa não interage com eles (não são marcadores A-E, nunca entram em `assign_alternative_content` como tal). Novo teste `test_roman_numeral_item_marker_is_never_treated_as_an_alternative` (sintético) trava esta garantia estrutural de forma permanente. Q24 permanece `failed`.

## O. Q45 (contraexemplo, intocado)

`test_q45_items_i_and_ii_are_now_complete` (Fase 3O) revalidado sem modificação. O caractere ausente em "o gráfico de e as retas" e a nuance de mesma linha ("então" antes de "para ci...") permanecem exatamente como estavam - nenhuma tentativa de correção nesta fase (fora do escopo, Seção 22). `same_row_ordering.py` não foi tocado. Q45 permanece `failed`.

## P. D40 (contraexemplo, intocado)

`test_d40_own_two_region_merge_residuals_are_now_resolved` (Fase 3O) revalidado sem modificação. O vazamento cosmético "F" (documentado desde a Fase 3G) permanece - nenhuma alteração de region membership ou same-row ordering nesta fase. D40 permanece `failed`.

## Q. Overrides da Fase 3O

Os 26 overrides `protect_from_region_membership` em `data/manifests/layout-overrides.yaml` permanecem **byte-idênticos** - confirmado via `git status --short` (o arquivo não aparece como modificado nesta fase) e via a contagem programática (`57` overrides totais, `26` com evidência apontando para `docs/phase-3o-report.md`, ambos inalterados). Todos os PNGs das 7 questões afetadas pela Fase 3O permanecem byte-idênticos (nenhum asset foi tocado por esta fase, que só modifica texto de alternativas/statement).

## R. Regressões de alternativas (obrigatórias)

| questão | mecanismo revalidado | resultado |
|---|---|---|
| Q13 | transbordamento de alternativa E para coluna seguinte | `test_q13_statement_no_longer_duplicates_alternative_e`, `test_q13_no_longer_receives_q12_own_diagram` — passam |
| Q28 | alternativas numéricas curtas, nenhuma região próxima | `test_q28_alternatives_are_not_regressed_by_the_new_alternative_ownership_mechanism` (novo) — passa |
| Q29 | rótulos internos de diagrama não vazam para o statement | `test_q29_no_longer_has_sidebar_fragment_inserted_mid_sentence` — passa |
| Q52 | falso candidato a marcador resolvido por margem (caso histórico que motivou a Fase 3I) | `test_q52_alternatives_are_not_regressed_by_the_new_alternative_ownership_mechanism` (novo) — passa |
| Q71 | boundary B/C corrigido por margem (Fase 3I) | `test_q71_alternative_b_c_boundary_is_now_correct`, `test_q71_statement_is_now_complete` — passam |
| Q75 | statement completo, sem vazamento de diagrama para alternativa D | `test_q75_statement_is_now_complete`, `test_q75_alternative_d_no_longer_bleeds_diagram_labels` — passam |

## S. Regressões gerais

`test_extraction_pipeline_2008.py` inteiro (41 testes após esta fase) executado - todos passam, cobrindo a lista completa da Seção 26 do prompt (Q01, Q06, Q12, Q25, Q33, Q41, Q50, Q54, Q56, Q57, Q61, Q62, Q63, Q68, Q69, Q73, D09, D10, D20, D39, D59, D60) através dos testes já existentes de fases anteriores, nenhum modificado além do necessário (apenas o teste de Q07 - a única questão que genuinamente mudou). Nenhuma correção anterior foi reaberta.

## T. `ContentAssignment`

Não instanciado como um ledger em produção nesta fase (confirmado: `ContentAssignment` nunca é construído fora de `tests/test_content_assignment.py` em todo o código-fonte - é um schema/gate de auditoria, não um artefato gerado automaticamente pelo pipeline). Nenhuma mudança a este módulo; `AlternativeContentAssignment` é complementar, cobrindo exatamente a faceta (statement vs. alternativa) que `ContentAssignment` declara mas nunca preenche automaticamente.

## U. `AlternativeContentAssignment`

Gates implementados e testados: `detect_duplicate_alternative_assignments` (nunca ocorre por construção - cada linha visitada exatamente uma vez), `detect_missing_alternative_assignments` (nunca ocorre pelo mesmo motivo), `detect_foreign_alternative_assignments` (nunca produz um owner estrangeiro internamente; existe para um chamador que agregue múltiplas questões), `detect_ambiguous_published_assignments` (reporta toda linha retida sem evidência suficiente - o gate realmente ativo em uso). Para Q07 real: 0 duplicados, 0 ausentes, 0 estrangeiros, 0 ambíguos (a citação foi resolvida com confiança alta, não retida como ambígua).

## V. Source coverage

Nenhuma linha do span de Q07 foi perdida: a citação, antes concatenada ao texto de E, agora aparece integralmente no statement - confirmado por contagem de palavras (o teste real `test_q07_alternative_e_is_no_longer_contaminated_by_the_chart_citation` verifica o texto final exato de cada alternativa e do statement, não apenas ausência/presença de substring).

## W. Auditoria visual e gold

```text
published = 77
visual_passed = 74 (era 73; +Q07)
visual_failed = 3 (Q24, Q45, D40)
visual_not_performed = 0
gold: 71/77 verified (era 70/77; +Q07), maturity=provisional
```

Exatamente o resultado que o próprio prompt desta fase previu como consequência possível ("Se apenas Q07 for integralmente resolvida: passed = 74, failed = 3, not_performed = 0") - confirmado, não forçado. Nenhuma promoção em massa: apenas Q07 teve seu status reavaliado, com base em reinspeção visual direta contra `figure-01.png` (Seção M).

## X. Proteção de 2011/2021

- `data/manifests/protected-files-2011-2021.json`: 288 arquivos (270 questões + 18 manifests derivados) - confirmado inalterado (`test_protected_corpus.py`, 4 testes, passam).
- 2011 (caderno unificado, 55 questões): regeneração completa com os mesmos parâmetros do `enade.cli extract` real (parser de gabarito, auditoria visual, overrides) → 0 mismatches, 0 arquivos faltando. `enade verify-gold --year 2011 --course all-computing`: OK, 54/55 verified (inalterado). `enade assess-readiness`: `READY_FOR_LEGACY_LAYOUT_TEST` (inalterado).
- 2021, três cursos rastreados (CC-bacharelado 40, CC-licenciatura 35, Sistemas de Informação 35 = 110 questões): mesma regeneração completa → 0 mismatches, 0 arquivos faltando. `enade verify-gold --year 2021 --course ciencia-da-computacao-bacharelado`: OK, 40/40 verified (inalterado). `enade assess-readiness`: `READY_FOR_2011` (rótulo de convenção pré-existente do projeto, inalterado).
- Gold protegido (2011/2021): **não** atualizado (nenhuma mudança a atualizar - ambos já refletem o estado real, inalterado).
- `2011_drift = 0`, `2021_drift = 0`, `protected_paths_missing = 0`, `protected_paths_unexpected = 0`.

## Y. Testes, gates e reprodutibilidade

- Testes antes desta fase: 701. Novos: 35 (`test_alternative_content_assignment.py`) + 3 líquidos em `test_extraction_pipeline_2008.py` (1 reescrito, 2 novos: Q07 completo, Q28, Q52) = 38. Total: **739**, todos passando (confirmado por execução completa da suíte, duas vezes, ao final da fase).
- `ruff check .`: limpo. `ruff format --check .`: limpo (408 arquivos já formatados). `mypy src/`: limpo (60 arquivos-fonte). `enade validate-schema`: 13/13. `enade validate-manifest`: OK, 0 avisos. `enade audit-extraction` (2008/2011/2021): OK em todos.
- Reprodutibilidade: uma regeneração completa e independente de 2008-b + 2011 + todos os 3 cursos de 2021 (script temporário, nunca escrevendo no corpus publicado), comparada byte a byte contra o corpus publicado **após** a publicação de Q07, produziu **zero mismatches, zero arquivos faltando** em toda a extensão (77+55+110 = 242 questões). Como essa mesma comparação já havia sido executada, com resultado idêntico, imediatamente antes da publicação (contra o corpus pré-Q07, mostrando a diferença esperada em exatamente 1 arquivo), a cadeia `execução A = publicado = execução B` está estabelecida transitivamente sem necessidade de uma terceira regeneração completa redundante.

## Z. Arquivos, bugs e Git final

**Novos:**
- `src/enade/extraction/alternative_content_assignment.py`
- `tests/test_alternative_content_assignment.py`
- `docs/phase-3p-report.md`

**Modificados:**
- `src/enade/extraction/assembler.py` (integração do novo mecanismo; novo parâmetro `force_included_lines` em `_build_statement_segments`; novo campo `alternative_content_assignments` em `ExtractedQuestion`)
- `tests/test_extraction_pipeline_2008.py` (1 teste reescrito, 3 novos)
- `data/questions/2008/all-computing/enade-2008-computing-q07.md`
- `data/manifests/blocker-ledger-2008.yaml`, `visual-audit-2008-computing.json`, `extraction-audit-2008-computing.{csv,json}`, `gold-2008-computing.json`, `extraction-capabilities.json`

**Removidos:** nenhum arquivo de produção. Scripts de diagnóstico temporários (`diag_q07_check.py`, `diag_q64_region.py`, `diag_full_corpus_diff.py`), todos apagados antes do fim da fase.

**Tentativas revertidas:** o mecanismo "somente falha de margem" (sem a condição "move-se para trás") - implementado, testado, encontrado causar 3 regressões reais por regeneração completa, corrigido no mesmo commit de trabalho (nunca publicado em estado quebrado). Documentado na Seção L e no próprio docstring do módulo (`alternative_content_assignment.py`) para que uma fase futura não repita a experiência.

**Git:** nenhum commit, push, PR, merge ou tag nesta fase. `master`/`origin/master` inalterados (`a5dfaab`). Branch de trabalho: `feat/enade-2008-cc-b-pilot`.

## Recomendação

Q07 está integralmente resolvida. Recomenda-se uma **Fase 3Q** dedicada a Q24 (marcadores "I"/"II" ausentes - mecanismo ainda não identificado, candidato mais promissor por ser uma perda de conteúdo documental genuína) e, secundariamente, Q45 (caractere ausente + nuance de ordem, dois defeitos menores e de mecanismos distintos). D40 (vazamento cosmético "F") deve ficar para uma fase cosmética posterior, de menor prioridade dado que não perde conteúdo nem contamina alternativas. Não iniciar Q8/Q38/Q55 (alternativas puramente visuais, exigem mecanismo próprio) nem processar o bundle `e` ou qualquer prova inédita nesta continuação.
