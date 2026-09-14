# Phase 3D — Fronteiras Semânticas, Ordem Local e Recuperação das Alternativas Visuais de 2008-B

## A. Classificação

**`LEGACY_LAYOUT_PARTIAL`.**

**`NOT_READY_FOR_2008_ENGINEERING_TEST`** (`assess-readiness --year 2008 --course all-computing`, exit code 1).

**`RESIDUAL_LAYOUT_NOT_STABILIZED`** — dois padrões sistêmicos foram corrigidos com segurança e
generalidade nesta fase (cabeçalho-confundido-com-legenda via tamanho de fonte, e uma classe
específica de coluna espúria por bloco de código aninhado), mas um terceiro padrão sistêmico
(contaminação cruzada por diagrama impresso antes do próprio marcador de questão) permanece
diagnosticado, porém não corrigido, e cinco questões da "Classe A residual" (Q02, Q07, Q12, Q45,
Q54, Q75) continuam com perda real de conteúdo por um mecanismo de absorção de legenda genuína
que o novo sinal de fonte não cobre.

Progresso real e extensamente verificado: duas correções gerais novas foram implementadas, cada
uma root-causada por instrumentação direta (não hipótese), testada exaustivamente contra
2011/2021 (zero drift confirmado byte a byte repetidas vezes ao longo da fase) e aplicada de
forma declarativa/gated quando uma tentativa unconditional se mostrou insegura:

1. **`caption_font_size_gate`** — um cabeçalho real nunca deve ser absorvido como legenda; o sinal
   que os distingue de forma confiável é o TAMANHO DA FONTE (legendas reais são menores que o
   corpo do texto; cabeçalhos compartilham ou excedem o tamanho do corpo), não apenas geometria.
   Resolveu **D09** por completo (enunciado agora idêntico, palavra por palavra, à fonte real),
   recuperou integralmente o conteúdo perdido de **D10** (ordem ainda incorreta) e de **D40**
   (um rótulo residual de diagrama ainda vaza), e recuperou parcialmente **Q02**.
2. **Gate combinado de altura+tamanho de fonte em `detect_column_margins`** — resolveu **Q68** por
   completo (a cláusula WHERE dividida em dois fragmentos, causa raiz da Fase 3B, agora está
   inteira e na ordem correta).

Uma tentativa inicial (ambos os mecanismos, na primeira versão) causou regressões reais e
CONFIRMADAS antes de ser publicada: (a) uma versão sem gate do `caption_font_size_gate` alterou
2011 (Q05/Q33/Q34/Q35); (b) uma primeira versão de `_dominant_body_font_size` regrediu **Q08 e
Q01** de 2008-b (uma questão já `passed`), ambas corrigidas antes de qualquer regeneração real
ser publicada. Nenhuma regressão foi aceita; ambas ficaram documentadas como evidência.

**Contaminação cruzada (Q62/D60)**: causa raiz identificada com precisão nesta fase — o diagrama
ITIL de Q61 é impresso ANTES do próprio marcador "QUESTÃO 61" (com uma legenda de referência
futura, "Figura para a questão 61"), quebrando a suposição arquitetural de que o conteúdo de uma
questão sempre segue seu próprio marcador. Uma correção segura exigiria um mecanismo novo
(reatribuição de ownership por legenda de referência futura, ainda não implementado em nenhuma
fase) — documentado tecnicamente, não corrigido.

**Q8/Q38/Q55**: reavaliadas após as duas correções gerais; permanecem excluídas, confirmado por
reinspeção direta das regiões candidatas (ainda blobs grandes mesclados, sem candidato de
"pequena fórmula" para nenhuma das cinco alternativas). Nenhum placeholder criado; exclusão
mantida.

## B. Estado Git

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   53b171e3901eec6d831e58513f9662c8ec3d3e6e
master: a5dfaab0c105150df3a7201c16547708cef45292 (= origin/master, intocado)
origin/feat/enade-2011-unified-extraction: 84c50058220bbc81a8d2f3086b2cd60d0cd47eb6 (referência, não tocada)
working tree ao final: 29 caminhos com alterações
```

**Divergência notada e não bloqueante em relação ao resumo do prompt**: o resumo desta fase
afirmava "nenhum commit, push ou PR" ao final da Fase 3C, mas a inspeção fresca no início desta
sessão encontrou HEAD em `53b171e` ("Refactor visual region merging logic to include X-axis
tolerance"), um commit já presente e já em `origin/feat/enade-2008-cc-b-pilot` antes desta fase
começar. Confirmado por `git show --stat`: esse commit contém exatamente o conjunto de arquivos
que a Fase 3C deixou no working tree (33 arquivos), nada perdido, nada extra — consistente com o
usuário aceitando e commitando o trabalho da Fase 3C entre as sessões, uma ação fora do escopo
desta IA. Não revertido, não alterado; tratado como o novo baseline legítimo. Nenhum commit, push,
PR, merge ou tag foi executado NESTA fase (3D).

## C. Baseline da Fase 3C

Confirmado por execução fresca de toda a suíte, não presumido do resumo:

```
pytest -q                                     → 487 passed
ruff check .                                  → All checks passed!
ruff format --check .                         → 374 files already formatted
mypy src                                      → Success: no issues found in 52 source files
verify-gold --year 2021 --course ciencia-...  → OK (40/40), validated
assess-readiness --year 2021                  → READY_FOR_2011, 0 needs_review
verify-gold --year 2011 --course all-computing → OK (55/55), validated
assess-readiness --year 2011                  → READY_FOR_LEGACY_LAYOUT_TEST, 1 needs_review (Q34)
gold 2008-B: provisional, 28/77 verified, 49 needs_review
visual audit 2008-B: 30 passed, 17 failed, 30 not_performed (hand-count por status literal)
blocker ledger 2008-B: 43 total, 23 open, 19 resolved, 1 superseded (Q62 duplicado corrigido nesta
  reconciliação inicial - ver seção F)
