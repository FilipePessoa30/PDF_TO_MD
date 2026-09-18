# Fase 3W — Auditoria, Classificação e Remoção Justificada das Exclusões Históricas de Q8, Q38 e Q55

## A. Classificação

**`EXCLUSION_CONTRACT_RECONCILED`**.

Justificativa: as três exclusões (Q8, Q38, Q55) foram investigadas individualmente, com evidência
forense fresca (nunca presumindo os diagnósticos das Fases 3A/3I como corretos até re-verificar).
Uma delas (Q55) foi genuinamente resolvida e publicada, com testes permanentes. As outras duas
(Q8, Q38) permanecem `open`, mas agora com causa raiz precisamente conhecida, disposition
canônica explícita, e — no caso de Q38 — duas de três camadas de defeito já corrigidas
*generalicamente* (não por hack específico da questão), com o menor próximo trabalho documentado
para a camada restante. Nenhum blocker desapareceu silenciosamente; nenhuma exclusão foi removida
sem evidência; nenhum conteúdo foi fabricado. Gold e readiness derivam literalmente do estado real
(76/78 verified, 6 blockers, visual audit 78/0/0). 2011 e 2021 permanecem byte-idênticos.

Esta classificação não exige readiness aprovado — o estado agregado de 2008-b continua
**`NOT_READY_FOR_2011`** (herdado do gate literal), pelas razões corretas (D09/D10 `source_unavailable`
+ Q8/Q38 ainda abertos), nunca ocultadas.

## B. Estado Git inicial

- Branch: `feat/enade-2008-cc-b-pilot` (up to date com `origin/feat/enade-2008-cc-b-pilot`).
- `HEAD` inicial: `445640fbcdce660f8035d0972feef4fdfc00a9b3` ("feat: Implement paragraph break
  override for Q23 schema fragment" — commit da Fase 3V, feito por processo externo antes desta
  fase começar).
- `master` = `origin/master` = `a5dfaab0c105150df3a7201c16547708cef45292` (inalterado do início ao
  fim desta fase).
- Árvore de trabalho limpa (`git status --short` vazio) no início da fase.
- Confirmados presentes: `force_paragraph_break_after`, `force_region_membership`,
  `protect_from_region_membership`, `declare_inline_formula_region`, answer standard visual de D59
  (`visual_only_answer_standard`), Q23 corrigida, D09/D10 `source_unavailable`, visual audit 77/77,
  readiness com sete blockers, `docs/phase-3v-report.md` — todos confirmados via grep antes de
  qualquer edição.
- Nenhuma alteração pré-existente foi descartada; nenhuma nova branch foi criada.

## C. Baseline

Antes de qualquer alteração desta fase:

- `pytest`: 795 testes, todos passando (confirmado via execução real, não presumido).
- `ruff check`/`ruff format --check`/`mypy src`: limpos.
- `validate-schema`: 13/13. `validate-manifest`: OK, 0 warnings.
- `audit-extraction`: 77/77 (2008-b), 55/55 (2011), 120/120 (2021, três cursos).
- `assess-readiness --year 2008 --course all-computing`: `NOT_READY_FOR_2011`, 75/77 verified,
  visual audit 77/0/0, **7 blockers**: D09×2 (question_not_verified, missing_answer_standard),
  D10×2 (mesmos), Q8, Q38, Q55 (cada um `blocker_ledger_open`, categoria
  `unstructured-image-alternatives`).
