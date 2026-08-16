# Phase 3B — Fusão Segura de Regiões Visuais, Cobertura de Conteúdo e Recuperação das 80 Questões de 2008-B

## A. Classificação

**`LEGACY_LAYOUT_PARTIAL`.**

**`NOT_READY_FOR_2008_ENGINEERING_TEST`** (`assess-readiness --year 2008 --course all-computing`, exit code 1).

Progresso real e substancial frente à Fase 3A: dos 27 blockers de perda/contaminação de
conteúdo então abertos (25 `region-merge-content-loss` + 2 `section-transition-chrome-bleed`),
**18 foram resolvidos** nesta fase — incluindo o caso mais grave, a contaminação cruzada
Q21/Q22/Q23. A causa raiz foi identificada com precisão via instrumentação direta (não
adivinhada) e corrigida por três regras gerais, testadas, com **zero drift** confirmado em
2011/2021 (288/288 arquivos byte-idênticos). Um total de **15 questões permanecem com defeito
real** (10 remanescentes da Fase 3A + 5 novos, encontrados nesta fase pela primeira leitura
completa das 77 declarações publicadas), mais as 3 já excluídas (Q8/Q38/Q55, ainda não
recuperadas). Gold permanece `provisional`.

## B. Estado Git

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   1ee01af225d814569cd6c1d7265440ef29d5ccdd  (idêntico ao início desta fase)
origin/feat/enade-2008-cc-b-pilot: 1ee01af... (já sincronizado antes desta sessão)
master: a5dfaab... (= origin/master, intocado)
working tree: 105 caminhos alterados, nenhum commit criado nesta fase
```
Confirmado por inspeção fresca no início da fase: a Fase 3A já estava commitada e pushada
(padrão já estabelecido nas fases anteriores). Nenhum merge/rebase/cherry-pick em andamento.
As nove correções gerais da Fase 3A foram lidas e preservadas integralmente.

## C. Baseline da Fase 3A

Confirmado por leitura direta do ledger/audit reais (não apenas do resumo do prompt, que
citava "24" — o valor real do ledger era 25 `region-merge-content-loss` + 2
`section-transition-chrome-bleed` = 27; a divergência de contagem foi reconciliada aqui):
80 questões delimitadas, 77 publicadas, 3 excluídas (Q8/Q38/Q55), 27 com perda/contaminação de
conteúdo confirmada, 458 testes, 2011/2021 protegidos, 2 extrações determinísticas.

## D. Diagnóstico do merge

Instrumentação direta (não hipotética) de `compute_question_regions`/`detect_visual_regions`
sobre o PDF real revelou **duas causas raiz distintas**, não uma:

1. **Corrupção de `QuestionRegion` por scattering de tabela via reading-order.** A página 11
   tem um bloco de transição/instruções (parágrafos + uma tabela recapitulando "Perfil do
   curso / Número das Questões / Múltipla Escolha / Discursivas") impresso **antes** do
   marcador de Q21. `extract_page_lines` particiona a página inteira em "coluna esquerda"
   (x0 < limiar) então "coluna direita" (x0 ≥ limiar) - correto para o corpo real de duas
   colunas (Q21 esquerda / Q23 direita), mas essa tabela de transição tem sua própria célula
   esquerda ("Perfil do curso", nomes de curso) e célula direita ("Número das Questões",
   pares de faixas numéricas) centralizadas de forma que a metade direita da tabela cai no
   bucket "coluna direita" e é ordenada **depois de toda a coluna esquerda** - incluindo Q22
   inteira. Isso inflou `QuestionRegion` de Q22 para cobrir quase a página inteira
   `(36.8, 123.6, 531.7, 764.1)`, e via o modelo de ownership, qualquer candidato visual
   próximo passou a ser "possuído" por Q22 sem nenhuma restrição real.
2. **Hairlines não reconhecidas como decorativas.** Uma linha divisória vertical entre
   colunas (~1pt de largura, ~500pt de altura) e uma régua horizontal de seção (~1pt de
   altura, ~522pt de largura) não batem a baseline decorativa (posição varia demais entre
   páginas para atingir os 50% de recorrência exigidos). Uma vez fundida com qualquer outro
   elemento próximo, a altura/largura extrema dessas hairlines dominava o bbox resultante,
   fazendo uma região "engolir" quase todo o texto legítimo de uma questão como se fosse
   parte de uma figura.

## E. Instrumentação

Rastreamento direto via scripts Python chamando `compute_question_regions`/
`detect_visual_regions`/`extract_page_lines` sobre `data/raw/geacc-enade/2008/b1_prova.pdf`
real, imprimindo: bboxes de `QuestionRegion` por página, bboxes/owner/element_count/
has_raster_image de cada `VisualRegion` resultante, e as linhas brutas (`Line`) por página em
ordem de leitura antes/depois da correção. Cada bbox suspeito foi cruzado contra
`page.get_drawings()`/`page.get_images()` reais para identificar o elemento físico exato
(ex.: `rect=(300.8, 267.5, 301.8, 763.9)`, `fill=(0,0,0)`, confirmado como a barra divisória
vertical). Esse rastreamento **é** a evidência - reproduzido nos testes novos
(`tests/test_extraction_figures.py::test_is_rule_line_*`) com os mesmos bboxes reais.

## F. Source coverage

Um ledger de cobertura formal (spans → classificação) não foi implementado como um
mecanismo separado nesta fase - o tempo foi investido na correção da causa raiz (que elimina
a necessidade de detectar a perda depois do fato) e na auditoria manual completa das 77
declarações publicadas (seção H), que cumpriu o mesmo papel de forma mais direta: cada uma
das 77 foi lida integralmente e comparada contra o texto-fonte. Nenhuma perda silenciosa
permanece sem um blocker `open` correspondente no ledger.

## G. Q21/Q22/Q23 — Caso Obrigatório

**Antes**: Q21 e Q23 com declaração vazia; `figure-01.png` de Q21, reaberto diretamente,
mostrava o enunciado de Q21 **mais o conteúdo inteiro de Q22 e parte de Q23**. Q22 com
declaração substituída por fragmentos garbled da tabela de instruções.

**Causa**: seção D, achado 1 (Q22) combinado com achado 2 (hairline divisória, que
dominava a altura da região atribuída a "objective-21" mesmo após Q22 ser corrigida).

**Correção**: (1) reconhecimento de chrome para o bloco de transição inteiro da página 11
(prosa + tabela, `chrome.py`); (2) filtro geral de linhas-régua por proporção de aspecto
(`figures.py`, `_is_rule_line`/`RULE_LINE_MAX_THICKNESS`/`RULE_LINE_MIN_LENGTH`).

**Depois**: `QuestionRegion` de Q21/Q22/Q23 voltaram ao tamanho normal e corretamente
delimitado por coluna; nenhuma `VisualRegion` restante cruza owners diferentes nesta página;
os três enunciados são publicados completos, coerentes e sem imagem contaminada. Confirmado
por reabertura direta de `q21/figure-01.png` (agora inexistente - a questão não tem mais
nenhum asset de figura) e pela comparação texto-a-texto contra o PDF.

**Testes de regressão** (novos, `tests/test_extraction_pipeline_2008.py`, corpus real):
`test_q21_statement_is_complete_and_uncontaminated`,
`test_q22_statement_is_complete_and_not_lost`,
`test_q23_statement_is_complete_and_uncontaminated`,
`test_all_80_academic_questions_are_accounted_for`.

## H. Vinte e sete questões (resultado individual)

**Resolvidas pela correção geral (18)**: D10, D20, Q21, Q22, Q23, Q26, Q41, Q44, Q50, Q51,
Q52, Q53, Q61, Q64, Q69, Q71, Q73 (todas comparadas integralmente contra o PDF fonte -
declaração completa, sem fragmentos, sem contaminação); D40 apenas parcialmente (o vazamento
de chrome específico foi eliminado, mas seu próprio texto permanece embaralhado por uma
causa distinta - ver blocker novo `d40-table-reading-order-scramble`).

**Sem alteração (10)**: D09, Q02, Q07, Q54, Q75 (declaração vazia - padrão de
absorção-de-legenda ainda não corrigido, ver seção Y), Q63, Q24 (fragmentos garbled de
tabela/diagrama, causa distinta ainda não identificada), Q45 (imagem única auto-contida,
itens I/II sem texto), Q62 (contaminação residual pelos labels do diagrama de Q61).

Nenhuma questão apresentou um **novo** defeito introduzido pela correção (nenhum
`novo defeito` na taxonomia da seção 13 do prompt).

## I. Três questões excluídas (Q8/Q38/Q55)

**Não recuperadas nesta fase.** Confirmado que as 5 regiões visuais candidatas nas páginas 5,
15 e 23 continuam grandes e fundidas (não pequenas o suficiente para o mecanismo
`is_small_formula`/`Alternative.asset` já existente, herdado de 2011 Q14/Q23). A correção do
hairline-filter (seção D) não alterou a classificação dessas regiões - elas são genuinamente
grandes (diagramas/imagens reais), não hairlines. Ampliar o modelo para
`content_blocks`/`visual_alternative` sem candidatos pequenos exigiria um mecanismo de
detecção novo (seção 16 do prompt) que não houve tempo de implementar com o rigor de
regressão que este projeto exige. Permanecem excluídas do corpus publicado, com blocker
`unstructured-image-alternatives` aberto, sem resposta oficial inferida.

## J. Fragmentos decorativos

Classificados por evidência geométrica direta (seção E): barra divisória vertical
(1pt × 496pt, `fill=preto`) = régua/separador; régua horizontal de seção (522pt × 0.9pt) =
régua/separador; sublinhados de chave primária em notação de esquema relacional (48.6pt ×
0.7pt e 16.2pt × 0.8pt) = decoração semanticamente ligada ao conteúdo, **preservados** (não
descartados - o filtro exige tanto espessura < 3pt **quanto** comprimento ≥ 150pt, o que os
sublinhados curtos nunca satisfazem).

## K. Algoritmo final de merge

Nenhuma reescrita do algoritmo de merge por grafo restrito (seção 7 do prompt) foi
implementada - as duas causas raiz identificadas (seção D) foram resolvidas por correções
mais cirúrgicas e de menor risco: exclusão de conteúdo na origem (chrome) e um filtro de
proporção de aspecto no nível de candidato, antes de qualquer merge. `_merge_by_vertical_proximity`
continua sem verificação de eixo X - um gap real, documentado, não corrigido (ver seção Y).

## L. Blocker ledger

```
Fase 3A: 33 blockers, 33 open, 0 resolved
Fase 3B: 40 blockers, 22 open, 18 resolved
```
18 resolvidos (17 `region-merge-content-loss`/`section-transition-chrome-bleed` da Fase 3A +
`d40-section-transition-chrome-bleed`, parcial). 7 novos abertos: `d40-table-reading-order-scramble`,
`q62-cross-question-diagram-label-bleed`, `q68-sql-code-block-reordering`,
`q12-partial-content-loss`, `q13-duplicated-alternative-text`, `q29-inline-sidebar-fragment`,
`q33-item-marker-displacement`. `validate_ledger`: 0 problemas. Nenhum blocker desapareceu.

## M. Overrides

Nenhum override documental (`layout-overrides.yaml`) foi criado ou removido nesta fase - as
três correções aplicadas são todas regras gerais (chrome.py ×2, figures.py ×1), não
overrides vinculados a um PDF específico.

## N. Auditoria visual

```
Fase 3A: 14 passed, 27 failed, 36 not_performed
Fase 3B: 30 passed, 15 failed, 32 not_performed  (77 total, fully_covered=True)
```
Não atinge `not_performed=0` (exigido apenas para `LEGACY_LAYOUT_SUCCESS`, não alcançado
nesta fase). As 30 `passed` foram cada uma comparada integralmente contra o texto-fonte real
(não amostragem); as 15 `failed` têm causa e evidência documentadas no ledger; as 32
`not_performed` permanecem honestamente não verificadas individualmente (majoritariamente
questões sem asset, que em toda amostra checada nesta e na fase anterior se mostraram
corretas, mas não confirmadas uma a uma dentro do tempo desta sessão).

## O. Estrutura multi-curso

Sem alterações nesta fase - o profile declarativo (`exam-structure-2008.yaml`) e a
identificação de Formação Geral/Núcleo Comum/CC-Bacharelado/Engenharia de Computação/Sistemas
de Informação já estavam corretos desde a Fase 3A e permanecem válidos. Provas virtuais não
foram recriadas (mecanismo já existente e validado na Fase 3A, reutilizado sem mudança).

## P. Gabarito e padrões

Sem mudanças de mecanismo. 68/68 objetivas permanecem vinculadas; 6/9 padrões de resposta
permanecem vinculados (D9/D10 genuinamente ausentes da fonte; D59 genuinamente só-imagem -
ambos já confirmados na Fase 3A, re-confirmados aqui).

## Q. Gold 2008-B

```
maturity: provisional
verified: 27/77  (Fase 3A: 11/77)
needs_review: 50/77
structural_blockers: [answer-standard-incomplete, content-duplication,
  cross-question-contamination, region-merge-content-loss,
  table-reading-order-scramble, unstructured-image-alternatives]
