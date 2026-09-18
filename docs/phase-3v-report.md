# Fase 3V — Preservação de Texto Parcialmente Recortado e Separação Estrutural de Q23

## A. Classificação

**`PARTIAL_VISUAL_TEXT_PRESERVATION_STABILIZED`** para o único alvo de conteúdo desta fase (2008-b Q23).

Justificativa: o texto de Q23 permanece 100% preservado (nenhuma remoção, nenhuma fabricação); a
separação de parágrafo foi corrigida por um mecanismo estrutural, individualmente verificado e
declarativo (não um `text.replace`, não lógica por ID de questão); `figure-01.png` permanece
byte-idêntico; a regeneração completa de 2008-b (77), 2011 (55) e 2021 (120, três cursos) confirmou
que **somente** o Markdown da Q23 mudou. Duas hipóteses de regra geral foram exploradas e
corretamente rejeitadas após evidência empírica (Seções P e Q) — a fase manteve a disciplina de
"nunca generalizar sem prova de shadow-mode", produzindo um capability G1, não G3.

Estado agregado (herdado, não alterado nesta fase): 2008-b continua
**`NOT_READY_FOR_2008_ENGINEERING_TEST`** (7 blockers remanescentes, todos fora do escopo desta
fase); 2011 continua `READY_FOR_LEGACY_LAYOUT_TEST`; 2021 CC-B continua `READY_FOR_2011`.

## B. Estado Git inicial

`HEAD` no início da fase: `31c31c9ad1a2456b1ac96e5e623ef8d38465e6e4` ("feat: Enhance answer standard
extraction to support visual-only rubrics" — combina as Fases 3T+3U, já commitado por processo
externo). Árvore de trabalho limpa (`git status` sem alterações) antes de qualquer edição desta
fase. Branch: `feat/enade-2008-cc-b-pilot`. Nenhum commit, push, PR, merge ou tag foi criado nesta
fase; `master` não foi tocado.

## C. Baseline

Antes de qualquer alteração:

- `pytest`: 787 testes, todos passando.
- `ruff`/`mypy`: limpos.
- `validate-schema`/`validate-manifest`: OK.
- `audit-extraction`: 77/77 (2008-b), 55/55 (2011), 40+2021-l+2021-s (120 total 2021) — todos OK.
- `assess-readiness --year 2008`: `NOT_READY_FOR_2011`, 75/77 verified, 2 needs_review, visual
  audit 77/0/0, **8 blockers** (D09×2, D10×2, Q8/Q38/Q55, Q23).
- `assess-readiness --year 2011`: `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1 blocker não-estrutural
  (Q34).
- `assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado`: `READY_FOR_2011`,
  40/40, zero blockers.
- Hashes registrados: `enade-2008-computing-q23.md` sha256
  `b2ccd610f343a02aa07772871bbb3f2a05b04b2ed4756cb0ec4dd6cbeb6dfffc`; `figure-01.png` sha256
  `54d4c7766146ac13f8d5e5f37bd09928f8ecde74d1421190d5c2e8bcd2ac2fb5` (inalterado até o fim da fase);
  gold manifest `markdown_sha256` da Q23 idêntico ao hash acima.

## D. Diagnóstico anterior (Fases 3G/3T)

A Fase 3G documentou originalmente este resíduo como "cosmetic only - no information lost"
(`category: content-duplication`). A Fase 3T provou, por instrumentação direta de
`compute_line_region_relation`/`_text_consumption_decision` e inspeção visual de `figure-01.png`
em resolução real, que essa afirmação estava **errada**: a linha "IdRep:integer referencia
Republica)" (página 11) está genuinamente truncada no crop renderizado (o clip cobre apenas os
~2.3pt superiores dos ~9pt de altura da linha) — o texto é a única cópia completa desse fragmento
de esquema. A Fase 3T reclassificou o blocker para
`content-preserved-via-text-not-cosmetic-duplication` e recomendou explicitamente, como próximo
passo, "a narrow, individually-scoped mechanism to insert a paragraph break at this exact, verified
point (e.g. a new hash+bbox-locked 'force paragraph break' override)" — exatamente o mecanismo
implementado nesta fase.

## E. Reprodução

Reproduzido a partir de uma extração limpa (script de diagnóstico temporário, apagado ao final):

```
line.text: 'IdRep:integer referencia Republica)'
line.bbox: (310.4390869140625, 515.694091796875, 499.4087829589844, 524.694091796875)
region.bbox (grown): (310.4389953613281, 429.7738342285156, 559.1927490234375, 514.0137939453125)
region.raw_bbox: (310.4389953613281, 459.239013671875, 504.8390197753906, 481.4389953613281)
relation: state='touching', intersection_over_line_area=0.0, raw_intersects=False,
          matches_absorbed_label=False, horizontal_overlap_ratio=1.0, vertical_overlap_ratio=0.0