- `assess-readiness --year 2011`: `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1 blocker não-estrutural
  (Q34). `assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado`: `READY_FOR_2011`,
  40/40, zero blockers.
- Gold inicial: 75/77 verified (2008-b), `unresolved_question_ids: [D09, D10]`.

## D. Inventário dos sete blockers

| Blocker ID | Questão | Categoria | Motivo | Gold effect | Readiness effect |
|---|---|---|---|---|---|
| `d09-*` (question_not_verified) | D09 | structural | extraction_status=needs_review | needs_review | bloqueia |
| `d09-*` (missing_answer_standard) | D09 | structural | sem padrão de resposta oficial | - | bloqueia |
| `d10-*` (question_not_verified) | D10 | structural | extraction_status=needs_review | needs_review | bloqueia |
| `d10-*` (missing_answer_standard) | D10 | structural | sem padrão de resposta oficial | - | bloqueia |
| `q08-unstructured-image-alternatives` | Q8 | structural | alternativas em imagem, não publicada | não conta (excluída) | bloqueia |
| `q38-unstructured-image-alternatives` | Q38 | structural | alternativas em imagem/fórmula, não publicada | não conta (excluída) | bloqueia |
| `q55-unstructured-image-alternatives` | Q55 | structural | alternativas em imagem/fórmula, não publicada | não conta (excluída) | bloqueia |

Confirmado: nenhum blocker fora desta lista de 7 existia no gate real. D09/D10 correspondem
exatamente a 2 findings cada (4 no total); Q8/Q38/Q55 a 1 finding cada (3 no total) = 7. Composição
confirmada empiricamente, não presumida.

## E. Contrato de exclusões

Cada uma das 3 exclusões foi reclassificada com os seguintes campos (via `blocker-ledger-2008.yaml`,
sem criar um segundo sistema paralelo - os campos existentes `category`/`cause`/`description`/
`evidence`/`status`/`regression_tests`/`resolution` já cobrem o contrato pedido; `source_pages` e
`question_id` já identificam origem):

- **Categoria real** (todas as 3): `exclusion_from_extraction` (a Question nunca é construída -
  `pipeline.py`'s own per-question `ValidationError` isolation) — nunca
  `exclusion_from_automatic_validation`/`exclusion_from_gold_verification` isoladamente, já que a
  ausência é anterior a qualquer validação.
- **Estados finais** (Seção 8, canônicos): Q8 → `active_blocking` (bloqueia `document_fidelity`
  genuinamente — conteúdo real e identificável não pode ser publicado hoje). Q38 →
  `active_blocking` (mesma razão — um resíduo real, ainda visível, de garbling permanece). Q55 →
  `removed_after_validation` (as 8 condições da Seção 17 satisfeitas, ver Seção N).

## F. Q8 — diagnóstico original

Fase 3A (commit `1ee01af`) documentou Q8/Q38/Q55 com um único texto boilerplate copiado 3 vezes
("large, merged blobs (492x343pt, 342x681pt, 508x687pt)"), nunca citado em nenhum relatório de fase
(`git log -S` confirma: essa string exata nunca apareceu em nenhum `docs/*.md`). Fase 3I (Seção P)
fez uma re-verificação independente por questão e encontrou números DIFERENTES (Q8: 2 regiões,
492×343pt e 522×221pt; Q38: 1 região, 333×341pt; Q55: 2 regiões, 268×245pt e 317×84pt) — mas essa
tabela, embora mais cuidadosa, também nunca citou fonte real de imagem (raster vs. vetor) nem
confirmou a MESMA questão para cada bbox.

## G. Q8 — estado atual

Forense fresca (`page.get_image_info()`, `page.get_drawings()`) nesta fase:

- Página 5 tem **5 imagens raster reais, distintas** (nunca vetor): (51.0,241.8)-(193.4,437.6);
  (221.0,242.5)-(369.8,435.8); (405.2,238.8)-(558.7,435.2); (121.8,520.8)-(263.6,722.4);
  (292.0,518.6)-(463.9,719.6) — cada uma individualmente alinhada ao seu próprio marcador de letra
  (A/B/C em y≈346-356; D/E em y≈632-642).
- Visualmente confirmado (`figure-01.png` renderizado): A = "Homem idoso na poltrona" (Rembrandt),
  B = "Figura e borboleta" (Milton Dacosta), C = "O Grito" (Munch) — cada uma com legenda real
  impressa na própria página.
- `region_merge_x_tolerance: 150.0` (perfil 2008) funde A+B+C (gap 27.6-35.4pt) em um blob de
  492.1×343.3pt, e D+E (gap 28.4pt) em 522.2×220.9pt — ambos `is_small_formula=False` hoje,
  confirmado via `detect_visual_regions` real, não presumido do texto antigo.
- `_attach_alternative_formula_regions` só fatia por sobreposição em Y (modelo de lista vertical,
  válido para 2011 Q14/Q23) - arquiteturalmente incapaz de distinguir A/B/C, que compartilham quase
  o mesmo Y e diferem em X (arranjo horizontal, sem precedente no corpus).
- **Decisão**: `active_blocking`, `readiness_disposition: document_fidelity`. Nenhuma tentativa de
  correção nesta fase (mudança estrutural de alto raio: uma nova classe de fatiamento por X, sem
  caso real do corpus para validar com segurança). Menor próximo trabalho: estender
  `_attach_alternative_formula_regions` (ou construir um mecanismo paralelo) para reconhecer um
  "candidato de imagem completa por alternativa, alinhado de forma única e não-ambígua à própria
  linha/coluna", com shadow-mode completo antes de ativar.

## H. Q38 — diagnóstico original

Mesmo boilerplate da Fase 3A que Q8/Q55; Fase 3I encontrou "1 região: 333×341pt,
`is_small_formula=False`", texto competing corretamente resolvido (marcador real aceito via
`find_alternative_group`).

## I. Q38 — estado atual

Forense fresca prova Q38's alternativas 100% vetor-desenhadas (fórmulas booleanas com barra de
negação, ex. "Ā.B̄ + C̄.D̄ + D.E") — zero imagem raster, `page.get_text(clip=...)` vazio.
Arquiteturalmente idêntico a Q45 (Fase 3S), nunca a Q8.

Investigação em três camadas (todas com evidência real, nenhuma presumida):

1. **Camada 1 (alternativas)** — FIXADA: 5 `declare_inline_formula_region` (um bbox por
   alternativa, computado por clustering de gap natural dos elementos de desenho — nunca por
   posição de marcador, que se provou insegura ao cortar as barras de negação da alternativa C no
   lugar errado) + 1 `suppress_visual_region` para o blob agora redundante.
2. **Camada 2 (garbling do statement)** — descoberta ao regenerar: `_merge_orphan_markers`
   (mecanismo GERAL, usado em toda página de todo caderno) tratava os 5 rótulos internos do
   próprio diagrama de circuito ("A"-"E", x0~350-356, rótulos de pino) como marcadores órfãos
   reais, colando o rótulo "E" diretamente na primeira linha do statement real
   ("No circuito acima..."), duplicando e corrompendo o texto. **FIXADA GENERICAMENTE**: 5
   `exclude_from_orphan_marker_merge` (mesmo mecanismo já usado para o cabeçalho de tabela-verdade
   de 2011 Q22) + endurecimento de `_merge_orphan_markers` para nunca escolher uma frase de chrome
   inequívoca ("RASCUNHO" etc., `chrome.is_exact_chrome_phrase`, novo) como parceiro de merge, em
   qualquer página. Achado crítico: o próprio marcador real "E" de Q38 estava a 19.57pt de
   "RASCUNHO" — só 0.47pt abaixo do limite `_ORPHAN_MARKER_MAX_DISTANCE` (20.0pt); o "E" de Q55
   escapou por pura coincidência (20.04pt), não por estar genuinamente protegido.
3. **Camada 3 (resíduo do statement)** — AINDA ABERTA: a região detectada do próprio diagrama de
   circuito não se estende o suficiente para incluir seus próprios rótulos de pino nem sua própria
   anotação de saída ("f(A,B,C,D,E)") — ambos já totalmente visíveis em `figure-01.png` (confirmado
   por inspeção visual direta). `force_region_membership` (precedente D40) é o mecanismo provável,
   mas a fragmentação PDF-interna da anotação de saída (5 fragmentos de linha aparentemente
   sobrepostos no mesmo Y) exige mais investigação forense do que o orçamento desta fase permite.

**Decisão final**: `active_blocking` (a Camada 3 ainda impede fidelidade documental completa) — a
tentativa de publicação de alternativas foi revertida uma segunda vez (confirmado por regeneração:
zero traço no corpus publicado), mas as correções gerais das Camadas 1/2 (as 5 exclusões de
marcador órfão + o endurecimento de `_merge_orphan_markers`) foram mantidas, comprovadamente
seguras e valiosas por si mesmas.

## J. Q55 — diagnóstico original

Mesmo boilerplate da Fase 3A; Fase 3I encontrou "2 regiões: 268×245pt e 317×84pt" — a re-verificação
desta fase provou que o PRIMEIRO desses números (268×245pt) na verdade pertence a Q54 (coluna
esquerda, x0=50.2), não a Q55 (coluna direita, x0=332.2) — um erro de atribuição entre questões
vizinhas que nem a Fase 3A nem a 3I detectaram, corrigido nesta fase via checagem de
`owner_x_bounds` real.

## K. Q55 — estado atual

100% vetor-desenhado (fórmulas exponenciais, ex. "[1-e^-0.3t]³"), mesma causa raiz de Q38, nunca de
Q8. Único bbox relevante: 73.3×84.3pt (não 268×245pt). **RESOLVIDA**: mesmo mecanismo de Q38-camada-1
(5 `declare_inline_formula_region` + 1 `suppress_visual_region`), sem nenhuma Camada 2/3 — o
statement de Q55 não tem rótulos internos de diagrama, portanto não aciona
`_merge_orphan_markers` incorretamente. Um bug real foi corrigido no processo:
`_attach_alternative_formula_regions`'s própria construção de região fatiada não copiava
`is_declared_inline_formula` de `best`, fazendo `render_region` cair em `AssetType.DIAGRAM` em vez
de `EQUATION` — corrigido copiando o campo. Um segundo bug real: `validator.py` marcava QUALQUER
alternativa de texto vazio como defeito mecânico, sem verificar se um asset real a representa (a
própria `Alternative` do schema já permite isso desde a Fase 3A) — corrigido espelhando a lógica do
schema em `evaluate_extraction`.

## L. Comparação com a fonte

Todas as 5 alternativas de Q55 (figure-01.png a figure-05.png) foram individualmente re-renderizadas
a 6x zoom e comparadas visualmente contra a página fonte: cada uma mostra exatamente, apenas, e
completamente sua própria fórmula, sem vazamento de alternativas vizinhas, sem fabricação. A ordem
(A→E) e o texto do statement (verbatim, sem alteração) foram confirmados idênticos à fonte.

## M. Execução sem exclusão

Q55: pipeline completo com a exclusão removida (i.e., com os overrides ativos) produz uma Question
válida, `automatic_validation=passed`, `visual_validation=passed` (após auditoria manual registrada
em `visual-audit-2008-computing.json`), `extraction_status=verified`. Q38: com a exclusão removida
(overrides ativos), o pipeline detecta e relata um `ValidationError` genuíno após a Camada 3 não
resolvida seria necessária para publicar sem defeito - documentado, não escondido, pipeline mantido
excluído deliberadamente. Q8: nunca teve a exclusão removida (nenhum mecanismo construído).

## N. Exclusões removidas

Apenas Q55, com todas as 8 condições da Seção 17 satisfeitas:
1. Motivo original ("sem candidato pequeno de fórmula") não é mais reproduzível como causa de
   exclusão - substituído por evidência de que é 100% vetor, não imagem pequena ausente.
2. Output atual fiel (Seção L).
3. Mecanismo identificado (`declare_inline_formula_region` reaproveitado + correção de
   `is_declared_inline_formula` + correção de `validator.py`).
4. Gate executa sem bypass (nenhum override de conteúdo, nenhuma fabricação).
5. Teste dirigido: `test_q55_alternatives_are_now_published_as_vector_formula_equations`.
6. Gold verifica o artefato (78 questões, hash de Q55 incluído).
7. Readiness não depende mais desta exclusão (blocker removido da lista real).
8. Nenhuma regressão (regeneração completa de 2008-b/2011/2021, zero drift fora de Q55).

## O. Exclusões preservadas

Q8 e Q38 permanecem `open`/`active_blocking`. Motivo original preservado no histórico (`evidence`
aponta para as Fases 3A/3I originais, nunca apagadas); razão atual, precisa e re-verificada,
substitui a antiga apenas como entendimento corrente, não como reescrita da história. Próximos
trabalhos mínimos documentados nas Seções G e I.

## P. Exclusões diagnostic-only

Nenhuma das 3 exclusões qualifica como `diagnostic_only` (todas alteram, ou alterariam, o output
publicado - nunca são meramente informativas).

## Q. Blocker ledger

Estado final: 60 blockers no ledger total (inalterado em contagem - nenhum novo blocker criado,
nenhum apagado). `q55-unstructured-image-alternatives`: `open` → `resolved`, com `resolution`,
`regression_tests` (7 testes) e `evidence` atualizados. `q08-unstructured-image-alternatives` e
`q38-unstructured-image-alternatives`: `cause`/`description`/`evidence` completamente reescritos
com a forense desta fase, `status` permanece `open` (Q38 ganhou `regression_tests` mesmo aberto -
cobrindo as correções gerais das Camadas 1/2, que são permanentes independentemente do status da
questão em si).

## R. D09/D10

Confirmado intocado: `git diff` vazio para `enade-2008-computing-d09.md`/`-d10.md`. `status:
source_unavailable` preservado (não revisitado nesta fase, per Seção 5 do prompt - nenhuma
descoberta documental extraordinária buscada ou encontrada). Findings independentes
(`question_not_verified`, `missing_answer_standard`) continuam aparecendo no gate real, exatamente
como antes.

## S. Q23/D59/D40/Q45

Confirmado byte-idêntico via `git diff --stat` (saída vazia) para os 4 arquivos + seus diretórios de
asset. Nenhum destes foi tocado, lido para edição, ou mencionado em qualquer override novo desta
fase.

## T. Gold

Inicial: 75/77 verified, `unresolved_question_ids: [D09, D10]`.
Final: **76/78 verified**, `unresolved_question_ids: [D09, D10]` (inalterado - nunca promovido por
razão administrativa). Reconstruído via `enade build-gold` (nunca editado à mão); único efeito real
foi a adição da entrada de Q55 (hash do markdown + 5 assets) e o incremento de `verified_count`.
D09/D10 permanecem as únicas 2 questões não verificadas, exatamente como o prompt antecipou como
resultado provável (Seção 28).

## U. Readiness

Inicial: 7 blockers. Final: **6 blockers** (D09×2, D10×2, Q8, Q38 - Q55 não aparece mais).
Decisão literal do gate, não forçada: `NOT_READY_FOR_2011` (o prompt já antecipava que o resultado
poderia continuar `NOT_READY` por causa de D09/D10 - e de fato também por Q8/Q38, ainda abertos).
Visual audit: 78 passed/0 failed/0 not_performed (fully_covered=True) - subiu de 77 para 78 com a
publicação de Q55.

## V. Capability registry

Duas atualizações, nenhuma promovida a G3:
- `declared_inline_vector_formula_preservation`: **G1 → G2** (evidência real: o mesmo mecanismo,
  sem nenhuma mudança de detecção/verificação, agora provado em dois consumidores independentes -
  statement, desde a Fase 3S, e alternativa, novo nesta fase). Limitação registrada: Q38 continua
  sendo um caso "quase resolvido" explicitamente listado como protected/limitado, não como sucesso.
- `orphan_marker_chrome_partner_exclusion` (nova, G1): a correção geral de
  `_merge_orphan_markers`/`chrome.is_exact_chrome_phrase`, com casos reais (Q38's "E", Q57's
  alternativas numéricas como contraexemplo negativo que impediu uma generalização insegura).

## W. Proteção de 2011/2021

Regeneração completa: 2008-b (78/78, apenas Q55 difere do estado inicial), 2011 (`all-computing`,
55 questões, `diff -rq` byte-idêntico), 2021 (três cursos, 120 questões, `diff -rq` byte-idêntico).
A correção geral em `layout.py`/`chrome.py` (`_merge_orphan_markers`) é executada para TODO
booklet, não apenas 2008-b - confirmada segura via regeneração completa dos três anos, não apenas
argumentada.

## X. Testes e reprodutibilidade

- 795 → **818** testes (23 novos): 3 em `test_extraction_validator.py`, 1 em
  `test_extraction_assembler.py`, 2 em `test_extraction_pipeline_2008.py`, 2 funções (múltiplos
  casos parametrizados) em `test_extraction_layout.py` e `test_extraction_chrome.py` combinados.
- `pytest tests/ -q`: **818 passed**, 0 failed (execução real, 324.74s).
- `ruff check .` / `ruff format --check .` / `mypy src`: limpos.
- `validate-schema`: 13/13. `validate-manifest`: OK, 0 warnings.
- `audit-extraction`: 78/78 (2008-b), 55/55 (2011), 120/120 (2021).
- `verify-gold`/`assess-readiness` (2008/2011/2021 CC-B): todos executados com output literal
  reportado nas Seções C/U.
- Reprodutibilidade (A/B): duas execuções independentes de `enade extract --year 2008
  --course all-computing`, byte-idênticas entre si e contra o corpus canônico.

## Y. Git final e recomendação

`git status --short` final (sem scratch remanescente):
```
 M data/manifests/blocker-ledger-2008.yaml
 M data/manifests/extraction-audit-2008-computing.csv
 M data/manifests/extraction-audit-2008-computing.json
 M data/manifests/extraction-capabilities.json
 M data/manifests/gold-2008-computing.json
 M data/manifests/layout-overrides.yaml
 M data/manifests/visual-audit-2008-computing.json
 M data/questions/2008/all-computing/enade-2008-computing-q55/figure-01.png
 M src/enade/extraction/assembler.py
 M src/enade/extraction/chrome.py
 M src/enade/extraction/layout.py
 M src/enade/extraction/validator.py
 M tests/test_extraction_assembler.py
 M tests/test_extraction_chrome.py
 M tests/test_extraction_layout.py
 M tests/test_extraction_pipeline_2008.py
 M tests/test_extraction_validator.py
?? data/questions/2008/all-computing/enade-2008-computing-q55.md
?? data/questions/2008/all-computing/enade-2008-computing-q55/figure-0{2,3,4,5}.png
```
Nenhum commit, push, PR, merge ou tag foi criado. `master` não foi tocado. Nenhum script de
diagnóstico permanece fora do repositório (todos os arquivos temporários em `%TEMP%` foram
apagados).

**Recomendação**:
1. Os blockers restantes de 2008-b (D09/D10, Q8, Q38) não são mais forense pendente de baixo nível
   - são decisões de produto/priorização. D09/D10 devem continuar `source_unavailable`
   (definitivo, não reabrir). Q8 precisa de uma decisão de escopo: investir na nova classe de
   mecanismo "imagem completa por alternativa, arranjo horizontal" (Seção G) ou aceitar a exclusão
   permanentemente. Q38 está muito mais perto: só a Camada 3 (rótulos do circuito não totalmente
   cobertos pela própria região) falta.
2. Sugiro uma Fase 3X dedicada e estreita para: (a) resolver a Camada 3 de Q38 (via
   `force_region_membership` para os 5 rótulos de pino + investigação da fragmentação estranha da
   anotação de saída), o que provavelmente desbloqueia Q38 por completo; (b) decidir formalmente a
   política de readiness para limitações comprovadamente impostas pela fonte (D09/D10) vs.
   limitações de capability (Q8) - two categorias distintas que hoje contam igualmente como
   "blocker" mas têm naturezas bem diferentes.
3. Não fabricar conteúdo para Q8/Q38. Não converter `source_unavailable` em `resolved` para D09/D10.
   Não processar outro bundle/ano. Não iniciar prova inédita enquanto o gate continuar `NOT_READY`.
   Não commitar nada desta fase sem revisão humana explícita.

**PRINCÍPIO CONFIRMADO NESTA FASE**: exclusão não é sinônimo de falha, aprovação ou dispensa. Q55
só deixou de bloquear quando a fidelidade documental pôde ser verificada diretamente e o caso ficou
protegido por testes permanentes. Q38 permanece bloqueado precisamente porque, apesar de progresso
real e generalizável, sua fidelidade documental ainda não pode ser totalmente verificada - e essa
distinção foi mantida visível, nunca escondida atrás de uma contagem de readiness mais confortável.
