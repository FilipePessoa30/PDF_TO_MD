# Fase 3X — Cobertura Completa do Circuito Vetorial da Q38, Ownership dos Labels e Remoção Segura da Exclusão

## A. Classificação

**`Q38_VECTOR_CIRCUIT_RESOLVED`**.

Justificativa: o circuito está completo (todos os 5 pin labels + a anotação de saída
"f(A,B,C,D,E)" legíveis em `figure-01.png`); zero texto espúrio no enunciado (nenhuma duplicação,
nenhum vazamento de rótulo, nenhum "RASCUNHO"); as 5 alternativas estão completas, corretas e na
ordem certa; a exclusão foi removida com evidência (nunca por supressão de gate); os gates
mecânicos passam sem bypass; Q55/Q57/Q23/Q45/D40/D10/D09 permanecem intactos; 2011 e 2021
permanecem byte-idênticos; reprodutibilidade confirmada (run A = run B = corpus publicado); testes
permanentes adicionados. Reporto separadamente, como o prompt exige: **`EXCLUSION_CONTRACT_PARTIAL`**
continua sendo o estado correto do contrato agregado de exclusões (Q8 permanece aberta, por
desenho, fora do escopo desta fase) — não declaro `EXCLUSION_CONTRACT_RECONCILED` nem
`GENERALIZATION_SUCCESS` nesta fase apenas por resolver Q38.

O readiness gate real retorna **`NOT_READY_FOR_2011`** (nunca `NOT_READY_FOR_2008_ENGINEERING_TEST`
— esse rótulo não existe no código real; ver Seção B sobre esta e outras divergências do prompt).

## B. Estado Git inicial

- Branch: `feat/enade-2008-cc-b-pilot`, up to date com `origin/feat/enade-2008-cc-b-pilot`.
- `HEAD` inicial: `5bbe6d05adb843f6eada072d01e841e6b46c3b06` ("feat: Enhance extraction logic for
  inline formulas and chrome phrases" — commit da Fase 3W, feito por processo externo antes desta
  fase começar; conteúdo confirmado idêntico ao que a Fase 3W produziu).
- `master` = `origin/master` = `a5dfaab0c105150df3a7201c16547708cef45292` (inalterado).
- Árvore de trabalho limpa no início da fase.
- **Divergências do prompt em relação ao estado real, documentadas em vez de presumidas**:
  - `data/manifests/blocker-ledger-2008-b.yaml`/`visual-audit-2008-b.json`/`gold-2008-b.json`
    citados no prompt não existem; os arquivos reais são `blocker-ledger-2008.yaml`,
    `visual-audit-2008-computing.json`, `gold-2008-computing.json`.
  - O curso `engenharia-da-computacao-bacharelado` citado no prompt não existe como opção de CLI;
    2008-b é um caderno unificado, extraído via `--course all-computing` (Q38 pertence a
    `applicable_courses: [ciencia-da-computacao-bacharelado]`, não a engenharia).
  - O rótulo `NOT_READY_FOR_2008_ENGINEERING_TEST` citado no prompt nunca é retornado pelo gate
    real; o rótulo literal é `NOT_READY_FOR_2011`/`READY_FOR_2011` (herdado desde a Fase 3A).
  - Usei o estado real da CLI/manifests em todos os comandos executados nesta fase.

## C. Baseline

- `pytest`: **818 testes**, todos passando (confirmado por execução real).
- `ruff check .`/`ruff format --check .`/`mypy src`: limpos.
- `validate-schema`: 13/13. `validate-manifest`: OK, 0 warnings.
- `audit-extraction`: 78/78 (2008-b), 55/55 (2011), 120/120 (2021, três cursos).
- `assess-readiness --year 2008 --course all-computing`: `NOT_READY_FOR_2011`, 76/78 verified,
  visual audit 78/0/0, **6 blockers** (D09×2, D10×2, Q8, Q38).