gap to next line ("Suponha que existam..."): 15.92pt (< PARAGRAPH_GAP_THRESHOLD=19.0pt)
published (antes): 'IdRep:integer referencia Republica) Suponha que existam as seguintes tuplas
                    no banco de dados:'  (um único content_block: paragraph)
```

A linha sobrevive corretamente à exclusão (`_line_in_region` retorna `False`: decisão
`"ambiguous"`, nunca `"accepted"`), mas o gap real ao próximo conteúdo cai abaixo do limiar
compartilhado de continuação de parágrafo — sem nenhum sinal estrutural adicional, as duas frases
são unidas por um único espaço.

## F. Métricas de cobertura

Calculadas diretamente (nunca aproximadas), para a linha "IdRep:integer referencia Republica)":

| métrica | valor |
|---|---|
| `intersection_height_over_line_height` | 2.3197 / 9.0003 = **0.2577** |
| `intersection_area_over_line_area` | **0.2577** (largura 100% coberta, altura 25.77%) |
| `contained_by_raw_region` | **False** (`raw_intersects=False`) |
| `contained_by_grown_region` | **False** (`state="touching"`, não `"contained"`) |
| `contained_by_final_crop` | **False** (parcial: overlap_ratio contra o crop final renderizado = 0.2577, ver Seção Q) |
| `visible_height_ratio` | **0.2577** |
| `visible_width_ratio` | **1.0** |
| `full_object_containment` | **False** |

Comparação com a linha imediatamente anterior do mesmo esquema ("Republica(IdRep:integer,"), que É
um duplicado seguro: `visible_height_ratio=1.0`, `visible_width_ratio=1.0`,
`full_object_containment=True`, `state="contained"` — mostrando exatamente a diferença entre
"totalmente preservado" e "parcialmente interceptado".

## G. Relação estrutural

Não foi criada uma nova estrutura `VisualCoverageRelation`. `LineRegionRelation` (já existente em
`assembler.py`) já expõe todos os campos necessários (`state`, `intersection_over_line_area`,
`horizontal_overlap_ratio`, `vertical_overlap_ratio`, `raw_intersects`, `matches_absorbed_label`) —
a Seção F mapeia cada métrica exigida pela Fase 3V diretamente a um campo já existente, confirmando
que a estrutura já cobre corretamente o caso (regra do prompt: "não crie estrutura redundante se
`LineRegionRelation` puder ser estendida corretamente" — aqui nem extensão foi necessária, os campos
já bastam). Uma classificação textual equivalente às cinco categorias sugeridas
(`fully_preserved`/`partially_preserved`/`barely_intersecting`/`not_preserved`/`ambiguous`) já é
efetivamente codificada pela combinação `(state, raw_intersects, matches_absorbed_label)` +
`_text_consumption_decision`; Q23 mapeia para "partially_preserved" (kept, não íntegro no asset).

## H. Comparação Q23 × D40 (positivo × negativo de deduplicação segura)

| critério | D40 "F"→σ (Fase 3R, seguro) | Q23 "IdRep..." (inseguro) |
|---|---|---|
| objeto completo no asset | Sim — glyph inteiro, já visível em `figure-01.png` (crop se estende mais à esquerda que a bbox lógica) | **Não** — crop corta a linha aos ~2.3pt de ~9pt (25.77%) |
| cobertura vertical | 100% (rendering confirma o glifo inteiro) | **25.77%** |
| cobertura horizontal | 100% | 100% (mas irrelevante sem a vertical) |
| legibilidade do asset | Sim, glifo nítido e identificado por fonte/charcode | Sim, mas mostra só a metade superior do texto cortado |
| cópia externa necessária | Não — nada se perde ao remover o texto | **Sim** — o texto é a única cópia completa |
| relação estrutural | `state="touching"`, decisão `"ambiguous"` | `state="touching"`, decisão `"ambiguous"` (mesma classe geométrica!) |
| decisão correta | Excluir o texto (`force_region_membership`) | **Preservar o texto integralmente**, corrigir apenas a separação de parágrafo (`force_paragraph_break_after`) |

O ponto central: as duas linhas caem na **mesma classe geométrica** (`ambiguous`/`touching`) — é
exatamente por isso que um sinal geométrico genérico não poderia, sozinho, diferenciá-las
automaticamente sem uma prova positiva adicional (identidade de fonte/glifo para D40; nenhuma
equivalente disponível para Q23, pois o texto de Q23 é texto real, não um glifo substituído).
`force_region_membership` já documentava essa exigência (Fase 3T já havia provado, por essa mesma
razão, que aplicá-lo a Q23 causaria perda real de conteúdo) — esta fase não reabre essa decisão, e
não aplica `force_region_membership` a Q23 em nenhum momento.

## I. Primeiro estágio divergente

Pipeline reconstruído estágio a estágio para esta linha:

1. **PDF → linha bruta**: correto — `page.get_text("rawdict")` extrai a linha inteira, sem
   truncamento no texto.
2. **Region membership** (`_line_in_region`): correto — decisão `"ambiguous"`, linha preservada
   como texto visível.
3. **Figure crop** (`assets._render_bbox`): correto por design — o crop é intencionalmente mais
   estreito que a altura completa da linha (a linha nunca deveria ter sido absorvida; o crop não
   precisa cobri-la).
4. **Visual coverage**: correto (recém-formalizado nesta fase, Seção F) — mostra 25.77%, nunca
   presumido 100%.
5. **Content assignment**: correto — a linha é atribuída à `statement` (não à figura, não a outra
   questão) — confirmado também no `content-assignment-2008-b.json` pré-existente
   (`assignment_id: enade-2008-computing-q23:24`, `anchor: statement`).
6. **Paragraph grouping** (`_build_statement_segments`): **aqui diverge**. O gap real (15.92pt)
   cai abaixo de `PARAGRAPH_GAP_THRESHOLD` (19.0pt) e nenhum outro sinal estrutural existente
   (mudança de fonte não é usada por este código; a linha não é monoespaçada) interrompe o run de
   prosa — as duas frases são unidas.
7. **Content blocks / Markdown**: consequência direta do estágio 6, não um defeito independente.

A fase corrigiu exclusivamente o estágio 6 (a causa raiz), nunca pós-processando o texto/Markdown
já gerado nos estágios 7 (nenhum `text.replace`, nenhuma busca por string literal).

## J. Papel documental

A linha "IdRep:integer referencia Republica)" foi classificada, por evidência estrutural (não por
proximidade), como **fragmento interno de esquema (schema-internal), continuação truncada da
mesma tabela de definições que aparece parcialmente no `figure-01.png`** — não uma legenda, não uma
alternativa, não uma linha de outra questão. Evidência: mesma fonte (`TT2EDCo00`, 9.0pt) da linha
imediatamente anterior do mesmo esquema ("Republica(IdRep:integer,", também 9.0pt,
`TT2EDCo00`), mesmo x0 de coluna (310.44), y0 sequencial imediatamente após a borda inferior da
região. A frase seguinte ("Suponha que existam...") usa uma fonte diferente (`TT2EC3o00`, 9.96pt —
a mesma fonte de prosa usada no resto do enunciado de Q23), confirmando que é um parágrafo
genuinamente novo. Esse par de fontes foi investigado como possível *sinal geral* de quebra de
parágrafo e rejeitado (Seção Q) — usado aqui apenas como evidência de classificação, nunca como
gatilho de código.

## K. Content blocks

Nenhum novo tipo de `content_block` foi criado. O bloco `paragraph` único e colado foi dividido em
dois blocos `paragraph` consecutivos, usando a estrutura já existente (`type: paragraph`) — a
sugestão do próprio prompt de preferir "um parágrafo independente com provenance" a um novo tipo
(`asset_companion_text`) se aplicou diretamente: nenhuma estrutura nova foi necessária.

Antes:
```yaml
- type: paragraph
  text: 'IdRep:integer referencia Republica) Suponha que existam as seguintes tuplas
    no banco de dados:'