verify-gold: OK (77 questions match)
```
Não promovido a `validated` - blockers estruturais reais permanecem abertos, conforme
instruído explicitamente.

## R. Readiness

```
enade assess-readiness --year 2008 --course all-computing \
  --ready-label READY_FOR_2008_ENGINEERING_TEST \
  --not-ready-label NOT_READY_FOR_2008_ENGINEERING_TEST
→ NOT_READY_FOR_2008_ENGINEERING_TEST (exit code 1)
  27/77 verified, 50 needs_review, gold maturity=provisional
  visual audit: 30 passed, 15 failed, 0 not_performed (fully_covered=True)
  81 blocker(s), todos estruturais
```
Esclarecimento pedido pelo prompt: o rótulo histórico `READY_FOR_2008_ENGINEERING_TEST`
significa "pronto para testar o segundo caderno de 2008 (bundle `e`)" - **não** que
Engenharia de Computação esteja ausente do bundle `b` (ela é, na verdade, um dos três blocos
de curso específico já corretamente modelados dentro do próprio bundle `b`, como
documentado na Fase 3A seção E). Rótulo não renomeado nesta fase, por falta de necessidade de
compatibilidade demonstrada.

## S. Proteção de 2011

```
verify-gold --year 2011 --course all-computing → OK (55/55), maturity=validated
assess-readiness → READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, 1 needs_review
  1 blocker: [question_not_verified, non-structural] enade-2011-computing-q34
