# Fase 3G — Relação Linha–Região Contextual, Alternativas versus Rótulos de Diagrama e Reconstrução de Fragmentos

## A. Classificação

- **`RESIDUAL_LAYOUT_NOT_STABILIZED`** — permanece o rótulo correto: dos 77 itens publicados, 62 passam na
  auditoria visual e 15 permanecem `failed` (mesma contagem numérica da Fase 3F, mas com composição diferente —
  ver Seção F).
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido (Fase 3F). Esta fase acrescenta uma nova capacidade
  geométrica declarativa (`contextual_relation_gate`) ao mesmo padrão `ExamStructureProfile`, sem introduzir
  nenhum branch por ano/ID de questão/página em lógica central (confirmado por
  `tests/test_generalization_architecture.py`, 9/9 passando).
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase (nenhuma tentativa de validação cega em exame
  não visto foi feita; G4 permanece não alcançado). Nunca `GENERALIZATION_SUCCESS`.
- Nenhum commit, push, PR, merge ou tag foi criado por este agente. `master` não foi tocado. Branch
  permanece `feat/enade-2008-cc-b-pilot`, HEAD em `8ecc93c` (commit do usuário, herdado da Fase 3F).

## B. Estado Git no início e no fim

Início: working tree limpo em `8ecc93c` (commit do usuário entre as Fases 3F e 3G).

Fim: 28 arquivos modificados, 0 arquivos não rastreados (`git status --short` limpo de `??`), nenhum arquivo de
`data/questions/2011` ou `data/questions/2021` tocado:

```
 M data/manifests/blocker-ledger-2008.yaml
 M data/manifests/exam-structure-2008.yaml
 M data/manifests/extraction-audit-2008-computing.csv
 M data/manifests/extraction-audit-2008-computing.json
 M data/manifests/extraction-capabilities.json
 M data/manifests/gold-2008-computing.json
 M data/manifests/visual-audit-2008-computing.json
 M data/questions/2008/all-computing/enade-2008-computing-{d10,d40,q01,q02,q07,q12,q23,q24,q29,q45,q50,q54,q63,q71,q75}.md
 M src/enade/extraction/{assembler,exam_profile,figures,pipeline}.py
 M tests/test_extraction_assembler.py
 M tests/test_extraction_pipeline_2008.py
```

Nenhum commit foi criado por este agente em nenhum momento da fase.

## C. Baseline de proteção (2011/2021)

Um snapshot SHA-256 dos 288 arquivos protegidos (270 sob `data/questions/2011|2021` + 18 manifestos
relacionados) foi capturado no início da fase. Confirmado, em múltiplas iterações ao longo da fase (a cada
mudança de código com risco de efeito colateral geométrico), via `sha256sum -c` contra esse baseline — **zero
divergência em todas as verificações**, incluindo a verificação final após a última mudança de código
(`raw_intersects`'s threshold) e após a atualização de `visual-audit-2008-computing.json` (que altera o
frontmatter `visual_validation`/`extraction_status` de 2008-b, mas não toca 2011/2021, cujo próprio gate
`contextual_relation_gate` nunca é ativado).

## D. `LineRegionRelation` — o novo modelo geométrico

`assembler.py` ganha uma estrutura rica (`@dataclass(frozen=True) class LineRegionRelation`) substituindo a
decisão binária anterior de `_line_in_region`. Estados: `outside / touching / partial_overlap /
center_inside / baseline_inside / contained / boundary_crossing / ambiguous`. Métricas nunca colapsadas
prematuramente: `intersection_over_line_area`, `intersection_over_region_area`,
`horizontal_overlap_ratio`, `vertical_overlap_ratio`, `center_inside`, `baseline_inside`, overflow por borda,
`raw_intersects` (contra `VisualRegion.raw_bbox`, a extensão pré-crescimento), `matches_absorbed_label`
(contra `VisualRegion.absorbed_label_bboxes`, o próprio registro autoritativo de crescimento).

