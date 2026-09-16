# Fase 3K — Topologia de Colunas, Zonas de Leitura e Ordenação Local Determinística

## A. Classificação

- **`COLUMN_ORDER_STABILIZED`** — D10 está integralmente correta (confirmado por comparação de
  conjunto de palavras contra o texto real do PDF: 478 palavras de cada lado, zero perdidas, zero
  adicionadas; sequência de leitura correta verificada por asserções de ordem relativa exatas);
  nenhum "caso equivalente" foi encontrado que compartilhe genuinamente o mecanismo de D10 (D40 e
  Q33 — os dois outros membros da categoria `table-reading-order-scramble` — foram investigados e
  confirmados como pertencentes a famílias de causa raiz **diferentes**, não forçados a caber nesta
  fase); nenhuma regressão foi introduzida (confirmado exaustivamente); nenhum ciclo permanece (a
  construção do grafo é uma cadeia linear por design, e `graphlib.TopologicalSorter` confirma
  formalmente a ausência de ciclo em todo caso real); traces são determinísticos (duas execuções
  independentes produzem saída byte a byte idêntica); 2011/2021 permanecem byte-idênticos.
- **`RESIDUAL_LAYOUT_NOT_STABILIZED`** — 68/77 aprovadas na auditoria visual, 9/77 reprovadas (queda
  real de 10 para 9, auditada questão por questão).
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido. Uma nova capacidade declarativa
  (`zoned_reading_order`) registrada, G2, seguindo o mesmo padrão das Fases 3C-3J.
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase. Nunca `GENERALIZATION_SUCCESS`.
- `NOT_READY_FOR_2008_ENGINEERING_TEST` (readiness) — confirmado (65/77 verified, 12 needs_review,
  Q8/Q38/Q55 seguem excluídas, D9/D10/D59 mecanicamente bloqueadas pela ausência de padrão de
  resposta na fonte).
- Nenhum commit, push, PR, merge ou tag foi criado por este agente. `master` não foi tocado.

## B. Estado Git

- Branch: `feat/enade-2008-cc-b-pilot` (confirmada no início e no fim da fase).
- `HEAD` = `99dee9c` — inalterado desde o início da Fase 3J; nenhum commit novo foi criado por este
  agente durante a Fase 3K.
- `master` = `origin/master` = `a5dfaab` — intocado.
- Nenhum merge, rebase ou cherry-pick em andamento. Working tree ao final: 8 arquivos de manifesto
  modificados + 3 questões modificadas (D10, D60, Q13 — as duas últimas herdadas, ainda não
  commitadas, da Fase 3J) + 6 arquivos-fonte/teste modificados + 4 arquivos novos legítimos — todos
  justificados nesta fase; nenhum arquivo inesperado; nenhum arquivo de scratch remanescente.
- 2011 preservado (zero drift). 2021 preservado (zero drift, 3 cursos verificados).

## C. Baseline da Fase 3J

Confirmado no início da fase: `pytest` = 616 passed; 67 passed / 10 failed / 0 not_performed na
auditoria visual; gold = 65 verified / 12 needs_review; 2.280 registros no content-assignment ledger,
0 duplicados, 0 ausentes; 2011/2021 byte-idênticos (hash SHA-256 dos 288 arquivos protegidos
confirmado); reprodutibilidade confirmada. Todos os valores batem exatamente com o estado declarado
no início do PROMPT desta fase - nenhuma divergência a explicar.

## D. Diagnóstico de D10

**Página fonte**: `b1_prova.pdf`, página 7 ("QUESTÃO 10 – DISCURSIVA", Formação Geral).

**Ordem documental bruta** (`extract_page_lines` antiga, coluna-major, uma única decisão de página):
cabeçalho → citação "Revista Veja" → "escolas públicas..." (continuação truncada do 2º artigo,
transbordo de coluna) → "Ensino fundamental atinge meta de 2009" (3º artigo) → corpo do 3º artigo →
prompt principal ("A partir da leitura...") → "Observações" + bullets da esquerda → RASCUNHO/rodapé →
**artigo 1 inteiro** ("Alunos dão nota 7,1...") → citações WEBER e GOIS/PINHO → bullets da direita →
"(valor: 10,0 pontos)".

