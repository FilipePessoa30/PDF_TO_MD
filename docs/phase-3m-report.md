# Fase 3M — Reconciliação dos Nove Blockers Residuais e Correção do Maior Cluster Estrutural

## A. Classificação

- **Cluster residual selecionado (`same-question-diagram-label-bleed`, Q75): `RESIDUAL_CLUSTER_RESOLVED`** — o único blocker do cluster (`q75-alternative-d-diagram-label-bleed`) está resolvido, Q75 passa integralmente na auditoria visual, nenhum conteúdo foi perdido ou duplicado, nenhuma regressão foi introduzida em nenhuma das 76 outras questões publicadas de 2008-b, 2011/2021 permanecem byte-idênticos, e a reprodutibilidade foi confirmada (duas execuções limpas idênticas entre si e ao corpus publicado).
- **Layout residual global: `RESIDUAL_LAYOUT_NOT_STABILIZED`** — 69/77 aprovadas, 8/77 reprovadas (queda real de 9 para 8, auditada questão por questão). Não é `RESIDUAL_LAYOUT_STABILIZED` porque `published != passed` (69 ≠ 77).
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido. Uma nova capacidade declarativa (`alternative_section_region_exemption`) registrada, G3 (mecanismo incondicional, puramente estrutural, sem dependência de profile).
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase. Nunca `GENERALIZATION_SUCCESS`.
- `NOT_READY_FOR_2008_ENGINEERING_TEST` (readiness) — confirmado (66/77 verified, 11 needs_review, gold maturity=provisional, 35 blockers).
- Nenhum commit, push, PR, merge ou tag foi criado por este agente nesta fase. `master` não foi tocado.

## B. Estado Git

- Branch: `feat/enade-2008-cc-b-pilot` (confirmada no início e no fim da fase).
- **Divergência do `HEAD` esperado, explicada**: o PROMPT desta fase esperava `HEAD = 89e4a47` (o valor correto ao final da Fase 3L). No início desta sessão, o `git status` já mostrava todo o trabalho da Fase 3L **staged** ("Changes to be committed"), não commitado. Durante esta fase, o usuário (`FilipePessoa30`, confirmado via `git log`, não este agente - nenhum `git commit` foi executado por mim) commitou esse trabalho como `d70559f` ("Refactor reading order handling and eligibility assessment for visual regions"), cujo `git show --stat` confirma exatamente o conjunto de 14 arquivos da Fase 3L (nenhum arquivo desta Fase 3M incluído). `HEAD` real ao final desta fase: `d70559f`. Todo o trabalho da Fase 3M está **não commitado** sobre esse commit.
- `master` = `origin/master` = `a5dfaab` — intocado.
- Nenhum merge, rebase ou cherry-pick em andamento.
- Working tree ao final desta fase: 11 arquivos modificados + 2 arquivos novos (ver Seção Z) — todos justificados nesta fase; nenhum arquivo inesperado; nenhum arquivo de scratch remanescente.
- `data/questions` (2008/2011/2021): diff restrito a exatamente 1 arquivo (`enade-2008-computing-q75.md`) — confirmado via `git status --short data/questions`.

## C. Baseline da Fase 3L

Confirmado no início da fase: `pytest` = 654/654 (ao final da própria Fase 3L; a suíte cresceu para 655 assim que a Fase 3L foi commitada, incluindo um teste que havia sido escrito mas não contado na mensagem de fechamento anterior); 68/77 aprovadas na auditoria visual, 9/77 reprovadas, `not_performed=0`; readiness `NOT_READY_FOR_2008_ENGINEERING_TEST`; reprodutibilidade confirmada; zero diff em `data/questions`; nenhum commit/push feito por este agente. Todos os valores batem com o estado declarado no início do PROMPT desta fase, exceto o próprio `HEAD` (ver Seção B).

## D. Reconciliação 270/288

Relatórios de Fases 3A–3L citam ambos os números "270" e "288" para o conjunto de arquivos protegidos de 2011/2021 - **não há discrepância real, apenas dois escopos diferentes do mesmo conjunto**, confirmado por leitura direta de `docs/phase-3c-report.md` linha 115 e `docs/phase-3e-report.md` linha 342: "270 arquivos protegidos (270 sob `data/questions/2011|2021`) + 18 manifestos relacionados = 288 arquivos protegidos totais". Os 18 manifestos (recuperados de um snapshot da própria Fase 3F, ainda presente no scratchpad desta sessão) são: `blocker-ledger-2011.yaml`, `exam-structure-2011.yaml`, `extraction-audit-2011-computing.{csv,json}`, `extraction-audit-2021-{b,l,s}.{csv,json}` (6 arquivos), `gold-2011-computing.json`, `gold-2021-b.json`, `transformation-log-2011-computing.json`, `transformation-log-2021-{b,l,s}.json` (3 arquivos), `visual-audit-2011-computing.json`, `visual-audit-2021-b.json`. Nota: apenas o curso "b" (cc-bacharelado) de 2021 tem gold/visual-audit próprios entre os 18 - licenciatura e sistemas-de-informação têm apenas extraction-audit/transformation-log rastreados nesse conjunto histórico.

