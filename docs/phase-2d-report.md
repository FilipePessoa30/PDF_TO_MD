# Phase 2D — Adjudicação dos Blockers e Fechamento Documental do ENADE 2011

## A. Classificação final

**GENERALIZATION_PARTIAL.** 51/55 questões com `visual_validation: passed`
(4 permanecem `failed`: Q14, Q23, Q27, Q38); gold 2011 permanece
`provisional`; 2021 permanece protegido e byte-idêntico em todos os
pontos de verificação.

**NOT_READY_FOR_LEGACY_LAYOUT_TEST** — `assess-readiness --year 2011
--course all-computing` retorna 20 blockers (5 blockers de conteúdo
estrutural ainda abertos, mais seus espelhos `*-not-verified`/
`recorded_structural_blocker`/`question_not_verified`). Nenhum blocker
estrutural pode permanecer aberto para `READY_FOR_LEGACY_LAYOUT_TEST`;
isso não ocorre aqui.

Nenhuma heurística geral nova foi criada apenas para reduzir a contagem
de blockers. Toda resolução usou um mecanismo já comprovado
(`force_fraction_merge`, `protect_from_region_membership`, extensão da
tabela fechada de `symbol_fonts.py`, extensão do próprio modelo de
propriedade espacial `ownership.py` para o estágio de renderização) ou
uma correção de escopo estritamente local (`_rescue_table_row_numbers`).

## B. Estado git inicial e final