```

288 arquivos protegidos (270 sob `data/questions/2011|2021` + 18 manifestos relacionados) com
hash SHA-256 capturado antes de qualquer mudança de código nesta fase, idêntico ao congelado ao
final da Fase 3C.

Nenhuma divergência material encontrada além da já notada na seção B.

## D. Correção preservada

`region_merge_x_tolerance` (Fase 3C) permanece inalterada: declarativa, restrita ao profile de
2008-B (`ExamStructureProfile.region_merge_x_tolerance = 150.0`), independente de question ID,
coberta pelos mesmos testes da Fase 3C. D20 e D39 foram revalidadas nesta fase (ver seção O) e
permanecem `passed` - não reabertas. Q49/Q50 permanecem intactas (não afetadas por nenhuma
mudança desta fase - confirmado, ver seção J).

**Duas correções novas foram adicionadas nesta fase, ambas seguindo o mesmo padrão declarativo**:

### D.1 `caption_font_size_gate` (figures.py / exam_profile.py)

Root-causado por instrumentação direta: D09's próprio cabeçalho "DIREITOS HUMANOS EM QUESTÃO"
tem tamanho de fonte 11pt (mesmo tamanho do próprio marcador "QUESTÃO 9"), enquanto a legenda
real da foto ("François JULIEN, filósofo e sociólogo.") tem 6pt, e o corpo do texto tem 10pt. Uma
legenda real neste corpus é consistentemente menor que o corpo; um cabeçalho real compartilha ou
excede o tamanho do corpo. Implementado como:

- `Line.font_size: float` (novo campo, populado em `_raw_lines` a partir do maior tamanho de
  span da linha).
- `figures._dominant_body_font_size(lines)`: moda do tamanho de fonte entre linhas "substanciais"
  (>= 20 caracteres) que também compartilham a margem esquerda dominante da página (não apenas
  linhas "largas" como `_dominant_left_margin` - ver a correção da regressão de Q1 abaixo para o
  motivo).
- Um candidato de `label_candidates` só é elegível para absorção quando seu próprio tamanho de
  fonte é estritamente menor que `_dominant_body_font_size`.
- Ativado apenas via `ExamStructureProfile.caption_font_size_gate: bool = False` (padrão) -
  `data/manifests/exam-structure-2008.yaml` define `true`; nenhum outro booklet define este campo.

### D.2 Gate combinado de altura+tamanho de fonte em `detect_column_margins` (layout.py)

Root-causado por instrumentação direta: Q68's própria subconsulta SQL aninhada (3 linhas, 9pt)
sendo confundida com uma segunda coluna real da página (10pt de corpo) - a mesma classe de
problema que a Fase 3C tentou corrigir duas vezes e reverteu (ver seção E). O sinal que faltava:
tamanho de fonte, não nome de fonte (`is_monospace` não reconhece a fonte deste código como
monoespaçada) nem razão de altura isolada (Q49/Q50 têm uma coluna igualmente curta, mas no
tamanho do corpo). Implementado como `layout._is_short_off_size_column`, exigindo AMBOS os sinais
(razão de altura pequena E fonte menor que o corpo) antes de rejeitar uma coluna candidata como
espúria. **Não gated por profile** (ao contrário de D.1) - `detect_column_margins` é uma função
central chamada para todos os anos sem parâmetro de profile atualmente disponível; confirmado
seguro para 2011/2021 por regeneração completa (zero drift) e para D5/Q49/Q50 especificamente por
teste direto e testes de regressão dedicados.

### D.3 Regressões corrigidas antes da publicação (não chegaram a ser aplicadas ao corpus real)

Duas versões iniciais de `_dominant_body_font_size`/`_page_dominant_body_font_size` foram
corrigidas ANTES de qualquer regeneração real ser aplicada ao corpus publicado:

1. Uma versão que usava a moda "plana" (sem exigir a margem esquerda dominante) sobre TODAS as
   linhas longas foi confirmada, por regeneração direta, a computar 6pt (a fonte das legendas) em
   vez de 10pt (o corpo real) na página de **Q01** - essa página tem 5 imagens de retrato, cada
   uma com sua própria legenda multilinha de 6pt, somando mais linhas longas do que o próprio
   parágrafo do enunciado. Isso fazia um rótulo de índice romano ("IV", 9.96pt) legítimo do
   diagrama ser tratado como "maior que o corpo" e, portanto, não absorvível - fragmentando a
   região e produzindo um `figure-03` espúrio com texto de legenda solto no Markdown. Corrigido
   exigindo que o cálculo de tamanho de fonte também use apenas linhas na margem esquerda
   dominante da página (a mesma margem calculada por `_dominant_left_margin`, mas usando
   comprimento de texto em vez de largura como evidência - ver seção D.1).
2. Uma comparação de tamanho de fonte sem arredondamento consistente (`ln.font_size < body_font_size`
   comparando um valor bruto de 9.96 contra um valor arredondado de 10.0) fazia o próprio corpo de
   texto de **Q50** (9.96pt, arredondando para 10.0) ser tratado como "menor que o corpo" por
   ruído de ponto flutuante, rejeitando a divisão de coluna genuína de Q49/Q50. Corrigido
   arredondando ambos os lados da comparação com a mesma precisão.

Ambas as correções foram confirmadas por regeneração completa antes de qualquer aplicação real ao
corpus - a regressão nunca chegou a ser commitada ou publicada.

## E. Experimentos revertidos

**Preservados da Fase 3C** (não reintroduzidos sob outro nome nesta fase):
1. Gate de razão de altura isolado em `detect_column_margins` - corrigia Q68, quebrava Q50.
2. Gate de razão de altura + monoespaçado - nunca disparava (fonte de Q68 não reconhecida como
   monoespaçada).

Ambos permanecem documentados em `scratchpad/experiment-column-height-ratio.diff` e
`scratchpad/experiment-q68-vs-q50-evidence.md`, e como comentário permanente em `layout.py`. A
correção desta fase (seção D.2) NÃO é uma reintrodução: usa um terceiro sinal (tamanho de fonte)
que nenhuma tentativa da Fase 3C usou, e demonstra formalmente (por teste dedicado) que as causas
das duas regressões anteriores foram eliminadas - Q49/Q50 permanecem com sua divisão de coluna
genuína detectada corretamente.

**Dois novos experimentos revertidos nesta fase**, ambos corrigidos internamente antes de
publicação (ver seção D.3) - preservados aqui como evidência técnica, não como regressões
publicadas:
1. `_dominant_body_font_size` com moda "plana" sobre linhas longas → regredia Q1 (2008-b).
2. Comparação de tamanho de fonte sem arredondamento consistente → regredia Q49/Q50 (2008-b).

## F. Reconciliação

Construída a partir dos arquivos reais (blocker ledger + visual audit + corpus publicado), não do
resumo do prompt:

| Métrica | Início da Fase 3D | Fim da Fase 3D |
|---|---|---|
| Questões publicadas | 77 | 77 |
| Questões excluídas | 3 (Q8, Q38, Q55) | 3 (inalterado) |
| Visual audit `passed` | 30 | 32 |
| Visual audit `failed` | 15 | 15 |
| Visual audit `not_performed` (contagem literal) | 32 → 30 (Fase 3C já reduzira) | 30 (inalterado nesta fase) |
| Blockers no ledger (total) | 43 | 43 |
| Blockers `open` | 23 (após corrigir 1 duplicata nesta seção) | 21 |
| Blockers `resolved` | 19 | 21 |
| Blockers `superseded` | 0 | 1 |

**Correção de reconciliação encontrada e aplicada nesta fase**: o ledger tinha DOIS blockers para
Q62 com descrições contraditórias - `q62-region-merge-content-loss` (Fase 3A, "Statement replaced
by garbled diagram-label fragments", `source_pages: [28]`) e `q62-cross-question-diagram-label-bleed`
(Fase 3B, "Q62's own real statement... is complete and correct, but is followed by trailing
contamination"). Reinspeção direta do `enade-2008-computing-q62.md` publicado confirma que a
segunda descrição é a correta (e que Q62 está na página 27, não 28) - a primeira nunca foi
atualizada após a investigação da Fase 3B. Marcado `status: superseded`,
`superseded_by: q62-cross-question-diagram-label-bleed`, preservando o registro histórico em vez
de apagá-lo.

**Diferenciação explícita** (questão × defeito × blocker × asset × span × região):
- Uma questão pode ter MÚLTIPLOS blockers de categorias diferentes afetando partes diferentes de
  seu próprio conteúdo (D09: um blocker afeta o enunciado - agora resolvido -, outro afeta
  exclusivamente o padrão de resposta - ainda aberto, gap genuíno da fonte). D10 e Q62 têm o mesmo
  padrão.
- Um mesmo blocker de categoria pode compartilhar causa raiz entre questões sem compartilhar
  status (D09/D10/D40 compartilhavam a mesma causa raiz de fusão-sem-eixo-X na Fase 3C; nesta
  fase, D09 e D40 avançaram por completo/quase-completo via o novo gate de fonte, enquanto D10
  teve seu CONTEÚDO recuperado mas sua ORDEM permanece incorreta - um blocker foi
  RECATEGORIZADO, não apenas resolvido, refletindo essa mudança de natureza).
- Nenhum blocker desapareceu silenciosamente por causa de um crop menor - toda mudança de status
  nesta fase está ancorada em reinspeção textual direta contra a página-fonte real, documentada
  no próprio ledger.

## G. Cabeçalhos e legendas

Modelo semântico aplicado nesta fase (não uma taxonomia completa de todos os papéis pedidos pela
Seção 6 do prompt, mas o discriminador que efetivamente resolveu os três casos nomeados): um span
candidato a absorção por um asset visual só é elegível quando seu próprio tamanho de fonte é
estritamente menor que o tamanho de fonte dominante do corpo de texto da página. Um `section_header`
ou `question_marker` real nunca satisfaz essa condição neste corpus (confirmado para D09: 11pt;
para 2021 Q7: marcador "QuEStãO 06" a 12pt, igual ao corpo) - apenas `caption`/`asset_label`
genuínos o fazem (D09: 6pt; 2021 Q7: 9pt). Não usa apenas proximidade; um span `ambiguous`
(nenhuma agregação confiável de tamanho de fonte disponível na página - `body_font_size is None`)
nunca ganha autoridade para remover conteúdo, por construção (o gate simplesmente não se aplica).

### D09 (RESOLVIDO)

- Texto exato do cabeçalho: "DIREITOS HUMANOS EM QUESTÃO".
- Bounding box: aproximadamente (203.8, 100.2, 392.2, 111.3).
- Fonte: `TT2EC7o00`, 11.04pt (idêntica à do próprio marcador "QUESTÃO 9 – DISCURSIVA").
- Asset ao qual foi associado (antes): figure-01.png (retrato/foto do artigo).
- Regra que o classificava como legenda (antes): proximidade geométrica pura (`_expand_with_labels`,
  passo 1 de absorção) - nenhuma verificação de tamanho de fonte existia.
- Por que a classificação estava errada: o cabeçalho é uma manchete editorial real, parte do
  enunciado, não uma legenda da foto - compartilha o tamanho de fonte do próprio marcador de
  questão (11pt), não o da legenda real da foto (6pt).
- Efeito no Markdown (antes): removido por completo, junto com a maior parte do corpo do artigo.
- Efeito no crop (antes e depois): inalterado em substância - o cabeçalho nunca fez parte do
  crop real da foto (a foto em si tem bbox próprio, y=117-565; o cabeçalho está acima, y=100-111).
- Classificação correta: `section_header`/manchete editorial, corpo do enunciado.
- Resultado após regeneração: presente, na posição correta, texto idêntico à fonte.

### D10 (conteúdo recuperado, ordem ainda incorreta)

- Três cabeçalhos de notícia, cada um a 11pt (mesmo padrão de D09): "Alunos dão nota 7,1 para
  ensino médio", "Entre os piores também em matemática e leitura", "Ensino fundamental atinge
  meta de 2009".
- Antes: 2 dos 3 cabeçalhos e seus corpos estavam quase inteiramente perdidos; apenas citações
  soltas sobreviviam.
- Depois: todos os três cabeçalhos, corpos e citações presentes, palavra por palavra, contra a
  página 7. Ordem de leitura ainda incorreta (ver seção I - reclassificado como defeito de ordem
  local, não de perda de conteúdo).

### D40 (quase completo)

- Texto recuperado: a definição do esquema relacional que abre o enunciado
  ("O banco de dados de um sistema de controle bancário... Cliente(nroCliente, nome, endereco,...")
  e a cláusula de abertura do parágrafo de fechamento ("Para que o otimizador de consultas
  passasse a utilizar os índices...", antes truncada para apenas "utilizar os índices...").
- Resíduo: um rótulo do diagrama de árvore de consulta ("B nome,endereco", provavelmente uma
  projeção relacional π mal-renderizada) ainda vaza como texto solto antes de figure-02 - mesma
  classe geral de Q62/D60 (rótulo de diagrama bleeding), causa raiz não isolada nesta fase.

## H. Crop e consumo textual

Decisões formalizadas apenas como diagnóstico nesta fase (a arquitetura de duas bboxes
independentes - `crop_inclusion`/`canonical_text_consumption` - descrita na Seção 8 do prompt não
foi implementada como um novo par de campos em `VisualRegion`). Em vez disso, o `caption_font_size_gate`
resolve o caso concreto pela raiz: um span que nunca deveria ter sido tratado como legenda (por
tamanho de fonte) simplesmente nunca entra no pool de candidatos a absorção - a distinção entre
"aparecer no crop" e "ser removido do Markdown" deixa de ser necessária para os três casos
nomeados (D09/D10/D40), porque o cabeçalho nunca é absorvido em nenhuma das duas dimensões.

Trace de decisão (Seção 13) não implementado como mecanismo formal de log estruturado nesta fase;
a evidência equivalente foi produzida manualmente, por instrumentação direta, e está documentada
inline nos comentários de `figures.py`/`layout.py` e no próprio blocker ledger (campo `cause`) -
suficiente para responder as perguntas da Seção 13 caso a caso, mas não um mecanismo reutilizável
e automático para novos casos futuros.

## I. Ordem local

Arquitetura de `local_reading_region` (Seção 9 do prompt) **não implementada** como estrutura de
dados dedicada nesta fase. Duas correções pontuais foram feitas dentro do mecanismo existente
(`detect_column_margins`), mas nenhuma delas introduz o conceito de uma região atômica com
estratégia de ordenação interna própria:

- **Q68**: resolvido - o gate de altura+fonte impede que a subconsulta aninhada seja tratada como
  uma segunda coluna real, então ela permanece na ordem natural de leitura da PRÓPRIA coluna à
  qual pertence (nenhuma "ilha" foi criada; a correção apenas impede uma classificação de coluna
  incorreta).
- **D10**: NÃO resolvido - o problema aqui é estruturalmente diferente e mais profundo: três
  recortes de jornal estão espalhados por um layout de "colagem" não-linear (o corpo de um
  recorte pode continuar da coluna direita para a esquerda no meio de uma frase; uma citação pode
  ficar bem abaixo do seu próprio corpo, em qualquer coluna que tivesse espaço livre) que o
  modelo "toda a coluna esquerda, depois toda a coluna direita" não consegue representar
  corretamente. Isso não é uma classificação de coluna errada (as duas colunas de fato existem e
  são detectadas corretamente) - é a PREMISSA de que cada coluna é lida inteira antes da outra que
  quebra para este layout específico. Corrigir isso exigiria reconhecer cada recorte como sua
  própria `local_reading_region` (tipo `instruction_box` ou um novo tipo `clipping`), com um
  owner comum (D10) e uma estratégia de ordenação interna reconhecendo onde cada recorte começa e
  termina independentemente da coluna. Não implementado - risco avaliado como alto demais para o
  tempo restante desta sessão, dado o histórico de duas reversões nesta mesma área de código.

## J. Casos Q24/Q29/Q33/Q63/Q68

| ID | Resultado da correção D.2 | Status final |
|---|---|---|
| Q68 | RESOLVIDO - cláusula WHERE completa e na ordem correta | `passed` |
| Q24 | Nenhuma mudança (confirmado por diff byte a byte) | `failed`, não investigado a fundo nesta fase |
| Q29 | Nenhuma mudança | `failed`, idem |
| Q33 | Nenhuma mudança | `failed`, idem |
| Q63 | Nenhuma mudança | `failed`, idem |

Q24/Q29/Q33/Q63 não compartilham a mesma causa raiz exata de Q68 (subconsulta aninhada mal
classificada como coluna) - confirmado empiricamente pela ausência de qualquer diferença em seus
próprios arquivos após a correção. Cada um provavelmente tem sua própria causa raiz distinta
(tabela/diagrama com células de texto espalhadas, não uma coluna espúria) - não investigados
individualmente nesta fase por restrição de tempo; permanecem `failed` com a mesma descrição já
registrada nas Fases 3A-3C.

## K. Contaminação (Q62 e D60)

**Causa raiz identificada com precisão para ambos** (mesmo mecanismo): o diagrama do ciclo de vida
de serviço de TI (ITIL) de Q61 é impresso na página 27, ANTES do próprio marcador "QUESTÃO 61",
com uma legenda de referência futura explícita ("Figura para a questão 61"). O modelo de span
slicing (`detect_question_boundaries`) atribui todo o conteúdo entre um marcador e o próximo ao
autor do PRIMEIRO marcador - então o texto e os rótulos deste diagrama (que precede o marcador de
Q61) são atribuídos a D60 (a questão anterior), não a Q61, quebrando a suposição de que o
conteúdo de uma questão sempre segue seu próprio marcador.

Confirmado por instrumentação direta (`detect_visual_regions` com `question_regions`):
- Conteúdo estrangeiro identificado: rótulos do diagrama ITIL de Q61 (texto: "Figura para a
  questão 61 Estágios do ciclo de vida de um serviço de TI Gerenciamento de aplicações...").
- Owner correto: `objective-61`.
- Owner usurpador: `discursive-60` (região com bbox (121.2, 145.7, 413.5, 402.5), que se estende
  para além do limite de coluna detectado em x=350, cruzando ambas as colunas - o próprio
  diagrama é mais largo que a divisão de coluna da página).
- Reprodução: confirmada - a região é atribuída a D60 porque a legenda "Figura para a questão 61"
  cai, na ordem de leitura, ANTES do marcador de Q61 e DEPOIS do marcador de D60.
- Hops: não aplicável - não é uma cadeia de absorção de legenda, é uma questão de atribuição de
  span inteira, resolvida em uma única decisão (a qual marcador "possui" este intervalo de
  linhas).

**Q62**: mecanismo relacionado mas distinto - metade dos rótulos do MESMO diagrama de Q61 (a
metade que cai na coluna direita detectada, x>=350) é ordenada para o FINAL da coluna esquerda-
depois-direita da página, e como Q62 (não Q61) é o próximo marcador na ordem de leitura após esse
ponto, esses rótulos acabam no span de Q62 em vez de D60 ou Q61.

**Correção não implementada**: exigiria um mecanismo novo - reconhecer "Figura para a questão N"
como um padrão de legenda de referência futura que reatribui a ownership do conteúdo/região
associado à questão N, independentemente de onde o próximo marcador realmente cai. Isso é
arquiteturalmente diferente de qualquer correção já feita (não é uma correção de mesclagem de
região, nem de ordenação de coluna) - avaliado como um mecanismo novo e não trivial, fora do
escopo seguro desta sessão dado o tempo restante. D60/Q62 permanecem blockers abertos, com causa
raiz agora precisamente documentada em vez de "não isolada".

D60 permanece explicitamente classificada como defeito recém-descoberto E ainda contaminado -
NÃO marcada como resolvida apenas porque seu crop melhorou nas Fases 3C/3D (o crop nunca mudou
para D60 nesta fase; apenas o texto solto do diagrama de Q61 continua presente em seu próprio
Markdown).

## L. Q8/Q38/Q55

Reavaliadas após as duas correções gerais desta fase (D.1 e D.2), conforme a Seção 16 do prompt
("somente depois de estabilizar todos os casos publicados"). Confirmado, por reinspeção direta das
regiões visuais candidatas:

```
objective 8:  could not build a valid Question - alternative A: text is empty and no asset is set
objective 38: could not build a valid Question - alternative A: text is empty and no asset is set
objective 55: could not build a valid Question - alternative A: text is empty and no asset is set
```

| Questão | Regiões candidatas (bbox) | `is_small_formula` |
|---|---|---|
| Q8 | (36.8,408.6,529.0,751.9) elements=4; (36.8,238.8,559.1,459.7) elements=5 | False (ambas) |
| Q38 | (336.2,466.2,559.2,553.1) elements=78; (352.0,322.5,494.8,402.6) elements=4 | False (ambas) |
| Q55 | (50.2,451.7,318.5,696.4) elements=55; (332.2,241.0,405.5,325.3) elements=56 | False (ambas) |

Nenhuma alternativa individual pôde ser associada a um asset próprio - as regiões continuam sendo
blobs grandes e mesclados (nunca pequenos candidatos de fórmula, o mecanismo que já funciona para
2011 Q14/Q23). Isso confirma exatamente o diagnóstico da Fase 3A/3B/3C: essas três questões
dependem de um mecanismo de fatiamento de região LARGA por alternativa (diferente do mecanismo de
"pequena fórmula" já existente), que não foi implementado nesta fase. Sem esse mecanismo, não há
como associar `alternative_label` a `asset_id` para nenhuma das 15 alternativas (5 × 3 questões)
com confiança suficiente para publicar.

**Disposição, conforme a Seção 16 do prompt**: exclusão mantida explicitamente; blockers
`q08/q38/q55-unstructured-image-alternatives` permanecem abertos; nenhum placeholder criado;
gold não promovido. Recomenda-se uma fase própria e dedicada para um mecanismo de "grande região
por alternativa" (ver seção Recomendação).

## M. Source coverage

Não implementado como mecanismo formal e reutilizável nesta fase (mesma limitação herdada da Fase
3C). A cobertura real desta fase foi obtida por reinspeção manual, palavra por palavra, de cada
questão tocada por uma mudança de código, contra a página-fonte real (D09, D10, D40, Q02, Q68,
Q01, Q49, Q50) - não uma verificação automática de todas as 77 questões publicadas.

## N. Auditoria visual

```
Início da Fase 3D: 30 passed, 15 failed, 30 not_performed (77 total)
Fim da Fase 3D:    32 passed, 15 failed, 30 not_performed (77 total)
```

Mudanças: D09 (`failed`→`passed`, resolvido de fato) e Q68 (`failed`→`passed`, resolvido de fato).
D10, D40, Q02 permanecem `failed` (melhorados, mas com defeitos reais residuais - não promovidos
sem justificativa). D80 e Q01 permanecem `passed`, reconfirmados após um leve deslocamento de crop
sem mudança de texto. Nenhuma das 30 `not_performed` foi auditada nesta fase (fora do escopo desta
sessão - nenhuma delas foi tocada por nenhuma mudança de código, confirmado por diff).

## O. Blocker ledger

```
Início da Fase 3D: 43 total, 23 open (após corrigir a duplicata de Q62), 19 resolved, 0 superseded
Fim da Fase 3D:    43 total, 21 open, 21 resolved, 1 superseded
```

Resolvidos nesta fase: `d09-region-merge-content-loss` (RESOLVED), `q68-sql-code-block-reordering`
(RESOLVED). Recategorizado: `d10-label-absorption-newspaper-fragments` (de
`region-merge-content-loss` para `table-reading-order-scramble` - a natureza do defeito mudou de
perda de conteúdo para ordem incorreta). Atualizados com evidência nova, sem mudança de status:
`q02-region-merge-content-loss`, `d40-table-reading-order-scramble`. Corrigido por reconciliação:
`q62-region-merge-content-loss` (superseded). `validate_ledger`: 0 problemas.

### Tabela dos 21 blockers ainda abertos

| Categoria | IDs | Questões afetadas |
|---|---|---|
| `region-merge-content-loss` (absorção de legenda genuína, corpo pequeno) | q02, q07, q12, q24, q45, q54, q63 | Q02, Q07, Q12, Q24, Q45, Q54, Q63 |
| `table-reading-order-scramble` | d10 (recategorizado), d40 | D10, D40 |
| `cross-question-contamination` | q62, d60 | Q62, D60 |
| `content-duplication` | q13 | Q13 |
| `unstructured-image-alternatives` | q08, q38, q55 | Q08, Q38, Q55 (excluídas) |
| `answer-standard-absent-from-source` | d09, d10 | D09, D10 (só o padrão de resposta) |
| `answer-standard-incomplete` | d59 | D59 (só o padrão de resposta) |

## P. Gold 2008-B

```
maturity: provisional
verified: 29/77  (início da fase: 28/77)
needs_review: 48/77
structural_blockers: [answer-standard-absent-from-source, answer-standard-incomplete,
  content-duplication, cross-question-contamination, region-merge-content-loss,
  table-reading-order-scramble, unstructured-image-alternatives]