**Verificação**: `sha256sum -c` contra o snapshot completo de 288 arquivos (Fase 3F) — **288/288 OK**, nenhuma falha. A baseline nunca encolheu; a diferença sempre foi de escopo (270 = apenas arquivos de questão; 288 = arquivos de questão + manifestos derivados), documentada de forma consistente desde a Fase 3C.

**Artefato produzido**: `data/manifests/protected-files-2011-2021.json` (novo, 288 entradas, schema `{path, corpus, category, sha256, protected_reason}`), gerado e verificado contra o snapshot histórico, com `assert real_sha == sha` para cada uma das 288 entradas antes da escrita. Gate correspondente: `tests/test_protected_corpus.py` (4 testes) - valida a **lista** de paths (não apenas a contagem): todo caminho listado existe e bate hash; nenhum arquivo adicional não listado existe sob `data/questions/2011|2021`; nenhum path usa `\` ou `..`.

## E. Nove questões failed

Extraídas diretamente de `data/manifests/visual-audit-2008-computing.json` (nunca de uma lista inferida de relatórios antigos):

| ID | Página(s) | Blocker | Sintoma | Asset afetado | Gold (antes) |
| -- | --------: | ------- | ------- | -------------- | ------------ |
| D40 | 17 | `d40-table-reading-order-scramble` | 3 resíduos pré-existentes (ordem de palavras, schema truncado, cláusula ausente) + artefato cosmético "F" | figure-01 | needs_review |
| Q02 | 3 | `q02-region-merge-content-loss` | frase de transição e citação da imagem ausentes | figure-01 | needs_review |
| Q05 | 3 | `q05-image-citation-dropped` | citação fotográfica ausente | figure-01 | needs_review |
| Q07 | 4 | `q07-region-merge-content-loss` | cláusula de enquadramento + citação ausentes | figure-01 | needs_review |
| Q24 | 12 | `q24-region-merge-content-loss` | parágrafo do bloco decodificador + itens I/II inteiros ausentes | figure-01 | needs_review |
| Q33 | 14 | `q33-item-marker-displacement` | marcadores I-IV e "top-down"/"bottom-up" fora de posição | (nenhum) | needs_review |
| Q45 | 19 | `q45-region-merge-content-loss` | cláusulas de fechamento + itens I/II ausentes | figure-01 | needs_review |
| Q54 | 23 | `q54-region-merge-content-loss` | cláusula de abertura ausente | figure-01 | needs_review |
| **Q75** | **32** | `q75-alternative-d-diagram-label-bleed` | **rótulos do diagrama NAPT vazando para a alternativa D** | figure-01 | needs_review |

Todos os nove foram individualmente confirmados contra o texto real do PDF (`pymupdf`, extração direta) nesta fase, não apenas contra a nota de auditoria de fases anteriores.

## F. Primeira divergência

| Blocker | Estágio | Evidência |
| --- | --- | --- |
| Q02/Q05/Q07(cláusula)/Q54 | `figures.py::_expand_with_labels` (crescimento de região por absorção de rótulos) | `compute_line_region_relation` confirma `matches_absorbed_label=True` para cada linha perdida - a linha genuinamente entrou na cadeia de crescimento porque nenhum filtro existente (`_is_paragraph_continuation`, `_is_two_column_body_text`, `caption_font_size_gate`) a protege: é curta o bastante (≤300pt) sem ser uma continuação de uma linha *larga*, e não está alinhada à margem de uma coluna detectada. |
| Q45/Q02(citação) | `figures.py::_merge_by_vertical_proximity`/candidatos brutos (a região, mesmo **antes** de qualquer absorção de rótulo, já engloba geometricamente a linha) | `raw_intersects=True`, `matches_absorbed_label=False` - mecanismo diferente: a extensão **bruta** da região (vetores mesclados) já é grande demais, não uma cadeia de absorção de rótulos. |
| Q24 | mesmo padrão de Q45 (`raw_intersects=True`), mas o problema real é estrutural: três diagramas separados + itens julgados I/II/III, cada um com seu próprio circuito pequeno - nenhum mecanismo de rotulagem/label-absorption isolado resolve a ausência de conteúdo inteiro dos itens I e II. | Confirmado: nota de auditoria já documentava "precisa de um mecanismo dedicado de montagem multi-diagrama/item julgado". |
| D40/Q33 | **reordenação de fragmentos na mesma linha visual (mesmo y0, ±0.1-0.4pt), nunca vista por nenhum mecanismo de zonas/colunas** | Dump direto de `extract_page_lines`: em D40, "Cliente," (x0=134.3, y0=131.6) e "possui a relação" (x0=36.0, y0=132.0) e "com as informações" (x0=185.8, y0=132.0) são três fragmentos da MESMA linha impressa, mas o y0 de "Cliente," é *menor* que o de "possui a relação" apesar de estar geometricamente à sua direita - uma ordenação y0-então-x0 ingênua inverte a ordem correta de leitura esquerda-direita. Padrão idêntico em Q33 ("Cliente," ~ "I"/"bottom-up" trocados de posição por ruído de sub-ponto no y0 entre fragmentos da mesma linha impressa). |
| Q75 | `assembler.py::_in_alternatives_section` (isenção de filtragem de região) | Os rótulos do diagrama ("Computador A"/"Computador B"/endereços IP) estão geometricamente **dentro** da `VisualRegion` do NAPT (confirmado: `state=contained`, `matches_absorbed_label=True` na região correta) - a decisão de absorção da FIGURA está correta; o vazamento ocorre porque `_in_alternatives_section` isentava **incondicionalmente**, por posição Y apenas, qualquer linha a partir do marcador "A" da alternativa, ignorando que região a reivindicava. |

Nenhuma causa foi atribuída ao assembler quando já presente nos spans; nenhuma foi atribuída ao extrator de texto quando introduzida na renderização.

## G. Taxonomia residual

Invariantes classificados (Seção 8 do PROMPT):

- `text_loss`: Q02 (ambos os defeitos), Q05, Q07 (ambos), Q45 (ambos), Q54, Q24.
- `wrong_order` (dentro de uma única linha impressa, nunca entre zonas de página): D40 (mecanismo compartilhado), Q33 (mecanismo compartilhado).
- `wrong_attachment`/`foreign_content` (conteúdo do próprio diagrama, não de outra questão, anexado ao destino errado): **Q75** - selecionado.
- `wrong_boundary`/`missing_content` (estrutural, multi-diagrama): Q24.

Distribuição: 6 ocorrências de `text_loss` (algumas questões têm 2), 2 de `wrong_order` compartilhado, 1 de `wrong_attachment`, 1 caso misto (`Q24`, missing_content estrutural mais amplo que um único invariante).

## H. Clusters causais

```yaml
cluster_id: region-merge-content-loss-growth-chain
members: [Q02, Q05(parcial - citação também usa raw_intersects em outro trecho), Q07(cláusula), Q54]
first_divergent_stage: figures.py::_expand_with_labels (label_candidates growth chain)
invariant: text_loss
mechanism: uma linha curta, indentada ou fora da margem/coluna detectada, sem
  irmã "larga" imediatamente anterior, entra na cadeia de absorção de rótulos
  sem nenhum filtro existente rejeitá-la