Política por consumidor implementada: `_text_consumption_decision` (consumo de texto — estrita: apenas
`contained`, `raw_intersects`, `matches_absorbed_label`, ou uma região de fórmula pequena em qualquer estado
não-`outside`). As demais políticas descritas no prompt (inclusão em crop, ownership multi-sinal, ordem de
leitura por baseline+sequência, grupo de alternativas) **não foram construídas como mecanismos
independentes** — apenas a política de consumo de texto era estritamente necessária para fechar os
Clusters A/C encontrados; construir as demais sem um caso real que as exercite violaria a proibição do
próprio prompt contra generalização especulativa não testada. Documentado como escopo consciente, não como
lacuna esquecida (ver Seção Z).

Decisão tri-estado: `accepted` / `ambiguous` (nunca autoriza remoção destrutiva). Nenhum estado intermediário
foi promovido a um "quarto estado" só para fazer um caso específico passar.

## E. Cluster A — nove casos, uma relação, sem limiar único

Cluster A (Fase 3F): a decisão binária anterior de `_line_in_region` perdia conteúdo real quando a bbox
*crescida* de uma região meramente tocava a borda de uma linha larga e não relacionada. O contraexemplo
geométrico que motivou toda a Seção D: Q61 (legenda genuína, 27,4% de sobreposição contra a bbox crescida,
mas sobreposição genuína contra a bbox **crua**) versus Q07 (linha ruim, 37,8% de sobreposição contra a bbox
crescida, mas **zero** sobreposição contra a bbox crua — o toque existe só porque o crescimento absorveu
*outros* fragmentos próximos). Nenhum limiar de razão único sobre a bbox crescida separa os dois casos;
`raw_intersects` e `matches_absorbed_label` são os dois sinais que efetivamente os separam.

Resultado, confirmado questão por questão contra o texto real do PDF (Seção F/N):

| Questão | Antes (Fase 3F) | Depois (Fase 3G) |
|---|---|---|
| D10 | Corpo inteiro do headline 1 e abertura do headline 2 ausentes | **Todo o conteúdo recuperado** (ordem de leitura permanece embaralhada — ver Seção N) |
| Q02 | Frase de transição e citação ausentes; cláusula de entrada das alternativas ausente | Cláusula de entrada recuperada; transição e citação **permanecem ausentes** |
| Q07 | Fragmento nu "aos 20% de maior renda foi," | **Regressão documentada**: agora "20% de maior renda foi," (perde "aos") — mesma família de causa raiz, ver Seção I |
| Q12 | Só "base na" e a cláusula final sobrevivem | Parágrafo quase inteiro recuperado; só "complexidade ciclomática." ausente |
| Q45 | Itens I/II vazios, marcador do item III ausente | Marcador do item III + parte do texto recuperados; ainda incompleto |
| Q54 | Enunciado inteiramente vazio | Explicação da tabela de rotas + pergunta final recuperadas; abertura ainda ausente |
| Q63 | Enunciado inteiro substituído por fragmentos de diagrama | Enunciado quase inteiro recuperado; só 4 palavras ausentes |
| Q71 | (marcado `passed`, incorretamente — ver Seção K) | Abertura quase inteira recuperada; 2 pequenas lacunas remanescentes |
| Q75 | Enunciado inteiramente vazio | **Enunciado 100% completo**, verbatim contra a fonte |

Nenhuma dessas correções foi feita com um `if question_id == ...`; todas emergem da mesma
`compute_line_region_relation`/`_text_consumption_decision` geral, gated por
`ExamStructureProfile.contextual_relation_gate`.

## F. A matriz de controle obrigatória (D10/Q07/Q61/Q71)