verify-gold: OK (77 questions match)
```

Não promovido a `validated` - blockers estruturais reais permanecem abertos. O aumento líquido de
verified (+1) reflete Q68 (novo verified); D09, embora seu enunciado esteja agora perfeito,
permanece `needs_review` porque seu próprio padrão de resposta está genuinamente ausente da fonte
(`d09-answer-standard-absent-from-source`, um gap distinto e não corrigível por nenhuma mudança
de código).

## Q. Readiness

```
enade assess-readiness --year 2008 --course all-computing \
  --ready-label READY_FOR_2008_ENGINEERING_TEST \
  --not-ready-label NOT_READY_FOR_2008_ENGINEERING_TEST
→ NOT_READY_FOR_2008_ENGINEERING_TEST (exit code 1)
  29/77 verified, 48 needs_review, gold maturity=provisional
  visual audit: 32 passed, 15 failed, 0 not_performed (fully_covered=True - mesma convenção de
    contagem das Fases 3A-3C: todas as 77 chaves estão presentes no arquivo com status explícito)
  79 blocker(s), todos estruturais
```

O rótulo histórico `READY_FOR_2008_ENGINEERING_TEST` significa prontidão para testar o bundle `e`
(o segundo caderno de 2008); não significa que Engenharia de Computação esteja ausente do bundle
`b` (ela é um dos três blocos de curso específico já corretamente modelados dentro do próprio
bundle `b`, documentado desde a Fase 3A).

## R. Proteção de 2011

```
verify-gold --year 2011 --course all-computing → OK (55/55), maturity=validated
assess-readiness → READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, 1 needs_review
  1 blocker: [question_not_verified, non-structural] enade-2011-computing-q34