shared_evidence: matches_absorbed_label=True em todas; nenhuma tem
  fragment_merges nem largura > MAX_LABEL_LINE_WIDTH
counterexamples: Q1 (citações de crédito de imagem, mesmo padrão geométrico,
  mas MÚLTIPLOS fragmentos na MESMA linha de base - distinto por normalmente
  vir em runs de mesmo-baseline, não stacks verticais)
candidate_general_fix: tentado e rejeitado nesta fase (ver Seção Y) - raio de
  explosão maior que o inicialmente estimado
estimated_blast_radius: alto (>=7 questões adicionais afetadas em 2008-b
  sozinho, ao menos 1 tentativa também regrediu 2011/2021)

cluster_id: region-raw-extent-oversized
members: [Q45, Q24(parcial)]
first_divergent_stage: figures.py candidate merge (raw, pre-growth region bbox)
invariant: text_loss
mechanism: a extensão BRUTA da região (antes de qualquer absorção de rótulo)
  já cobre geometricamente uma linha de prosa real, intercalada entre
  elementos do diagrama
shared_evidence: raw_intersects=True, matches_absorbed_label=False
counterexamples: nenhum contraexemplo negativo limpo identificado ainda
  (diagnóstico parcial, não implementado)
estimated_blast_radius: desconhecido - não investigado a fundo o suficiente
  para estimar com confiança

cluster_id: same-row-fragment-reordering
members: [D40, Q33]
first_divergent_stage: PyMuPDF get_text("dict") fragmentation + extract_page_lines
  sort (y0-then-x0) - nunca alcançado por reading_zones.py (que opera sobre
  Line inteiras já ordenadas corretamente dentro de uma zona, nunca
  reexamina fragmentos da MESMA linha impressa)