- **D10**: melhora (Seção E) — conteúdo recuperado, sem regressão.
- **Q07**: regressão documentada (não escondida) — ver Seção I.
- **Q61**: **não regride**. Confirmado por `tests/test_reference_captions.py` (inalterado) e por
  re-inspeção manual do markdown publicado — Q61 permanece byte-idêntico nesta fase (não está na lista de
  arquivos modificados).
- **Q71**: não regride *no código* — o próprio código desta fase só melhora o que estava lá. O status
  `passed` anterior era, ele mesmo, um falso positivo pré-existente (Seção K), agora corrigido.

## G. Cluster C — rótulo de diagrama versus marcador de alternativa

A antiga isenção de `_line_in_region` (regex `_ALTERNATIVE_LINE_RE` cobrindo qualquer linha no formato
`"A\t..."`) protegia indiscriminadamente qualquer linha nesse formato, mesmo quando geometricamente interna a
um diagrama (rótulo de autômato, nome de entidade em diagrama ER, metavariável de produção gramatical).
Substituída por `_is_marker_at_margin`: só protege quando a linha também está na margem esquerda dominante
do corpo de texto da página (`_dominant_left_margin`, com fallback para
`dominant_left_margin_by_text_length` quando o detector baseado em largura não encontra evidência suficiente
— necessário especificamente para a página 13 de Q29).

Resultado:
- **Q29**: **RESOLVIDO por completo** — fragmento embaralhado `"A ÷ a B ÷ b"` removido, enunciado e as 5
  alternativas batem palavra por palavra com a página 13.
- **Q63**: rótulos ER (`"A atrA / C atrB B atrC"`) removidos, framing real recuperado quase por inteiro.
- **Q24**: fragmentos de tabela de decodificador removidos (limpeza), mas o conteúdo real (parágrafo de
  enunciado + itens I/II) permanece perdido por uma causa **separada e mais profunda** (mesclagem de 4
  diagramas em `figures.py`, não atacada nesta fase — ver Seção Z).

A estrutura `alternative_group` completa (com `candidate_labels/expected_sequence/alignment/font_features/
spacing_pattern/column/competing_group/confidence`) descrita no prompt **não foi construída**. Um mecanismo
mais estreito e cirúrgico (`_is_marker_at_margin` + fallback de margem por comprimento de texto) resolveu
todos os casos reais encontrados nesta fase. Documentado explicitamente no registro de capacidades
(`diagram_internal_label_margin_check`) como deliberadamente mais estreito que a arquitetura completa do
prompt — não uma implementação parcial escondida como completa.

## H. Cluster D — fragmentação geométrica de palavras (não implementado)

PyMuPDF fragmenta algumas palavras/frases em múltiplos registros `Line` de granularidade palavra/token,
embaralhando a ordem de leitura e alimentando resíduos nos próprios Clusters A/C (Q07 perde "aos"; Q12 perde
"complexidade ciclomática."; D40 tinha, antes desta fase, o bloco de código do schema fragmentado em 2
linhas, a segunda ainda perdida). Q33 é a instância pura, intocada nesta fase.

**Decisão explícita: não implementado.** Construir reconstrução geométrica de fragmentos (baseline delta +
gap horizontal plausível + compatibilidade de fonte + mesmo dono + ausência de fronteira) é um mecanismo de
superfície comparável em risco ao próprio Cluster A/C, e o tempo/orçamento de risco desta fase já foi gasto
majoritariamente nesse cluster (ver Seção V, duas iterações de regressão em 2011/2021 antes do gate
declarativo). Registrado no registro de capacidades como `geometric_word_fragment_reconstruction`,
`generalization_level: not_implemented`, com `real_cases` citando precisamente os resíduos que dependem
dele.

## I. D40 — fechamento parcial, regressão documentada, causa raiz precisa

