# Fase 3L — Substituição do Override de Página por Elegibilidade Estrutural e Views Explícitas de Ordem

## A. Classificação

- **`AUTO_ZONE_ELIGIBILITY_VALIDATED`** — D10 é selecionada e reordenada **integralmente por
  evidência estrutural** (`reading_zones.assess_eligibility`: `zone_count=36`, `topology_transitions=1`,
  grafo acíclico) mais o oráculo de segurança diferencial (`same_lines`/`word_conserved`/
  `insertion_points_conserved`, todos `True`), **sem qualquer override de página/hash** —
  `LayoutOverrideSet.forces_zoned_reading_order` foi removido de `layout_overrides.py` e nenhum
  código o consulta mais; o teste dedicado
  `test_d10_activates_automatically_with_no_layout_override_present` roda a extração real com um
  `LayoutOverrideSet(overrides=[])` completamente vazio e reproduz exatamente a mesma ordem de
  leitura correta. Regeneração completa do corpus publicado (2008-b/2011/2021) produz **zero diff**
  (`git status --short data/questions` vazio). A varredura em shadow mode (seção J) confirma que o
  detector generaliza para fora do caso único em que foi construído (2021 D05, nunca publicado por
  2021 permanecer em modo `disabled`) sem nenhum falso positivo genuíno chegando a ser publicado em
  nenhum dos três corpora — Q50 é estruturalmente elegível mas corretamente rejeitada pelo próprio
  oráculo de segurança antes de qualquer publicação.
- **`RESIDUAL_LAYOUT_STABILIZED`** para D10 (mecanismo generalizado, sem regressão). **Ainda
  `RESIDUAL_LAYOUT_NOT_STABILIZED`** no agregado: 68/77 aprovadas na auditoria visual, 9/77
  reprovadas — número idêntico ao final da Fase 3K, nenhuma mudança neste ciclo (a fase não tocou
  nenhum outro defeito estrutural).
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido e reforçado: a arquitetura de separação de
  views (`PageLineViews`, Seção E) e o detector de elegibilidade puramente estrutural (Seção F)
  substituem o mecanismo documentalmente seguro-mas-não-automático da Fase 3K por um mecanismo
  seguro-e-automático, sem introduzir nenhuma dependência de ID de questão, número de página, hash de
  PDF ou coordenada literal em nenhum ponto de decisão central.
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase, como em todas as anteriores. Nunca
  `GENERALIZATION_SUCCESS`: a validação em modo `active` só ocorreu contra 2008-b; 2011 e 2021 foram
  exercidos apenas em modo `shadow` forçado (nunca ativados de fato), e o próprio registro de
  capacidades (Seção Q) documenta este limite explicitamente ao manter a classificação em G2, não G3.
- `NOT_READY_FOR_2008_ENGINEERING_TEST` (readiness) — confirmado sem alteração: 65/77 verified,
  12 needs_review, 38 blocker(s), maturity=provisional. `READY_FOR_LEGACY_LAYOUT_TEST` (2011,
  54/55) e `READY_FOR_2011` (2021, 40/40) também confirmados sem alteração.
- Nenhum commit, push, PR, merge ou tag foi criado por este agente. `master` não foi tocado.

## B. Estado Git

- Branch: `feat/enade-2008-cc-b-pilot` (confirmada no início e no fim da fase).
- `HEAD` = `89e4a47` — inalterado desde o início da Fase 3L (herdado do fim da Fase 3K/3J); nenhum
  commit novo foi criado por este agente durante a Fase 3L.
- `master` = `a5dfaab` — intocado.
- Nenhum merge, rebase ou cherry-pick em andamento. Working tree ao final: 14 arquivos modificados
  (3 manifestos + 8 arquivos-fonte + 3 arquivos de teste) + 1 arquivo de teste novo
  (`tests/test_assembler_zone_reorder.py`) — todos justificados nesta fase; nenhum arquivo
  inesperado; nenhum arquivo de scratch remanescente (`diag_wide_activation.py`,
  `diag_categorize.py`, `diag_shadow_scan.py` e `scripts/_phase3l_update_registry.py` foram todos
  criados e deletados durante a própria fase, nunca commitados).
- `data/questions` (2008/2011/2021): **zero diff** — `git status --short data/questions` vazio.
- 2011/2021 preservados (zero drift confirmado por `git status --short` e por verificação
  SHA-256 contra a baseline de 270 arquivos protegidos herdada da Fase 3I,
  `protected-288-baseline.sha256` — todas as entradas batem, nenhuma falha).