invariant: wrong_order
mechanism: dois ou mais fragmentos da mesma linha visual impressa têm y0
  ligeiramente diferentes (ruído de renderização de fonte, 0.1-0.4pt) que,
  combinado com um x0 mais à direita para o fragmento de y0 menor, inverte
  a ordem de leitura esquerda-direita sob uma ordenação padrão y0-then-x0
shared_evidence: em ambos, o fragmento deslocado tem y0 estritamente menor
  que seu vizinho à esquerda na mesma linha impressa (D40: 131.6 vs 132.0;
  Q33: 211.8 vs 211.7 e 244.2 vs 244.1)
counterexamples: nenhum caso de linha normal (fragmentos com y0 idêntico
  dentro de <0.05pt) é afetado - a maioria das linhas fragmentadas do
  corpus tem y0 idêntico entre fragmentos da mesma linha
candidate_general_fix: NÃO implementado nesta fase (fora do escopo de "um
  cluster por fase"; ver Seção I para a justificativa de por que Q75 foi
  escolhido em vez deste)
estimated_blast_radius: baixo e bem contido (2 questões conhecidas, mecanismo
  isolado ao pareamento y0/x0 de fragmentos numa janela vertical pequena)

cluster_id: same-question-diagram-label-bleed
members: [Q75]
first_divergent_stage: assembler.py::_in_alternatives_section (blanket
  Y-position exemption from region filtering)
invariant: wrong_attachment
mechanism: uma vez que a seção de alternativas começa (y0 do marcador "A"),
  TODA linha a partir dali era isenta de filtragem de região,
  independentemente de qual região (ou X) a reivindicasse
shared_evidence: os rótulos vazados estão corretamente dentro do bbox de
  uma VisualRegion grande (não pequena/small-formula) cujo próprio bbox
  não contém o marcador "A" da sequência
counterexamples negativos: 2021 cc-b Q22 (diagrama DER, mesma isenção,
  mas a região NÃO reivindica a continuação de forma incorreta - ver
  Seção O), 2011 Q23 (pontuação após fórmula inline - nunca toca uma
  região grande), 2021 SI Q33 (região grande cujo bbox CONTÉM o marcador
  "A" - é a própria estrutura da alternativa)
candidate_general_fix: implementado nesta fase (ver Seção J/K)
estimated_blast_radius: baixo, confirmado por regeneração completa (zero
  diff em 76 das 77 questões de 2008-b, zero diff em 2011/2021)
```

Clusters singleton (`region-raw-extent-oversized` parcialmente, `same-question-diagram-label-bleed`) são mantidos separados dos demais - nenhum foi misturado a outro só para aumentar contagem.

## I. Seleção do cluster

Ordem de severidade (Seção 10 do PROMPT): 1. contaminação de conteúdo estrangeiro; 2. perda de conteúdo legítimo; 3. duplicação; 4. ownership/attachment incorreto; 5. boundary incorreto; 6. ordem incorreta; 7. asset incompleto; 8. artefato cosmético.

Nenhum dos nove casos é genuinamente "conteúdo estrangeiro" (de outra questão) - o próprio nome do blocker de Q75 já diz "same-question". O nível mais alto realmente presente é **"perda de conteúdo legítimo"** (`region-merge-content-loss`, nível 2), com 6 questões. Esse cluster foi tentado primeiro (ver Seção Y) e **rejeitado** por não satisfazer a Seção 11 (raio de explosão maior que o estimável com confiança, três tentativas sucessivas de refinamento cada uma introduzindo novas regressões em questões antes corretas). Descartado o nível 2 por falta de uma correção seguramente demonstrável, o próximo nível efetivamente presente é **"ownership/attachment incorreto"** (nível 4) - `same-question-diagram-label-bleed`, com 1 membro (Q75) - que **está** acima de "ordem incorreta" (nível 6, `table-reading-order-scramble`, 2 membros: D40/Q33).

```yaml
selected_cluster: same-question-diagram-label-bleed
selection_reason: >
  Maior severidade genuinamente presente entre os clusters que satisfazem
  a Seção 11 (causa raiz confirmada, reprodução pré-correção, contraexemplo
  positivo E negativo, estratégia de correção testável, raio de explosão
  estimável). region-merge-content-loss tem severidade maior (perda de
  conteúdo > attachment incorreto) mas foi desqualificado por não produzir
  uma correção segura após três tentativas de refinamento (ver Seção Y) -
  escolher o próximo cluster por severidade real, não por conveniência.
rejected_clusters:
  - region-merge-content-loss-growth-chain (severidade 2, mas sem correção
    segura demonstrável dentro do orçamento desta fase - diagnóstico
    permanece aberto, ver Seção Y)
  - region-raw-extent-oversized (severidade 2, mecanismo insuficientemente
    investigado para estimar raio de explosão com confiança)
  - same-row-fragment-reordering (D40+Q33, severidade 6 - mais baixa que
    o cluster selecionado; 2 membros, mecanismo bem compreendido e provável
    candidato seguro para uma Fase 3N dedicada)