**Inicial** (verificado no início da fase): `HEAD=d696fb3` ("Implement
ownership model for visual regions and enhance readiness checks"),
branch `feat/enade-2011-unified-extraction`, working tree limpo. `master`
e `origin/master` ambos em `a5dfaab`, inalterados desde o início do
projeto. Confirma que todo o trabalho da Fase 2C foi commitado por
ferramenta externa do usuário entre sessões — padrão já observado em
toda transição de fase deste projeto; nenhuma ação corretiva foi tomada
(apenas confirmar e encerrar, conforme orientação já estabelecida).

**Final**: `HEAD=d696fb3` (inalterado — nenhum commit foi feito nesta
fase, conforme exigido). `master`/`origin/master` ainda em `a5dfaab`,
inalterados. 64 arquivos com mudanças no working tree (59 modificados
com diff stat: 2047 inserções, 759 remoções; 5 novos arquivos não
rastreados — 3 assets PNG + 2 arquivos de teste). `git diff --check`:
sem erros de whitespace (apenas avisos informativos de conversão
LF→CRLF, específicos do Windows). Nenhum commit, push ou PR foi feito.

## C. Matriz de adjudicação — os 23 blockers abertos no início da fase

| Blocker | Questão | Categoria | Causa confirmada | Afeta resposta? | Solução mínima | Risco 2021 | Status final |
|---|---|---|---|---|---|---|---|
| q09-math-notation-loss | Q09 | asset_contamination (descoberto) + math-notation | Contaminação cross-coluna (novo) + conteúdo já presente via imagem | Não (itens I/II/IV textuais, III via figura) | Fix geral de largura de crop + fallback visual já existente | Nenhum (gate de coluna) | **resolved_by_visual_fallback** |
| q10-fraction-numerators-lost | Q10 | missing_inline_raster (texto, não imagem) | Numerador órfão descartado por chrome.py | Sim (5 alternativas) | `force_fraction_merge` (override hash+bbox) | Nenhum (override locked ao SHA-256) | **resolved** |
| q12-grammar-block-missing | Q12 | boundary_error (growth cap) | `MAX_ABSORPTION_GROWTH` como teto rígido | Sim (item IV) | `protect_from_region_membership` | Nenhum (override locked) | **resolved** |
| q14-alternatives-empty | Q14 | prose_absorbed_by_asset / missing_inline_raster | Alternativas via regex textual, sem attachment de imagem por letra | Sim (5 alternativas ficam vazias) | Generalização `inline_asset` (não implementada) | N/A | **open** (inalterado) |
| q20-missing-second-assertion | Q20 | figure-region-absorption | Já resolvido na Fase 2C | — | — | — | resolved (herdado) |
| q23-inline-symbols-residual | Q23 | missing_inline_raster | Símbolos Σ/λ nunca preservados (texto nem asset) | Marginal (contexto ainda permite responder) | Não tentado (fora de escopo) | N/A | **open** (inalterado) |
| q24-q25-q26-... | — | asset_contamination | Já resolvido na Fase 2C | — | — | — | resolved (herdado) |
| q27-pseudocode-not-code-block | Q27 | metadata_only (formatação) | Fonte não-monoespaçada na origem | Não (conteúdo 100% presente) | Não tentado (cosmético, precedente Q46) | N/A | **open** (inalterado) |
| q38-q40-cross-question-figure-contamination | Q38/Q40 | asset_contamination | Já superseded na Fase 2C (parcialmente correto) | — | — | — | superseded (mantido) |
| q43-q44-q45-q48-lead-in-sentence-loss | Q43/44/45/48 | figure-region-absorption | Já superseded na Fase 2C | — | — | — | superseded (mantido) |
| d03-arrow-glyph-corruption | D3 | source_ambiguity → font substitution | Fonte Wingdings-Regular, codepoint 0xC5 | Sim (pseudocódigo do padrão de resposta) | Extensão de `symbol_fonts.py` | Nenhum (tabela fechada por fonte+codepoint) | **resolved** |
| d03-fibonacci-formula-missing | D3 | math-notation | Já resolvido na Fase 2C | — | — | — | resolved_by_visual_fallback (herdado) |
| d05-answer-standard-bit-width-tables-missing | D5 | table_incomplete | Números de tabela tratados como chrome (rodapé) | Sim (3 tabelas de bit-width) | `_rescue_table_row_numbers` (heurística local) | Nenhum (2021 não tem tabelas de 1 linha comparáveis) | **resolved** |
| q38-remaining-content-defects | Q38 | incorrect_content_order | Gramática BNF intercalada com refs de figura | Não (assertivas PORQUE presentes) | Não tentado (fora de escopo) | N/A | **open**, notas atualizadas |
| q44-q45-q48-remaining-content-loss | Q44/45/48 | boundary_error (growth cap / candidate absorption) | Mesma classe do Q12, confirmada individualmente | Sim (parágrafos, equações, frase de ligação) | `protect_from_label_absorption` (Q44 x4, Q45 x5) + `protect_from_region_membership` (Q48 x1) | Nenhum (overrides locked) | **resolved** |
| q09/q10/q12/q14/q23/q27/q34/q38/q44/q45/q48/d03/d05-not-verified (13 entradas) | — | readiness-status | Espelha o status `extraction_status` de cada questão | — | — | — | 8 **resolved** (q09,q10,q12,q44,q45,q48,d03,d05); 5 **open** (q14,q23,q27,q34[deliberado],q38) |

Todos os 23 blockers abertos no início da fase foram individualmente
adjudicados; nenhum foi fechado sem evidência (cada `resolved` tem
`evidence` + `regression_tests` populados, exigido por
`validate_ledger`).

## D. Contagens finais do ledger de blockers

- `baseline_count`: 32 (constante histórica da Fase 2B, nunca reescrita)
- Total de blockers no ledger: **38** (34 originais + 4 novos encontrados
  nesta fase)
- Abertos no início da fase: 23
- Resolvidos nesta fase: 17 (14 dos 23 originais + 3 novos, já
  encontrados e corrigidos na mesma fase)
- `resolved_by_visual_fallback`: 2 (q09-math-notation-loss,
  d03-fibonacci-formula-missing — este último herdado da Fase 2C)
- `source_ambiguity`: 0
- `superseded`: 2 (inalterado — histórico preservado, nunca deletado)
- Estruturalmente aberto (bloqueia prontidão): **10** — soma:
  `open(10) + resolved(26) + superseded(2) + source_ambiguity(0) +
  not_reproducible(0) = 38 = total`. `validate_ledger` roda limpo, zero
  issues.
- Nenhum blocker desapareceu; nenhum ID foi reutilizado ou deletado.

## E. As 12 questões reprovadas no início da fase — antes/depois

| Questão | Antes (início Fase 2D) | Depois (fim Fase 2D) |
|---|---|---|
| Q09 | `failed` — resíduo "A função" sem continuação | **`passed`** — conteúdo completo via imagem, contaminação corrigida, fragmento duplicado documentado como cosmético |
| Q10 | `failed` — todos os 5 numeradores ausentes | **`passed`** — 5 frações completas via override hash-locked |
| Q12 | `failed` — item IV cortado | **`passed`** — item IV recuperado, imagem da gramática confirmada limpa |
| Q14 | `failed` — alternativas vazias | **`failed`** (inalterado) — imagens confirmadas limpas e completas, mas ainda não posicionadas por alternativa |
| Q23 | `failed` — símbolos Σ/λ ausentes | **`failed`** (residual real inalterado) — mas contaminação cross-coluna (Q22) corrigida, achado novo desta fase |
| Q27 | `failed` — pseudocódigo sem formatação de bloco | **`failed`** (inalterado) — cosmético, sem perda de conteúdo |
| Q38 | `failed` — o caso mais danificado do corpus | **`failed`** (grande melhoria) — contaminação com Q40 corrigida (achado novo), parágrafo de ambiguidade hex confirmado via imagem limpa, PORQUE confirmado presente; permanece a ordem intercalada da gramática BNF |
| Q44 | `failed` — 3 parágrafos + 2 equações ausentes | **`passed`** — conteúdo completo, 3 imagens próprias posicionadas corretamente |
| Q45 | `failed` — frase de abertura + itens II-V ausentes | **`passed`** — conteúdo completo |
| Q48 | `failed` — frase de ligação ausente | **`passed`** — conteúdo completo |
| D3 | `failed` — setas do padrão de resposta corrompidas | **`passed`** — substituição Wingdings aplicada |
| D5 | `failed` — 3 tabelas de bit-width ausentes no padrão | **`passed`** — heurística de resgate de linhas numéricas |

**8 de 12 promovidas a `passed`; 4 permanecem `failed`** com residuais
reais, disclosed, e — no caso de Q23/Q38 — com melhorias adicionais
significativas encontradas e corrigidas nesta mesma fase.

## F. Modelo de conteúdo inline (raster inline formulas)

`content_blocks` já suporta intercalação de parágrafo → imagem →
continuação (verificado nas 5 questões corrigidas nesta fase: Q10 via
texto puro, Q12/Q44/Q45/Q48 via `figure_regions` posicionados
inline na ordem correta do documento). A generalização explícita para um
tipo `inline_asset` (Seção 6 do prompt) **não foi implementada** — o
mecanismo existente de posicionamento de `VisualRegion`s na ordem de
leitura já satisfaz os casos resolvidos nesta fase sem precisar dessa
extensão. O único caso que genuinamente precisaria dela é Q14 (anexar
uma fórmula por alternativa), permanece aberto.

## G. Q10 × Q34/2021 — caso de regressão obrigatório

Reproduzido e confirmado nos dois sentidos:

- **Positivo** (`test_merge_orphan_markers_applies_a_matching_fraction_merge_override`):
  as 5 frações de Q10 reconstruídas corretamente, linha/região/ordem
  corretas.
- **Negativo** (`test_merge_orphan_markers_fraction_override_never_matches_unrelated_pairs`):
  modela a forma do grafo de Dijkstra de 2021-Q34 com um `pdf_sha256`
  diferente do declarado no override — resultado `["A\t2", "B\t5", "C\t8"]`,
  zero contaminação cruzada.
- Regeneração completa de 2021: `git status` limpo, `verify-gold`
  40/40, `enade-2021-cc-b-q34.md` byte-idêntico ao estado anterior à
  Fase 2C inteira.

## H. Gates de propriedade (`ownership.py`) e casos de contaminação

`ownership.py` **não foi redesenhado** — permanece a base aceita,
exatamente como instruído. Todos os seus gates originais continuam
válidos e testados. Dois problemas **novos e distintos**, em estágios
*fora* de `ownership.py`, foram encontrados e corrigidos:

1. **`assets.py`'s `_render_bbox`** (estágio de renderização, pós-clip):
   alargava todo crop até a largura de conteúdo da página inteira, sem
   noção de colunas — reabrindo o clip que `ownership.py` já havia
   aplicado corretamente à região. Corrigido com `VisualRegion.owner_x_bounds`,
   aplicado apenas em páginas genuinamente de duas colunas. Afetou Q09 e
   Q23 (ambas confirmadas limpas após a correção); Q17 (página de coluna
   única) foi testado e confirmado **não afetado** — um diagrama de
   largura total pode legitimamente exceder a bbox textual da própria
   questão, e a correção respeita isso.

2. **`figures.py`'s `_merge_overlapping_regions`** (estágio de
   pós-processamento de página inteira): mesclava quaisquer duas regiões
   com sobreposição substancial em Y, sem checar se pertenciam a
   diferentes owners — mesmo já corretamente clipadas por
   `ownership.py`. Corrigido com `VisualRegion.owner_key`, recusando
   fusão entre owners diferentes. Este é precisamente o par Q38/Q40, o
   caso de regressão nomeado do próprio ADR 29 (Fase 2C) — a fusão
   indevida sobreviveu ao fix da Fase 2C porque acontecia em um estágio
   posterior e diferente do que aquele fix cobria.