- `assess-readiness --year 2011`: `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1 blocker. `assess-readiness
  --year 2021 --course ciencia-da-computacao-bacharelado`: `READY_FOR_2011`, 40/40, zero blockers.
- Combined hash do corpus publicado completo (2008+2011+2021), 404 arquivos: registrado antes de
  qualquer alteração.

## D. Blockers reais iniciais

| Blocker | Categoria | Efeito |
|---|---|---|
| D09 question_not_verified | structural | bloqueia |
| D09 missing_answer_standard | structural | bloqueia |
| D10 question_not_verified | structural | bloqueia |
| D10 missing_answer_standard | structural | bloqueia |
| q08-unstructured-image-alternatives | structural | bloqueia |
| q38-unstructured-image-alternatives | structural | bloqueia |

Confirmado via execução real do gate — 6 blockers, composição idêntica ao herdado da Fase 3W.

## E. Estado herdado da Fase 3W

Q38 tinha, na entrada desta fase: 5 overrides `exclude_from_orphan_marker_merge` (protegendo os 5
pin labels do circuito contra fusão de marcador órfão) + o endurecimento geral de
`_merge_orphan_markers`/`chrome.is_exact_chrome_phrase` (código de produção, já testado). Nenhum
override de alternativa/supressão para Q38 (revertidos ao final da Fase 3W). Estatuto:
statement limpo (sem duplicação, sem RASCUNHO), mas com um resíduo documentado: os pin labels
(B-E) e a anotação de saída do circuito ainda vazavam como texto solto, e as 5 alternativas
continuavam sem representação (questão inteira excluída).

## F. Inventário documental da Q38

| componente | página | bbox aproximado | representação | texto? | status inicial |
|---|---|---|---|---|---|
| marcador "QUESTÃO 38" | 15 | (336.2,297.6)-(?,308.7) | texto real | sim | publicado |
| enunciado (4 linhas) | 15 | x0=336.2, y=413.9-454.8 | texto real | sim | publicado, mas com vazamento colado |
| circuito (portas lógicas) | 15 | (357.8,323.2)-(494.8,402.6) drawings | vetor | não | região detectada, incompleta |
| pin labels A-E | 15 | x0=350.2-352.0, y=322.5-401.9 | texto real, fonte 7.3pt | sim | vazando como texto solto (exceto A, já absorvida) |
| anotação de saída f(A,B,C,D,E) | 15 | x0=499.9-547.2, y=347.7-355.0, 5 fragmentos PDF | texto real, fonte 7.3pt | sim | vazando como texto solto |
| alternativas A-E (fórmulas) | 15 | x0=355.7-443.3, y=466.2-531.6 | 100% vetor | não | sem asset, questão excluída |
| RASCUNHO | 15 | x0=343.6, y=543.1-550.0 | texto real, chrome | sim | corretamente nunca vazou nesta fase (protegido desde a Fase 3W) |
| conteúdo de página vizinha (coluna esquerda) | 15 | x0<330 | texto real, outra questão | sim | nunca tocado |

Nenhum label foi tratado como uma única região; a distinção entre pin labels (internos ao
circuito), enunciado (texto legítimo) e RASCUNHO/vizinho (chrome/outra questão) foi feita por
evidência geométrica (posição x0, relação com o desenho, relação com o marcador da questão) — nunca
por lista de palavras específicas de Q38.

## G. Forense rawdict/texttrace

Todos os 5 pin labels e os 5 fragmentos da anotação de saída confirmados via `rawdict`: fonte
`TT2F07o00`/`TT2F08o00`, tamanho ~7.32pt (bem abaixo do corpo de texto, 9.96pt), `flags=4`. Nenhuma
ambiguidade de charcode/glyph — são caracteres Latinos reais, sem substituição de fonte (diferente
de D40's "F"→σ). O desafio aqui foi puramente geométrico (region membership), não de identidade de
caractere — por isso nenhuma entrada nova foi adicionada a `source-token-ledger-2008.yaml` (mesma
convenção já estabelecida para Q23 na Fase 3V: decisão estrutural, não reivindicação de identidade).

## H. Forense de drawings

`page.get_drawings()` confirma exatamente 4 elementos vetoriais formando as portas lógicas do
circuito, envelope (357.8,323.2)-(494.8,402.6) — bem mais estreito que a região já detectada
(352.0,322.5)-(494.8,402.6), que já havia absorvido o pin label "A" via label-absorption growth
antes desta fase. As alternativas (69 elementos de desenho) e a caixa RASCUNHO (10 elementos, borda
do quadro) formam envelopes totalmente separados, sem overlap Y com o circuito (gap real ~64pt).

## I. Pipeline de regiões

Reconstruído estágio a estágio via instrumentação direta (nunca inferido do crop final):

1. **Drawing candidates**: 4 elementos do circuito, envelope (357.8,323.2)-(494.8,402.6).
2. **VisualRegion inicial**: mesmo envelope, `is_small_formula=False`.
3. **Label absorption (growth)**: absorve pin label "A" (x0=351.96, a única cujo próprio parceiro
   de merge órfão nunca existiu em alcance) → região cresce para x0=352.0. B/C/D/E e a anotação de
   saída NÃO são absorvidos (ver Seção J, root cause).
4. **Merge/growth adicional**: nenhum (a região já atingiu seu estado estável nesta fase, antes de
   qualquer alteração).
5. **Ownership**: região atribuída a `objective-38` (owner_key), `owner_x_bounds=(316.24,579.20)`.
6. **Filtragem de texto** (`_line_in_region`): pin label "A" → `contained`/`accepted` (excluído,
   correto). B/C/D/E e os 5 fragmentos de saída → `boundary_crossing`/`outside` com
   `decision=ambiguous` (mantidos como texto solto — o vazamento).
7. **Crop/render**: `_render_bbox` alarga horizontalmente até `owner_x_bounds` (316.24-579.20) +
   4pt vertical — cobrindo TODO o conteúdo (confirmado por re-render direto, ver Seção K) mesmo
   antes de qualquer correção nesta fase.
8. **Inserção no conteúdo**: pin labels/fragmentos de saída inseridos como texto solto no meio do
   enunciado (o vazamento visível na Fase 3W).

**Primeiro estágio divergente**: o estágio 3 (label absorption) — a região nunca tentou (e, com o
mecanismo real de crescimento, não deveria ter tentado de forma geral) absorver B/C/D/E/saída,
porque o pool de candidatos a label desta função (`detect_visual_regions`'s própria chamada interna
a `extract_page_lines`) nunca recebe `overrides`/`pdf_sha256` — portanto nunca se beneficia da
proteção `exclude_from_orphan_marker_merge` já ativa em todo o resto do pipeline. Isso não é
"bbox pequena" — é uma lacuna de threading identificada precisamente (ver Seção J).

## J. Root cause

```
função: detect_visual_regions
arquivo: src/enade/extraction/figures.py
condição: sua própria chamada interna a extract_page_lines (usada apenas
          para construir label_candidates) nunca recebeu overrides/pdf_sha256