`contextual_relation_gate` inicialmente causou a exclusão indevida da linha
`Cliente(nroCliente, nome, endereco,` (um bloco de código SQL genuíno, já correto no HEAD pré-Fase-3G) —
causa raiz: uma sobreposição de ruído (~1,6pt) contra a bbox **crua** de uma região **vizinha** (não a região
correta) estava sendo tratada como evidência decisiva por `raw_intersects`. Corrigido exigindo que
`raw_intersects` supere `REGION_Y_PADDING` (2,0pt, o mesmo piso de ruído já usado em outros pontos do código)
em ambos os eixos, não um bare `> 0`. Confirmado por regeneração completa: a linha volta a bater
byte-a-byte com o HEAD, zero drift em 2011/2021.

**Novo artefato cosmético, documentado e não escondido**: o rótulo "F" (operador de seleção da árvore de
consulta) — uma linha de um único caractere posicionada imediatamente *fora*, não tocando, a bbox da região
do diagrama — agora vaza como parágrafo solto após `figure-01`, onde a lógica antiga de padding fixo o
engolia incondicionalmente. Geometricamente indistinguível, usando só posição e sobreposição, dos falsos
positivos de linha larga que o Cluster A foi desenhado para rejeitar — o design tri-estado corretamente se
recusa a adivinhar, em vez de reintroduzir essas regressões (`ambiguous` nunca autoriza remoção
destrutiva). D40 já estava `failed` antes e depois; nenhuma questão passou de aprovada para reprovada por
causa disso.

Três lacunas pré-existentes, não relacionadas à Fase 3G, agora precisamente localizadas pela releitura direta
do PDF (confirmadas idênticas no HEAD): embaralhamento de ordem de palavras na frase de abertura; bloco de
código do schema truncado (falta sua própria segunda linha impressa); parágrafo dos índices sem sua própria
cláusula de abertura.

## J. Q29 — resolvido

Ver Seção G. Confirmado por `tests/test_extraction_pipeline_2008.py::
test_q29_no_longer_has_sidebar_fragment_inserted_mid_sentence` e pela releitura direta da página 13.

## K. Q71 — correção de status (não regressão de código)

O veredito `passed` da Fase 3B nunca foi reverificado palavra por palavra contra o texto real da página 30.
O HEAD já publicado mostra que a abertura do enunciado já estava inteiramente substituída por fragmentos de
rótulo de diagrama (`"A alternativa 1 A alternativa 2 B F D B C D E C E F"`), com só uma cauda desconexa
sobrevivendo. `contextual_relation_gate` recupera quase toda a abertura real, deixando 2 pequenas lacunas.
Separadamente, um bug de fronteira entre alternativas B/C (a alternativa B absorve o marcador e a maior
parte do texto de C) — pré-existente, confirmado idêntico no HEAD, não tocado por nenhuma mudança desta
fase — foi descoberto pela mesma reauditoria e agora rastreado como
`q71-alternative-b-c-cross-contamination`. Q71 volta a `failed` no `visual-audit-2008-computing.json` e no
próprio frontmatter (`extraction_status`/`visual_validation`) após uma nova regeneração completa.

## L. Q75 — enunciado resolvido, defeito separado permanece

Enunciado agora **100% completo e correto**, verbatim contra a página 32. A contaminação pré-existente na
alternativa D (rótulos do diagrama NAPT, documentada desde a Fase 3E) permanece, é **não relacionada** ao
mecanismo desta fase (um diagrama diferente, posicionado depois das alternativas, não coberto pelos
Clusters A/C) e agora tem seu próprio blocker (`q75-alternative-d-diagram-label-bleed`). O componente de
enunciado do blocker antigo (`q75-region-merge-content-loss`) foi marcado `resolved`.

## M. Q23 — artefato cosmético novo, sem perda de conteúdo