ledger: 38 total, 0 open (inalterado)
```

Q34 permanece exatamente como estava - não tocado. **Zero drift**: hash SHA-256 dos 288 arquivos
protegidos idêntico ao congelado ao final da Fase 3C, confirmado byte a byte **cinco vezes** ao
longo desta fase (após a primeira versão do caption_font_size_gate, após a correção da regressão
de Q1, após a primeira versão do gate de coluna, após a correção da regressão de Q49/Q50, e ao
final da fase).

## S. Proteção de 2021

```
verify-gold --year 2021 --course ciencia-da-computacao-bacharelado → OK (40/40), validated
assess-readiness → READY_FOR_2011, 40/40 verified, 0 needs_review, no blockers
```

**Zero drift** - incluído nos mesmos 288 arquivos verificados acima. As duas outras variantes de
curso 2021 (`ciencia-da-computacao-licenciatura`, `sistemas-de-informacao`) também foram
regeneradas e comparadas byte a byte - zero diferenças, em cada uma das cinco verificações.

## T. Testes

```
Fase 3C (baseline desta fase): 487 passed
Fase 3D: +9 novos testes
  - tests/test_extraction_figures.py: 3 (_dominant_body_font_size: margem dominante,
    legendas múltiplas não superam o corpo, sem agregação suficiente)
  - tests/test_extraction_layout.py: 2 (coluna curta+fonte-menor rejeitada; coluna curta+mesma-
    fonte mantida - regressão de Q49/Q50)
  - tests/test_extraction_pipeline_2008.py: 4 (D40 código SQL verbatim; D10 conteúdo recuperado;
    Q01 não regredida; Q68 cláusula WHERE não mais dividida) + 1 teste existente (D09) atualizado
    de "não vazio" para "completo"