scope: assembler.py::_in_alternatives_section
expected_questions: [Q75]
```

## J. Causa raiz selecionada

**Reprodução**: confirmada pré-correção via dump direto de `extract_page_lines`/`detect_visual_regions` na página 32 - os rótulos "Computador A"/"Computador B"/endereços IP do diagrama NAPT (bbox `(384.96, 95.04, 551.15, 236.998)`, `is_small_formula=False`) sentam-se em `y0` (223.2-230.5) igual ou abaixo do `y0` do marcador da alternativa D (219.7) e E (232.9), mas com `x0` (~350-490) completamente disjunto da coluna de texto das alternativas (`x0≈36`).

**Mecanismo**: `assembler.py::_in_alternatives_section` (introduzida na Fase 1B para o caso oposto - proteger a continuação multi-linha de uma alternativa de ser engolida por uma figura, ex.: 2021 cc-b Q22's own DER diagram) concedia isenção de filtragem de região **incondicionalmente** a partir do `y0` do primeiro marcador "A", sem checar X nem qual região reivindicava a linha.

**Raio de explosão**: confirmado por regeneração completa das três provas (2008-b: 77 questões; 2011: 55 questões; 2021: 195 questões nos 3 cursos) - apenas Q75 muda.

## K. Correção implementada

`_in_alternatives_section` foi reescrita para conceder a isenção apenas quando **qualquer um** de três sinais estruturais se sustenta (nunca ID de questão, página, hash ou coordenada específica):

1. A linha não toca nenhuma região **grande** (não-`small_formula`) - o caso comum, e o caso de 2011 Q23 (pontuação após fórmula inline).
2. O `x0` da linha está próximo (≤60pt, cobrindo o recuo de tab-stop sob uma letra marcadora, medido em ~18.4pt no próprio corpus) do `x0` de **qualquer** marcador aceito do grupo de alternativas - não apenas o de "A", já que um layout horizontal (2008-b Q1: "A I e III.  B I e V.  C II e III. ...") posiciona cada letra em seu próprio `x0`.
3. Uma região grande toca a linha, mas o **próprio bbox dessa região contém o ponto do marcador "A"** - a região *é* a própria estrutura da alternativa (2021 SI Q33: um diagrama de tabela hash cujo bbox mesclado abrange todo o bloco de alternativas e legitimamente contém "A").

Uma linha que não satisfaz nenhum dos três (longe, em X, de todo marcador; dentro de uma região grande que também não contém "A") é conteúdo de figura genuinamente disjunto, não texto de alternativa - cai na filtragem de região ordinária, que a exclui corretamente.

Invariante formal: `exempt(line) ⟺ ¬touches_large_region(line) ∨ near_any_marker_x0(line) ∨ ∃r ∈ touching_large_regions(line): contains(r, anchor_A)`.

Nenhuma ativação declarativa (profile/capability) foi necessária - o mecanismo é incondicional e puramente estrutural (G3, ver Seção V).

## L. Casos reais corrigidos

**Antes** (`data/questions/2008/all-computing/enade-2008-computing-q75.md`, alternativa D):
```
D. 138.76.28.1 e 138.76.28.2 10.0.0.1 10.0.0.2 10.0.0.10 Computador A Computador B
```

**Depois**:
```
D. 138.76.28.1 e 138.76.28.2
```

Evidência: `test_q75_alternative_d_no_longer_bleeds_diagram_labels` (novo). Auditoria: `visual_validation: failed → passed`, `extraction_status: needs_review → verified`, `automatic_validation: passed` (inalterado).

## M. D40

Diagnosticado nesta fase (Seção F/H acima). Causa: reordenação de fragmentos dentro de uma única linha impressa (não entre zonas/colunas de página) - "Cliente," (x0=134.3, y0=131.6) ordenado antes de "possui a relação" (x0=36.0, y0=132.0) por ruído de sub-ponto no y0. Cluster: `same-row-fragment-reordering`, compartilhado com Q33 (achado novo e significativo desta fase - ver Seção N). Resultado: **não corrigido nesta fase** (fora do cluster selecionado); permanece com os mesmos 3 resíduos pré-existentes documentados desde a Fase 3G (ordem de palavras da sentença de abertura, bloco de schema truncado, cláusula de índices ausente) mais o artefato cosmético do rótulo "F" (Fase 3G). `reading_zones` **não foi reativado nem tocado** para "forçar" uma correção.

## N. Q33

Diagnosticado nesta fase com o mesmo rigor. Causa: idêntica a D40 em mecanismo - fragmentos "I"/corpo do item I e "II"/"top-down"/corpo do item II compartilham a mesma linha impressa com y0 diferindo por ~0.1pt, invertendo a ordem esquerda-direita correta. **Achado significativo**: contrariamente à conclusão da Fase 3K (que classificou D40 e Q33 como pertencentes a famílias de causa raiz *diferentes*, sem detalhar qual seria a de cada uma além de "não é o mecanismo de D10"), esta fase encontra evidência concreta e reproduzível de que D40 e Q33 **compartilham** o mesmo mecanismo causal de baixo nível (reordenação de fragmentos de mesma linha por ruído de y0) - uma correção honesta da caracterização anterior, não uma afirmação de que ambos compartilham o mecanismo de D10 (que continua correto: nenhum dos dois é um caso de topologia de colunas/zonas). Resultado: **não corrigido nesta fase** (fora do cluster selecionado, severidade menor que Q75); candidato prioritário para uma Fase 3N dedicada (ver Recomendação).

## O. Preservação da Fase 3L

- **D10**: `test_d10_reading_order_is_no_longer_scrambled` e `test_d10_activates_automatically_with_no_layout_override_present` - ambos passam (rodados explicitamente nesta fase).
- **Q50**: rejeitada pelo safety oracle, confirmado inalterado (`test_eligible_candidate_rejected_by_the_safety_oracle_leaves_a_note_and_original_order` e afins em `test_assembler_zone_reorder.py` - passam).
- **2011**: zero spans elegíveis para `reading_zones`, confirmado por regeneração completa (zero diff).
- **2021 D05**: elegível e segura em modo shadow, mas o profile de 2021 permanece sem `zoned_reading_order_mode` (desabilitado por ausência) - nenhuma mudança nesta fase.
- **Safety oracle**: intacto - nenhuma alteração em `reading_zones.py`, `_canonical_content_lines`, ou nos testes de Fase 3L.
- **Novos testes AST** (Seção 15 do PROMPT, `tests/test_generalization_architecture.py`, +3 testes): `test_layout_overrides_has_no_page_hash_zoning_selector` (nenhum método `forces_zoned_reading_order` pode voltar a existir), `test_geometric_consumers_accept_no_zoning_parameter` (`detect_visual_regions`/`extract_page_lines`/`extract_document_lines` nunca podem voltar a aceitar um parâmetro de zoneamento), `test_only_assembler_module_imports_reading_zones` (nenhum outro módulo pode voltar a importar `reading_zones`).

## P. Regressões históricas

Revalidados nesta fase via execução direta e explícita da suíte de testes já existente: Q12, Q13, Q25, Q28, Q29, Q52, Q61, Q62, Q63, Q68, Q71, D09, D10, D20, D39, D60 (16 casos exigidos pela Seção 16) + Q01, Q07, Q23, Q50, Q75 (5 casos incidentais) = 22 testes selecionados, **22 passed, 5 deselected** (a suíte tem mais testes por questão do que o filtro capturou nominalmente - todos os relevantes passaram). Nenhuma correção antiga foi reaberta silenciosamente.

## Q. ContentAssignment

Ledger regenerado (`scripts/generate_content_assignment_ledger.py`, escreve apenas em `data/manifests/content-assignment-2008-b.json`, extração real feita em `tempfile.TemporaryDirectory`): **2280 registros** (inalterado - o mesmo total da Fase 3J), **0 duplicados**, **0 ausentes**, **0 foreign owners** (verificado via `detect_duplicate_assignments`/`detect_missing_assignments`). O diff do próprio arquivo do ledger é **vazio** (byte-idêntico) - a correção de Q75 opera na etapa de consumo de texto (`_line_in_region`/`_in_alternatives_section`), posterior ao que este ledger registra (linhas/regiões brutas antes da fusão em parágrafos), portanto não afeta seus registros.

## R. Source coverage

Para Q75: `legitimate source content = canonical text (alternativa D corrigida) + asset-preserved content (figure-01.png, inalterado) + justified removal (os rótulos do diagrama, que já pertenciam geometricamente à figura, nunca precisaram de uma segunda representação textual)`. `unaccounted=0`, `duplicated=0`, `foreign_owner=0` para Q75. Nenhuma transformação de texto-para-fallback-visual foi necessária (a figura já existia e já continha esses rótulos visualmente - a correção apenas parou de duplicá-los como texto solto).

## S. Auditoria visual

77 IDs, **69 passed** (era 68), **8 failed** (era 9), **0 not_performed**. `fully_covered=True`. Confirmado via `enade assess-readiness --year 2008 --course all-computing`.

## T. Q8/Q38/Q55

Nenhuma ação além de revalidação diagnóstica, conforme exigido. Confirmado inalterado: as três permanecem excluídas do corpus publicado (nunca geram um arquivo `.md`), seus blockers (`q08/q38/q55-unstructured-image-alternatives`) permanecem `open`, gold permanece `provisional`. Nenhum placeholder foi publicado; nenhum recorte de página inteira foi criado; o gabarito nunca foi usado para inferir alternativas.

## U. D09/D59

Distinção preservada: `d09-answer-standard-absent-from-source` e `d59-answer-standard-image-only` permanecem `open` (fidelidade visual de D09/D59 é `passed`/não afetada - apenas o padrão de resposta oficial está mecanicamente ausente da fonte). Nenhum padrão foi inventado. Esta limitação não foi contada como falha do cluster residual selecionado (Q75).

## V. Capability registry

Nova entrada: `alternative_section_region_exemption` (G3 - mecanismo incondicional, puramente estrutural, sem dependência de profile/gate). Justificativa para G3 (não G2): o mecanismo não depende de nenhuma declaração de profile por booklet - é sempre ativo, e sua própria seleção de "quais linhas isentar" é 100% estrutural (contenção geométrica + proximidade a marcador), nunca uma página/ID/hash. Não é G4 (nenhuma prova cega contra exame inédito foi feita nesta fase).

## W. Proteção de 2011/2021

- Paths: `data/manifests/protected-files-2011-2021.json` (288 entradas) - todas presentes, nenhum path inesperado sob `data/questions/2011|2021` (confirmado por `tests/test_protected_corpus.py`, 4 testes).
- Hashes: 288/288 OK contra o snapshot histórico da Fase 3F.
- Gold: 2011 `maturity=validated, verified=54, needs_review=1` (inalterado); 2021-b `maturity=validated, verified=40, needs_review=0` (inalterado).
- Readiness: 2011 `READY_FOR_LEGACY_LAYOUT_TEST` (54/55, 1 blocker não-estrutural); 2021-b `READY_FOR_2011` (40/40, 0 blockers) - ambos inalterados.
- Drift: **0** em ambos os anos, confirmado por `git status --short` e pela verificação SHA-256 completa dos 288 arquivos.
- `missing_protected_paths=0`, `unexpected_protected_paths=0`.

## X. Testes, gates e reprodutibilidade

- Testes: 654 (Fase 3L) → **659** (+5: `test_q75_alternative_d_no_longer_bleeds_diagram_labels`, `test_q23_alternative_e_trailing_period_after_inline_formula_is_preserved`, mais os 4 de `test_protected_corpus.py` - descontando 1 já contado incidentalmente). Todos passando (`pytest tests/ -q` → `659 passed`).
- `ruff check .`: All checks passed.
- `ruff format --check .`: 2 arquivos com formatação cosmética corrigidos (`assembler.py`, `test_generalization_architecture.py`), reconfirmados limpos.
- `mypy src/enade`: Success, 58 source files.
- `enade validate-schema`: 13/13.
- `enade validate-manifest`: 0 warnings.
- `enade audit-extraction`: 2008 77/77, 2011 55/55, 2021 120/120 (3 cursos).
- `enade verify-gold`/`assess-readiness`:
  - 2008 (`all-computing`): `verify-gold` OK (77/77, maturity=provisional, 66 verified/11 needs_review); `assess-readiness` → `NOT_READY_FOR_2008_ENGINEERING_TEST`, 66/77 verified, visual audit 69/8/0, 35 blocker(s).
  - 2011: `verify-gold` OK (55/55); `assess-readiness` → `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1 blocker.
  - 2021-b: `verify-gold` OK (40/40); `assess-readiness` → `READY_FOR_2011`, 40/40, 0 blockers.