entrada: page, page_number (sem overrides/pdf_sha256 threading)
decisão incorreta: _merge_orphan_markers roda, dentro desta chamada
                    específica, sem a proteção exclude_from_orphan_marker_merge,
                    fundindo os pin labels B/C/D com fragmentos vizinhos
                    (incluindo a própria anotação de saída do circuito) em
                    linhas únicas e muito largas
efeito observado: a linha fundida ultrapassa MAX_LABEL_LINE_WIDTH (300pt) e
                  é descartada da candidatura a label - growth nunca tenta
                  absorver B/C/D/saída; "A" escapa por não ter parceiro
                  elegível dentro da distância, permanecendo como candidato
                  limpo e sendo absorvido sozinho
```

Uma correção geral (threading de `overrides`/`pdf_sha256` nesta chamada) foi **tentada e
rejeitada** — ver Seção L.

## K. Ownership dos labels

Métricas registradas para cada um dos 10 fragmentos (9 exigindo override + "A", já resolvida):

| label | state | decision | já visível em figure-01.png (re-render direto)? |
|---|---|---|---|
| A | contained | accepted (já excluído, sem override) | sim |
| B | boundary_crossing | ambiguous | sim |
| C | boundary_crossing | ambiguous | sim |
| D | boundary_crossing | ambiguous | sim |
| E | boundary_crossing | ambiguous | sim |
| saída frag 1-5 | outside | ambiguous | sim |

Nenhum label foi removido do texto sem essa prova dupla (relação geométrica `ambiguous`, nunca
`accepted` por si só, **e** confirmação visual direta e fresca do crop já publicado, byte-idêntico,
antes de escrever qualquer override — nunca inferido do caso D40). O enunciado (texto legítimo) foi
deixado helper totalmente intacto — nenhuma linha do enunciado foi tocada ou reclassificada.

## L. Mecanismo implementado

**Tentativa rejeitada** (documentada, não escondida): threading de `overrides`/`pdf_sha256` na
chamada interna de `extract_page_lines` dentro de `detect_visual_regions`. Corrigia o sintoma
exato (B/C/D deixam de ser fundidos), mas instrumentação direta provou que isso libera growth de
forma tão eficaz que a região do circuito e a região das alternativas passam a crescer uma em
direção à outra (`TEXT_ABSORPTION_PADDING=90pt`, `MAX_ABSORPTION_GROWTH=110pt` por borda —
individualmente razoáveis, mas juntos o suficiente para superar o gap real de ~64pt entre elas) até
se sobreporem e `_merge_overlapping_regions` fundi-las em uma única região cobrindo o circuito, o
enunciado real, as 5 alternativas e o RASCUNHO — uma regressão em cascata, não uma correção.
Revertida integralmente; `figures.py` permanece com o comportamento de growth/merge idêntico ao
início da fase (documentado em comentário no código, não apenas no relatório).

**Mecanismo final, aplicado**: 9 overrides `force_region_membership` individualmente verificados
(o mesmo mecanismo, já G1, usado para o "F"→σ de D40 na Fase 3R) — sem nenhuma mudança ao código
de detecção/crescimento/merge de regiões. Cada um dos 9 fragmentos foi confirmado, antes de
declarado: (1) `decision=ambiguous` (nunca `accepted`) contra a região já existente e inalterada do
circuito; (2) já completa e legivelmente visível em `figure-01.png`, via re-render direto do crop
exato (sem qualquer alteração de bbox de região). `declare_inline_formula_region` NÃO foi reutilizado
para o circuito (ele representa fórmula vetorial inline, um tipo documental diferente de um
diagrama de circuito com labels textuais reais) — decisão consciente para não falsificar o tipo
documental, exatamente como a Seção 10 do prompt exige.

## M. Overrides

11 novos overrides nesta fase (todos travados por SHA-256+página+bbox+justificativa+evidência):
- 9 `force_region_membership` (pin labels B/C/D/E + 5 fragmentos da anotação de saída).
- 1 `suppress_visual_region` (blob redundante das alternativas, re-adicionado após a correção do
  circuito).
- 5 `declare_inline_formula_region` (uma por alternativa, re-adicionadas com os mesmos bboxes já
  verificados na Fase 3W).

Total de overrides no arquivo: 71 (início da fase, após a Fase 3W) → **91** (fim).

## N. Alternativas A–E

Revalidadas individualmente: cada uma tem seu próprio marcador (A-E), seu próprio asset
(`figure-02.png`-`figure-06.png`, tipo `equation`, confirmado — não `diagram`), texto vazio
sustentado por asset válido (aceito pela correção do validador da Fase 3W, sem regressão), ordem
A→E preservada, nenhum compartilhamento de asset entre alternativas, nenhum conteúdo do circuito
principal misturado, nenhuma contaminação cruzada. Os bboxes das 5 alternativas são idênticos aos
já verificados e revertidos na Fase 3W (nenhuma alteração nesta fase).

## O. Exclusões removidas ou preservadas

**Removida**: `q38-unstructured-image-alternatives` → `resolved`. **Preservada**: Q8 (fora de
escopo, nenhuma tentativa). D09/D10 permanecem `source_unavailable` (não tocados). `automatic
validation exclusion`/`gold-verification exclusion`/`readiness exclusion`/`capability claim` para
Q38 foram todos reconciliados juntos (nenhuma camada ficou "silenciosamente" removida enquanto
outra permanecia bloqueando): `automatic_validation: passed`, gold inclui Q38 com hash real,
readiness não lista mais Q38, capability registry reflete o novo caso sem promover a G3.

## P. Contraexemplos

Todos confirmados **byte-idênticos** via `git diff --stat` (saída vazia): Q55, Q57, Q23, Q45, D40,
D10, D09, D59. Q8: `git status` confirma diretório completamente intocado (nenhum arquivo staged,
modificado ou novo). Nenhuma fotografia horizontal foi tratada como fórmula ou circuito; nenhuma
heurística específica de Q8 foi implementada; capability registry continua distinguindo o caso de
Q8 (ver `q08-unstructured-image-alternatives`, inalterado).

## Q. Shadow mode

A tentativa rejeitada (Seção L) foi, na prática, seu próprio shadow-mode: rodada sobre a página real
de Q38 via instrumentação direta (`_expand_with_labels`, `_merge_overlapping_regions`), nunca
publicada, e comparada byte a byte contra o corpus canônico antes de qualquer decisão - a
regressão foi encontrada e revertida antes de tocar qualquer arquivo publicado. O mecanismo final
(9 `force_region_membership` individuais) não é uma regra geral - não precisa de shadow-mode
corpus-wide, pelo mesmo motivo que D40's "F" não precisou: cada bbox é travado a um SHA-256+página+
bbox exato, não pode disparar em nenhuma outra linha, página ou documento.

## R. Auditoria visual

```yaml
statement_complete: true
diagram_complete: true
labels_complete: true
alternatives_complete: true
no_duplicate_text: true
no_chrome: true
no_neighbor_content: true
correct_order: true
legible_assets: true
```

Confirmado por inspeção visual direta em resolução 6x de `figure-01.png` (circuito completo) e de
cada `figure-02.png`-`figure-06.png` (cada uma mostrando exatamente sua própria fórmula, glyph por
glyph idêntica à fonte). `visual-audit-2008-computing.json` atualizado com uma entrada `passed`
individual para Q38, documentando toda a investigação (nunca uma promoção em massa).

## S. Source-token ledger

Não alterado. Decisão consciente (não omissão): os 10 fragmentos investigados nesta fase nunca
tiveram sua própria identidade de caractere em dúvida (fonte/charcode/glyph confirmados como
Latinos reais, sem substituição) - o desafio foi inteiramente geométrico (region membership), a
mesma categoria de decisão que Q23 já estabeleceu, na Fase 3V, como não exigindo entrada neste
ledger.

## T. Capability registry

`forced_region_membership_for_proven_duplicates`: **G1 → G2** (segundo caso real, independente,
provando que o mecanismo generaliza além da prova por identidade de fonte/glyph de D40 para uma
prova por re-render visual direto - sem nenhuma mudança de código). Um bug real foi encontrado e
corrigido durante esta atualização: o campo `trigger_features` desta entrada mencionava "D40"/"Q38"
por nome, violando a própria regra do projeto (testada por
`test_capability_registry_never_cites_a_question_id_as_a_trigger`) de que `trigger_features` deve
descrever apenas características observáveis, nunca identidade de questão - corrigido antes de
finalizar a fase. Nenhuma capability foi promovida a G3. A tentativa rejeitada (Seção L) não gerou
nova capability (não é um mecanismo, é uma lição documentada no código-fonte e neste relatório).

## U. Gold

Inicial: 76/78 verified. Final: **77/79 verified**, `unresolved_question_ids` inalterado
(`[D09, D10]`). Reconstruído via `enade build-gold` (nunca editado à mão); único efeito real foi a
adição da entrada de Q38 (hash do markdown + 6 assets) e o incremento de `verified_count`.

## V. Readiness

Inicial: 6 blockers. Final: **5 blockers** (D09×2, D10×2, Q8) — resultado literal do gate, nunca
forçado. `assess-readiness --year 2008 --course all-computing`: `NOT_READY_FOR_2011` (nunca
declarado "pronto" globalmente; D09/D10/Q8 continuam bloqueando, corretamente visíveis). 2011:
`READY_FOR_LEGACY_LAYOUT_TEST`, inalterado. 2021 CC-B: `READY_FOR_2011`, inalterado.

## W. Testes e quality gates

- 818 → **818 testes** (a fase substituiu 1 teste antigo, agora obsoleto -
  `test_q38_remains_excluded_after_q55s_own_fix` - por um novo,
  `test_q38_circuit_and_alternatives_are_now_fully_published`, e ajustou
  `test_all_80_academic_questions_are_accounted_for` para a nova contagem - contagem líquida
  inalterada).
- `pytest tests/ -q`: **818 passed**, 0 failed (confirmado em execução real, 287.32s).
- Um teste falhou durante o desenvolvimento e foi corrigido antes da finalização:
  `test_capability_registry_never_cites_a_question_id_as_a_trigger` (Seção T) - documentado, não
  escondido.
- `ruff check .`/`ruff format --check .`/`mypy src`: limpos.
- `validate-schema`: 13/13. `validate-manifest`: OK, 0 warnings.
- `audit-extraction`: 79/79 (2008-b), 55/55 (2011), 120/120 (2021).
- `verify-gold`/`assess-readiness`: reportados nas Seções C/U com output literal.

## X. Reprodutibilidade e arquivos

Duas execuções independentes de `enade extract --year 2008 --course all-computing`: byte-idênticas
entre si e contra o corpus canônico. `git status --short` final:
```
 M data/manifests/blocker-ledger-2008.yaml
 M data/manifests/extraction-audit-2008-computing.csv
 M data/manifests/extraction-audit-2008-computing.json
 M data/manifests/extraction-capabilities.json
 M data/manifests/gold-2008-computing.json
 M data/manifests/layout-overrides.yaml
 M data/manifests/visual-audit-2008-computing.json
 M data/questions/2008/all-computing/enade-2008-computing-q38/figure-01.png
 M data/questions/2008/all-computing/enade-2008-computing-q38/figure-02.png
 M src/enade/extraction/figures.py
 M tests/test_extraction_pipeline_2008.py
