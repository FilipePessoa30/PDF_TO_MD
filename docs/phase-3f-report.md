# Fase 3F — Fechamento dos 15 Defeitos Publicados e Contrato de Generalização sem IA Generativa

## A. Classificação

```
LEGACY_LAYOUT_PARTIAL
RESIDUAL_LAYOUT_NOT_STABILIZED
GENERALIZATION_ARCHITECTURE_ESTABLISHED
GENERALIZATION_NOT_YET_VALIDATED
NOT_READY_FOR_2008_ENGINEERING_TEST
```

**`RESIDUAL_LAYOUT_NOT_STABILIZED`**: 62/77 `passed`, 15 `failed`, 0 `not_performed`, 3
excluídas — número absoluto de `passed` inalterado frente ao início da fase (Q13 permanece
`failed`, agora por uma causa diferente e menor). `LEGACY_LAYOUT_FAILED` não se aplica: nenhuma
reatribuição enganosa, nenhuma perda/duplicação de asset introduzida por esta fase (a única
duplicação de imagem existente — Q13/Q12 — foi corrigida, não criada, aqui), 2011/2021
permanecem byte-a-byte idênticos em todas as verificações.

**`GENERALIZATION_ARCHITECTURE_ESTABLISHED`**: o contrato (`docs/generalization-contract.md`)
foi escrito, o registro de capacidades (`data/manifests/extraction-capabilities.json`) foi
criado com 8 entradas classificadas por nível G0–G4, um gate estático (AST-based,
`tests/test_generalization_architecture.py`) verifica automaticamente que nenhum módulo central
ramifica por ano/ID/página e que nenhuma dependência de IA generativa/rede existe no runtime
declarado, nenhum caso novo desta fase foi codificado por ID (a correção de Q13 é uma
capacidade declarativa geral, `owner_exclusion_gate`, gated pelo profile - nunca um
`if question_id == "Q13"`), e o comportamento diante de ambiguidade permanece fail-safe (a
tentativa de generalizar a correção de D10/Q07/Q12 foi revertida precisamente porque não pôde
ser feita com segurança suficiente - ver Seção U - em vez de publicada meio-verificada).

**`GENERALIZATION_NOT_YET_VALIDATED`**: obrigatório nesta fase - nenhuma prova inédita foi
processada; nenhum código foi congelado para esse fim.

**`NOT_READY_FOR_2008_ENGINEERING_TEST`**: 15 questões publicadas continuam com defeito real.