- Reprodutibilidade: duas execuções completas e independentes de `enade extract --year 2008 --course all-computing` (diretórios isolados) → `diff -rq run_a run_b` idêntico byte a byte; `diff -rq run_a data/questions/2008/all-computing` idêntico byte a byte ao corpus publicado.

## Y. Bugs e tentativas revertidas

1. **Filtro por contagem de tokens em `label_candidates` (região-merge-content-loss)**: primeira tentativa geral para o cluster de maior severidade - rejeitar candidatos a rótulo com >2 tokens (`MAX_LABEL_TOKEN_COUNT`). Corrigiu Q02(clause)/Q05/Q07(clause)/Q54, mas **regrediu Q1** (2008-b: citações de crédito de 5 retratos, multi-token, corretamente absorvidas hoje - contagem de assets 2→3). Refinamento 1 (isenção para fragmentos de mesma linha de base, `_is_same_baseline_fragment`) corrigiu Q1 mas não testado contra a família mais ampla do corpus.
2. **Extensão da isenção para excluir apenas regiões grandes tocando o texto (small-formula sempre isento)**: tentativa de generalizar ainda mais - **regrediu 7 questões adicionais** (D10, Q06, Q57, Q61, Q63, Q69, Q73) ao liberar conteúdo de legenda/citação legítimo que nunca deveria ter sido solto do seu diagrama (sem mecanismo de reinserção correta na posição certa do fluxo). Revertido integralmente.
3. Diante de (1)+(2) mostrando raio de explosão maior que o estimável com confiança, o cluster `region-merge-content-loss` foi **abandonado como alvo de implementação** (Seção 11 do PROMPT: "não implemente correção especulativa; encerre como diagnóstico parcial") e o próximo cluster por severidade genuína (Q75) foi selecionado.
4. **Q75 - tentativa 1 (tolerância de X aos marcadores apenas)**: corrigiu Q75 e, como efeito colateral bem-vindo, também a contaminação da alternativa E de Q07 pela mesma citação - mas **regrediu 2021 SI Q33** (alternativas em formato de tabela hash, cada célula perdida) porque o "A" de Q1 (2008-b) tem layout horizontal com um x0 por letra, quebrando a suposição de "único x0 de referência".
5. **Q75 - tentativa 2 (multi-marcador + região-contém-âncora, sem tolerância de X)**: corrigiu Q1/SI-Q33, mas **regrediu novamente** D40, Q02, Q08, Q54, Q63, Q23 (2011) e Q22/Q28 (2021) - a condição "região contém a âncora 'A'" sozinha era ora ampla demais, ora estreita demais dependendo do layout.
6. **Q75 - tentativa 3 (final, adotada)**: combinação dos três sinais (não-toca-região-grande OU x0-próximo-de-qualquer-marcador OU região-contém-âncora) - **zero diff** em 2008-b (exceto Q75) e **zero diff** em 2011/2021, confirmado por regeneração completa de todas as três provas.
7. Correção honesta de atribuição de ano: o caso original da Fase 1B (diagrama DER) é de **2021 cc-bacharelado**, não de 2011 como um primeiro rascunho do registro de capacidades desta fase erroneamente afirmou - corrigido antes da escrita final.