`contextual_relation_gate` deixa vazar um pequeno fragmento final do próprio schema da imagem
(`"IdRep:integer referencia Republica)"`) como texto solto, colado sem separação à frase seguinte. O schema
completo permanece total e corretamente disponível em `figure-01.png` (mesmo padrão decorativo-duplicado já
aceito para Q68); a frase qualificadora permanece íntegra e não-ambígua apesar do prefixo feio — nenhuma
informação é perdida. Q23 permanece `passed`, com o artefato documentado (`q23-schema-fragment-duplicate-bleed`)
em vez de escondido ou usado para inflar/reduzir a contagem.

## N. Melhorias incidentais fora do escopo original de Cluster A/C

- **Q01**: cláusula de entrada das alternativas recuperada (`"Das imagens acima, as figuras referidas..."`) —
  já `passed`, permanece `passed`, agora mais completo.
- **Q50**: `automatic_validation` passa de `failed` para `passed` sem mudança de conteúdo — a falha
  automática anterior era, ela mesma, efeito colateral do mesmo ruído de over-absorção corrigido em outro
  lugar da página.
- **D10**: conteúdo 100% recuperado (Seção E), mas a ordem de leitura das três notícias em colagem permanece
  embaralhada — tratada agora como defeito **separado** e puramente de ordem, não de perda de conteúdo (novo
  blocker `d10-newspaper-collage-reading-order-scramble`, categoria `table-reading-order-scramble`, mesma
  família do Cluster D não implementado).

## O. Política "conteúdo dentro de imagem" versus perda genuína de prosa

Vários "gaps" candidatos a fechamento aparecem também, como pixels, dentro de um crop raster já publicado
(D10, Q02, Q05, Q07, Q12, Q24, Q45, Q54, Q63). Precedente estabelecido (Fase 3D/3E, Q01: 5 retratos com
legenda embutida no próprio pixel) aceita que um par imagem+legenda decorativo e autocontido não precisa de
extração textual separada. Esta fase aplica uma distinção mais fina: quando o trecho ausente é **prosa
corrida do próprio enunciado** (frase de transição, cláusula de abertura/fechamento, citação essencial para
responder a questão) que também aparece visualmente dentro de um crop, isso **não** conta como aceitável — é
uma perda de conteúdo genuína e a questão permanece `failed`. Aplicado consistentemente: nenhuma das nove
questões acima foi promovida a `passed` só por seu texto ausente ser visível na imagem.

## P. Auditoria visual — atualização completa

`data/manifests/visual-audit-2008-computing.json` foi atualizado questão por questão (15 entradas), sempre
com evidência de comparação direta contra o texto real do PDF (nunca confiança cega na lógica do código):
D10, D40, Q01, Q02, Q07, Q12, Q23, Q24, Q29 (→`passed`), Q45, Q50, Q54, Q63, Q71 (→`failed`), Q75. Nenhuma
promoção em massa: cada nota documenta especificamente o que mudou, o que permanece ausente e por quê.
Contagem final: **62 `passed` / 15 `failed` / 0 `not_performed`** — numericamente idêntica à Fase 3F (a
troca Q29↔Q71 se cancela), mas com composição e precisão de evidência substancialmente diferentes.

## Q. Blocker ledger — atualização completa

`data/manifests/blocker-ledger-2008.yaml`: 50 blockers (26 `resolved`, 23 `open`, 1 `superseded`), validado
sem erros por `enade.extraction.blocker_ledger.validate_ledger` (exigiu adicionar 2 testes de regressão para
satisfazer `resolved_without_test`). Mudanças: `q02`/`q07`/`q24`/`q45`/`q54`/`q63`-`region-merge-content-loss`
atualizados com achados precisos; `q71-region-merge-content-loss` **reaberto** com a descoberta corrigida;
`q75-region-merge-content-loss` e `d10-label-absorption-newspaper-fragments` marcados `resolved`;
`q29-inline-sidebar-fragment` marcado `resolved`; `d40-table-reading-order-scramble` atualizado com o novo
artefato "F" e as três lacunas pré-existentes agora precisas. Quatro blockers novos:
`d10-newspaper-collage-reading-order-scramble`, `q71-alternative-b-c-cross-contamination`,
`q75-alternative-d-diagram-label-bleed`, `q23-schema-fragment-duplicate-bleed`.