## C. Baseline da Fase 3K

Confirmado no início da fase: `pytest` = 638 passed (628 herdados + os 21 de `test_reading_zones.py`
mais os testes de annotations/content_assignment); auditoria visual = 68 passed / 9 failed / 0
not_performed; gold 2008 = 65 verified / 12 needs_review; readiness = `NOT_READY_FOR_2008_ENGINEERING_TEST`,
38 blockers; 2011/2021 byte-idênticos. D10 corrigida via override de página/hash
(`force_zoned_reading_order_page`), documentadamente seguro para D10 mas explicitamente não
generalizado (a própria Fase 3K admite isso na sua Seção Y). Todos os valores batem exatamente com o
estado declarado no início do PROMPT desta fase.

## D. Diagnóstico: por que o override não generaliza, e a regressão dos 66 arquivos

`diag_wide_activation.py` (script de diagnóstico, deletado após uso) substituiu
`zoned_reading_order_gate: false` por `true` incondicionalmente para todo o booklet 2008-b (sem
nenhum override de página), reextraindo para um diretório temporário. Resultado: 60/77 questões
publicadas (18 excluídas, uma delas — Q38 — espuriamente incluída por engano do próprio script de
diagnóstico, não do pipeline). `diag_categorize.py` (também deletado) comparou o multiset de palavras
de cada questão entre essa extração "wide activation" e o corpus publicado: **apenas D40** ficou na
categoria `reorder_only_or_serialization` (mudança pura de ordem, sem perda/ganho de palavras); todas
as outras 65 divergências caíram em `content_addition`/`content_loss_and_addition` — perda ou ganho
real de conteúdo, não apenas reordenação.

Causa raiz identificada por inspeção direta de `figures.py`: `_is_paragraph_continuation(index, lines)`
usa `lines[index-1]` (**posição na lista**) como proxy geométrico implícito para "a linha
imediatamente acima desta, visualmente" — válido apenas quando a página inteira compartilha **uma**
ordem consistente (a antiga divisão página-inteira left-then-right). Ao trocar a ordem de uma página
inteira para a ordem zoneada, esse proxy quebra silenciosamente para toda página cujo layout de
absorção de rótulos dependesse da posição antiga — mesmo em páginas que nada têm a ver com o defeito
de D10 (Q28, Q63, Q71, entre muitas outras). Esta é exatamente a razão pela qual a Fase 3K precisou
do override página/hash: não porque a elegibilidade de D10 fosse difícil de expressar estruturalmente,
mas porque **qualquer** reordenação de página-inteira vazava para consumidores geométricos que nunca
deveriam depender de ordem de leitura canônica.

## E. Separação de views: `figures.py`/`layout.py` nunca mais veem uma reordenação

A correção arquitetural (não um seletor mais estreito) foi isolar completamente os consumidores
geométricos da reordenação canônica:

- `figures.py::detect_visual_regions` **não aceita mais nenhum parâmetro de zoneamento** — sua
  chamada interna a `extract_page_lines` é sempre a ordem estável, geométrica, página-inteira
  (comentário explicativo adicionado no próprio call site: `_is_paragraph_continuation` depende de
  posição de lista como proxy de adjacência visual e nunca deve ver uma reordenação canônica).
- `layout.py::extract_page_lines`/`extract_document_lines` **não aceitam mais `zoned_reading_order_gate`
  de forma alguma** — revertidos ao comportamento exato pré-Fase-3K; o ramo de zoneamento e o import
  local de `reading_zones.zoned_reading_order` foram removidos inteiramente.
- `pipeline.py`: a chamada de `extract_document_lines` em nível de documento (que alimenta
  `detect_question_boundaries`) e a chamada de `extract_page_lines` da renderização de tabelas são
  **ambas sempre estáveis/não-zoneadas** agora.
- O **único** lugar em todo o pipeline onde `reading_zones` é consultado é dentro de
  `assembler.assemble_question`, via `_canonical_content_lines`, operando sobre o span **já fatiado**
  de uma questão — nunca uma página inteira, nunca alimentando detecção de fronteira ou detecção de
  figura.