```

Depois:
```yaml
- type: paragraph
  text: IdRep:integer referencia Republica)
- type: paragraph
  text: 'Suponha que existam as seguintes tuplas no banco de dados:'
```

## L. Paragraph separation (mecanismo escolhido)

Duas alternativas gerais foram avaliadas e **rejeitadas com evidência** antes de se optar pelo
mecanismo final (ver Seções P e Q para os dados completos):

1. **Baixar `PARAGRAPH_GAP_THRESHOLD`** para cobrir 15.92pt: rejeitado — uma varredura direta do
   corpus 2008-b encontrou 46 outros pares de linha com gap no mesmo intervalo [14, 19)pt, a
   esmagadora maioria continuações legítimas do mesmo parágrafo (ex.: D40 "consulta em SQL foi
   utilizada:" → "SELECT nome, endereco", gap 17.49pt) que seriam incorretamente quebradas.
2. **Regra geral "linha tocando uma região força quebra de parágrafo"**: rejeitado — shadow-mode
   completo em 2008-b (77 questões) encontrou 61 candidatos, a esmagadora maioria conteúdo já
   correto e protegido (o parágrafo de notícia de D10 ao lado de uma imagem; os parágrafos de
   Q12/Q54/Q63/Q75 ao lado de diagramas; o vazamento irmão "B" de D40, deliberadamente fora de
   escopo).

**Mecanismo escolhido**: novo override declarativo `force_paragraph_break_after`
(`layout_overrides.py`/`layout-overrides.yaml`), travado por hash+página+bbox exatamente como
`force_region_membership` (Fase 3R) e `declare_inline_formula_region` (Fase 3S). Em
`assembler._build_statement_segments`, após processar cada linha (independentemente de ser prosa
ou código), se o override casar com a bbox exata da linha, `flush_all()` é chamado imediatamente —
terminando o parágrafo/bloco atual ali, sem tocar `PARAGRAPH_GAP_THRESHOLD`, `_line_in_region`, ou
qualquer lógica de merge/crop compartilhada. Nunca compara strings, nunca usa `question_id`/`year`
em código central — apenas geometria exata declarada uma única vez.

## M. Anchors

- `source_line_id` (conceitual): página 11, bbox `(310.439, 515.694, 499.409, 524.694)`.
- `anchor_before`: bloco `asset` (`figure-01`).
- `anchor_after`: novo parágrafo "Suponha que existam...".
- `asset_id`: `figure-01` (não modificado).
- `relative_position`: imediatamente após o asset, antes do bloco `code` de exemplo de tuplas.
- `paragraph_boundary`: agora explícito entre os dois parágrafos (antes inexistente).

Nenhum campo novo de schema foi adicionado para representar esses anchors — eles são
inteiramente reconstituíveis a partir da ordem de `content_blocks` + do override declarado, mesma
convenção usada por `force_region_membership`/`declare_inline_formula_region`.

## N. Asset

`figure-01.png` permanece **byte-idêntico** (sha256
`54d4c7766146ac13f8d5e5f37bd09928f8ecde74d1421190d5c2e8bcd2ac2fb5`, inalterado). Nenhuma
justificativa para alterá-lo foi encontrada nem buscada: a propriedade já é clara (esquema da
própria Q23), nenhuma questão vizinha é capturada, nenhuma coluna errada é incluída, e um recrop
mais alto não eliminaria a necessidade de preservar o texto (a linha nunca poderia ser
"completada" visualmente sem repetir texto já mostrado acima dela no mesmo crop).

## O. Safety oracle

Verificação por objeto, não apenas por string, aplicada via regeneração completa + diff:

- **texto antes = texto depois** (concatenado): confirmado idêntico, caractere a caractere — apenas
  o ponto de junção mudou de `" "` para um novo boundary de parágrafo.
- **ordem documental**: preservada (statement → asset → \[novo: 2 parágrafos] → code → statement
  final → alternativas).
- **sem perda**: `git diff` mostra apenas a divisão do bloco, nenhum caractere removido.
- **sem duplicação**: nenhum texto passou a aparecer duas vezes.
- **sem alteração textual**: nenhuma palavra/pontuação mudou.
- **sem mudança de owner**: `canonical_owner`/`anchor` no content-assignment ledger continuam
  `question`/`statement`.
- **sem mudança de alternativa**: as 5 alternativas de Q23, byte-idênticas.
- **sem mudança de asset**: `figure-01.png` byte-idêntico.
- **sem contaminação**: nenhuma outra questão de 2008-b, 2011 ou 2021 mudou (Seção W).

## P. Shadow mode (regra geral "linha tocando região", rejeitada)

Shadow-mode instrumentado (monkeypatch de diagnóstico, nunca ativado em produção) rodado sobre as
77 questões de 2008-b (única prova onde `contextual_relation_gate=True` — 2011/2021 nunca alcançam
este código, portanto têm risco zero por construção). Resultado: 61 linhas "mantidas, mas com
relação geométrica não-`outside`/não-`contained`" foram encontradas, entre elas: o parágrafo
protegido de D10 (página 7, 10 linhas, `h_ratio=0.0` — coluna diferente), 8 linhas de Q12,
7 linhas de Q54, 3 linhas de Q63, 7 linhas de Q75 (todos casos de "texto ao lado de figura"
genuinamente corretos), o vazamento irmão "B" de D40 (fora de escopo). Apenas a linha de Q23 combina
`state="touching"` com `horizontal_overlap_ratio≈1.0` **e** `vertical_overlap_ratio≈0.0`
simultaneamente — uma assinatura única entre as 61, mas amostra de tamanho 1 não justifica
promover essa combinação a regra corpus-wide sem mais casos reais confirmados em outras provas.

## Q. Contraexemplos (verificação adicional, pedido do usuário mid-fase)

Uma segunda hipótese de generalização foi levantada e testada: usar a sobreposição contra o **crop
final renderizado** (mais largo, alargado até a borda da coluna do dono) em vez da bbox lógica da
região. Resultado empírico, medido nas mesmas 61 linhas: **50 delas** (incluindo D10, Q12, Q54, Q63,
Q75 inteiros) passaram a mostrar `crop_overlap_ratio=1.0000` — o alargamento horizontal do crop
(até a largura total da coluna, para não cortar contexto visual) elimina exatamente a precisão
espacial que distinguia os casos seguros dos inseguros. A própria Q23 (o caso real) ficou com
`crop_overlap_ratio=0.2577` — **menor** que praticamente todos os falsos positivos. Esta hipótese
foi refutada pelos dados e descartada; documentada aqui porque nasceu de uma pergunta direta do
usuário durante a fase e o teste (não a intuição) é o que decide.

Fixtures negativas cobertas (via os 61 candidatos acima, já publicados e confirmados corretos):
parágrafo contínuo ao lado de figura (D10), texto ao lado de figura em múltiplas linhas (Q12, Q75),
fragmento same-row de fonte diferente (D40 "Cliente,"/"B" — mecanismo `same_row_ordering`, não
tocado), item-marker overlapping região grande (Q24 "III", Q45 "III"). Fixtures adicionais
(legenda multilinha, alternativa multilinha, tabela, fórmula inline, texto de outra
questão/coluna) permanecem cobertas pelos testes já existentes das Fases 2F/3G/3N/3S — nenhuma
delas passa a atravessar o novo código (o override só é consultado após a linha já ter sido
processada normalmente, e só produz efeito para a bbox exata declarada).

## R. Content assignment ledger

Não alterado. `data/manifests/content-assignment-2008-b.json` é um snapshot offline (não
regenerado por `extract_exam`, confirmado nas Fases 3R/3T); a entrada existente para esta linha
(`enade-2008-computing-q23:24`, `canonical_owner: question`, `anchor: statement`) já estava e
continua correta — o fix não muda ownership nem anchor, apenas separação de parágrafo.

## S. Source-token ledger

Não alterado. `source-token-ledger-2008.yaml` documenta identidade de caractere/glifo (charcode,
glyph_id, fingerprint de fonte) — esta fase não envolve nenhuma reivindicação de identidade de
caractere (o texto de Q23 nunca foi questionado como texto real), portanto não se aplica.

## T. Blocker ledger

`q23-schema-fragment-duplicate-bleed`: `status: open` → **`status: resolved`**. `category`
mantida (`content-preserved-via-text-not-cosmetic-duplication` — ainda descreve corretamente a
natureza do achado). `resolution` e `regression_tests` preenchidos com a explicação completa do
mecanismo e as 5 novas evidências de teste. Histórico de diagnóstico (Fases 3G, 3T) preservado
integralmente em `evidence`, nunca sobrescrito.

## U. D09/D10/D59

Não tocados nesta fase. Confirmado por `git status`/`git diff` (nenhuma linha alterada nos arquivos
de D09/D10/D59) e por `assess-readiness` (D09/D10 continuam nos blockers com a mesma descrição
`source_unavailable`/`question_not_verified`/`missing_answer_standard`; D59 não aparece na lista de
blockers, como esperado desde a Fase 3U).

## V. Gold e readiness

Gold reconstruído via `enade build-gold --year 2008 --course all-computing` (nunca editado à mão):
único campo alterado foi `markdown_sha256` da Q23
(`b2ccd610f3...` → `354dc71cc7...`). `verified_count` permanece 75/77, `unresolved_question_ids`
permanece `[D09, D10]`.

`assess-readiness --year 2008 --course all-computing`: `NOT_READY_FOR_2011`, 75/77 verified, visual
audit 77 passed/0 failed/0 not_performed, **7 blockers** (queda de 8 → 7: D09×2, D10×2,
Q8/Q38/Q55×3 — a entrada de Q23 não aparece mais). `assess-readiness --year 2011`:
`READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1 blocker (Q34), inalterado.
`assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado`: `READY_FOR_2011`, 40/40,
zero blockers, inalterado.