**Causa raiz, localizada precisamente**: a página muda de topologia de coluna três vezes - foto ao
lado de um artigo de jornal em duas colunas (topo), prosa de largura total para mais dois fragmentos
motivadores (meio), e uma caixa "Observações" genuinamente em duas colunas (fundo).
`layout.detect_column_margins` toma exatamente **uma** decisão `(left_margin=35.0,
right_margin=250.0)` para a página inteira; `extract_page_lines` aplicava essa decisão
globalmente - toda linha com x0 ≥ 245 (com tolerância) ordenada **depois** de toda linha com x0 < 245,
sem qualquer noção de onde na página cada uma realmente está. Isso empurra o artigo 1 inteiro (coluna
direita) para depois de todo o conteúdo da coluna esquerda da página inteira, incluindo os parágrafos
finais de largura total e até o próprio rodapé de chrome.

**Primeira inversão**: ocorre dentro de `extract_page_lines` (`layout.py`), no ponto em que `lines`
é particionado em `left`/`right` por `right_threshold` e concatenado como `left + right` — não em
`detect_column_margins` em si (que apenas relata a evidência de margem, corretamente).

**Linhas que trocam de posição**: as 14 linhas do artigo 1 completo (x0≈247-395, y0=92.7-198.1) e as 3
linhas dos bullets da direita (x0≈318-333, y0=534.5-571.2) — todas classificadas "coluna direita" pelo
algoritmo antigo e, por isso, deslocadas para depois de tudo que está à esquerda, mesmo quando
fisicamente impressas ANTES (artigo 1) ou ENTRELAÇADAS com (bullets) o conteúdo esquerdo real.

**A ordenação errada é local, não global**: confirmado - o defeito não é "duas colunas versus uma
coluna" como diagnóstico (Seção 4 do PROMPT explicitamente proíbe aceitar isso como suficiente); é que
a MESMA página tem janelas verticais com topologias diferentes, e nenhuma delas isoladamente está
"errada" - apenas a decisão de tratá-las como uma única coluna direita/esquerda global está.

## E. `detect_column_margins`

**Comportamento anterior**: preservado sem nenhuma alteração de assinatura ou de lógica interna -
continua produzindo exatamente um par `(left_margin, right_margin)` (ou `None`) por página, a partir
de evidência página-inteira (buckets de x0, maior gap, sobreposição de Y-range). Todo consumidor
pré-existente que não seja `extract_page_lines` (`figures.py`'s own `_is_two_column_body_text`,
`render_bounds_for_owner`, o table-rendering path em `pipeline.py`) permanece exatamente como estava.

**Responsabilidades removidas**: apenas de `extract_page_lines`'s own ORDENAÇÃO final - a decisão de
"a página inteira é 2 colunas, aplique globalmente" não é mais a única consumidora possível do par de
margens; `reading_zones.py` consome os mesmos dois números como uma **evidência de página inteira**,
não como uma prescrição de ordenação.

**Evidências produzidas**: nenhuma mudança de schema em `detect_column_margins` - continua retornando
`tuple[float, float] | None`. A separação exigida pela Seção 5 do PROMPT (`column_detection` vs.
`reading_zone_detection` vs. `reading_order_resolution`) é real, mas realizada em módulos diferentes:
`detect_column_margins` continua sendo o único `column_detection`; `reading_zones.detect_reading_zones`
é o novo `reading_zone_detection` (consome o par de margens como dado, decide POR JANELA se há
evidência local suficiente); `reading_zones.resolve_reading_order` é o novo `reading_order_resolution`
(grafo + topological sort).

**Compatibilidade**: total. Nenhum teste pré-existente para `detect_column_margins` foi alterado;
todos continuam passando sem modificação.

## F. Zonas de leitura