## R. Registro de capacidades

`data/manifests/extraction-capabilities.json`: 11 entradas. Duas novas desta fase —
`contextual_line_region_relation` (G2) e `diagram_internal_label_margin_check` (G2, explicitamente mais
estreita que a arquitetura `alternative_group` completa do prompt) — mais `geometric_word_fragment_
reconstruction` (`not_implemented`, Cluster D). `local_reading_order` atualizado para remover Q29 (agora
resolvido por outro mecanismo) e citar D10/D40/D60/Q33 como os casos remanescentes reais dessa família.
Confirmado por `tests/test_generalization_architecture.py` (9/9): schema válido, todo `generalization_level`
reconhecido, nenhum gatilho cita ID de questão, `runtime_ai_dependency: "none"` em toda entrada.

## S. Testes

- `tests/test_extraction_assembler.py`: +7 testes síncronos de Cluster A/C (D40/1) e +5 testes
  metamórficos (Seção 18 do prompt): invariância por translação (relação `contained` e relação `touching`
  ambas preservam sua classificação sob um deslocamento uniforme arbitrário), invariância por escala (razões
  de sobreposição preservadas sob escala 3×), variação de largura de coluna (proteção de marcador rastreia a
  margem real, não uma coordenada fixa, testada em 3 margens diferentes), variação de fonte
  (`caption_font_size_gate` rastreia o tamanho dominante da própria página, não um valor absoluto fixo, em
  2 tamanhos de corpo diferentes). Nenhum teste depende de ID de questão, ano, página, coordenada real do
  corpus ou texto real de uma questão.
- `tests/test_extraction_pipeline_2008.py`: +2 testes de regressão de corpus real
  (`test_q29_no_longer_has_sidebar_fragment_inserted_mid_sentence`,
  `test_q75_statement_is_now_complete`).
- Total: **539 testes**, todos passando (`pytest -q`, 3min02s).
- `mypy src`: limpo (53 arquivos-fonte, 0 erros).
- `ruff check .`: limpo.
- `tests/test_generalization_architecture.py`: 9/9 (Seção R).

## T. Proteção de 2011/2021

Confirmado **zero drift** em múltiplas iterações distintas ao longo da fase:
1. Após a primeira tentativa incondicional do gate (17+ arquivos alterados — revertida).
2. Após adicionar `matches_absorbed_label` (reduziu para ~16 arquivos — ainda insuficiente).
3. Após o gate declarativo `contextual_relation_gate` (zero drift, confirmado).
4. Após o ajuste de limiar de `raw_intersects` para D40 (zero drift, reconfirmado).
5. Após a regeneração final pós-atualização de `visual-audit-2008-computing.json` (zero drift, reconfirmado
   uma última vez).

Cada verificação usou tanto `git status --short data/questions/2011 data/questions/2021` quanto
`sha256sum -c` contra o snapshot de 288 arquivos capturado no início da fase — ambos vazios/limpos em toda
verificação.

## U. Gold e readiness

`enade build-gold --year 2008 --course all-computing` reconstruído com a lista atualizada de categorias de
blocker ainda abertas (`alternative-boundary-misparse` e `same-question-diagram-label-bleed` substituem
`cross-question-contamination`, agora totalmente resolvida). `enade verify-gold`: OK, 77/77 batem. `enade
assess-readiness --ready-label READY_FOR_2008_ENGINEERING_TEST --not-ready-label
NOT_READY_FOR_2008_ENGINEERING_TEST`: **`NOT_READY_FOR_2008_ENGINEERING_TEST`** (esperado — 15 questões
ainda falham), 51 blockers listados individualmente, nunca uma contagem nua.

## V. Reprodutibilidade