**Casos de regressão obrigatórios, todos confirmados**: Q24/Q25 (limpo),
Q26 (limpo), Q38/Q40 (corrigido nesta fase — a contaminação *residual*
não pega pelo fix original da Fase 2C), todos os casos previamente
corrigidos (Q6, Q20, Q22, Q23-símbolos), 2021 completo (zero drift).

## I. Overrides declarativos — ativos, removidos, superseded nesta fase

**Novos ativos** (16 entradas, todas hash-locked ao SHA-256 de
`1_prova.pdf`, `status: reviewed`):
- 5× `force_fraction_merge` (Q10, uma por alternativa)
- 2× `protect_from_region_membership` (Q12 item IV; Q48 frase de ligação)
- 9× `protect_from_label_absorption` (Q45 itens I-V; Q44 4 fragmentos)

Nenhum override foi removido ou superseded nesta fase (nenhuma
correção anterior precisou ser desfeita). Todos passam por
`validate_ledger`-equivalente (schema Pydantic `extra="forbid"`,
`pdf_sha256` obrigatório, `bbox` validado).

## J. Auditoria visual — passou/reprovou/não realizado

55/55 questões têm entrada em `visual-audit-2011-computing.json`
(`not_performed = 0`). 51 `passed`, 4 `failed`. Nenhuma entrada ausente,
nenhuma reescrita não-determinística entre execuções (confirmado pela
checagem de reprodutibilidade, Seção Q).