Isso implementa a separação de views pedida pelo PROMPT (`source_order` — ordem bruta de extração
PyMuPDF; `geometry_order` — a ordem estável página-inteira que `layout.py`/`figures.py` sempre
recebem; `canonical_reading_order` — a saída, potencialmente reordenada, de
`_canonical_content_lines`; `question_local_order` — o span já fatiado sobre o qual essa reordenação
opera) não como um novo tipo de dado formal adicional, mas como uma garantia estrutural no próprio
grafo de chamadas: nenhuma função fora de `assembler.assemble_question` pode observar
`canonical_reading_order`.

## F. Elegibilidade estrutural: `ReadingZoneEligibility`/`assess_eligibility`

`reading_zones.assess_eligibility(zones, cycles) -> ReadingZoneEligibility` (novo em `reading_zones.py`)
substitui o override de página/hash por três critérios puramente estruturais, nunca por ID de
questão, número de página, hash de PDF ou coordenada literal:

1. `zone_count >= 2` — evidência de mais de uma janela vertical distinta na página.
2. `topology_transitions >= 1` — pelo menos uma mudança real de modo (`single_column` ↔
   `multi_column`) entre zonas adjacentes, ordenadas por `y_interval`.
3. `graph_acyclic` — o grafo de ordem de leitura (`ReadingOrderTrace.cycles`) não contém ciclo.

A primeira tentativa de implementação (apenas `zone_count >= 2`) foi **rejeitada por um falso
positivo real**: D40 produz 1 zona `multi_column` genuína seguida de ~42 zonas de uma linha só
("não reivindicadas"), satisfazendo trivialmente `zone_count >= 2` sem nenhuma transição de topologia
real — daí o critério explícito de `topology_transitions >= 1`, que rejeita corretamente essa forma
(ver `test_reading_zones.py::test_assess_eligibility_rejects_a_single_uniform_multi_column_zone`, que
reproduz exatamente essa forma).

## G. Fronteira de marcadores de item: por que D40/Q50 continuam intocadas

Mesmo com `assess_eligibility` mais rigoroso, uma segunda salvaguarda estrutural foi necessária:
`annotations.find_item_markers` (tornada pública nesta fase — antes `_find_item_markers`, privada,
usada apenas por `reattach_value_annotations`) localiza a sequência estritamente crescente A, B, C...
de marcadores de item/alternativa na ordem estável de um span. Quando **≥ 2** marcadores são
encontrados em sequência real, a reordenação só é considerada para o prefixo **antes** do primeiro
marcador (`eligible_prefix`); tudo a partir dali (`frozen_suffix`) — os próprios marcadores e
qualquer conteúdo/tabela/rótulo de diagrama depois deles (ex.: "Tabela I"/"Tabela II" de Q50) —
permanece completamente intocado, byte a byte, por identidade de objeto.