?? data/questions/2008/all-computing/enade-2008-computing-q38.md
?? data/questions/2008/all-computing/enade-2008-computing-q38/figure-0{3,4,5,6}.png
```
`src/enade/extraction/figures.py` contém apenas um comentário documentando a tentativa rejeitada -
zero mudança funcional em relação ao início da fase (confirmado: `figures.py` produz exatamente o
mesmo comportamento de growth/merge para todo o resto do corpus). Nenhum arquivo de scratch
remanescente fora do repositório.

## Y. Estado Git final e recomendação

Nenhum commit, push, PR, merge ou tag foi criado. `master` não foi tocado.

**Recomendação**:
1. Recomendo uma fase isolada, dedicada, para a arquitetura de fotografias horizontais de Q8 (um
   mecanismo genuinamente novo de fatiamento por X, sem precedente no corpus) - não iniciar
   automaticamente.
2. Manter D09/D10 como limitações documentais (`source_unavailable`) até existir uma política
   formal de readiness para esse status - não reabrir, não fabricar.
3. Com Q38 resolvida, os 5 blockers restantes de 2008-b são: D09 (2), D10 (2), Q8 (1) - todos já
   bem compreendidos, nenhum mais exigindo forense de baixo nível.
4. Não processar outro bundle/ano. Não iniciar teste de prova inédita enquanto o gate continuar
   `NOT_READY_FOR_2011`. Não commitar nada desta fase sem revisão humana explícita.

**PRINCÍPIO CONFIRMADO NESTA FASE**: uma correção geral que "parece" resolver o sintoma exige
verificação por instrumentação direta, não apenas inspeção do crop final - a tentativa rejeitada
nesta fase (Seção L) teria sido publicada como uma correção válida se eu tivesse confiado apenas na
imagem final (que, isoladamente, parecia perfeita). A remoção da exclusão de Q38 é consequência de
fidelidade comprovada por evidência dupla (relação geométrica + re-render visual), nunca uma meta
contábil.