## K. D1-D5 — completude

Todos os 5 discursivos agora `passed`: texto, assets, fórmulas e
proveniência revalidados. D1/D2/D4 inalterados nesta fase (confirmados
sem diff). D3: estatement já resolvido na Fase 2C, padrão de resposta
(setas Wingdings) resolvido nesta fase. D5: estatement já correto,
padrão de resposta (3 tabelas de bit-width) resolvido nesta fase.
5/5 padrões de resposta vinculados (`answer standards linked: 5/5`).

## L. Os 4 exames virtuais

Materializados e validados diretamente contra os 55 arquivos reais em
disco (não apenas fixtures sintéticas de teste unitário):

| Curso | Objetivas | Discursivas | Total | Issues |
|---|---|---|---|---|
| ciencia-da-computacao-bacharelado | 35 | 5 | 40 | nenhuma |
| ciencia-da-computacao-licenciatura | 35 | 5 | 40 | nenhuma |
| engenharia-da-computacao | 35 | 5 | 40 | nenhuma |
| sistemas-de-informacao | 35 | 5 | 40 | nenhuma |

Zero duplicação, zero vazamento entre cursos, ordem correta
(`question_number` ascendente), gabarito e assets corretos em todos os
4 conjuntos.

## M. Gold 2011

`maturity: provisional` (mantido — não promovido, corretamente, dado que
4 questões permanecem `failed`). Reconstruído nesta fase
(`build-gold`) para travar as mudanças revisadas: 50/55 `verified`, 5
`needs_review`. 5 `structural_blockers` registrados:
`q14-alternatives-empty`, `q22-table-asset-contamination`,
`q23-inline-symbols-residual`, `q27-pseudocode-not-code-block`,
`q38-remaining-content-defects`. `verify-gold`: OK, 55/55 hashes
conferem contra o próprio gold recém-travado.