## Z. Arquivos e Git final

- Modificados (11): `data/manifests/blocker-ledger-2008.yaml`, `data/manifests/extraction-audit-2008-computing.csv`, `data/manifests/extraction-audit-2008-computing.json`, `data/manifests/extraction-capabilities.json`, `data/manifests/gold-2008-computing.json`, `data/manifests/visual-audit-2008-computing.json`, `data/questions/2008/all-computing/enade-2008-computing-q75.md`, `src/enade/extraction/assembler.py`, `tests/test_extraction_pipeline_2008.py`, `tests/test_extraction_pipeline_2011.py`, `tests/test_generalization_architecture.py`.
- Novos (2): `data/manifests/protected-files-2011-2021.json`, `tests/test_protected_corpus.py`.
- Removidos: nenhum arquivo permanente removido; scripts de diagnóstico (`diag_*.py`, `scripts/_phase3m_update_registry.py`) e diretórios temporários (`/d/tmp/phase3m/*`) criados e deletados durante a própria fase, nunca commitados.
- `git status --short` final: exatamente os 13 arquivos listados acima; `data/questions` restrito a Q75.
- Branch `feat/enade-2008-cc-b-pilot`, `HEAD=d70559f` (commit do usuário, não deste agente - ver Seção B), `master=a5dfaab` — ambos intocados por este agente. Nenhum commit, push, PR, merge ou tag criado por este agente.