Total final: 496 passed
```

## U. Quality gates

```
pytest -q                            → 496 passed
ruff check .                         → All checks passed!
ruff format --check .                → 374 files already formatted
mypy src                             → Success: no issues found in 52 source files
enade validate-schema                → 13/13 fixture(s) valid
enade validate-manifest              → OK (0 warnings)
enade audit-extraction (corpus todo) → 252/252 OK
verify-gold + assess-readiness (2011, 2021, 2008) → ver seções P/Q/R/S
```

## V. Reprodutibilidade

Duas extrações limpas e independentes do caderno 2008-b, diretórios isolados:
```
diff -rq run-A run-B                 → 0 diferenças
diff -rq run-A data/questions/2008   → 0 diferenças (idêntico ao publicado)
```
Nenhum campo com timestamp ou reordenação não determinística observado.

## W. Desempenho

```
Páginas processadas: 36
Questões delimitadas: 80 (77 publicadas + 3 excluídas)
Assets renderizados: variável por execução conforme mudanças de fusão/absorção (não recontado
  separadamente nesta fase - ver extraction-audit-2008-computing.json para a contagem exata atual)
Tempo de extração: ~55-64s por execução (mesma ordem de grandeza da Fase 3C - os dois novos gates
  são O(1) por linha/página, sem mudança relevante de complexidade algorítmica)