Uma única linha "A"-shaped que não é seguida de uma "B" real (o próprio caso de D10: "A partir da
leitura dos fragmentos...") **não conta** como sequência (`len(item_markers) < 2`) — D10 permanece
inteiramente elegível para reordenação. `test_assembler_zone_reorder.py::
test_a_lone_sentence_opening_a_does_not_count_as_a_marker_sequence` fixa esse comportamento.

## H. Oráculo de segurança diferencial

Mesmo um span estruturalmente elegível só é publicado reordenado se o oráculo de segurança
diferencial em `_canonical_content_lines` confirmar três invariantes entre a ordem candidata e a
ordem original (estável):

1. `same_lines` — multiset de identidades de linha idêntico (nenhuma linha perdida, duplicada ou
   inventada).
2. `word_conserved` — multiset de texto idêntico.
3. `insertion_points_conserved` — para **cada** `VisualRegion`/`DetectedTable` da página, o
   **conjunto** de linhas (por identidade) que precederiam seu ponto de inserção
   (`_find_region_insertion_index`) é idêntico entre as duas ordens.

O item 3 existe especificamente por causa de uma regressão real encontrada durante o desenvolvimento
desta fase (Seção K) e é deliberadamente baseado em **conjunto**, não em índice bruto nem em
identidade de uma única linha-âncora — ambas as alternativas mais simples foram tentadas e revertidas
por quebrarem D10 (ver Seção X).

## I. D10 depois da correção — sem override

`test_d10_activates_automatically_with_no_layout_override_present` roda a extração completa de
2008-b com `layout_overrides=LayoutOverrideSet(overrides=[])` — nenhuma entrada carregada, nem mesmo
a de D10. As mesmas asserções de ordem relativa exata de
`test_d10_reading_order_is_no_longer_scrambled` (herdadas da Fase 3K) passam identicamente: os três
artigos de jornal (com seus próprios títulos e citações), a prosa motivadora e a caixa de
"Observações" de duas colunas aparecem na ordem correta, terminando em
"motivadores. (valor: 10,0 pontos)", sem nenhuma contaminação de "QUESTÃO 11". A varredura de shadow
mode (Seção J) confirma independentemente: página 7 de 2008-b é elegível
(`zone_count=36, topology_transitions=1`) e passa nos três checks de segurança
(`same_lines=True, word_conserved=True, insertion_points_conserved=True`).

## J. Modo shadow — varredura completa do corpus (Seção 10 do PROMPT)

Um script de diagnóstico (`diag_shadow_scan.py`, deletado após uso) instrumentou
`assembler._canonical_content_lines` para registrar todo span estruturalmente elegível encontrado,
sem nunca publicar uma reordenação fora do modo real de cada extração, e rodou:

- **2008-b, modo real (`active`)**: extração completa para diretório temporário.
- **2011, `all-computing`, forçado para `shadow`** via `profile.model_copy(update=
  {"zoned_reading_order_mode": "shadow"})`.
- **2021, `ciencia-da-computacao-bacharelado`, forçado para `shadow`** via um wrapper fino em torno
  de `pipeline.assemble_question` (2021 não usa `structure_profile` — o modo é injetado diretamente
  nos kwargs da chamada).

Matriz de confusão resultante (D10 é o verdadeiro-positivo obrigatório do PROMPT):

| Span | Ano/curso | Elegível | `same_lines` | `word_conserved` | `insertion_points_conserved` | Seguro | Resultado |
|---|---|---|---|---|---|---|---|
| D10 (página 7) | 2008-b | Sim (36 zonas, 1 transição) | Sim | Sim | Sim | **Sim** | Ativado — verdadeiro positivo |
| Q50 (página 21) | 2008-b | Sim (34 zonas, 1 transição) | Sim | Sim | **Não** | Não | Rejeitado pelo oráculo — nota registrada, ordem original publicada |
| D05 (página 17) | 2021 cc-b | Sim (9 zonas, 1 transição) | Sim | Sim | Sim | Sim | **Nunca publicado** — 2021 permanece em `disabled` por perfil; shadow mode garante que a ordem original é sempre publicada |
| (todo o resto) | 2011 | Não — zero spans elegíveis em todo o corpus | — | — | — | — | Verdadeiro negativo |

2011 não produziu **nenhum** span estruturalmente elegível em todo o seu corpus — um verdadeiro
negativo forte, não apenas "nunca testado". 2021 D05 é uma evidência valiosa de generalização: o
detector encontrou, de forma totalmente independente, um segundo span genuinamente elegível **e**
seguro em um ano e curso completamente diferentes de onde foi construído — sem que isso jamais
arriscasse alterar a saída publicada de 2021 (que permanece com `zoned_reading_order_mode` no seu
padrão `disabled`).

## K. Q50 — o bug real e a correção correta

Mesmo após a fronteira de marcadores, Q50 ainda mostrava uma diferença de conteúdo: o parágrafo
introdutório de duas colunas era corretamente reordenado, mas o **ponto de inserção da própria
figura** (via `_find_region_insertion_index`, que varre por posição de lista até achar a primeira
linha com `y0 >= region.y0`) mudava, porque essa varredura depende de posição de lista, não apenas de
`y0` — uma reordenação zone-local pode colocar a mesma janela de `y0` em posições de lista diferentes
conforme a ordem "esquerda-então-direita" seja calculada por zona ou pela página inteira.

**Primeira tentativa de correção (errada)**: comparar o índice bruto (`int`) de
`_find_region_insertion_index` entre as duas ordens, ou comparar apenas a identidade de uma única
linha-âncora. Ambas as formas quebraram **D10** de volta para a ordem embaralhada, porque "inserir
antes de tudo" (a foto de D10, sempre primeira) tem literalmente uma identidade de primeira-linha
diferente em cada ordem, mesmo quando a decisão semântica (inserir antes de tudo) é a mesma.

**Correção correta**: comparar o **conjunto inteiro** de identidades de linha que precedem o ponto de
inserção (`frozenset(id(ln) for ln in ordered_lines[:idx])`) entre as duas ordens — para D10 ambos os
conjuntos são vazios (conservado, permitido); para Q50 o conjunto ganha linhas extras na ordem
candidata (não conservado, corretamente rejeitado). Isso corrigiu Q50 sem jamais reintroduzir a
regressão de D10.

Uma segunda regressão relacionada foi encontrada e corrigida na mesma janela: a nota de rejeição para
Q50 estava sendo adicionada à lista genérica `warnings`, que `validator.py` trata como "qualquer
warning → needs_review" — sinalizando incorretamente uma questão cujo texto publicado estava correto
e intocado. Corrigido adicionando o campo dedicado `ExtractedQuestion.zone_reorder_notes` (mesmo
padrão de `fragment_merges`/`value_annotations` das Fases 3H/3J: uma decisão de mecanismo
determinística — sucesso ou rejeição segura — nunca deve por si só penalizar uma questão) e removendo
o `warnings.extend(...)` do call site.

## L. D40/Q33 — confirmação de não-seleção nesta fase

D40 e Q33 são os dois outros membros da família `table-reading-order-scramble` (além de D10), já
confirmados na Fase 3K como pertencentes a mecanismos de causa raiz diferentes. Reconfirmado nesta
fase com evidência fresca: nem D40 nem Q33 aparecem em **nenhum** dos três achados da varredura em
shadow mode (Seção J) — a única evidência de D40 encontrada é sua própria forma de zona única
uniforme, explicitamente rejeitada por `assess_eligibility` (zero transições de topologia) mesmo
antes de a fronteira de marcadores entrar em jogo, per
`test_reading_zones.py::test_assess_eligibility_rejects_a_single_uniform_multi_column_zone`. Q33
nunca aparece em nenhuma zona elegível em toda a extração real de 2008-b. Nenhum dos dois foi forçado
a caber no mecanismo desta fase.

## M. Regressões obrigatórias — corpus completo, zero diff

Regeneração completa de `enade extract --year 2008 --course all-computing` (e reproduzida
independentemente duas vezes — Seção W) produz `git status --short data/questions` **vazio**: as
77 questões publicadas são byte-idênticas às já existentes, incluindo todas as antigamente-regredidas
pela tentativa "wide activation" (Q28, Q63, Q71, entre as demais da Seção D) e todas as protegidas por
Q68 (`height`/`font` gate), Q13 (`_reading_order_index`) e D60 (`annotations.py`). A suíte completa de
654 testes passa sem nenhuma falha.

## N. ContentAssignment, source coverage, alternativas e anotações

Como o corpus publicado é byte-idêntico ao estado no fim da Fase 3J/3K (zero diff confirmado na
Seção M), todas as garantias já verificadas nessas fases permanecem válidas sem necessidade de
regeneração: `data/manifests/content-assignment-2008-b.json` (2280 registros, 0 duplicados,
0 ausentes) não muda, pois nenhum conteúdo publicado mudou. Os grupos de alternativas
(`alternative_groups.py`, Fase 3I) e as anotações de valor (`annotations.py`, Fase 3J) operam sobre o
resultado **já reordenado** por `_canonical_content_lines` (que roda antes de
`reattach_value_annotations` no call site de `assemble_question` — ver `assembler.py` linhas
1531–1556) exatamente como antes desta fase para todo span onde a reordenação nunca ativa (99,9% do
corpus) e de forma estritamente equivalente para D10 (cujo conteúdo final é idêntico ao já produzido
pela Fase 3K, apenas por um caminho de decisão diferente).

## O. D09/D59/Q8/Q38/Q55 — preservação reconfirmada

`enade assess-readiness --year 2008 --course all-computing` (Seção V) reproduz exatamente os mesmos
38 blockers da Fase 3K, incluindo `d09-answer-standard-absent-from-source`,
`d59-answer-standard-image-only` (ambos bloqueados mecanicamente pela ausência do padrão de resposta
na fonte, não relacionados a este mecanismo) e as três exclusões
`q08-unstructured-image-alternatives`/`q38-.../q55-...` (questões nunca publicadas, mecanismo de
isolamento por questão do Phase 3A, também não relacionado). Nenhuma mudança.

## P. Estados de ativação e retirada do override de página/hash

`ExamStructureProfile.zoned_reading_order_mode: Literal["disabled", "shadow", "active"] = "disabled"`
substitui o `zoned_reading_order_gate: bool` da Fase 3K. O perfil **declara a capacidade disponível**
para um booklet e escolhe sua postura diagnóstica-vs-viva — nunca seleciona páginas específicas:

- `disabled` (padrão): `_canonical_content_lines` retorna a entrada sem qualquer computação de zona.
  2011 nunca define este campo (permanece `disabled`); 2021 não usa `structure_profile` (também
  `disabled` por ausência).
- `shadow`: zonas/elegibilidade/segurança são computadas normalmente, mas a ordem original é **sempre**
  publicada; qualquer achado elegível é registrado apenas em `zone_reorder_notes`. Usado nesta fase
  para varrer 2011/2021 sem nenhum risco de alterar sua saída (Seção J).
- `active`: publica a ordem candidata apenas quando elegibilidade **e** segurança concordam. 2008-b
  é o único booklet com `zoned_reading_order_mode: active` (`data/manifests/exam-structure-2008.yaml`).

O override de página/hash da Fase 3K (`force_zoned_reading_order_page`, D10, página 7) foi mantido no
manifesto (`data/manifests/layout-overrides.yaml`), nunca deletado, mas marcado `status: superseded`
com uma nota explicando que nenhum código o consulta mais —
`LayoutOverrideSet.forces_zoned_reading_order` foi removido inteiramente de `layout_overrides.py`.
Todas as 10 condições da Seção 12 do PROMPT foram atendidas: seleção automática (Seções F/G/I),
nenhuma dependência de ID/página/hash/coordenada (grep confirmando zero referências operacionais —
Seção X), 478/478 palavras preservadas (Seção I, herdado da Fase 3K, reconfirmado por
`word_conserved` no oráculo), sequência correta (asserções de ordem relativa, Seção I), grafo acíclico
(`assess_eligibility.graph_acyclic`), consumidores a jusante corretos (Seção E: `figures.py` nunca vê
a reordenação), 2011/2021 byte-idênticos (Seção B).

## Q. Capability registry

`data/manifests/extraction-capabilities.json`: entrada `zoned_reading_order` (introduzida na Fase 3K)
atualizada para refletir o mecanismo de duas etapas (fronteira de marcadores + elegibilidade+segurança),
o novo parâmetro `zoned_reading_order_mode`, o status `superseded` do override antigo, os novos casos
reais (D10 sem override, 2021 D05 em shadow) e os casos protegidos (Q50 rejeitada pelo oráculo,
D40/Q33 não selecionados, todo o resto do corpus 2008-b/2011/2021). Classificação mantida em **G2**,
não elevada a G3: a seleção de página **dentro** de um booklet já ativado é agora inteiramente
automática/estrutural (uma propriedade de formato G3), mas a ativação ainda exige uma declaração de
perfil explícita por booklet, e o mecanismo só foi exercitado em modo `active` contra **um** booklet
(2008-b) — 2011/2021 apenas em `shadow` forçado, nunca `active`. Consistente com a regra permanente do
projeto ("nunca reivindicar G4 sem validação cega contra um exame não visto"), a promoção a G3 deve
esperar por uma extração `active` real contra um booklet que este projeto ainda não usou para
construir o mecanismo. A entrada `local_reading_order` (ainda `not_implemented`) foi corrigida para
não listar mais D10/D60 como pendentes (ambos resolvidos por mecanismos nomeados nas Fases 3J/3K/3L),
mantendo apenas D40/Q33 como genuinamente pertencentes a essa categoria.

## R. Ausência de IA

`tests/test_generalization_architecture.py` (9 testes, incluindo o teste que verifica que nenhuma
`trigger_features` do registro cita um ID de questão específico) roda limpo. Nenhuma dependência de
rede, LLM, VLM ou IA generativa foi adicionada em nenhum arquivo desta fase — `reading_zones.py`,
`annotations.py` e `_canonical_content_lines` são puramente geométricos/estruturais
(`graphlib.TopologicalSorter`, regex, comparação de conjuntos).

## S. Proteção de 2011

`zoned_reading_order_mode` nunca é definido em `data/manifests/exam-structure-2011.yaml` (grep
confirma zero ocorrências) — permanece `disabled` pelo padrão do próprio campo. A varredura em shadow
mode (Seção J) confirma adicionalmente que **nenhum** span de 2011 é sequer estruturalmente elegível,
um verdadeiro negativo mais forte do que "nunca testado". `git status --short` e a verificação
SHA-256 contra a baseline de 270 arquivos protegidos confirmam zero drift.

## T. Proteção de 2021

2021 nunca usa `structure_profile` (extração por `course=`), então `zoned_reading_order_mode` resolve
para `disabled` por ausência de perfil (`pipeline.py`: `structure_profile.zoned_reading_order_mode if
structure_profile is not None else "disabled"`). A varredura forçada em shadow mode (Seção J)
encontrou um span genuinamente elegível e seguro (D05), prova de que o detector generaliza — mas essa
descoberta nunca poderia ter sido publicada mesmo se não tivesse sido forçada para shadow, porque o
perfil de 2021 nunca ativa o modo `active`. `git status --short` e a verificação SHA-256 confirmam
zero drift.

## U. Testes

- `tests/test_reading_zones.py`: 21 → 26 testes (+5: `test_assess_eligibility_accepts_a_genuine_topology_change`,
  `test_assess_eligibility_rejects_a_single_uniform_multi_column_zone`,
  `test_assess_eligibility_rejects_a_single_zone_page`,
  `test_assess_eligibility_rejects_when_the_graph_has_a_cycle`,
  `test_assess_eligibility_on_no_zones_is_not_eligible`).
- `tests/test_assembler_zone_reorder.py` (novo, 10 testes): modo `disabled` é no-op puro; ativação
  automática de uma página com a forma de D10 (sem nota); mesma página em modo `shadow` nunca muda a
  saída; fronteira de marcadores reais congela o marcador e tudo depois dele; uma única "A" sem "B"
  não conta como sequência; uma página de duas colunas uniforme (forma de D40) não é elegível e não
  produz nota; um candidato elegível rejeitado pelo oráculo de segurança (forma de Q50) publica a
  ordem original e registra exatamente uma nota; a nota nunca é surfaceada como warning (verificação
  de forma do contrato de retorno); reordenação nunca cruza fronteira de página; teste metamórfico —
  a mesma forma estrutural decide identicamente entre duas chamadas com objetos `Line` totalmente
  novos (nenhuma identidade compartilhada — equivalente a "o hash do arquivo-fonte mudou sem nenhuma
  mudança estrutural").
- `tests/test_extraction_pipeline_2008.py`: +1 teste
  (`test_d10_activates_automatically_with_no_layout_override_present`) contra a extração real,
  usando um `LayoutOverrideSet(overrides=[])` totalmente vazio.
- Total: 638 → 654 testes (+16), todos passando (`pytest -q` → `654 passed`).

## V. Quality gates

- `ruff check .`: All checks passed.
- `ruff format --check .`: 2 arquivos com formatação puramente cosmética corrigidos
  (`assembler.py`, `reading_zones.py`) e reconfirmados limpos.
- `mypy src/enade`: Success, 58 source files.
- `enade validate-schema`: 13/13.
- `enade validate-manifest`: 0 warnings.
- `enade audit-extraction --questions-dir data/questions/2008`: 77/77 OK.
- `enade verify-gold`/`assess-readiness`:
  - 2008 (`all-computing`): `verify-gold` OK (77/77, maturity=provisional, 65 verified/12 needs_review);
    `assess-readiness` → `NOT_READY_FOR_2008_ENGINEERING_TEST`, 65/77 verified, 12 needs_review,
    visual audit 68/9/0, 38 blocker(s) — idêntico à Fase 3K.
  - 2011 (`all-computing`): `verify-gold` OK (55/55, maturity=validated, 54/1); `assess-readiness` →
    `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1 blocker não-estrutural (Q34) — idêntico à Fase 3K.
  - 2021 (`ciencia-da-computacao-bacharelado`): `verify-gold` OK (40/40, maturity=validated);
    `assess-readiness` → `READY_FOR_2011`, 40/40, 0 blockers — idêntico à Fase 3K.

## W. Reprodutibilidade

Duas execuções completas e independentes de `enade extract --year 2008 --course all-computing`
(run A, run B) para diretórios de saída isolados sob um diretório temporário (nunca o corpus real):
`diff -rq run_a/questions/2008/all-computing run_b/questions/2008/all-computing` → idêntico byte a
byte (exit 0). `diff -rq run_a/questions/2008/all-computing data/questions/2008/all-computing` →
idêntico byte a byte ao corpus publicado (exit 0).

## X. Bugs encontrados e tentativas revertidas

1. **Falso positivo D40/D20 com elegibilidade ingênua (`zone_count >= 2` sozinho)**: rejeitado por
   requerer também `topology_transitions >= 1` (Seção F).
2. **Falso positivo Q50/D40 mesmo com `assess_eligibility` mais rigoroso, por a reordenação alcançar
   a própria sequência de marcadores/alternativas**: corrigido pela fronteira de marcadores
   (`find_item_markers`, Seção G).
3. **Regressão de D10 causada pela primeira tentativa de checagem de ponto de inserção (índice bruto
   ou identidade de âncora única)**: revertida em favor da comparação por conjunto de identidades
   (Seção K).
4. **Nota de rejeição de Q50 vazando para `warnings` e sinalizando `needs_review` incorretamente**:
   corrigida pelo campo dedicado `zone_reorder_notes`, nunca mesclado a `warnings` (Seção K).
5. **Falso positivo do próprio teste de generalização (`test_capability_registry_never_cites_a_question_id_as_a_trigger`)**:
   o texto de `trigger_features` da entrada `zoned_reading_order`, ao **negar** explicitamente que o
   mecanismo usa "question ID" como seletor, acidentalmente citava a própria frase proibida como
   substring. Corrigido reescrevendo para "número de página, número de questão, hash de PDF..." sem
   alterar o significado. Nenhum código de produção foi afetado — puramente um ajuste de texto no
   manifesto.
6. **Confusão de caminho Windows/git-bash em `diag_shadow_scan.py`**: um import inicial equivocado
   (`enade.extraction.models.CourseCode`, módulo inexistente) e um nome de arquivo 2021 incorreto
   (`1_prova.pdf` em vez de `b1_prova.pdf`) foram corrigidos por inspeção direta do corpus e dos
   testes de integração existentes antes da varredura em shadow mode.

## Y. Arquivos e Git final

- Modificados (14): `data/manifests/exam-structure-2008.yaml`, `data/manifests/extraction-capabilities.json`,
  `data/manifests/layout-overrides.yaml`, `src/enade/extraction/annotations.py`,
  `src/enade/extraction/assembler.py`, `src/enade/extraction/exam_profile.py`,
  `src/enade/extraction/figures.py`, `src/enade/extraction/layout.py`,
  `src/enade/extraction/layout_overrides.py`, `src/enade/extraction/pipeline.py`,
  `src/enade/extraction/reading_zones.py`, `tests/test_annotations.py`,
  `tests/test_extraction_pipeline_2008.py`, `tests/test_reading_zones.py`.
- Novos (1): `tests/test_assembler_zone_reorder.py`.
- `data/questions/**`: **nenhuma mudança** (77 questões 2008-b, 55 questões 2011, 40 questões 2021 —
  todas byte-idênticas ao estado pré-Fase-3L).
- Scratch criados e deletados durante a fase (nunca commitados, nenhum remanescente):
  `diag_wide_activation.py`, `diag_categorize.py`, `diag_shadow_scan.py`,
  `scripts/_phase3l_update_registry.py`.
- `git status --short` final: 14 modificados + 1 novo, exatamente como listado acima; nenhum arquivo
  inesperado; `data/questions` vazio.
- Branch `feat/enade-2008-cc-b-pilot`, `HEAD=89e4a47`, `master=a5dfaab` — ambos intocados por este
  agente. Nenhum commit, push, PR, merge ou tag criado.

## Recomendação

O mecanismo de elegibilidade estrutural + oráculo de segurança diferencial está pronto para ser
commitado como está: D10 ativa automaticamente sem qualquer override de página/hash, zero regressão
em todo o corpus publicado (2008-b/2011/2021), 654/654 testes passando, e a arquitetura de separação
de views garante que nenhuma reordenação canônica futura pode vazar para `figures.py`/detecção de
fronteira/detecção de tabela por acidente. A classificação G2 (não G3) no registro de capacidades
deve ser mantida até que um booklet real, ainda não usado para construir este mecanismo, seja
extraído em modo `active` (não apenas `shadow`) com auditoria limpa — a promoção prematura a G3 ou
G4 violaria a própria regra permanente do projeto contra reivindicar generalização sem validação cega.
D40 e Q33 permanecem genuinamente fora do escopo deste mecanismo e devem ser tratados por uma fase
futura dedicada à sua própria família de causa raiz (`local_reading_order`, ainda `not_implemented`).
Nenhuma ação além da revisão e eventual commit pelo usuário é necessária desta fase.