## B. Estado Git

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   cad602c1764090ab2aa2269f2dbbafe0434b84ff
master: a5dfaab0c105150df3a7201c16547708cef45292 (= origin/master, intocado)
origin/feat/enade-2008-cc-b-pilot: cad602c... (= HEAD)
origin/feat/enade-2011-unified-extraction: 84c50058220bbc81a8d2f3086b2cd60d0cd47eb6
```
Confirmado por inspeção fresca no início da fase: o trabalho da Fase 3E já estava commitado e
pushado (`cad602c`, "Implement forward-reference caption handling in extraction pipeline") -
ação do usuário entre sessões, fora do controle deste agente, que nunca commita por conta
própria. `git diff --check` sem problemas. Nenhum merge/rebase/cherry-pick em andamento. Nenhum
commit foi criado nesta fase - `HEAD` permanece exatamente `cad602c` do início ao fim.

## C. Baseline

Confirmado por execução direta no início da fase (antes de qualquer mudança de código):
```
pytest -q                                    → 514 passed
published = 77, passed = 62, failed = 15, not_performed = 0, excluded = 3
2011: verify-gold OK (55/55) validated; assess-readiness READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, Q34 needs_review (inalterado)
2021-b: verify-gold OK (40/40) validated; assess-readiness READY_FOR_2011, 40/40, sem blockers
ruff check/format, mypy: limpos
validate-schema: 13/13; validate-manifest: 0 warnings
audit-extraction: 77/77 OK (2008-b)
```
Hashes dos 288 arquivos protegidos (2011: 270 arquivos de `data/questions` + 4 manifestos
próprios listados individualmente; 2021: 14 manifestos próprios) capturados em
`scratchpad/phase3f/protected-288-baseline.sha256` antes de qualquer mudança - usados como
referência para todas as comparações desta fase (feitas via `git status --short`, que já evita
a armadilha CRLF-vs-`git show` documentada em fases anteriores).

## D. Contrato de generalização

`docs/generalization-contract.md` (novo). Formaliza três categorias de regra (núcleo,
capacidade declarativa, override documental - Seção 5 do prompt) e os cinco níveis G0–G4
(Seção 6). Nunca usa "generalizada" para G0/G1. Metade do contrato é comprovável
automaticamente: `tests/test_generalization_architecture.py` (novo, 9 testes) verifica, via
AST (não regex ingênuo sobre comentários), que nenhum módulo em `src/enade/extraction/` (exceto
`exam_profile.py`/`layout_overrides.py`, cujos próprios campos são verificados separadamente)
compara `year`/`question_id`/`question_number`/`page_number`/`source_page`/`.number` contra um
literal, que nenhum módulo importa uma biblioteca de LLM/VLM/rede genérica, e que
`pyproject.toml` não declara tais dependências. Confirmado (via um teste direto contra um trecho
de código sintético, não parte da suíte) que o próprio gate detecta a violação que deveria
detectar, não apenas passa vazio.

## E. Registro de capacidades

`data/manifests/extraction-capabilities.json` (novo, schema validado por 4 testes dedicados).
8 entradas:

| capability_id | nível | profile_dependency |
|---|---|---|
| `region_merge_x_tolerance` | G2 | opcional, `None`=comportamento original |
| `caption_font_size_gate` | G2 | opcional, `False`=comportamento original |
| `column_margin_height_font_gate` | G3 | nenhuma - sempre ativa |
| `owner_exclusion_gate` | G2 (novo nesta fase) | opcional, `False`=comportamento original |
| `forward_reference_caption` | G3 | nenhuma - segura incondicionalmente pela especificidade do padrão |
| `question_ownership` | G3 | nenhuma - sempre ativa desde a Fase 2C |
| `source_coverage_audit` | G3 | nenhuma - sempre ativa desde a Fase 1C |
| `local_reading_order` | `not_implemented` | n/a - registrado honestamente como lacuna, não fabricado |

Todas com `runtime_ai_dependency: "none"`. Nenhum `trigger_features` cita um ID de questão
específico (verificado por teste). `local_reading_order` é a única capacidade que os clusters
B/C/D (Seção G) precisariam para fechar seus próprios defeitos - registrada como lacuna
explícita, não implementada nesta fase.

## F. Os 15 casos

Inventário completo, re-derivado do estado real do ledger/manifests desta fase (não presumido):

| question_id | página | categoria(s) | status | causa raiz | tentativa nesta fase |
|---|---|---|---|---|---|
| d10 | 7 | region-merge-content-loss | failed | Cluster A (ver Seção G) | root-caused com precisão; correção geral tentada e revertida (Seção U) |
| d40 | 17 | table-reading-order-scramble | failed | rótulo de diagrama ("F"/"B nome,endereco") não absorvido pela fonte maior-que-corpo | reconfirmado, nenhuma nova tentativa (experimento já revertido na Fase 3E) |
| q02 | 3 | region-merge-content-loss | failed | Cluster A | root-caused; correção não aplicada (revertida) |
| q05 | 3 | region-merge-content-loss | failed | absorção-além-do-necessário (citação de imagem descartada) | não investigado a fundo nesta fase (orçamento em Q13/Cluster A) |
| q07 | 4 | region-merge-content-loss | failed | Cluster A | root-caused; correção geral corrigia 100% deste caso, revertida por regressão em outro lugar |
| q12 | 8 | region-merge-content-loss | failed | Cluster A (mais um sub-caso: fragmento absorvido como label na própria fonte) | root-caused; correção geral corrigia parcialmente, revertida |
| q13 | 8 | content-duplication (aberto) + cross-question-contamination (**resolvido**) | failed | overflow de alternativa E para o topo da próxima coluna, alargando o bbox e alcançando o diagrama de Q12 | **RESOLVIDO** (`owner_exclusion_gate`, G2) |
| q24 | 12 | region-merge-content-loss | failed | Cluster A + Cluster C (rótulos "A"/"B" internos ao diagrama confundidos com marcador de alternativa) | root-caused (dois mecanismos compostos); não corrigido |
| q29 | 13 | table-reading-order-scramble | failed | Cluster C | root-caused; não corrigido |
| q33 | 14 | table-reading-order-scramble | failed | Cluster D (fragmentação de linha por y0 quase-idêntico) | root-caused; não corrigido |
| q45 | 19 | region-merge-content-loss | failed | Cluster A (região nativa já larga, não por growth) | root-caused; não corrigido |
| q54 | 23 | region-merge-content-loss | failed | crescimento em Y (não em X) absorve o parágrafo de abertura e fechamento | root-caused; não afetado pelo experimento de X (era um problema de Y) |
| q63 | 27 | region-merge-content-loss | failed | Cluster A + Cluster C | root-caused; não corrigido |
| q75 | 32 | region-merge-content-loss | failed | Cluster A (gutter nativo ~9.8pt, menor que a folga de crescimento) + Cluster B (legenda vazando para alternativa D) | root-caused; não corrigido |

Confirmado explicitamente, sem presumir resolução: **Q24, Q29, Q33, Q63 permanecem abertas**,
cada uma com causa própria (não uma causa única compartilhada, mas dois clusters compostos -
Seção G).

## G. Clusters de causa raiz

Investigação forense (instrumentação direta contra `data/raw/geacc-enade/2008/b1_prova.pdf`,
reproduzindo o pipeline real estágio a estágio) encontrou **quatro mecanismos distintos**, não
quinze causas isoladas:

- **Cluster A — "estouro de crescimento/sobreposição estatui perda de enunciado"** (D10, Q02,
  Q07, Q12, Q24, Q45, Q54, Q63, Q75 - 9 dos 15 casos): `_line_in_region` (assembler.py) usa um
  teste de *sobreposição*, não de *contenção*, no eixo X (`line.x0 <= region.x2+5 and line.x1 >=
  region.x0-5`) - uma linha larga e não relacionada, de uma coluna diferente, satisfaz esse
  teste bastando tocar a borda com folga de apenas 5pt, mesmo quando a maior parte da própria
  linha está bem fora da região. Em várias páginas de 2008-b, o gutter real entre coluna/figura
  é mais estreito que essa folga fixa (D10: ~4.3pt; Q07: ~1.6pt antes de qualquer crescimento).
- **Cluster B — "vazamento de legenda/rótulo para dentro de uma alternativa"** (Q07, Q75): a
  isenção de filtragem de região para a seção de alternativas (`_in_alternatives_section`) não
  distingue uma continuação real de alternativa de uma legenda/rótulo de figura que caiu na
  mesma faixa Y.
- **Cluster C — "rótulo interno de diagrama confundido com marcador de alternativa"** (Q24,
  Q29, Q63): `_merge_orphan_markers` (layout.py) funde uma letra isolada (rótulo de estado A/B
  de um autômato, nome de entidade A/B/C de um DER) com texto vizinho da mesma forma que faz
  para um marcador real de alternativa; `_ALTERNATIVE_LINE_RE`/`_line_in_region` então isentam
  esse rótulo de qualquer filtragem geométrica, deixando-o vazar como texto solto - ao contrário
  de `figures.py`'s própria `_is_marker_at_margin`, que já exige a linha estar na margem real do
  corpo antes de tratá-la como marcador protegido.
- **Cluster D — "fragmentação de linha por y0 quase-idêntico embaralha a ordem de leitura"**
  (Q33 isolado; contribui também para a extração de fragmentos em Q02/Q07/Q12/Q45): o pymupdf
  ocasionalmente separa uma linha visual/lógica em vários registros `Line` no nível de
  palavra/token, cada um com um y0 ligeiramente diferente; a ordenação por `(round(y0,1), x0)`
  desordena esses fragmentos quando o arredondamento os coloca fora de ordem relativa ao x0 real.

Cada cluster tem uma correção geral candidata identificada com precisão (ver
`data/manifests/extraction-capabilities.json`, `local_reading_order`, e a Seção U abaixo para a
tentativa real do Cluster A) - nenhuma foi implementada com segurança suficiente nesta fase.
Q24 e Q63 são instâncias de **dois** clusters compostos simultaneamente (A+C), não um só bug com
dois sintomas.

## H. D10

**Estágio exato da perda, determinado por instrumentação direta** (PROMPT Seção 11): todas as
linhas reais do enunciado de D10 estão presentes e não-chrome em `span.lines` desde a extração
bruta - a perda **não** ocorre em `extraction`/`normalization`/`question segmentation`. Ocorre
em `caption_font_size_gate`/`asset_consumption`: uma foto real (bbox 36.7–243.5, elemento único,
não crescida) tem sua própria borda direita 4.3pt mais próxima da margem esquerda da coluna
direita (x0=247.8, onde começa o corpo real da manchete 1) do que a folga fixa de 5pt de
`REGION_X_PADDING` - a manchete 1 inteira (título + 8 linhas de corpo) e as duas primeiras linhas
do corpo da manchete 2 são então tratadas como "dentro da figura" e descartadas do Markdown
final, apesar de nunca terem sido, de fato, geometricamente absorvidas pelo próprio crescimento
da região (a foto nunca cresceu em X - o problema é a folga fixa, não a absorção).

**Correção tentada e revertida** (ver Seção U): substituir a folga fixa por um teste de
sobreposição relativa (≥50% da largura mais estreita entre linha e região) corrigiu D10 por
completo, mas causou uma regressão real em duas questões já aprovadas (Q61, Q71) - revertida
antes de qualquer publicação.

**Teste adicionado**: nenhum (a correção foi revertida; nenhum novo comportamento para testar).
O achado em si está documentado no *blocker ledger*
(`d10-label-absorption-newspaper-fragments`, já com a causa corrigida na Fase 3E e agora
precisada ainda mais nesta fase) e nos comentários de `assembler.py`'s própria
`REGION_X_PADDING`.

## I. D40

Recuperado do relatório da Fase 3E: o defeito (rótulo "B\tnome,endereco" vazando antes de
figure-01) e o experimento revertido (exceção de texto curto em `caption_font_size_gate`, que
corrigiu o rótulo mas engoliu a palavra real "Cliente," da própria prosa de D40, partindo uma
frase em duas). **Não repetido nesta fase.** Confirmado que o defeito atual é exatamente o
mesmo, mais um residual adicional pequeno (um rótulo isolado "F" - o próprio nó "F" da árvore de
consulta, mencionado no enunciado como "B e F representam as operações de projeção e seleção")
observado apenas durante o experimento revertido do Cluster A (nunca chegou a ser publicado -
revertido junto com o resto). D40 permanece `failed`, sem alteração de comportamento nesta fase
- fielmente textual/visual quanto ao resto do enunciado, mas com o rótulo residual conhecido.

## J. Q12/Q13

**Q13 (resolvido)**: `figure-01.png` de Q13 era byte-idêntico ao de Q12 (SHA-256
`edd04b77...`). Causa: a alternativa E de Q13 é impressa no topo da próxima coluna de página
(overflow real de layout, não um bug em si), alargando o bbox bruto de Q13 o bastante para
satisfazer a tolerância y/x antiga (sem verificação de dono) contra a região de Q12. **Gate
geral implementado**: `owner_exclusion_gate` (ExamStructureProfile/assembler.py) - "um asset não
pode ter múltiplos owners" tornado operacional como "uma região cujo `owner_key` nomeia uma
questão diferente nunca é admitida, independentemente da sobreposição do bbox". Esta regra só
pode *remover* uma região indevidamente admitida, nunca adicionar uma - risco assimétrico
mínimo.

**Validado**: Q12 mantém seu próprio asset inalterado (mesmo SHA-256 de antes); Q13 perde
apenas o asset estrangeiro (`assets: []`, correto - Q13 é uma questão de partição de conjuntos
sem nenhum diagrama na própria página fonte); nenhum arquivo órfão ficou para trás (o PNG
duplicado simplesmente deixa de ser escrito na próxima regeneração); nenhuma questão protegida
muda (confirmado: aplicar o gate incondicionalmente ALTERA 2011 Q34 - avaliado e rejeitado,
gate mantido restrito ao profile de 2008-b). Q13 continua `failed` no total (o defeito de
duplicação de texto da alternativa E, mecanismo não relacionado, `q13-duplicated-alternative-text`,
segue aberto - não investigado nesta fase).

## K. Q05

**Não investigado a fundo nesta fase** (orçamento consumido pela investigação do Cluster A e
pela correção de Q13/Q12). O achado da Fase 3E permanece a melhor evidência disponível: a
citação de imagem ("STRICKLAND, Carol; BOSWELL, John...") está ausente do Markdown renderizado,
e `caption`/`alt_text` do asset são `null`. Nenhuma decisão foi tomada sobre se essa referência
deveria ser preservada no texto, incluída no asset, consumida com equivalência, ou duplicada de
modo justificado - as quatro opções da Seção 14 do prompt permanecem em aberto. Blocker
`q05-image-citation-dropped` inalterado.

## L. Ordem local

Q29, Q33, Q63 permanecem abertas - Clusters C e D (Seção G), não corrigidos. Nenhuma tabela ou
bloco de código foi reconstruído semanticamente; onde uma tabela real foi detectada
(`detect_tables`), ela continua entrando na ordem global como unidade atômica, sem alteração
nesta fase. `local_reading_order` registrado explicitamente como capacidade **não implementada**
no registro de capacidades (Seção E), em vez de fabricar uma correção pontual para cada caso.

## M. Source coverage

`enade audit-extraction --questions-dir data/questions/2008/all-computing`: **77/77 OK**, sem
alteração de cobertura. Nenhum asset órfão introduzido (o antigo `q13/figure-01.png`, duplicado,
simplesmente não é mais escrito - nenhum arquivo ficou desconectado do seu próprio `.md`). Q12
continua com seu único asset correto.

## N. Auditoria visual

```
Antes desta fase: 62 passed, 15 failed, 0 not_performed
Depois desta fase: 62 passed, 15 failed, 0 not_performed
```
Contagem absoluta inalterada (Q13 permanece `failed`, apenas por uma causa menor e diferente -
ver Seção J). `data/manifests/visual-audit-2008-computing.json` atualizado apenas para a
entrada de Q13, com evidência concreta (nunca aprovação em massa). O alvo do prompt (77/0/0/3)
**não foi atingido**.

## O. Q8/Q38/Q55

Confirmado, sem tentativa de recuperação: `enade extract` continua reportando exatamente
```
objective 8: could not build a valid Question - 1 validation error for Alternative
objective 38: could not build a valid Question - 1 validation error for Alternative
objective 55: could not build a valid Question - 1 validation error for Alternative
```
idêntico às fases anteriores. `test_all_80_academic_questions_are_accounted_for` continua verde.
Nenhuma inferência por gabarito, nenhum placeholder, nenhuma promoção a gold.

## P. Runtime sem IA

```
NO_LLM_RUNTIME = PASS   (tests/test_generalization_architecture.py::test_core_extraction_modules_import_no_network_or_llm_library,
                          ::test_declared_runtime_dependencies_contain_no_llm_or_network_client)