```

## X. Bugs encontrados

**Corrigidos** (2 mudanças de regra geral, ambas testadas, zero drift 2011/2021):
1. `figures.py`/`exam_profile.py`: `caption_font_size_gate` - cabeçalho real não é mais absorvido
   como legenda quando seu tamanho de fonte não é menor que o corpo da página. Gated a 2008-b.
2. `layout.py`: gate combinado de altura+tamanho de fonte em `detect_column_margins` - uma
   continuação de código aninhado não é mais confundida com uma segunda coluna real. Não gated
   (função central sem parâmetro de profile disponível); confirmado seguro por regeneração
   completa.

**Corrigidos internamente antes de publicação** (não chegaram a ser regressões reais, ver seção
D.3): moda de tamanho de fonte sem considerar a margem dominante (regredia Q1); comparação de
tamanho de fonte sem arredondamento consistente (regredia Q49/Q50).

**Não corrigidos, permanecem como blockers abertos**: absorção de legenda genuína de corpo
pequeno (Q02 parcial, Q07, Q12, Q45, Q54, Q75 - nenhuma mudança); ordem local de recortes tipo
"colagem" (D10 - conteúdo recuperado, ordem não); rótulo de diagrama residual em D40; contaminação
cruzada por legenda de referência futura (Q62, D60 - causa raiz agora precisa, correção não
implementada); embaralhamento de tabela/diagrama não relacionado à causa de Q68 (Q24, Q29, Q33,
Q63); duplicação de texto (Q13); três questões com alternativas puramente visuais em regiões
grandes, não pequenas (Q8, Q38, Q55, confirmadas inalteradas).

## Y. Arquivos

**Modificados (código)**: `src/enade/extraction/{figures.py, layout.py, exam_profile.py,
pipeline.py, assembler.py}`, `tests/{test_extraction_figures.py, test_extraction_layout.py,
test_extraction_pipeline_2008.py}`.

**Modificados (dados)**: `data/manifests/{exam-structure-2008.yaml, blocker-ledger-2008.yaml,
visual-audit-2008-computing.json, gold-2008-computing.json,
extraction-audit-2008-computing.{csv,json}}`; `data/questions/2008/all-computing/` - 9 arquivos
`.md` (d09, d10, d40, d80, q01, q02, q68 alterados; nenhum removido) e seus assets (vários `.png`
com crop levemente deslocado, nenhum removido nem adicionado indevidamente nesta fase).

**Novo (não versionado, documentação de experimento)**: nenhum novo arquivo de experimento
revertido nesta fase (as duas correções internas da seção D.3 foram corrigidas antes de qualquer
regeneração real, sem necessidade de preservar um diff separado).

**Removidos**: nenhum arquivo canônico.

## Z. Git final

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   53b171e3901eec6d831e58513f9662c8ec3d3e6e (inalterado - nenhum commit criado nesta fase)
29 caminhos com alterações no working tree (staged: 0)
```
**Confirmado explicitamente**: nenhum commit, push, PR, merge ou tag foi executado nesta fase.