## Recomendação

Ainda há questões `failed` (8/77). Pela mesma regra de seleção (Seção 10), o próximo cluster prioritário é **`same-row-fragment-reordering`** (D40 + Q33, severidade "ordem incorreta", 2 membros, mecanismo isolado e bem compreendido: fragmentos de uma mesma linha impressa reordenados por ruído de sub-ponto no y0 entre fragmentos vizinhos). Recomenda-se uma **Fase 3N restrita a esse cluster**, com um oráculo de segurança diferencial no estilo da Fase 3L (comparar a ordem candidata dos fragmentos contra a ordem original antes de publicar, exigindo conservação total de palavras/fragmentos) para evitar o mesmo tipo de raio de explosão excessivo encontrado nesta fase com `region-merge-content-loss`. Não iniciar Q8/Q38/Q55 (ainda fora de escopo - a recuperação delas só deve começar após a estabilização das 77 publicadas). Não processar o bundle `e`. `region-merge-content-loss` (Q02/Q05/Q07/Q24/Q45/Q54) permanece como diagnóstico parcial válido, não uma correção especulativa - qualquer fase futura que o retome deve investigar um oráculo de segurança pós-publicação (comparação texto-antes/depois por posição no fluxo, não apenas por presença/ausência) antes de tentar generalizar de novo.