## W. Proteção de 2011/2021

Regeneração completa: 2008-b (77/77 questões geradas, apenas Q23 difere do corpus canônico
anterior), 2011 (`all-computing`, 55 questões — `diff -rq` byte-idêntico), 2021 (três cursos —
`ciencia-da-computacao-bacharelado`, `ciencia-da-computacao-licenciatura`,
`sistemas-de-informacao`, 120 questões no total — `diff -rq` byte-idêntico). Nenhuma proteção
adicional foi necessária além da já existente: `contextual_relation_gate` é `False` para 2011/2021
(confirmado em `data/manifests/exam-structure-2008.yaml` sendo o único perfil com esse campo
`true`), portanto o novo código em `_build_statement_segments` sequer é alcançado por esses anos —
proteção por construção, não apenas por teste.

## X. Testes e reprodutibilidade

- 787 → **795** testes (8 novos: 5 em `test_layout_overrides.py`, 2 em
  `test_extraction_assembler.py`, 1 em `test_extraction_pipeline_2008.py`).
- `pytest tests/ -q`: **795 passed** (0 failed, 0 skipped além do padrão já existente).
- `ruff check`: limpo nos arquivos alterados.
- `mypy`: limpo em `assembler.py`/`layout_overrides.py`.
- `validate-schema`: 13/13 fixtures válidas.
- `validate-manifest`: OK, 0 warnings.
- `audit-extraction`: 77/77 (2008-b), 55/55 (2011), 120/120 (2021, três cursos).
- Reprodutibilidade (A/B): duas execuções independentes de `enade extract --year 2008
  --course all-computing` produziram Markdown/hash idênticos para Q23 e para todo o restante do
  corpus.