NETWORK_INDEPENDENT_EXTRACTION = PASS (nenhuma importação de socket/requests/httpx/urllib/grpc/boto3
                          em src/enade/extraction/*.py, verificado via AST, não apenas grep textual)
```
Dependências de runtime declaradas (`pyproject.toml`): `pydantic`, `PyYAML`, `typer`, `pypdf`,
`pymupdf` - nenhuma delas é cliente de rede ou de modelo generativo. Nenhum OCR está em uso
(todo o corpus processado - 2008-b, 2011, 2021 - é PDF-nativo com camada de texto real);
`docs/generalization-contract.md`, Seção 5, formaliza a exigência de que qualquer OCR futuro
seja opcional, declarado por profile, e nunca substitua silenciosamente texto documental já
extraído.

## Q. Gold e readiness

```
gold-2008-computing.json: maturity=provisional, verified=59/77, needs_review=18/77
verify-gold --year 2008 --course all-computing → OK (77 questions match)
assess-readiness --year 2008 --course all-computing
  --ready-label READY_FOR_2008_ENGINEERING_TEST --not-ready-label NOT_READY_FOR_2008_ENGINEERING_TEST
  → NOT_READY_FOR_2008_ENGINEERING_TEST
  59/77 verified, 18 needs_review, gold maturity=provisional
  visual audit: 62 passed, 15 failed, 0 not_performed (fully_covered=True)
  49 blocker(s)  (antes desta fase: 50 - um blocker resolvido: q13-cross-question-image-contamination)
```
`maturity` permanece `provisional` (não `validated`) - correto mesmo que 77/77 fossem
alcançadas, já que Q8/Q38/Q55 continuam excluídas (a Seção 22 do prompt exige isso
explicitamente).

## R. Proteção de 2011/2021

Confirmado repetidamente ao longo da fase (a cada mudança de código, antes de decidir manter ou
reverter):
- `git status --short` sobre os 270 arquivos de `data/questions/2011|2021` + os 18 manifestos
  próprios - **saída vazia em toda verificação**, incluindo a verificação final.
- Regeneração completa (`enade extract`) para diretórios de scratch separados, comparada byte a
  byte (`diff -rq`) contra o corpus real: **zero diferenças**, em quatro rodadas distintas (após
  o `owner_exclusion_gate` sem gate condicional - **detectou drift em Q34**, revertido; após o
  `owner_exclusion_gate` com gate condicional - zero drift; após o experimento de sobreposição
  relativa em `_line_in_region` sem gate - **detectou drift em Q9/Q14/Q23/Q38**, revertido; após
  a decisão final de reverter esse experimento por completo - zero drift, confirmado uma última
  vez ao final da fase).
- `assess-readiness --year 2011`/`--year 2021 --course ciencia-da-computacao-bacharelado`
  inalterados: `READY_FOR_LEGACY_LAYOUT_TEST` (54/55, Q34 `needs_review`) e `READY_FOR_2011`
  (40/40, sem blockers), idênticos ao início da fase.

```
2011 drift = 0
2021 drift = 0
```

## S. Testes

**525 testes, todos verdes** (antes: 514; +11 novos):
- `tests/test_extraction_assembler.py`: +1
  (`test_owner_exclusion_gate_rejects_a_foreign_owned_region_when_enabled`) - fixture sintética,
  sem coordenadas reais da prova, sem ID de questão como condição.
- `tests/test_extraction_pipeline_2008.py`: +1 (`test_q13_no_longer_receives_q12_own_diagram`) -
  contra o corpus real, verifica Q13 sem asset e Q12 com o seu próprio inalterado.
- `tests/test_generalization_architecture.py` (novo arquivo): +9 - cobre exatamente as
  exigências da Seção 24 "Generalização" do prompt: regra sem year, regra sem question ID,
  campos de profile/override verificados como dado nunca como condição, nenhuma dependência de
  IA/rede no núcleo nem no `pyproject.toml`, schema do registro de capacidades, nenhum
  `trigger_features` cita um ID de questão específico.

Nenhum teste antigo alterado. Nenhum teste removido.

## T. Reprodutibilidade

Duas execuções independentes de `enade extract --year 2008 --course all-computing` para
diretórios de scratch separados, no estado final da fase: **byte-idênticas entre si** e
**byte-idênticas ao corpus real committed**. Confirmado também para 2011 (`all-computing`) e as
3 disciplinas de 2021, no mesmo run que gerou os números da Seção R.

## U. Quality gates

```
pytest -q                         → 525 passed
ruff check .                      → All checks passed!
ruff format --check .             → 380 files already formatted
mypy src                          → Success: no issues found in 53 source files
enade validate-schema             → 13/13 fixture(s) valid
enade validate-manifest           → OK (0 warnings)
enade audit-extraction (2008-b)   → 77/77 OK
verify-gold + assess-readiness (2011, 2021-b, 2008) → ver Seções C/Q/R
```

## V. Experimentos revertidos

**Filtro de sobreposição relativa em `_line_in_region`** (assembler.py, tentativa de
generalizar o Cluster A): substituir a folga fixa `REGION_X_PADDING` (5pt) por um requisito de
sobreposição genuína de pelo menos 50% da largura mais estreita entre a linha e a região.

- **Corrigiu por completo**: D10 (manchete 1 inteira + abertura da manchete 2 recuperadas,
  confirmado palavra por palavra contra a página 7) e Q07 (parágrafo real completo recuperado,
  idêntico à página 4).
- **Corrigiu parcialmente**: Q12 ("complexidade" recuperada; "ciclomática." permanece perdida -
  causa distinta, um fragmento de palavra sendo genuinamente absorvido como rótulo na própria
  origem, não um problema de janela de tolerância).
- **Regrediu duas questões já aprovadas**: Q61 (a legenda real "Figura para a questão 61" -
  posicionada à margem esquerda da página, cobrindo apenas 27,4% de sobreposição com seu próprio
  diagrama largo, x0=121.2–474.3 - passou a vazar como texto solto) e Q71 (fragmento "ao"
  vazando por um mecanismo análogo). Contraexemplo decisivo: a sobreposição de Q61 (27,4%,
  *deveria ser aceita*) é numericamente **menor** que a de Q07 (37,8%, *deveria ser rejeitada*)
  - nenhum limiar único de razão pode separar corretamente os dois casos usando apenas essa
  métrica geométrica.
- **Refinamento identificado, não implementado**: testar a razão contra o bbox **anterior ao
  crescimento** de cada região (não o bbox final, já expandido) resolveria D10/Q07
  corretamente sem tocar Q61 (cujo bbox nunca cresceu em X - o deslocamento é nativo da própria
  legenda, não causado por absorção) - mas exigiria adicionar um novo campo a `VisualRegion`
  capturando o bbox pré-crescimento em ambos os pontos de construção em `figures.py`, e testes
  extensivos próprios que não houve tempo de completar com o rigor que este projeto exige.
- **Decisão**: revertido por completo (código e profile), documentado em três lugares
  (`assembler.py`'s própria docstring de `REGION_X_PADDING`, o *blocker ledger* implicitamente
  via as entradas de D10/Q07/Q12 inalteradas, e este relatório) - nunca publicado meio-verificado.

**`owner_exclusion_gate` sem gate condicional** (tentativa inicial): aplicar a exclusão por
`owner_key` incondicionalmente a todo booklet. Regrediu 2011 Q34 (mudança de
`extraction_status`/`automatic_validation` de `needs_review`/`failed` para `verified`/`passed` -
sem mudança de conteúdo, com precedente documentado de falso positivo em
`blocker_ledger.py`'s `accepted_non_material_difference`, mas uma mudança byte-a-byte a um
corpus protegido nunca é aceita independentemente de como é caracterizada). Corrigido
adicionando `ExamStructureProfile.owner_exclusion_gate` (padrão `False`) - mantido, não
revertido, já que restrito a 2008-b resolve Q13 com zero *drift*.

Ambos os experimentos foram testados via regeneração completa + *diff* byte a byte antes de
qualquer decisão - nenhum foi aceito às cegas, e nenhum foi escondido.

## W. Arquivos e Git final

**Novos**: `docs/generalization-contract.md`, `data/manifests/extraction-capabilities.json`,
`tests/test_generalization_architecture.py`, `docs/phase-3f-report.md`.

**Modificados**: `src/enade/extraction/assembler.py` (novo parâmetro
`owner_exclusion_gate`/filtro de região atualizado; `REGION_X_PADDING`'s docstring documenta o
experimento revertido), `src/enade/extraction/exam_profile.py` (novo campo
`owner_exclusion_gate`), `src/enade/extraction/pipeline.py` (propaga o novo campo),
`src/enade/extraction/reference_captions.py` (comentário corrigido, sem mudança de
comportamento), `data/manifests/exam-structure-2008.yaml` (`owner_exclusion_gate: true` +
comentário), `data/manifests/blocker-ledger-2008.yaml` (`q13-cross-question-image-contamination`
resolvido), `data/manifests/visual-audit-2008-computing.json` (nota de Q13 atualizada),
`data/manifests/gold-2008-computing.json` (reconstruído, mesma maturidade `provisional`),
`data/manifests/extraction-audit-2008-computing.{csv,json}` (reflete o estado atual),
`tests/test_extraction_assembler.py` (+1 teste), `tests/test_extraction_pipeline_2008.py` (+1
teste).

**Corpus 2008** (`data/questions/2008/all-computing/`): 1 arquivo com mudança de conteúdo
(`enade-2008-computing-q13.md`), 1 asset removido (`q13/figure-01.png`, contaminado). Nenhum
outro arquivo de 2008-b tocado.

**Limpeza**: todos os scripts de diagnóstico temporários (`diag_*.py`) criados durante a
investigação foram removidos antes da conclusão da fase - `git status --short | grep "^??"`
confirma apenas os 3 arquivos novos intencionais.

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   cad602c1764090ab2aa2269f2dbbafe0434b84ff (inalterado - nenhum commit criado nesta fase)
14 caminhos com alterações no working tree (staged: 0), 3 não rastreados
```
**Confirmado explicitamente**: nenhum commit, push, PR, merge ou tag foi executado nesta fase.
`master` não foi tocado. Nenhum outro ano ou o bundle `e` foi processado.

## Recomendação

Dado que nem todas as 77 publicadas foram aprovadas, a Fase 3G não deve avançar para as três
excluídas (Q8/Q38/Q55) nem ampliar o corpus. O menor conjunto de causas estruturais restantes,
em ordem de impacto esperado:

1. **Refinar o Cluster A com o bbox pré-crescimento** (Seção V) - a correção mais promissora e
   mais precisamente compreendida desta fase. Exige um novo campo em `VisualRegion` (bbox antes
   de `_expand_with_labels`) e testes que comprovem, ao mesmo tempo, D10/Q07 corrigidos e
   Q61/Q71/Q9/Q14/Q23/Q38 inalterados - uma fase própria, dado o histórico de regressões sutis
   já encontradas nesta área.
2. **Cluster C** (Q24/Q29/Q63): reusar `figures._is_marker_at_margin` dentro de
   `_line_in_region`, exatamente como já é feito na absorção de rótulos em `figures.py` -
   fechraria três casos com uma mudança pequena e já precisamente especificada.
3. **Cluster D** (Q33): investigar por que o pymupdf fragmenta certas linhas por palavra/token
   antes de propor uma correção - a causa da fragmentação em si não foi isolada nesta fase,
   apenas seu efeito na ordenação.
4. **Cluster B** (Q07/Q75, resíduo além do Cluster A): reaplicar `_line_in_region` (já corrigido
   pelo item 1) dentro da própria isenção de `_in_alternatives_section`, em vez de pular a
   checagem geométrica por completo dentro da seção de alternativas.
5. **Q05**: decidir explicitamente entre as quatro opções da Seção 14 do prompt (preservar no
   texto / incluir no asset / consumir com equivalência / duplicar de modo justificado) - não
   feito nesta fase.
6. **`local_reading_order` como capacidade formal**: uma vez que os clusters acima estejam
   fechados, formalizar o mecanismo de "ilha de leitura local" já esboçado no registro de
   capacidades, promovendo-o de `not_implemented` a G2/G3.

Somente depois de 77/77 aprovadas, Q8/Q38/Q55 explicitamente excluídas, e 2011/2021
byte-idênticos, a Fase 3G dedicada a essas três questões (alternativas puramente visuais) faz
sentido - seguida pelo bundle `e`, e só então pelo congelamento de código/profiles para uma
validação cega em prova inédita (`GENERALIZATION_ARCHITECTURE_ESTABLISHED` →
`GENERALIZATION_SUCCESS` exige essa validação, nunca apenas a arquitetura em si).