## N. Proteção do 2021

Verificado no início e após cada mudança geral (não apenas ao final):
- `verify-gold --year 2021 --course ciencia-da-computacao-bacharelado`:
  OK, 40/40, `maturity=validated`
- `assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado`:
  `READY_FOR_2011`, 40/40 verified, 0 needs_review, visual audit 40
  passed/0 failed, **zero blockers**
- `git status --short data/questions/2021/`: limpo em toda checagem
- `enade extract --year 2021 --course ciencia-da-computacao-bacharelado`:
  `files written: 0, unchanged: 40` em toda checagem, inclusive após o
  fix mais profundo (`_merge_overlapping_regions`, ADR 36)
- 2021 nunca foi atualizado; gold 2021 nunca foi tocado.

## O. Testes e gates de qualidade

- Suite de testes: **386 → 407** (+21 nesta fase: 2 fraction-merge, 5
  region-membership, 2 assembler, 2 symbol-fonts, 4
  answer-standard [arquivo novo], 4 merge-ownership-gate, 3
  render-column-bounds [arquivo novo], mais 1 net de ajustes) — todos
  passando.
- `ruff check .`: All checks passed.
- `ruff format --check .`: todos os arquivos formatados.
- `mypy src`: Success, 52 arquivos, zero issues.
- `enade validate-schema`: 13/13 fixtures válidas.
- `enade validate-manifest`: OK, 0 warnings.
- `enade verify-gold --year 2021 ...`: OK.
- `enade assess-readiness --year 2021 ...`: READY_FOR_2011.
- `enade verify-gold --year 2011 --course all-computing`: OK, 55/55.
- `enade assess-readiness --year 2011 --course all-computing
  --ready-label READY_FOR_LEGACY_LAYOUT_TEST ...`:
  NOT_READY_FOR_LEGACY_LAYOUT_TEST, 20 blockers listados
  individualmente.

## P. Reprodutibilidade

Duas extrações limpas e independentes de 2011 (`--questions-dir`/
`--audit-dir` separados): `diff -rq` entre as duas — **zero diferença**,
incluindo Markdown, todos os assets PNG, e os relatórios de auditoria
(CSV/JSON/transformation-log). Confirma que o pipeline é totalmente
determinístico ponta a ponta, incluindo os mecanismos novos desta fase.

## Q. Novos bugs encontrados nesta fase (todos corrigidos, exceto um disclosed)

1. **Contaminação cross-coluna por alargamento de crop sem noção de
   colunas** (`assets.py`) — afetava Q09 e Q23 (achado por inspeção
   visual direta, não estava documentado em nenhuma fase anterior).
   **Corrigido** (ADR 35).
2. **Fusão de regiões sem checagem de owner** (`figures.py`,
   `_merge_overlapping_regions`) — afetava Q38/Q40, uma contaminação
   residual que sobreviveu ao próprio fix de ownership da Fase 2C por
   estar em um estágio diferente do pipeline. **Corrigido** (ADR 36).
3. **Q22's `table-01.png`** — mesma classe do bug 1, mas no caminho de
   `render_table_region`, não tocado nesta fase. **Não corrigido,
   disclosed** como novo blocker aberto (`q22-table-asset-contamination`),
   não afeta o status `passed` de Q22 (o texto/tabela reconstruído já é
   correto; o asset é um fallback supplementar).