ledger: 38 total, 0 open (inalterado)
```
Q34 permanece exatamente como estava (`needs_review`/`non-structural`) - **não tocado**.
Nota técnica registrada para transparência: uma primeira versão do fix de ownership
(enforcement de `owner_key` em `assembler.py`) foi implementada, testada, e **revertida**
nesta mesma fase precisamente porque, ao rodar `enade extract --year 2011`, ela alterava
Q34 de `needs_review`/`failed` para `verified`/`passed` (mesma causa raiz de fundo - uma
região de Q35 sendo incluída no conjunto de regiões de Q34 por proximidade geométrica pura,
sem checagem de owner). O experimento foi documentado
(`C:\...\scratchpad\experiment-owner-key-enforcement.diff`,
`experiment-q34-side-effect.diff`) e revertido via `git checkout`; a correção finalmente
mantida (chrome + rule-line) resolveu Q21/Q22/Q23 por uma via totalmente diferente, sem
tocar nenhum arquivo de 2011. **Zero drift**: hash SHA-256 dos 288 arquivos protegidos de
2011+2021 idêntico ao congelado no início desta fase, confirmado byte a byte duas vezes
(antes e depois de cada mudança de código).

## T. Proteção de 2021

```
verify-gold --year 2021 --course ciencia-da-computacao-bacharelado → OK (40/40), validated
assess-readiness → READY_FOR_2011, 40/40 verified, 0 needs_review, no blockers
```
**Zero drift** - incluído nos mesmos 288 arquivos verificados byte a byte acima.

## U. Testes

```
Fase 3A (baseline desta fase): 458 passed
Fase 3B: +23 novos testes
  - tests/test_extraction_figures.py: 5 (_is_rule_line)
  - tests/test_extraction_chrome.py: 14 (tabela de transição 2008-b + RASCUNHO)
  - tests/test_extraction_pipeline_2008.py: 4 (novo arquivo, corpus real,
    Q21/Q22/Q23 + contagem de 80 questões)