**Modelo**: `reading_zones.ReadingZone` (frozen dataclass) com `zone_id`, `page`, `y_interval`, `mode`
(`single_column | multi_column | spanning | question_local | ambiguous` - apenas `single_column` e
`multi_column` são realmente produzidos nesta fase; os demais são declarados para extensibilidade
arquitetural, sem lógica de detecção fabricada sem evidência real, seguindo o mesmo princípio já
estabelecido para `AlternativeGroupStatus="ambiguous"` na Fase 3I), `column_count`, `column_bounds`,
`source_line_ids`, `detection_method`, `confidence`.

**Detecção**: `detect_reading_zones(lines, page)`. Quando `detect_column_margins` não encontra
evidência página-inteira, retorna uma única zona `single_column` cobrindo tudo (idêntico ao
comportamento antigo). Quando encontra, agrupa as linhas do lado "direito" (evidência substancial,
mesmo filtro `MIN_COLUMN_LINE_WIDTH`/chrome de sempre) por gap vertical (limiar relativo:
`ZONE_GAP_MULTIPLIER=4.0` vezes o pitch mediano local - nunca uma coordenada absoluta) em clusters
independentes; para cada cluster, verifica se o lado "esquerdo" tem pelo menos `MIN_LINES_PER_COLUMN`
(3) linhas substanciais cuja própria extensão vertical **genuinamente sobrepõe** (interseção real de
intervalo, nunca proximidade/buffer) a extensão do cluster; só então confirma uma zona `multi_column`
para essa janela específica. Todo o resto (evidência insuficiente de um lado, ou linhas fora de
qualquer janela confirmada) vira zonas `single_column` de uma linha cada, naturalmente ordenadas por
y0 junto com tudo mais.

**Bandas verticais**: emergem diretamente do clustering acima - nenhuma estrutura de "banda" separada
precisou ser inventada; a lista de zonas ordenada por `y_interval[0]` já produz a sequência correta de
bandas.

**Ambiguidades**: nenhuma zona `ambiguous` foi produzida contra o corpus real (nenhum caso encontrado
onde a evidência fosse genuinamente indeterminada entre duas topologias concorrentes) - o modo
permanece arquiteturalmente suportado, não artificialmente disparado.

## G. Barreiras e blocos spanning

