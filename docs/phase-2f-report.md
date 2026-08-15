# Phase 2F — Adjudicação dos Cinco Blockers Abertos e Promoção Condicional do Corpus 2011

## A. Classificação

**GENERALIZATION_SUCCESS.**

- 55/55 questões com `visual_validation: passed` (0 `failed`, 0 `not_performed`).
- Blocker ledger: 38 registros, **0 `open`**, 31 `resolved`, 3
  `resolved_by_visual_fallback`, 2 `superseded`, 2
  `accepted_non_material_difference` (novo status geral introduzido
  nesta fase).
- Gold 2011: `maturity: validated`.
- `assess-readiness --year 2011 --course all-computing
  --ready-label READY_FOR_LEGACY_LAYOUT_TEST`: **`READY_FOR_LEGACY_LAYOUT_TEST`**,
  exit code 0, 1 finding remanescente (`enade-2011-computing-q34`,
  `question_not_verified`) explicitamente marcado `non-structural` -
  reportado, nunca escondido, mas não bloqueia.
- 2021: `verify-gold` OK (40/40, `validated`), `assess-readiness`
  `READY_FOR_2011`, zero blockers, zero drift em toda checagem desta
  fase.
- Reprodutibilidade: duas extrações independentes de 2011 e o corpus em
  disco - `diff -rq` zero em todos os pares.
- 435 testes passando, `ruff`/`mypy`/`validate-schema`/`validate-manifest`/
  `audit-extraction` limpos.

## B. Estado Git inicial