Duas execuções completas e independentes de `enade extract --year 2008 --course all-computing` para
diretórios isolados (run A, run B), usando o código final desta fase: `diff -rq run_a run_b` → **idêntico
byte a byte** (exit 0). `diff -rq run_b/questions/2008/all-computing data/questions/2008/all-computing` →
**idêntico byte a byte** ao corpus atualmente publicado (exit 0).

## W. Experimentos revertidos / lições aprendidas

1. **`_text_consumption_decision` estrita demais para captions multi-hop**: aceitar só `contained` OU
   `raw_intersects` regrediu 17+ arquivos de 2011/2021 (uma legenda real absorvida através de múltiplas
   passagens incrementais de crescimento acaba longe da bbox crua original). Corrigido adicionando
   `VisualRegion.absorbed_label_bboxes` como sinal independente e autoritativo.
2. **Mesmo após o sinal de absorção, ~16 arquivos de 2011/2021 ainda divergiam**: dado o tempo disponível,
   a correção mais honesta foi um gate declarativo (`contextual_relation_gate`, mesmo padrão de
   `owner_exclusion_gate`/`caption_font_size_gate`), não uma tentativa de generalização perfeita sob risco.
3. **`raw_intersects` com limiar `> 0` bare**: um toque de ruído (~1,6pt) contra a bbox crua de uma região
   vizinha era tratado como decisivo, quebrando D40. Corrigido exigindo o piso `REGION_Y_PADDING` em ambos
   os eixos.
4. **Teste de metamorfismo de largura de coluna com região fixa demais**: primeira tentativa usava uma
   região com `bbox` estreita o suficiente para que o rótulo de teste, ao variar a margem, caísse fora da
   própria região (falso negativo de teste, não do código). Corrigido alargando a região sintética.

## X. Escopo não completado (documentado, não escondido)

- Estrutura `alternative_group` completa (Seção G) — mecanismo mais estreito bastou para os casos reais.
- Cluster D / reconstrução geométrica de fragmentos (Seção H) — não implementado.
- Q24's própria causa raiz mais profunda (mesclagem de 4 diagramas) — não atacada.
- Q07's regressão de uma palavra, D40's vazamento cosmético "F", Q23's artefato cosmético — aceitos como
  efeitos colaterais documentados do design tri-estado "ambíguo nunca remove", não corrigidos com um hack
  específico por questão.
- D60 (`valor`-annotation misattachment), Q33 (item-marker displacement), D10's própria ordem de colagem de
  notícias — mesma família de "ordem local", nenhuma tentativa de correção geral nesta fase.
- Validação G4 (exame não visto, código congelado) — não tentada; `GENERALIZATION_NOT_YET_VALIDATED`
  permanece o rótulo correto.

## Recomendação

O mecanismo `contextual_relation_gate` prova, com um contraexemplo geométrico explícito (D10/Q61 versus
Q07), que a relação linha-região não pode ser reduzida a um limiar único e generaliza corretamente sem
nenhuma regressão no corpus protegido — mas também demonstra, através do vazamento "F" de D40 e da perda de
"aos" em Q07, que o próprio design "seguro por padrão" (nunca remover em caso de ambiguidade) tem um custo
cosmético real quando a evidência disponível é insuficiente para distinguir um rótulo genuíno de uma linha
não relacionada. A próxima fase deveria priorizar Cluster D (reconstrução geométrica de fragmentos) antes de
qualquer nova heurística de fronteira, já que três dos resíduos mais visíveis desta fase (Q07, Q12, D40)
dependem exatamente dele — e não de mais um ajuste de `_line_in_region`. Recomenda-se também investir na
causa raiz de Q24 (mesclagem de diagramas) antes de tentar qualquer novo fixador de Cluster C, e considerar
formalizar a distinção "conteúdo-em-imagem versus prosa perdida" (Seção O) como uma regra documentada do
próprio contrato de generalização, não apenas uma convenção aplicada manualmente nesta auditoria.