## Y. Git final e recomendação

`git status --short` ao final (nenhum scratch remanescente):
```
 M data/manifests/blocker-ledger-2008.yaml
 M data/manifests/extraction-capabilities.json
 M data/manifests/gold-2008-computing.json
 M data/manifests/layout-overrides.yaml
 M data/questions/2008/all-computing/enade-2008-computing-q23.md
 M src/enade/extraction/assembler.py
 M src/enade/extraction/layout_overrides.py
 M tests/test_extraction_assembler.py
 M tests/test_extraction_pipeline_2008.py
 M tests/test_layout_overrides.py
```
Nenhum commit, push, PR, merge ou tag foi criado. `master` não foi tocado. Todos os scripts de
diagnóstico temporários (`diag_q23_coverage.py`, `shadow_scan_q23_signal.py`,
`crop_overlap_check.py`, `shadow_scan_results.txt` e diretórios temporários em
`%TEMP%`) foram apagados antes do fim da fase.

**Recomendação**: com Q23 resolvido, os 7 blockers remanescentes de 2008-b não são mais forense de
PDF — são decisões de produto/contrato: (1) **D09/D10** devem permanecer `source_unavailable`
(prova negativa já definitiva desde a Fase 3T; não reabrir, não fabricar padrão de resposta).
(2) **Q8/Q38/Q55** precisam de uma decisão explícita de reconciliação contratual (estender o schema
para aceitar alternativas puramente visuais/não-estruturadas, ou aceitar a exclusão permanente) —
esta é a peça de maior prioridade para avançar 2008-b, e não deve ser resolvida por um hack
específico de questão. (3) Não reabrir D40, Q45 ou D59 (todos resolvidos e verificados em fases
anteriores). (4) Não processar nenhum outro bundle/ano (2005, "e", ou qualquer prova fora do
escopo atual). (5) Não iniciar testes de novel-exam enquanto 2008-b estiver bloqueado. (6) Não
commitar nada desta fase sem revisão humana explícita.