Confirmado no início desta fase: `HEAD=9593903` ("feat: Enhance
alternative handling for formula images and refine table rendering"),
branch `feat/enade-2011-unified-extraction`, working tree limpo,
sincronizado com `origin/feat/enade-2011-unified-extraction`. `master`/
`origin/master` ambos em `a5dfaab`, inalterados. Confirma, mais uma vez,
que todo o trabalho da Fase 2E foi commitado por ferramenta externa do
usuário entre sessões - o mesmo padrão observado em toda transição de
fase deste projeto. Nenhuma ação corretiva foi tomada.

## C. Cinco blockers iniciais

| ID | Questão | Status inicial | Resultado final |
|---|---|---|---|
| `q23-inline-symbols-residual` | Q23 | open | **resolved** (Seção E) |
| `q27-pseudocode-not-code-block` | Q27 | open | **accepted_non_material_difference** (Seção F) |
| `q23-not-verified` | Q23 | open | **resolved** (consequência de q23-inline-symbols-residual) |
| `q27-not-verified` | Q27 | open | **resolved** (consequência de q27-pseudocode-not-code-block) |
| `q34-not-verified` | Q34 | open | **accepted_non_material_difference** (Seção G) |

## D. Dez motivos de readiness (estado no início desta fase)

| # | Readiness reason | Origem | Blocker ID | Causa primária / consequência |
|---|---|---|---|---|
| 1 | `q23-inline-symbols-residual: still listed...` | `recorded_structural_blocker` | q23-inline-symbols-residual | Consequência (espelha o gold manifest) |
| 2 | `q27-pseudocode-not-code-block: still listed...` | `recorded_structural_blocker` | q27-pseudocode-not-code-block | Consequência |
| 3 | `enade-2011-computing-q23: extraction_status=needs_review` | `question_not_verified` | (via q23-inline-symbols-residual) | Consequência |
| 4 | `enade-2011-computing-q27: extraction_status=needs_review` | `question_not_verified` | (via q27-pseudocode-not-code-block) | Consequência |
| 5 | `enade-2011-computing-q34: extraction_status=needs_review` | `question_not_verified` | (via q34-not-verified) | Consequência de uma limitação aceita, não de defeito |
| 6 | `q23-inline-symbols-residual (...)` | `blocker_ledger_open` | q23-inline-symbols-residual | **PRIMÁRIA** |
| 7 | `q27-pseudocode-not-code-block (...)` | `blocker_ledger_open` | q27-pseudocode-not-code-block | **PRIMÁRIA** |
| 8 | `q23-not-verified (...)` | `blocker_ledger_open` | q23-not-verified | Bookkeeping |
| 9 | `q27-not-verified (...)` | `blocker_ledger_open` | q27-not-verified | Bookkeeping |
| 10 | `q34-not-verified (...)` | `blocker_ledger_open` | q34-not-verified | Limitação aceita |

Confirmado: os 10 motivos eram uma combinação de **2 defeitos reais**
(Q23, Q27) + **1 limitação aceita** (Q34) + **7 gates
derivados/consequências** - nunca 10 defeitos independentes. Todos os 10
foram eliminados nesta fase: 8 via `resolved` (as consequências diretas
somem quando a causa primária fecha corretamente), 2 via
`accepted_non_material_difference` (a causa primária de Q27, e a causa
raiz de Q34) - o único motivo que sobrevive ao final é um NOVO,
explicitamente não-estrutural, `question_not_verified` para Q34,
mantido visível por design (Seção G).

## E. Q23 — símbolos D/E

**Investigação** (sem transcrição por inferência - cada símbolo
confirmado por renderização direta em alta resolução):

| Alternativa | Página | Bbox (pt) | Dimensões | Texto anterior | Texto posterior | Conteúdo visual confirmado |
|---|---|---|---|---|---|---|
| D | 14 | (503.51, 462.06, 511.91, 471.26) | 8.4×9.2 | "o autômato reconhece a linguagem sobre" | "em que os strings possuem o prefixo ababc." | `Σ` |
| E | 14 | (313.47, 520.90, 447.07, 533.30) | 133.6×12.4 | "a linguagem reconhecida pelo autômato é a mesma que a representada pela expressão regular" | "." | `(a+b+c)*(ab)*abc(a+b+c)*.` |

**Estrutura adotada**: `Alternative.content_blocks: list[ContentBlock] |
None` - reaproveita **exatamente** o mesmo union `ContentBlock`
(`ParagraphBlock`/`AssetBlock`) já definido para
`Question.content_blocks` (Fase 1C), nenhuma taxonomia nova. Uma nova
função de extração, `_attach_alternative_inline_segments`, complementa o
mecanismo de asset único da Fase 2E (`_attach_alternative_formula_regions`,
para alternativas totalmente vazias - Q14) com o caso de texto real
intercalado com um ou mais símbolos pequenos. Um novo helper,
`_merge_alternative_reading_order`, funde as linhas próprias da
alternativa com as regiões candidatas sobrepondo sua própria linha em
uma única sequência de leitura, ancorando cada região à linha cuja faixa
Y ela sobrepõe (nunca ao seu próprio y0, que pode divergir levemente por
métrica de fonte).

**Dois bugs reais encontrados e corrigidos durante a implementação**
(nenhum capturado por teste unitário isolado - só por inspeção visual
direta dos assets renderizados):

1. Uma primeira versão, que só verificava o tamanho atual do bbox da
   região candidata, capturou a região grande das produções da gramática
   de Q23 (205×151.6pt) para as alternativas A/B/C também, já que ela
   geometricamente sobrepunha as linhas delas. Corrigido com um novo
   campo de proveniência, `VisualRegion.is_small_formula`, setado apenas
   pelo pool de candidatos pequenos na construção - nunca re-derivado do
   tamanho atual do bbox (o que quebraria Q14, cuja região fundida de 5
   fórmulas legitimamente excede `SMALL_IMAGE_MAX_HEIGHT` mesmo sendo
   composta só de elementos pequenos).
2. Uma segunda passagem de deslocamento de índices (contabilizando que
   as figuras do enunciado vêm antes das anexadas às alternativas na
   lista final `figure_regions`) atualizava só o campo antigo
   `figure_region_index` (Fase 2E), nunca o novo `segments` - aliasing
   silencioso da alternativa D para a primeira figura do enunciado.
   Encontrado por inspeção visual direta, reproduzido e corrigido via um
   teste de integração dedicado que exercita o pipeline completo com uma
   figura de enunciado e uma de alternativa juntas.

**Assets finais**: `figure-04.png` (D, mostra exatamente `Σ`),
`figure-05.png` (E, mostra exatamente `(a+b+c)*(ab)*abc(a+b+c)*.`).

**Validação**: comparação completa do Markdown de Q23 contra o PDF
oficial (não apenas os dois recortes) - enunciado completo; alternativas
A-E completas (A/B/C texto puro inalterado; D/E com o símbolo próprio na
posição correta); zero conteúdo de Q22 (reverificado); zero asset órfão
(gate de integridade: 42 assets, zero hash divergente, zero órfão, zero
colisão de caminho entre questões); zero contaminação de coluna. Um
resíduo cosmético já disclosed desde a Fase 2E permanece (fragmentos
"que"/"de" redundantes perto de `figure-03.png`, mesma classe do "A
função" de Q9) - não é perda de conteúdo, não afeta nenhuma alternativa.

## F. Q27 — divergência de apresentação

**Divergência objetiva**: o PDF renderiza o pseudocódigo de 7 linhas
como um bloco visualmente distinto (parágrafo próprio, numeração 1-7,
indentação crescente); o Markdown renderiza o mesmo texto como uma
sentença inline contínua (quebras de linha e indentação colapsadas pelas
regras normais de junção de prosa), mas todo o texto de cada linha -
números, colchetes, nomes de variáveis, índices - presente, completo, na
ordem exata correta.

**Impacto**: não oculta conteúdo; não duplica conteúdo; não altera
interpretação (o significado do algoritmo é 100% preservado,
inequívoco); afeta acessibilidade de forma mínima (uma ferramenta de
leitor de tela/busca não reconhece isso como bloco de código formatado,
embora o texto continue plenamente legível/pesquisável); não afeta o
gabarito (as afirmações I-IV não dependem de formatação visual).

**Classificação**: `presentation_fidelity` (defeito primário) +
`accessibility_limitation` (secundário, menor). Explicitamente NÃO
`content_loss`, NÃO `semantic_risk`, NÃO `ownership_contamination`.

**Adjudicação**: uma nova heurística geral de detecção de bloco de
código (ex.: "linhas numeradas com indentação crescente, mesmo em fonte
não-monoespaçada") foi considerada e rejeitada - exigiria o mesmo rigor
de regressão completa contra 2021 já historicamente demandado por
qualquer mudança de Nível 1, para um caso único, sem perda de conteúdo,
já aceito em outro lugar (Q46, D4) sem correção. Como nenhum status
existente do ledger capturava com precisão "diferença verificada e não
material, aceita formalmente, mas nada foi tecnicamente corrigido", foi
adicionado um novo `BlockerStatus`, **`accepted_non_material_difference`**
- geral (cobre também o caso de Q34, Seção G), com semântica
documentada, não bloqueia readiness (`Blocker.is_open` continua `False`
para ele), exige `evidence`+`regression_tests` (mesma barra de
`resolved*`), contado em sua própria propriedade separada
(`accepted_non_material_difference_count`) - nunca confundido com
`resolved_count`.

**Evidência**: `docs/decisions.md`, Phase 2F ADR 43.

## G. Outros três blockers (`q23-not-verified`, `q27-not-verified`, `q34-not-verified`)

- **`q23-not-verified`**: consequência direta de `q23-inline-symbols-
  residual` - resolvido automaticamente quando a causa primária fechou
  (Seção E); `extraction_status` de Q23 agora `verified`.
- **`q27-not-verified`**: consequência direta de
  `q27-pseudocode-not-code-block` - marcado `resolved` (não
  `accepted_non_material_difference`, já que o próprio
  `extraction_status` de Q27 SEGUE `verified` normalmente uma vez que
  `visual_validation` é promovido, ao contrário de Q34).
- **`q34-not-verified`**: reproduzido e confirmado - Q34 tem
  `visual_validation: passed` (conteúdo correto, confirmado
  visualmente desde a Fase 2A/2B), mas `extraction_status` nunca chega a
  `verified` porque `validator.py`'s própria regra conservadora ("uma
  questão com qualquer aviso mecânico sempre vai para `needs_review`,
  independente da causa") dispara incondicionalmente para o aviso
  "figure region(s) fell after the alternatives cutoff", mesmo quando
  `assets=[]` é o resultado correto (nada foi de fato perdido). Uma
  correção de código geral (relaxar essa classe específica de aviso) foi
  considerada e **rejeitada**: essa regra conservadora é uma proteção
  deliberada e fundamental, compartilhada por toda questão em 2011 E
  2021 - afrouxá-la arrisca promover silenciosamente um caso
  genuinamente quebrado em outro lugar do corpus que compartilhe a mesma
  forma superficial. Adjudicado como `accepted_non_material_difference`
  (a segunda forma coberta pelo status, ver Seção F) - **não** como
  "resolved" (nada foi corrigido tecnicamente).

Nenhum dos três exigiu se tornar `superseded` ou ser identificado como
duplicata - cada um permanece exatamente o que sua própria descrição
sempre disse que era, agora com um status terminal preciso.

## H. Contrato de alternativas

- `Alternative.content_blocks: list[ContentBlock] | None = None` -
  aditivo, retrocompatível; `None` para a esmagadora maioria das
  alternativas (texto puro).
- `Alternative.asset` (Fase 2E) preservado sem nenhuma alteração de
  comportamento - reverificado byte-idêntico para Q14.
- Validação: `Question._validate_content_blocks` estendida para também
  percorrer `alt.content_blocks` de cada alternativa, checando que todo
  `AssetBlock.asset_id` referencia um asset declarado em
  `Question.assets` (a mesma fonte única de verdade que qualquer outra
  referência de asset já usa) - uma referência quebrada gera
  `ValidationError`, nunca um asset fabricado.
- Parser/renderer Markdown: uma alternativa com `content_blocks`
  renderiza inline (`D. texto ![Alternativa D](path) texto`), com
  suporte a **múltiplos** assets na mesma alternativa; o parser
  distingue o formato de asset único da Fase 2E (imagem na posição 0,
  só pontuação depois) do formato intercalado da Fase 2F (qualquer outro
  padrão) por um sinal posicional inequívoco, nunca por contagem de
  correspondências isolada.
- Round-trip: `render → parse → Question.model_validate` confirmado
  exato (testes dedicados em `test_markdown_format.py` e
  `test_schema_question.py`).
- Um asset referenciado no corpo sem entrada correspondente em `assets`
  resolve para `None`/bloco omitido - nunca fabricado.
- Nenhum question ID na lógica central (`assembler.py`,
  `markdown_format.py`, `models/question.py`) - confirmado por varredura.

## I. Ownership e assets

- `VisualRegion.is_small_formula` (novo campo de proveniência) impede
  que uma região estatutária grande seja tratada como candidata de
  fórmula de alternativa, e sobrevive corretamente a merges (`AND`
  lógico entre os dois lados).
- `ownership.render_bounds_for_owner` agora usado em 3 pontos
  (`figures.py` ×2, `pipeline.py`'s próprio loop de renderização de
  tabelas) - nenhuma duplicação de lógica.
- Gate de integridade de asset (script dedicado, corpus completo): 42
  referências de asset resolvidas, zero hash divergente, zero arquivo
  órfão, zero caminho duplicado entre questões diferentes.
- Assets de D/E confirmados pertencendo simultaneamente à Q23 correta,
  à alternativa correta, e à posição correta dentro do texto da
  alternativa (verificado via `owner_key` e inspeção visual direta).

## J. Auditoria visual

55/55 IDs no `visual-audit-2011-computing.json` (`not_performed=0`).
**`passed=55, failed=0`.** Reinspecionadas nesta fase: Q22, Q23, Q27 (as
únicas questões cujo Markdown ou assets mudaram - confirmado via `git
status`). Q14 revalidada (mecanismo `Alternative.asset` intocado,
byte-idêntica). As 52 questões restantes permanecem byte-idênticas ao
estado da Fase 2E, preservando legitimamente sua auditoria anterior.

## K. Ledger final

38 registros totais: **0 `open`**, 31 `resolved`, 3
`resolved_by_visual_fallback`, 2 `superseded`, 2
`accepted_non_material_difference`. Soma: 31+3+2+2=38. `validate_ledger`:
zero issues. Nenhum registro desapareceu; `baseline_count` permanece 32
(constante histórica, nunca reescrita).

## L. Padrões D1-D5

Todos os 5 permanecem `passed`, inalterados nesta fase - confirmado por
`git status` mostrando zero diff para os arquivos D1-D5. Nenhuma mudança
em alternativas objetivas quebrou nenhuma questão discursiva.

## M. Provas virtuais

Revalidadas após todas as correções desta fase, diretamente contra os
55 arquivos reais em disco:

| Curso | Objetivas | Discursivas | Total | Issues |
|---|---|---|---|---|
| ciencia-da-computacao-bacharelado | 35 | 5 | 40 | nenhuma |
| ciencia-da-computacao-licenciatura | 35 | 5 | 40 | nenhuma |
| engenharia-da-computacao | 35 | 5 | 40 | nenhuma |
| sistemas-de-informacao | 35 | 5 | 40 | nenhuma |

Zero duplicação, zero contaminação entre cursos, ordem correta, Q23/Q27
atribuídas somente aos cursos corretos, D1-D5 presentes.

## N. Gold 2011

`maturity`: `provisional` → **`validated`** (promovido nesta fase, na
ordem exigida: corrigir → testar → extrair → reauditar → fechar
blockers → verificar critérios → **então** promover → reexecutar
`verify-gold`/`assess-readiness`/suíte completa). `structural_blockers`
agora vazio (`[]`) - reconstruído sem nenhum blocker estrutural
registrado, refletindo o estado real: zero blockers abertos no ledger.
`verify-gold`: OK, 55/55 hashes conferem contra o gold recém-travado.

## O. Readiness

`assess-readiness --year 2011 --course all-computing
--ready-label READY_FOR_LEGACY_LAYOUT_TEST
--not-ready-label NOT_READY_FOR_LEGACY_LAYOUT_TEST`:

```
assess-readiness: READY_FOR_LEGACY_LAYOUT_TEST
  54/55 verified, 1 needs_review, gold maturity=validated
  visual audit: 55 passed, 0 failed, 0 not_performed (fully_covered=True)
  1 blocker(s):
    - [question_not_verified, non-structural] enade-2011-computing-q34: extraction_status=needs_review
exit code: 0
```

Mecanismo novo: `ReadinessBlocker.structural` (campo já existente,
nunca antes ativado) agora é consultado por `ReadinessReport.ready`
(`not any(b.structural for b in blockers)`, não mais `not blockers`
cru). `assess_readiness` carrega o ledger antecipadamente para saber
quais `question_id`s têm um blocker `accepted_non_material_difference`
próprio, marcando o `question_not_verified` correspondente como
`structural=False` - reportado, nunca escondido (`cli.py` já imprimia a
tag `structural`/`non-structural`, outro recurso dormente finalmente
exercitado), mas não contado para readiness. Uma entrada do ledger não
relacionada (question_id diferente) nunca suprime um achado real e não
documentado (testado explicitamente).

## P. Proteção de 2021

Verificado no início desta fase e após cada mudança de código
compartilhado (5 vezes ao todo, incluindo depois da promoção do gold
2011):

- `verify-gold --year 2021 --course ciencia-da-computacao-bacharelado`:
  OK, 40/40, `maturity=validated`, em toda checagem.
- `assess-readiness`: `READY_FOR_2011`, 40/40 verified, 0 needs_review,
  **zero blockers**, em toda checagem.
- `enade extract --year 2021 ...`: `files written: 0, unchanged: 40`,
  em toda checagem.
- `git status --short data/questions/2021/`: limpo em toda checagem.
- 2021 nunca foi atualizado; gold 2021 nunca foi tocado; nenhuma
  regressão em nenhum ponto, incluindo a introdução do novo mecanismo
  `accepted_non_material_difference`/`structural` (2021 não tem nenhuma
  entrada desse tipo no ledger, então o mecanismo é um no-op para ele).

## Q. Testes

**435 no total** (418 herdados do fim da Fase 2E + 17 novos desta fase:
1 teste de integração completo para a interação figura-de-enunciado +
asset-de-alternativa; testes unitários para
`_attach_alternative_inline_segments`/`_merge_alternative_reading_order`;
7 testes para `Alternative.content_blocks` em `test_schema_question.py`
(default, ordem, asset-no-início, dois-assets-intercalados, asset
inexistente/hash indeclarado, `Alternative.asset` preservado,
round-trip Markdown); 5 testes para `accepted_non_material_difference`
em `test_blocker_ledger.py`; 3 testes para o mecanismo
`structural`/ledger-covered em `test_readiness.py`) - todos passando.

## R. Quality gates

```
pytest -q                                     -> 435 passed
ruff check .                                  -> All checks passed!
ruff format --check .                         -> 292 files already formatted
mypy src                                      -> Success: no issues found in 52 source files
enade validate-schema                         -> 13/13 fixture(s) valid
enade validate-manifest                       -> OK (0 warning(s))
enade audit-extraction --questions-dir ...    -> 55/55 OK
enade verify-gold --year 2021 --course cc-b   -> OK (40/40), maturity=validated
enade assess-readiness --year 2021 ...        -> READY_FOR_2011, no blockers
enade verify-gold --year 2011 --course all... -> OK (55/55), maturity=validated
enade assess-readiness --year 2011 ...        -> READY_FOR_LEGACY_LAYOUT_TEST, exit 0
```

Gate de integridade de asset (script dedicado): 45 referências de asset,
42 caminhos únicos, zero hash mismatch, zero órfão, zero duplicata entre
questões.

## S. Reprodutibilidade

Duas extrações limpas e independentes de 2011 (diretórios separados):
`diff -rq` entre as duas - **zero diferença**. Uma delas comparada
diretamente contra o corpus em disco - **zero diferença** também,
confirmando que o repositório reflete exatamente o que o pipeline
determinístico produz.

## T. Bugs encontrados nesta fase

1. **Filtro de tamanho re-checado após merge** (regressão descoberta
   durante o próprio desenvolvimento, nunca chegou a afetar o corpus
   publicado): uma primeira implementação do filtro de candidato de
   fórmula de alternativa verificava o tamanho ATUAL do bbox da região,
   rejeitando a própria região legítima e fundida de Q14 (5 fórmulas,
   bbox resultante > 40pt de altura) - corrigido com um campo de
   proveniência (`is_small_formula`) em vez de re-checar tamanho.
2. **Segunda passagem de offset de índice incompleta** (mesma situação -
   descoberta e corrigida durante o desenvolvimento): atualizava só
   `figure_region_index`, não o novo `segments`, causando aliasing
   silencioso do asset da alternativa D de Q23 para a primeira figura do
   enunciado. Encontrado por inspeção visual direta do asset renderizado
   (mostrava o diagrama errado), não por nenhum teste unitário isolado -
   levou à criação de um teste de integração dedicado especificamente
   para essa classe de interação.
3. **Grandes regiões estatutárias sobrepondo linhas de alternativas**
   (Q23's grammar-productions region overlapping A/B/C's own rows): um
   achado geométrico real sobre a própria estrutura do PDF, não um bug
   de código per se, mas que expôs a necessidade do filtro de
   proveniência acima.

Nenhum desses bugs chegou a ser commitado ou publicado - todos foram
encontrados e corrigidos dentro desta mesma sessão de trabalho, antes de
qualquer extração final.

## U. Arquivos

**Modificados (código-fonte, 6 arquivos)**: `src/enade/extraction/
{assembler,blocker_ledger,figures,to_question}.py`,
`src/enade/markdown_format.py`, `src/enade/models/question.py`,
`src/enade/readiness.py`

**Modificados (testes, 4 arquivos)**: `tests/test_blocker_ledger.py`,
`tests/test_extraction_assembler.py`, `tests/test_readiness.py`,
`tests/test_schema_question.py`

**Modificados (manifests/dados)**: `data/manifests/{blocker-ledger-2011.yaml,
extraction-audit-2011-computing.{csv,json},gold-2011-computing.json,
visual-audit-2011-computing.json}`

**Modificados (documentação)**: `docs/decisions.md` (+3 ADRs, seções
42-44); `docs/phase-2f-report.md` (este arquivo, novo)

**Modificados/novos (dados extraídos, 2011 apenas)**: `enade-2011-
computing-q23.md` (conteúdo real mudou - D/E agora completos) e
`enade-2011-computing-q27.md` (só metadados: `extraction_status`/
`visual_validation` promovidos, corpo do texto inalterado); 2 assets PNG
novos (`q23/figure-04.png`, `q23/figure-05.png`).

**Nada foi removido.** Nenhum arquivo de 2021 foi tocado.
`data/manifests/layout-overrides.yaml` não mudou nesta fase (nenhum
override novo foi necessário - toda correção usou mecanismo de código
geral).

## V. Estado Git final

`HEAD=9593903` (inalterado - nenhum commit foi feito nesta fase),
branch `feat/enade-2011-unified-extraction`, `master`/`origin/master`
ambos `a5dfaab`, inalterados. **Nenhum commit, push, merge, rebase, tag
ou PR foi criado nesta fase.** 21 itens com mudanças no working tree (19
modificados + 2 novos não-rastreados), prontos para revisão do usuário.

## W. Recomendação

Dado o resultado **GENERALIZATION_SUCCESS**, recomenda-se:

1. **Revisão integral do diff acumulado das Fases 2A-2F** antes de
   qualquer commit - o working tree atual representa a soma de seis
   fases de trabalho sobre a mesma branch, nunca commitada
   incrementalmente por decisão explícita do usuário ao longo de todo o
   projeto.
2. **Checkpoint/commit separado** antes de processar qualquer novo
   corpus - consolidar este marco (2011 unificado, `validated`,
   `READY_FOR_LEGACY_LAYOUT_TEST`) como um ponto de recuperação estável.
3. **2008 como próximo teste de layout legado** - o objetivo original
   desta linha de fases (generalizar o pipeline além do booklet único de
   2021) está agora demonstrado com um segundo formato estruturalmente
   diferente (2011, multi-curso, duas colunas) processado com
   fidelidade completa e zero regressão em 2021.

**Esta fase não inicia 2008 automaticamente** - a decisão de avançar,
assim como o commit das Fases 2A-2F, permanece com o usuário.
