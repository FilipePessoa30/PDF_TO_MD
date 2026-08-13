# Phase 2E — Fechamento dos Blockers Restantes, Promoção Condicional do Gold 2011 e Gate Final

## A. Classificação

**GENERALIZATION_PARTIAL.** 53/55 questões com `visual_validation: passed`
(2 permanecem `failed`: Q23, Q27); gold 2011 permanece `provisional`; 2021
permanece `validated` e byte-idêntico em todos os pontos de verificação.

**NOT_READY_FOR_LEGACY_LAYOUT_TEST** — `assess-readiness --year 2011
--course all-computing` retorna 10 blockers (2 blockers de conteúdo
estrutural ainda abertos — Q23, Q27 — mais seus espelhos
`*-not-verified`/`recorded_structural_blocker`/`question_not_verified`,
mais Q34's próprio caso benigno já documentado). Nenhum blocker
estrutural pode permanecer aberto para `READY_FOR_LEGACY_LAYOUT_TEST`;
isso não ocorre aqui, mas o número caiu de 20 (início desta fase) para
10.

Nenhuma heurística nova foi criada apenas para reduzir a contagem de
blockers. Toda resolução usou um mecanismo já comprovado
(`ownership.render_bounds_for_owner` estendido a um terceiro call site;
`protect_from_region_membership` aplicado a regiões pequenas; remoção de
2 overrides que se tornaram obsoletos por um mecanismo geral já existir)
ou uma generalização nova e explicitamente justificada (o mecanismo de
asset inline por alternativa, Q40).

## B. Estado Git inicial

Confirmado no início desta fase: `HEAD=2e0a181` ("feat: Enhance ownership
handling in visual regions and layout processing"), branch
`feat/enade-2011-unified-extraction`, working tree limpo,
`origin/feat/enade-2011-unified-extraction` sincronizado. `master`/
`origin/master` ambos em `a5dfaab`, inalterados. Confirma, mais uma vez,
que todo o trabalho da Fase 2D foi commitado por ferramenta externa do
usuário entre sessões — o mesmo padrão observado em toda transição de
fase deste projeto. Nenhuma ação corretiva foi tomada.

## C. Reconciliação do ledger

**A contagem "38 blockers, 17 resolvidos, 10 abertos, 2 superseded = 29"
citada no início desta fase estava incompleta, não incorreta nos números
individuais**: "17 resolvidos" referia-se apenas às resoluções *novas*
da Fase 2D (Seção D do relatório da Fase 2D), não ao total acumulado no
ledger. Os 9 registros "ausentes" da soma eram os blockers já resolvidos
**antes** da Fase 2D (herdados da Fase 2C): `q20-missing-second-
assertion`, `q24-q25-q26-cross-question-figure-contamination`,
`d03-fibonacci-formula-missing`, e seus 6 espelhos `*-not-verified`
(q20, q24, q25, q26, q40, q43). Reconciliação completa, derivada
programaticamente:

- Total de IDs no ledger: **38**, todos únicos, nenhum duplicado.
- No início desta fase: `resolved`=24, `resolved_by_visual_fallback`=2
  (26 no total "resolvido"), `open`=10, `superseded`=2. Soma: 26+10+2=38.
- Os 10 blockers abertos no início desta fase: `q14-alternatives-empty`,
  `q22-table-asset-contamination`, `q23-inline-symbols-residual`,
  `q27-pseudocode-not-code-block`, `q38-remaining-content-defects`
  (os 5 "estruturais", listados no `gold-2011-computing.json`'s próprio
  `structural_blockers`) mais `q14-not-verified`, `q23-not-verified`,
  `q27-not-verified`, `q34-not-verified`, `q38-not-verified` (os 5
  espelhos de `extraction_status`).
- Situação dos outros cinco blockers abertos (os espelhos): cada um
  reflete diretamente se a questão correspondente atingiu
  `extraction_status: verified` - não são blockers de conteúdo
  independentes, mas o pipeline (`readiness.py`) os trata com o mesmo
  peso que qualquer outro blocker aberto (nenhuma distinção de
  severidade), então todos afetam readiness igualmente.
- Ao final desta fase: `resolved`=28, `resolved_by_visual_fallback`=3
  (31 no total "resolvido"), `open`=5, `superseded`=2. Soma: 31+5+2=38.
  `validate_ledger`: zero issues.
- Os 5 blockers que permanecem abertos: `q23-inline-symbols-residual`,
  `q27-pseudocode-not-code-block`, `q23-not-verified`,
  `q27-not-verified`, `q34-not-verified`.
- Nenhum registro desapareceu; nenhum ID foi reutilizado ou deletado;
  `baseline_count` permanece 32 (constante histórica da Fase 2B, nunca
  reescrita).

## D. Correções por questão

### Q22 (prioridade 1)

**Causa confirmada**: `table-01.png` (crop de fallback visual
obrigatório da tabela-verdade de Q22, via `render_table_region`) exibia
o diagrama de autômato e a gramática completos de Q23 vazando pela
borda direita. O bbox da própria tabela já estava corretamente confinado
à coluna de Q22 (`detect_tables` roda sobre as linhas já escopadas de
uma única questão); o vazamento era inteiramente do alargamento
incondicional de `_render_bbox` até a largura de conteúdo da página
inteira - o mesmo defeito geral já corrigido em `render_region` na Fase
2D (ADR 35), mas nunca estendido a `render_table_region`.

**Correção**: novo parâmetro `column_bounds` em `render_table_region`,
mais um helper compartilhado novo, `ownership.render_bounds_for_owner`,
fatorado das duas computações quase-idênticas já inline em `figures.py`
(reduzindo duplicação, não adicionando um mecanismo novo).
`pipeline.py`'s próprio loop de renderização de tabelas agora calcula o
`QuestionRegion` do próprio span (via `question_key`) e o
`detect_column_margins` da própria página da tabela, e chama o mesmo
helper.

**Resultado**: `table-01.png` agora mostra apenas a tabela-verdade de
Q22, com no máximo um sliver de 1-2pt na borda da página (o resíduo
pequeno e esperado de `OWNERSHIP_MARGIN`).

### Q23 (prioridade 2, avaliada após Q22 por design)

**Causa confirmada (residual original, Fase 2B)**: os três overrides
`exclude_from_region_candidates` que suprimiam as imagens dos símbolos
`Sigma={a,b,c}`/`Sigma*`/`lambda` foram escritos **antes** do mecanismo
de pequenas imagens de fórmula existir (Fase 2C) - a própria razão do
override citava "muito pequeno para `MIN_REGION_HEIGHT`", mas as três
imagens (12-57pt largura x ~12pt altura) na verdade se qualificam
confortavelmente para o pool separado de pequenas fórmulas
(`SMALL_IMAGE_MAX_WIDTH`/`_HEIGHT` + `MIN_FORMULA_WIDTH`/`_HEIGHT`), que
nunca participa do chain-merge de candidatos grandes que o override
existia para impedir.

**Correção**: os três overrides obsoletos foram removidos (nenhum
mecanismo novo). Diagrama de autômato (`figure-02.png`) e gramática/
introdução-de-alternativas (`figure-01.png`) reverificados inalterados;
um novo `figure-03.png` agora captura a frase completa com os 3
símbolos, legíveis, em contexto.

**Residual genuinamente distinto, não corrigido**: investigar isso
revelou um segundo defeito, separado - o próprio símbolo Sigma ausente
da alternativa D e a própria notação de expressão regular ausente da
alternativa E são cada um uma pequena imagem **dentro** do texto já
substancial de uma alternativa, uma forma diferente da de Q14 (onde a
alternativa inteira é vazia). O mecanismo geral construído para Q14 só
dispara para uma alternativa sem nenhum texto real. Corrigir isso
exigiria embutir assets no meio do texto de uma alternativa - uma
mudança de schema maior, fora de escopo para dois símbolos únicos. O
gap de D agora é de baixa severidade (redundante com a introdução já
corrigida); o de E é relevante para a capacidade de resposta (a
alternativa inteira é uma comparação com uma expressão regular
específica). **Q23 permanece `failed`/aberto** por esta razão mais
estreita.

### Q38 (prioridade 3)

**Causa confirmada**: a nota da Fase 2D descrevia o residual como
"gramática lida de forma embaralhada" - reler o Markdown atual contra a
página fonte, lado a lado, encontrou essa caracterização imprecisa: a
ordem de leitura já estava correta. O defeito real era que 5 linhas de
texto genuíno e corretamente decodificado estavam **ausentes por
completo** (nem no texto nem em nenhum crop de figura) - engolidas por
`REGION_Y_PADDING` (2pt) sozinho, porque uma região de pequena-fórmula
vizinha (carregando um símbolo terminal de 1 caractere) tinha um bbox
tão apertado que a linha seguinte, sem relação, caía dentro da sua
margem de exclusão.

**Correção**: uma varredura sistemática (toda região própria de Q38
cruzada contra toda linha própria de Q38, procurando a mesma assinatura
"padding alcança além do que a região realmente renderiza"), executada
repetidamente até não encontrar mais nada, achou 5 linhas engolidas no
total (não apenas a primeira notada). 5 novos overrides
`protect_from_region_membership` (mesmo mecanismo já provado para
Q12/Q48 na Fase 2D).

**Resultado**: o texto completo agora lê na ordem exata correta,
linha por linha, batendo com a fonte. Investigar isso também esclareceu
dois discrepâncias texto/imagem previamente incertas (o artefato "g" é
um glifo genuíno e isolado no próprio PDF fonte, não uma substituição de
fonte-símbolo; o símbolo ausente na frase de ambiguidade hex é "x",
confirmado via imagem correta) - ambas agora `resolved_by_visual_fallback`
explicitamente, ao invés de deixadas como um defeito de "embaralhamento"
mal-caracterizado.

### Q14 (prioridade 4)

**Causa confirmada**: as 5 alternativas de Q14 são, cada uma, **apenas**
uma imagem de fórmula booleana, sem nenhum outro texto - a linha do
marcador não deixa nada além de pontuação. Os 5 candidatos de
pequena-fórmula (um por alternativa) se fundiram em **uma** região
cobrindo as 5 linhas, já que o merge por proximidade vertical não tem
noção de fronteira de alternativa entre eles.

**Correção (mecanismo geral novo, não um patch específico de Q14)**:
`Alternative` ganhou um campo opcional `asset: Asset | None`; uma nova
função em `assembler.py` (`_attach_alternative_formula_regions`)
fatia, para cada alternativa com texto vazio após o marcador, a região
candidata com maior sobreposição em Y contra a própria linha daquela
alternativa - "recorte a linha visual inteira", nunca uma tentativa de
reconstruir os componentes da fórmula. `markdown_format.py` renderiza o
asset inline (`A. ![Alternativa A](path) .`) e o resolve de volta via
`Question.assets` na releitura. Disparado apenas pela forma geométrica/
textual "alternativa vazia + região sobreposta", nunca por question id -
confirmado inerte para as outras 54 questões (só os arquivos de Q14
mudaram ao reextrair o corpus inteiro).

**Resultado**: `figure-03.png` a `figure-07.png` mostram, cada um, a
fórmula própria e distinta de uma alternativa, com seu próprio marcador
de letra circulada, batendo com a fonte exatamente.

### Q27 (prioridade 5)

**Defeito reproduzido e causa reconfirmada** (não presumida do resumo):
inspeção direta de rawdict confirmou que todo o pseudocódigo de 7 linhas
está na fonte `ArialMT` - proporcional, não monoespaçada - a mesma causa
já documentada para Q46 (Fase 2A) e D4 (Fase 1C). Conteúdo verificado
nesta fase: as 7 linhas estão presentes, completas, na ordem exata
correta - zero perda de conteúdo. Um novo override declarativo
(`force_code_block`) foi considerado (Seção 11) e rejeitado: o gap é
formatação opcional, não fidelidade de conteúdo, e criar um novo tipo de
regra de override para um único caso, sem perda, já aceito em outro
lugar (Q46/D4), é uma troca de risco/valor pior do que deixá-lo
disclosed. **Permanece `failed`/aberto** deliberadamente, categoria
`formatting`.

## E. Outros blockers inicialmente abertos

| Blocker | Situação ao final |
|---|---|
| `q14-not-verified` | resolved (Q14 agora `verified`) |
| `q22-table-asset-contamination` | resolved (ver Seção D) |
| `q38-not-verified` | resolved (Q38 agora `verified`) |
| `q23-not-verified` | permanece open (Q23 permanece `needs_review`) |
| `q27-not-verified` | permanece open (Q27 permanece `needs_review`, deliberado) |
| `q34-not-verified` | permanece open (caso benigno deliberado, inalterado desde a Fase 2A/2B - falso positivo confirmado de novo, não uma correção pendente) |

Nenhum destes exigiu reclassificação como duplicata, source_ambiguity ou
superseded - cada um é exatamente o que sua descrição sempre disse que
era.

## F. Ownership

- **Alargamento de crop**: `render_table_region` agora recebe
  `column_bounds`, igual a `render_region` desde a Fase 2D - as duas
  computações de `owner_x_bounds` já existentes em `figures.py` foram
  refatoradas para o mesmo helper compartilhado
  (`ownership.render_bounds_for_owner`), agora usado em 3 pontos.
- **Merge**: nenhuma mudança em `_merge_overlapping_regions` (o
  `owner_key` gate da Fase 2D permanece intocado e continua correto).
- **Colunas**: `render_bounds_for_owner` continua retornando `None`
  quando a página não é de duas colunas genuínas (o caso Q17 da Fase 2D
  permanece protegido).
- **Clipping**: inalterado (`QuestionRegion.clip`, `OWNERSHIP_MARGIN`).
- **Owner obrigatório**: o novo mecanismo de asset por alternativa
  (Q14) propaga `owner_key`/`owner_x_bounds` da região original para
  cada fatia derivada, preservando a cadeia de proveniência.
- **Detector de contaminação**: `ownership.detect_contamination`
  permanece intocado; um gate de integridade de asset dedicado (script
  desta fase, ver Seção sobre gates) confirmou zero hash mismatch, zero
  arquivo órfão, zero caminho duplicado entre questões, para os 45
  registros de asset (40 caminhos únicos) do corpus 2011 inteiro.

## G. Notação e fallbacks

- Q14: fallback visual **estrutural** (um asset por alternativa,
  posicionado corretamente, não apenas um crop solto) - o primeiro caso
  deste tipo no corpus.
- Q22/Q23/Q38: fallback visual de trecho (crops corrigidos/recuperados),
  mecanismo já estabelecido.
- Limitação de acessibilidade/pesquisabilidade explícita, registrada:
  as fórmulas de Q14, os símbolos de Q23 e os trechos de Q38 recuperados
  via imagem não são pesquisáveis como texto puro - só a imagem.
- Nenhuma notação foi inventada ou reconstruída semanticamente em
  nenhum ponto desta fase - toda recuperação foi geométrica/textual
  (bbox, contagem de caracteres via rawdict, comparação direta com a
  página fonte).

## H. Overrides

**Inventário final (30 overrides ativos)**: `protect_from_label_absorption`
(17), `protect_from_region_membership` (7 - 2 herdados da Fase 2D +
5 novos para Q38), `force_fraction_merge` (5, Q10, inalterado),
`exclude_from_orphan_marker_merge` (1, Q22, inalterado).

**Removidos nesta fase**: 3 `exclude_from_region_candidates` (Q23,
Sigma/Sigma*/lambda) - obsoletos, substituídos pelo mecanismo geral de
pequena-fórmula.

**Novos nesta fase**: 5 `protect_from_region_membership` (Q38).

**Nenhum question_id na lógica central**: confirmado por varredura
(`grep`) - nenhum arquivo em `src/enade/extraction/` contém um
question_id literal fora de comentários/docstrings.

## I. Auditoria visual

55/55 questões com entrada em `visual-audit-2011-computing.json`
(`not_performed=0`). **53 `passed`, 2 `failed`** (Q23, Q27) - subindo de
51/4 no início desta fase. Reinspecionados nesta fase: Q14, Q22, Q23,
Q38 (Markdown ou assets mudaram) e Q40 (vizinho de Q38, confirmado
inalterado via `git status`, auditoria anterior preservada por hash). As
51 questões restantes permanecem byte-idênticas ao estado da Fase 2D,
preservando sua auditoria anterior legitimamente.

## J. Padrões D1-D5

Todos os 5 permanecem `passed`, inalterados nesta fase (nenhuma mudança
compartilhada afetou tabelas/fórmulas/ownership de forma que os
tocasse) - confirmado por `git status` mostrando zero diff para os
arquivos D1-D5.

## K. Provas virtuais

Materializadas e validadas diretamente contra os 55 arquivos reais em
disco após todas as correções desta fase:

| Curso | Objetivas | Discursivas | Total | Issues |
|---|---|---|---|---|
| ciencia-da-computacao-bacharelado | 35 | 5 | 40 | nenhuma |
| ciencia-da-computacao-licenciatura | 35 | 5 | 40 | nenhuma |
| engenharia-da-computacao | 35 | 5 | 40 | nenhuma |
| sistemas-de-informacao | 35 | 5 | 40 | nenhuma |

## L. Gold 2011

`maturity: provisional` antes e depois (mantido corretamente - Q23/Q27
permanecem `failed`). Reconstruído nesta fase: 50→**52/55** `verified`,
3 `needs_review` (Q23, Q27, Q34). `structural_blockers` atualizado para
apenas os 2 blockers de conteúdo restantes:
`q23-inline-symbols-residual`, `q27-pseudocode-not-code-block`.
`verify-gold`: OK, 55/55 hashes conferem contra o gold recém-travado.

## M. Readiness

`assess-readiness --year 2011 --course all-computing
--ready-label READY_FOR_LEGACY_LAYOUT_TEST`:
**NOT_READY_FOR_LEGACY_LAYOUT_TEST**, 10 blockers listados
individualmente (queda de 20 no início desta fase). Consome: maturity do
gold (`provisional`), o ledger de blockers completo (via
`blocker_ledger_path` auto-detectado), `extraction_status` por questão,
e a cobertura de auditoria visual. Nenhuma contagem agregada esconde um
blocker individual - cada um dos 10 é impresso com seu próprio id e
descrição.

## N. Proteção de 2021

Verificado no início desta fase e após **cada** mudança de código
compartilhado (5 vezes ao todo: após o fix de Q22, após o fix de Q38,
após o fix de Q14, após a remoção dos overrides de Q23, e na varredura
final):

- `verify-gold --year 2021 --course ciencia-da-computacao-bacharelado`:
  OK, 40/40, `maturity=validated`, em toda checagem.
- `assess-readiness`: `READY_FOR_2021`... `READY_FOR_2011`, 40/40
  verified, 0 needs_review, 40 passed/0 failed, **zero blockers**, em
  toda checagem.
- `enade extract --year 2021 --course ciencia-da-computacao-bacharelado`:
  `files written: 0, unchanged: 40`, em toda checagem.
- `git status --short data/questions/2021/`: limpo em toda checagem.
- 2021 nunca foi atualizado; gold 2021 nunca foi tocado; nenhuma
  regressão em nenhum ponto.

## O. Testes

**418 no total** (414 herdados do fim da Fase 2D + 12 novos desta fase -
3 `render_bounds_for_owner`/`ownership.py`, 2 `render_table_region`/
`assets.py`, 2 `_line_in_region` pequena-região/`assembler.py`, 3
`_attach_alternative_formula_regions`/`assembler.py`, 1 round-trip de
asset em alternativa/`markdown_format.py`, menos ajustes de contagem
líquidos ao longo do caminho) - todos passando.

## P. Quality gates

```
pytest -q                                     -> 418 passed
ruff check .                                  -> All checks passed!
ruff format --check .                         -> 291 files already formatted
mypy src                                      -> Success: no issues found in 52 source files
enade validate-schema                         -> 13/13 fixture(s) valid
enade validate-manifest                       -> OK (0 warning(s))
enade audit-extraction --questions-dir ...    -> 55/55 OK
enade verify-gold --year 2021 --course cc-b   -> OK (40/40), maturity=validated
enade assess-readiness --year 2021 ...        -> READY_FOR_2011, no blockers
enade verify-gold --year 2011 --course all... -> OK (55/55), maturity=provisional
enade assess-readiness --year 2011 ...        -> NOT_READY_FOR_LEGACY_LAYOUT_TEST, 10 blockers
```

Gate de integridade de asset (script dedicado desta fase, ver Seção F):
45 referências de asset, 40 caminhos únicos, zero hash mismatch, zero
arquivo órfão, zero caminho duplicado entre questões diferentes.

## Q. Reprodutibilidade

Duas extrações limpas e independentes de 2011 (diretórios de saída
separados): `diff -rq` entre as duas - **zero diferença** (Markdown,
assets PNG, relatórios de auditoria). Uma terceira extração limpa
comparada diretamente contra o corpus em disco (`data/questions/2011/
all-computing`) - **zero diferença** também, confirmando que o estado
atual do repositório é exatamente o que o pipeline determinístico
produz, não um artefato de edição manual.

## R. Bugs encontrados nesta fase

1. **`render_table_region` sem `column_bounds`** (Q22) - a mesma classe
   de bug do ADR 35 (Fase 2D), não corrigida naquela fase por escassez
   de tempo, corrigida agora exatamente como esboçado.
2. **`REGION_Y_PADDING` engolindo linhas reais adjacentes a regiões de
   pequena-fórmula** (Q38) - uma variante nova do padrão já conhecido
   (Fase 2D, Q12/Q48), mas em um tipo de região diferente (pequena, não
   com crescimento limitado por `MAX_ABSORPTION_GROWTH`) - encontrado
   via varredura sistemática, não caso a caso.
3. **`_merge_by_vertical_proximity` sem noção de fronteira de
   alternativa** (Q14) - uma lacuna nova, nunca antes diagnosticada,
   descoberta ao reinvestigar Q14 a fundo.
4. **Overrides obsoletos por um mecanismo geral ter avançado além
   deles** (Q23) - não um bug de código, mas uma dívida de manutenção
   real: um override do Nível 3 escrito antes de um mecanismo do Nível 1
   existir, nunca revisitado depois que esse mecanismo passou a cobrir
   o mesmo caso de forma mais segura.
5. **Bugs de teste próprios, encontrados e corrigidos durante o
   desenvolvimento** (não bugs de produção): um teste round-trip
   pré-existente (`test_render_then_parse_round_trips`) quebrou porque o
   dict de alternativa recém-parseado não incluía a chave `asset`
   explicitamente quando ausente - corrigido no próprio código de
   produção (`alt["asset"] = ...` sempre setado), não no teste.

## S. Arquivos

**Modificados (código-fonte, 8 arquivos)**: `src/enade/extraction/
{assembler,assets,figures,ownership,pipeline,to_question}.py`,
`src/enade/markdown_format.py`, `src/enade/models/question.py`

**Modificados (testes, 4 arquivos)**: `tests/test_extraction_assembler.py`,
`tests/test_extraction_assets.py`, `tests/test_markdown_format.py`,
`tests/test_ownership.py`

**Modificados (manifests/dados)**: `data/manifests/{blocker-ledger-2011.yaml,
extraction-audit-2011-computing.{csv,json},gold-2011-computing.json,
layout-overrides.yaml,visual-audit-2011-computing.json}`

**Modificados (documentação)**: `docs/decisions.md` (+4 ADRs, seções
38-41); `docs/phase-2e-report.md` (este arquivo, novo)

**Modificados/novos (dados extraídos, 2011 apenas)**: 4 arquivos `.md`
de questão (Q14, Q22, Q23, Q38) + assets associados; 6 assets PNG novos
(`q14/figure-04..07.png`, `q23/figure-03.png`); 2 assets PNG modificados
(`q14/figure-02..03.png`, `q22/table-01.png`).

**Nada foi removido.** Nenhum arquivo de 2021 foi tocado.

## T. Estado Git final

`HEAD=2e0a181` (inalterado - nenhum commit foi feito nesta fase),
branch `feat/enade-2011-unified-extraction`, `master`/`origin/master`
ambos `a5dfaab`, inalterados. **Nenhum commit, push ou PR foi criado
nesta fase.** 31 itens com mudanças no working tree (26 modificados +
5 novos não-rastreados), prontos para revisão do usuário.

## U. Recomendação

Classificação **GENERALIZATION_PARTIAL** — o trabalho residual mínimo
restante é exclusivamente:

1. **Q23** — anexar o Sigma de D e a expressão regular de E exigiria
   estender `Alternative` para suportar assets no meio do texto (não
   apenas um asset por alternativa), uma mudança de schema maior que a
   desta fase. Prioridade menor para D (redundante); prioridade real
   para E (afeta a capacidade de resposta).
2. **Q27** — puramente cosmético, sem perda de conteúdo; menor
   prioridade de todas.

Nenhum dos dois exige heurística geral nova nem apresenta risco de
regressão para 2021. Dado que este é um resultado `PARTIAL`, não
`SUCCESS`, a recomendação de revisar/commitar as Fases 2A-2E e iniciar
2008 como próximo teste de generalização **não se aplica ainda** - não
deve ser iniciada automaticamente. Recomenda-se, antes disso, uma
revisão integral do diff das Fases 2A-2E (agora consolidado e estável)
e um checkpoint/commit separado, já que o pipeline está a apenas 2
questões, ambas de baixo risco e bem compreendidas, de `GENERALIZATION_
SUCCESS`.