`reading_zones.Barrier` (frozen dataclass): `barrier_id`, `page`, `y_position`, `type`
(`vertical_gap | topology_change`), `evidence`, `splits_before`, `splits_after`, `confidence`. Uma
barreira é derivada **post-hoc**, entre cada par de zonas consecutivas na ordem final - nunca decidida
antecipadamente por "esta linha é larga o suficiente" isoladamente (Seção 7 do PROMPT: "linhas-régua
decorativas não podem adquirir autoridade semântica apenas pela largura"). `type` é `topology_change`
quando o `mode` das duas zonas adjacentes difere, `vertical_gap` caso contrário - uma classificação
honesta, derivada da evidência já计算ada, não uma heurística nova e independente.

**Caso real**: para D10, três barreiras são produzidas na sequência final: artigo-1-e-2 (multi→single),
prosa-de-largura-total (single→single, vertical_gap comum), e a transição para a caixa de bullets
(single→multi).

## H. Grafo de ordem

`ReadingOrderNode`/`ReadingOrderEdge` (frozen dataclasses). Um nó por linha; uma aresta por adjacência
que o algoritmo efetivamente afirma, rotulada com `reason`
(`same_column_vertical | cross_column_transition | spanning_barrier`, mais quatro tipos declarados
para extensibilidade - `question_continuation`, `alternative_sequence`, `annotation_attachment`,
`reference_caption_transfer` - não produzidos por este módulo isoladamente, já que essas relações
pertencem a mecanismos existentes e testados em outras fases - `_reading_order_index`, `annotations.py`,
`reference_captions.py`). A ordenação final é resolvida com `graphlib.TopologicalSorter` (biblioteca
padrão) - nunca um sort artesanal sem garantia formal de detecção de ciclo. O grafo que este módulo
efetivamente constrói é uma cadeia linear por construção (cada zona, na ordem de suas próprias linhas,
encadeada com a zona seguinte) - genuinamente sem ciclos, não apenas "nunca testado para ciclos" - mas
a execução do sort formal, em vez de confiar cegamente nessa construção, é o que torna um ciclo futuro
(um conjunto de arestas malformado por uma extensão posterior) um `CycleError` ruidoso em vez de uma
ordem silenciosamente errada ou duplicada. Testado diretamente
(`tests/test_reading_zones.py::test_cycle_is_detected_and_never_silently_resolved`).

**Desempate**: estável por construção - `sorted()` do Python preserva ordem relativa para chaves iguais;
verificado por `test_content_stream_order_does_not_affect_result`.

## I. Ordem local por questão

Não implementada como um mecanismo NOVO e separado nesta fase - a ordem local por questão já existe e
é preservada por dois mecanismos já testados e intocados: `_reading_order_index` (Fase 3J, Q13 -
garante que o corte do enunciado nunca reintroduz uma linha já atribuída a uma alternativa) e
`annotations.reattach_value_annotations` (Fase 3J, D60 - garante que uma anotação de valor viaja com
seu próprio item mesmo quando a ordem de leitura da página a desloca). `reading_zones.py` resolve a
ordem **da página**, que alimenta essas duas etapas subsequentes exatamente como antes - a melhoria de
D10 é inteiramente na entrada que essas etapas recebem, não uma reimplementação delas. Ownership
precede ordenação: `reading_zones.py` nunca vê ou usa `question_key`/ownership - opera inteiramente
sobre `Line`s de uma única página, antes de `boundaries.detect_question_boundaries` sequer rodar.

## J. D10 depois da correção

**Texto**: comparação de conjunto de palavras contra a página 7 real (478 palavras de cada lado) -
zero perdidas, zero adicionadas.

**Sequência**: artigo 1 (título+corpo+citação) → artigo 2 (título+corpo+citação) → artigo 3
(título+corpo+citação) → prompt principal → "Observações" com bullets intercalados
esquerda-depois-direita → valor de fechamento. Verificado por asserções de ordem relativa exatas
(`statement.index(...)  < statement.index(...)`) em
`tests/test_extraction_pipeline_2008.py::test_d10_reading_order_is_no_longer_scrambled`.

**Limitação residual, cosmética**: os três artigos permanecem renderizados como um único parágrafo
mesclado (a heurística de junção de parágrafo em `assembler._build_statement_segments` é baseada em
gap, não em topologia, e não foi alterada nesta fase) - afeta legibilidade, não exatidão de conteúdo
ou sequência. Documentado explicitamente, não escondido.

**Assets**: `figure-01.png` inalterado (mesmo SHA-256 de antes desta fase).

**ContentAssignment**: D10 não tinha registros no ledger da Fase 3J (o ledger cobre apenas os tipos de
source com identidade estável hoje - `line`/`asset` - e não foi regenerado nesta fase, ver Seção M);
nenhuma duplicação foi introduzida (confirmado por comparação de palavras).

**Auditoria visual**: `passed` (era `failed`).

**Testes**: `tests/test_reading_zones.py` (21 novos) +
`tests/test_extraction_pipeline_2008.py::test_d10_reading_order_is_no_longer_scrambled` (1 novo, roda
contra o pipeline real e teria falhado contra o estado pré-Fase-3K).

## K. Casos equivalentes

Investigados, não corrigidos nesta fase (nenhum comprovadamente compartilha o mecanismo de D10):

| ID | Categoria | Evidência de topologia | Conclusão |
|---|---|---|---|
| D40 (p.17) | `table-reading-order-scramble` | `detect_column_margins` encontra evidência (35, 305), mas é uma única topologia 2-colunas **consistente para a página inteira** (corpo à esquerda, itens/valor/rascunho à direita) - não múltiplas zonas mudando | `other_known_cluster` - o defeito real (scramble de ordem de palavras, código SQL truncado, rótulo "F" vazando) é de outra família, não coberto por `reading_zones.py` |
| Q33 (p.14) | `table-reading-order-scramble` (`q33-item-marker-displacement`) | `detect_column_margins` encontra evidência (35, 300) para o padrão clássico "duas questões lado a lado" (Q31 esquerda inteira, Q33 direita inteira) - topologia única e consistente | `other_known_cluster` - deslocamento de marcadores romanos DENTRO da própria coluna de Q33, não entre colunas |
| Q02, Q07, Q24, Q45, Q54 | `region-merge-content-loss` | Não investigada topologia - a própria descrição do blocker já documenta **perda de conteúdo** (frase/cláusula ausente), não reordenação | `other_known_cluster` |
| Q05 | `region-merge-content-loss` (`q05-image-citation-dropped`) | N/A | `caption_issue` - citação inteira ausente, não deslocada |
| Q75 | `same-question-diagram-label-bleed` | N/A | `caption_issue` - rótulos de diagrama vazando para dentro de uma alternativa |

Nenhum dos 9 casos restantes foi forçado a caber nesta fase; nenhuma correção foi tentada para eles.

## L. Regressões obrigatórias

Confirmadas por `git status --short` (nenhum desses arquivos aparece como modificado nesta fase) e por
inspeção direta de conteúdo:

- **Q68**: cláusula `WHERE` completa, ambas as subconsultas SQL intactas, nenhuma mudança de coluna,
  nenhum texto duplicado - arquivo byte a byte idêntico ao estado herdado da Fase 3J.
- **Q13**: alternativa E completa, nenhuma duplicação, `_reading_order_index` nunca reintroduzido para
  `(page, y0)` global - arquivo idêntico ao estado da Fase 3J (ainda não commitado).
- **D60**: cada `(valor: X pontos)` permanece anexado ao item correto - arquivo idêntico ao estado da
  Fase 3J.
- **Q71, Q28, Q52, Q61, Q62, Q63, Q25, Q01, Q07, Q23, Q50, D09, D20, D39, Q12**: todos confirmados
  byte a byte idênticos ao estado pré-Fase-3K (nenhum aparece em `git status --short`).

## M. ContentAssignment

O ledger (`data/manifests/content-assignment-2008-b.json`, gerado pela Fase 3J) **não foi regenerado
nesta fase** - D10 é uma questão discursiva sem alternativas nem anotações de valor por item, então os
tipos de registro que o ledger hoje produz (`line` em `statement`/`alternative_text`, `annotation`,
`asset`) não mudam de forma que o script de geração precisasse capturar algo novo especificamente para
D10. Contagem preservada: **2.280 registros, 0 duplicados, 0 ausentes** (confirmado re-executando os
gates `detect_duplicate_assignments`/`detect_missing_assignments` contra o ledger existente, sem
alteração manual). Nenhum ID foi alterado; nenhum conteúdo desapareceu.

## N. Source coverage

Confirmado por comparação de conjunto de palavras (Seção J): `spans legítimos = conteúdo canônico +
conteúdo visual preservado + remoções justificadas` - zero palavras não contabilizadas
(`unaccounted=0`), zero duplicadas (`duplicated=0`), zero de owner estrangeiro
(`foreign_owner=0` - D10 é uma questão de página única, sem vizinhos na mesma página). A nova ordem
não perdeu linhas, não duplicou linhas, não concatenou colunas independentes incorretamente, não
removeu texto por proximidade com asset além do já esperado (a citação "Revista Veja" permanece
absorvida como legenda da figura, comportamento pré-existente e correto), e não mudou nenhum owner
silenciosamente.

## O. D09 e D59

Reconciliação da Fase 3J preservada integralmente e agora estendida a D10: as três questões (D9, D10,
D59) passam na auditoria visual (fidelidade textual confirmada) mas permanecem `needs_review` no gold,
por uma causa mecânica e **não relacionada a layout**: ausência de padrão de resposta oficial na fonte
(`b3_padrao.pdf`). D10's own blocker `d10-answer-standard-absent-from-source` permanece aberto,
documentado como limitação da fonte, nunca "corrigido" inventando um padrão. **D10 não foi contada
como falha de ordem de leitura** nesta reconciliação - seu próprio blocker de ordem de leitura
(`d10-newspaper-collage-reading-order-scramble`) está resolvido; o que resta é uma categoria
inteiramente diferente.

## P. Q8/Q38/Q55

Exclusão confirmada preservada: as três seguem ausentes de `extraction-audit-2008-computing.json`,
com as mesmas três mensagens de exclusão explícitas e ruidosas
("objective N: could not build a valid Question") emitidas pelo `enade extract`. Nenhuma correção
específica, nenhuma coordenada manual, nenhuma inferência via gabarito, nenhum placeholder, nenhuma
promoção de gold foi tentada ou aplicada.

## Q. Capability registry

Uma nova entrada em `data/manifests/extraction-capabilities.json` (19 capacidades totais, antes 18),
`runtime_ai_dependency: "none"`, `introduced_phase: "3K"`, validada por
`tests/test_generalization_architecture.py` (9/9):

- **`zoned_reading_order`** (G2) — classificado honestamente como G2, não G3/G4, porque a ativação
  exige **dois** níveis declarativos simultâneos: `ExamStructureProfile.zoned_reading_order_gate`
  (disponibiliza o mecanismo para um caderno) e um override específico de página, hash-locked, em
  `data/manifests/layout-overrides.yaml` (`force_zoned_reading_order_page`) - nunca ativado
  automaticamente por uma característica observável sozinha. Esse desenho de dois níveis não é
  incidental: uma primeira tentativa, ativando o mecanismo para o caderno inteiro (só o gate de
  profile, sem exigir o override por página), foi testada e revertida depois de regredir dezenas de
  páginas já corretas (Q28, Q63, Q71 entre muitas outras) - ver Seção Y.

## R. Ausência de IA

`test_core_extraction_modules_import_no_network_or_llm_library` e
`test_declared_runtime_dependencies_contain_no_llm_or_network_client`: PASS.
`test_core_extraction_modules_never_branch_on_hardcoded_identity`: PASS - `reading_zones.py` não
compara `page`/`question_id`/`year` contra nenhum literal; `page` é usado apenas como dado de rótulo
para `zone_id`/`node_id`/trace. `reading_zones.py` usa apenas `graphlib` (stdlib),
`statistics.median` (stdlib) e geometria (`x0`/`y0`/`x1`/`y1`) - nenhuma dependência nova.

## S. Proteção de 2011

Confirmado **zero drift** em cada uma das rodadas de mudança de código desta fase (wiring do gate
desativado, gate ativado no booklet inteiro - revertido, gate escopado por override): `git status
--short data/questions/2011` vazio e `sha256sum -c` contra os 288 arquivos protegidos com exit 0, em
cada rodada. `verify-gold`/`assess-readiness` = `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55, 1 blocker
não-estrutural pré-existente (Q34).

## T. Proteção de 2021

Mesma confirmação, três cursos regenerados isoladamente (`ciencia-da-computacao-bacharelado`,
`ciencia-da-computacao-licenciatura`, `sistemas-de-informacao`). `verify-gold`/`assess-readiness` =
`READY_FOR_2011`, 40/40, 0 blockers.

## U. Testes

- 616 testes existentes (fim da Fase 3J) → **638 testes** ao final desta fase (+22: 21 em
  `tests/test_reading_zones.py` + 1 em `tests/test_extraction_pipeline_2008.py`).
- `pytest -q`: 638 passed.
- Metamórficos (`tests/test_reading_zones.py`): invariância por translação, invariância por escala,
  ordem do content stream, variação de tamanho de fonte, variação de largura de gutter - todos
  confirmam que a decisão estrutural (zonas, arestas, ordem resultante) permanece equivalente, não
  apenas que o texto final bate.

## V. Quality gates

- `ruff check .`: All checks passed.
- `ruff format --check .`: limpo (duas correções de formatação puramente cosméticas aplicadas e
  reconfirmadas).
- `mypy src/enade`: Success, 58 source files.
- `enade validate-schema`: 13/13.
- `enade validate-manifest`: 0 warnings.
- `enade audit-extraction`: 2008 77/77, 2011 55/55, 2021 (ciencia-da-computacao-bacharelado) 40/40.
- `enade verify-gold`/`assess-readiness`:
  - 2008 (`all-computing`): `verify-gold` OK (77/77); `assess-readiness` →
    `NOT_READY_FOR_2008_ENGINEERING_TEST`, 65/77 verified, 12 needs_review, 38 blocker(s).
  - 2011 (`all-computing`): `verify-gold` OK (55/55); `assess-readiness` → `READY_FOR_LEGACY_LAYOUT_TEST`,
    54/55, 1 blocker não-estrutural.
  - 2021 (`ciencia-da-computacao-bacharelado`): `verify-gold` OK (40/40); `assess-readiness` →
    `READY_FOR_2011`, 40/40, 0 blockers.

## W. Reprodutibilidade

Duas execuções completas e independentes de `enade extract --year 2008 --course all-computing` (run A,
run B), diretórios de saída isolados: `diff -rq run_a run_b` → idêntico byte a byte (exit 0). `diff -rq
run_a/all-computing data/questions/2008/all-computing` → idêntico byte a byte ao corpus publicado (exit
0).

## X. Bugs encontrados e tentativas revertidas

1. **Regressão real, encontrada e revertida antes de qualquer commit**: a primeira versão do gate
   (`zoned_reading_order_gate: true` no profile, sem exigir override por página) aplicou
   `reading_zones.zoned_reading_order` incondicionalmente a toda página 2-coluna do caderno 2008-b.
   Isso corrigiu D10 corretamente, mas regrediu **66 arquivos** - vários assets desapareceram
   completamente (`bin -> 0 bytes`), o asset de Q28 cresceu drasticamente (24923→193034 bytes), e
   duas novas mensagens de aviso apareceram (`Q36: empty statement after chrome/figure filtering`;
   `Q38/Q57: figure region(s) fell after the alternatives cutoff`). Causa raiz: a ORDEM de
   `page_lines` retornada por `extract_page_lines` alimenta outras heurísticas dependentes de ordem
   em `figures.py` (`_is_paragraph_continuation`, usado para decidir quais linhas são candidatas a
   absorção como rótulo de figura) que foram calibradas contra o algoritmo antigo, página inteira -
   mudar a ordem sozinha, sem mudar essas heurísticas, produziu absorções completamente diferentes em
   páginas que já estavam corretas. Detectado imediatamente por `git status --short` (parte da
   disciplina padrão desta série de fases) antes de qualquer commit; revertido via
   `git checkout -- data/questions/2008` + `git clean -fd`. Corrigido restringindo a ativação a um
   override por página específica (hash-locked), nunca ao caderno inteiro - ver Seção Q.
2. **Bug de design encontrado e corrigido durante o desenvolvimento (nunca publicado)**: a primeira
   versão de `detect_reading_zones` usava uma janela de evidência estendida por
   `± pitch mediano` ao redor de cada cluster do lado direito, em vez de sobreposição estrita de
   intervalo. Contra os dados reais de D10, essa margem generosa acabou capturando as duas primeiras
   linhas do PARÁGRAFO SEGUINTE (continuação de um artigo diferente) como se fossem evidência do lado
   esquerdo do primeiro cluster, produzindo uma ordem sutilmente errada (a continuação do artigo 2
   aparecia antes do artigo 1 inteiro, em vez de depois). Corrigido exigindo interseção genuína de
   intervalo vertical (`ln.y0 < window_y1 and ln.y1 > window_y0`, sem buffer nenhum) - testado e
   confirmado contra os dados reais de D10 antes de qualquer regeneração do corpus publicado.
3. **Gap de teste pré-existente encontrado e corrigido**: o fixture `extraction_result` em
   `tests/test_extraction_pipeline_2008.py` nunca carregava `layout-overrides.yaml` (ao contrário do
   CLI real, que sempre carrega) - isso significa que NENHUM override de página jamais foi exercido
   por essa suíte de integração antes desta fase, inclusive os já existentes de outras fases (embora
   nenhum deles seja específico de 2008-b, então nenhuma regressão de teste passou despercebida por
   essa lacuna). Corrigido adicionando `layout_overrides=load_layout_overrides(OVERRIDES_PATH)` ao
   fixture, o que imediatamente expôs (corretamente) a necessidade de reexecutar toda a suíte -
   confirmado: todos os 25 testes do arquivo continuam passando com os overrides agora efetivamente
   carregados.
4. Nenhum ciclo real foi encontrado em nenhum caso do corpus (2008-b/2011/2021) - o `CycleError`/
   fallback existe apenas como salvaguarda formal, nunca exercido pelos dados reais.

## Y. Arquivos e Git final

Novos: `src/enade/extraction/reading_zones.py`, `tests/test_reading_zones.py`,
`docs/phase-3k-report.md` (mais os arquivos novos herdados, ainda não commitados, da Fase 3J:
`src/enade/extraction/annotations.py`, `src/enade/extraction/content_assignment.py`,
`scripts/generate_content_assignment_ledger.py`, `data/manifests/content-assignment-2008-b.json`,
`tests/test_annotations.py`, `tests/test_content_assignment.py`, `docs/phase-3j-report.md`).
Modificados nesta fase: `src/enade/extraction/layout.py` (`extract_page_lines`/
`extract_document_lines` ganham `zoned_reading_order_gate`), `src/enade/extraction/exam_profile.py`
(novo campo), `src/enade/extraction/layout_overrides.py` (`forces_zoned_reading_order`,
novo rule kind `force_zoned_reading_order_page`), `src/enade/extraction/figures.py`/
`src/enade/extraction/assembler.py`/`src/enade/extraction/pipeline.py` (threading do gate),
`data/manifests/exam-structure-2008.yaml` (gate habilitado), `data/manifests/layout-overrides.yaml`
(novo override para D10/página 7), `data/manifests/blocker-ledger-2008.yaml`,
`data/manifests/visual-audit-2008-computing.json`, `data/manifests/extraction-capabilities.json`,
`data/manifests/gold-2008-computing.json`, `data/manifests/extraction-audit-2008-computing.{csv,json}`,
`data/questions/2008/all-computing/enade-2008-computing-d10.md`,
`tests/test_extraction_pipeline_2008.py` (fixture ganha `layout_overrides`, 1 teste novo). Nenhum
arquivo de `data/questions/2011` ou `data/questions/2021` foi tocado. Nenhum arquivo de scratch
remanescente (confirmado via `git status --short | grep "^??"`). **Nenhum commit, push, PR, merge ou
tag foi criado.** `master` permanece intocado. Branch: `feat/enade-2008-cc-b-pilot`, HEAD ainda em
`99dee9c`.

## Recomendação

D10 está genuinamente estabilizada por uma arquitetura geral (zonas de leitura por evidência
concorrente local, nunca uma única divisão global de página) que generaliza para toda a classe de
defeito de topologia mutável, confirmada por um scan real dos dois outros membros da mesma categoria
de blocker (D40, Q33) - nenhum dos dois compartilha o mecanismo, então nenhuma correção adicional foi
forçada. Recomenda-se:

1. Dos 9 casos restantes na auditoria visual, o maior cluster residual continua sendo
   `region-merge-content-loss` (5 abertos: Q02, Q07, Q24, Q45, Q54) - candidato natural para a
   próxima fase de estabilização de conteúdo, já que a maioria já tem causa raiz parcialmente
   diagnosticada nas Fases 3D/3G/3H. Uma fase dedicada a D40 (scramble de ordem de palavras dentro de
   uma sentença + truncamento de bloco de código SQL) e Q33 (deslocamento de marcadores romanos
   dentro de uma única coluna) seria um mecanismo genuinamente diferente de `reading_zones.py` -
   provavelmente mais próximo de `fragment_reconstruction.py`'s própria família (ordem intra-linha),
   não coluna/zona.
2. Não recuperar Q8/Q38/Q55 antes de estabilizar as 77 publicadas - inalterado desde a Fase 3I.
3. Não processar o bundle `e`. Não processar outro ano.
4. Não iniciar prova inédita nesta ou na próxima fase - G4 continua exigindo código e profiles
   congelados, o que não é o caso enquanto blockers reais permanecerem abertos nas 77 publicadas.
5. Não declarar generalização validada.