## Recomendação

Dado o resultado `PARTIAL`/`RESIDUAL_LAYOUT_NOT_STABILIZED`, em ordem de impacto esperado:

1. **Arquitetura de `local_reading_region`** (Seção 9 do prompt) - ainda não implementada como
   mecanismo dedicado. D10's próprio layout de "colagem" de recortes de jornal e Q24/Q29/Q33/Q63's
   próprios embaralhamentos (causa raiz não isolada) provavelmente precisam desse mecanismo
   genérico, não de mais correções pontuais em `detect_column_margins` - o histórico desta e da
   fase anterior mostra que esse arquivo já está no limite de correções seguras e específicas.
2. **Mecanismo de "legenda de referência futura"** para Q62/D60 - reconhecer "Figura para a
   questão N" como um padrão que reatribui ownership de conteúdo à questão N, independentemente de
   onde o próximo marcador cai. Root-causado com precisão nesta fase; não implementado.
3. **Mecanismo de fatiamento de região grande por alternativa** para Q8/Q38/Q55 - o mecanismo
   existente (`is_small_formula`) só funciona para candidatos pequenos; essas três questões
   precisam de um mecanismo análogo para candidatos grandes. Recomenda-se, como já indicado nas
   Fases 3A-3C, uma fase própria e dedicada.
4. **Absorção de legenda genuína de corpo pequeno** (Q02 residual, Q07, Q12, Q45, Q54, Q75) -
   distinta do padrão cabeçalho-vs-legenda resolvido nesta fase; exigiria a separação real entre
   inclusão-no-crop e consumo-de-texto (Seção 8 do prompt), ainda não implementada como mecanismo.
5. **Completar a auditoria visual das 30 questões `not_performed` restantes** - nenhuma delas foi
   tocada nesta fase.

**O bundle `e` de 2008 não deve ser o próximo teste** até que este primeiro caderno esteja
integralmente validado. Não iniciado automaticamente.