4. **Stray "g" glyph em Q38** (não é um bug de código — descoberta sobre
   o próprio PDF fonte): confirmado, via inspeção rawdict, ser um glifo
   `U+0067` genuíno na fonte ArialMT, coexistindo com uma imagem correta
   do mesmo trecho — não um caso de substituição de fonte símbolo (ao
   contrário do Wingdings de D3). Disclosed, não fabricado, imagem
   correta identificada como fonte canônica.

## R. Arquivos novos/modificados/removidos

**Modificados (código-fonte, 7 arquivos)**: `src/enade/extraction/{answer_standard,
assembler,assets,figures,layout,layout_overrides,symbol_fonts}.py`

**Novos (testes, 2 arquivos)**: `tests/test_extraction_answer_standard.py`,
`tests/test_extraction_assets.py`

**Modificados (testes, 5 arquivos)**: `tests/test_extraction_{assembler,
figures,layout,symbol_fonts}.py`, `tests/test_layout_overrides.py`

**Modificados (manifests/dados)**: `data/manifests/{blocker-ledger-2011.yaml,
extraction-audit-2011-computing.{csv,json},gold-2011-computing.json,
layout-overrides.yaml,visual-audit-2011-computing.json}`

**Modificados (documentação)**: `docs/decisions.md` (+7 ADRs, seções
31-37); `docs/phase-2d-report.md` (este arquivo, novo)

**Modificados/novos (dados extraídos, 2011 apenas)**: 16 arquivos
`.md` de questão + seus assets PNG associados (Q06, Q09, Q10, Q12, Q14,
Q20, Q23, Q26, Q38, Q40, Q41, Q44, Q45, Q48, D3, D5); 3 assets PNG
novos (`q38/figure-06.png`, `q38/figure-07.png`, `q44/figure-03.png`).

**Nada foi removido.** Nenhum arquivo de 2021 foi tocado.

## S. Estado git final (confirmação)

`HEAD=d696fb3`, branch `feat/enade-2011-unified-extraction`, `master`/
`origin/master` ambos `a5dfaab`, inalterados. **Nenhum commit, push ou
PR foi criado nesta fase.** 64 arquivos com mudanças no working tree
(59 modificados + 5 novos não-rastreados), prontos para revisão do
usuário.

## T. Recomendação

Classificação **GENERALIZATION_PARTIAL** — os blockers estruturais
restantes são exclusivamente estes 5, todos documentados com evidência
completa:

1. **Q14** — anexar fórmula por alternativa requer a generalização
   `inline_asset` (Seção 6 do prompt): estender `ExtractedAlternative`
   com uma referência opcional a asset e propagá-la em
   `markdown_writer.py`. O conteúdo já está 100% presente e correto em
   `figure-02.png`; falta apenas o posicionamento estrutural.
2. **Q23** — os 3 símbolos inline (Σ, Σ*, λ) permanecem genuinamente
   ausentes de toda representação. Requer nova investigação de captura
   de glifo/imagem pequena, sem inventar notação.
3. **Q27** — puramente cosmético (formatação de bloco de código), sem
   perda de conteúdo; menor prioridade.
4. **Q38** — a ordem da gramática BNF/estados do autômato LR permanece
   intercalada com referências de figura em vez de uma sequência limpa;
   requer trabalho de reordenação de `content_blocks`.
5. **Q22** — `table-01.png` tem a mesma contaminação cross-coluna já
   corrigida em `render_region`, mas não em `render_table_region`. Fix
   mínimo já esboçado no ADR 37: adicionar o mesmo parâmetro
   `column_bounds` a `render_table_region`, calculando o
   `owner_x_bounds` equivalente para `DetectedTable` no ponto de
   chamada em `pipeline.py`.

Nenhum destes 5 é um blocker de alto risco ou exige uma heurística geral
nova — todos têm um caminho de correção estreito e já identificado.
Recomenda-se endereçá-los em uma fase subsequente antes de considerar
2011 pronto para o teste de layout legado (2008). Dado que este é um
resultado `PARTIAL`, não `SUCCESS`, a recomendação do prompt de revisar/
commitar as Fases 2A-2D e iniciar 2008 como próximo teste de
generalização **não se aplica ainda** — não deve ser iniciada
automaticamente.