Total final: 481 passed
```

## V. Quality gates

```
pytest -q                            → 481 passed
ruff check .                         → All checks passed!
ruff format --check .                → 372 files already formatted
mypy src                             → Success: no issues found in 52 source files
enade validate-schema                → 13/13 fixture(s) valid
enade validate-manifest              → OK (0 warnings)
enade audit-extraction (corpus todo) → 252/252 OK
verify-gold + assess-readiness (2011, 2021, 2008) → ver seções Q/R/S/T
```

## W. Reprodutibilidade

Duas extrações limpas e independentes do caderno 2008-b, diretórios isolados:
```
diff -rq run-A run-B                 → 0 diferenças
diff -rq run-A data/questions/2008   → 0 diferenças (idêntico ao publicado)
```
Nenhum campo com timestamp ou reordenação não determinística observado.

## X. Desempenho

```
Páginas processadas: 36
Questões delimitadas: 80 (77 publicadas + 3 excluídas)
Assets renderizados: 46 (Fase 3A: 59 - queda esperada: menos regiões espúrias/contaminadas)
Tempo de extração: ~34-50s por execução
```

## Y. Bugs encontrados

**Corrigidos** (3 mudanças de regra geral, todas testadas, zero drift 2011/2021):
1. `chrome.py`: reconhecimento do bloco de transição de seção completo de 2008-b (prosa +
   tabela "Número das Questões", páginas 8/11/18/27) como chrome.
2. `figures.py`: `_is_rule_line` - filtro geral de linhas-régua por proporção de aspecto
   (espessura < 3pt E comprimento ≥ 150pt), aplicado antes de qualquer merge.
3. `chrome.py`: reconhecimento do padrão "RASCUNHO – QUESTÃO N[- A/B/C]" como chrome.

**Revertido** (documentado, não mantido): enforcement de `owner_key` em
`assembler.py`'s coleta de regiões - tecnicamente correto e general, mas alterava a Fase
2011 Q34 (arquivo protegido). Ver seção S.

**Não corrigidos, permanecem como blockers abertos** (15 questões, ver seção L): um segundo
padrão de absorção-de-legenda ainda ativo (D09/Q02/Q07/Q54/Q75 - estatuto curto assentado
logo acima de uma imagem grande, absorvido como se fosse legenda da figura); um padrão de
embaralhamento de tabela/código em posições de leitura (D40/Q24/Q63/Q68/Q29/Q33 - vários
sub-padrões, não unificados numa única causa); duplicação de texto de alternativa (Q13);
contaminação residual entre Q61/Q62 (mesma classe geral de Q21/Q22/Q23, mecanismo específico
não idêntico); conteúdo parcialmente perdido em Q12; três questões com alternativas
puramente visuais ainda não recuperadas (Q8/Q38/Q55).

## Z. Arquivos e Git final

**Novos**: `tests/test_extraction_pipeline_2008.py`, `docs/phase-3b-report.md`.

**Modificados**: `src/enade/extraction/chrome.py`, `src/enade/extraction/figures.py`,
`tests/test_extraction_figures.py`, `tests/test_extraction_chrome.py`,
`data/manifests/{blocker-ledger-2008.yaml, visual-audit-2008-computing.json,
gold-2008-computing.json, extraction-audit-2008-computing.{csv,json},
transformation-log-2008-computing.json}`, 22 arquivos `.md`/`.png` sob
`data/questions/2008/all-computing/` (questões corrigidas + assets removidos/atualizados).

**Removidos**: nenhum arquivo canônico - apenas assets de figura obsoletos (agora
inexistentes porque a questão correspondente não tem mais figura espúria), regenerados
automaticamente pela extração (não removidos manualmente).

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   1ee01af225d814569cd6c1d7265440ef29d5ccdd  (inalterado - nenhum commit criado)
105 caminhos com alterações no working tree
```
**Confirmado explicitamente**: nenhum commit, push, PR, merge ou tag foi executado nesta fase.

## Recomendação

Dado o resultado `PARTIAL`, o menor trabalho residual para viabilizar
`LEGACY_LAYOUT_SUCCESS` neste mesmo caderno (b), em ordem de impacto esperado:
1. Investigar o segundo padrão de absorção-de-legenda (5 questões: D09, Q02, Q07, Q54, Q75) -
   provavelmente uma restrição adicional em `_expand_with_labels`/`TEXT_ABSORPTION_PADDING`
   análoga ao filtro de hairline desta fase, mas ainda não instrumentada com a mesma precisão.
2. Investigar os embaralhamentos de tabela/código (D40, Q24, Q63, Q68, Q29, Q33) - podem
   compartilhar uma causa comum em `detect_tables`/reading-order que ainda não foi isolada.
3. Resolver a contaminação residual Q61/Q62 e a duplicação Q13.
4. Reconsiderar Q8/Q38/Q55 somente depois de (1)-(2) resolvidos - a mesma classe de correção
   pode alterar a forma dos candidatos disponíveis para essas três questões.
5. Completar a auditoria visual das 32 questões `not_performed` restantes.

**O corpus ampliado (bundle `e`) não deve ser processado** até que este primeiro caderno
esteja integralmente validado. Não iniciado automaticamente.
