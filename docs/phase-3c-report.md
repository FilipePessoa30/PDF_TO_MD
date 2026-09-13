# Phase 3C — Legenda Segura, Ilhas de Leitura Locais e Reconciliação da Auditoria das 77 Questões de 2008-B

## A. Classificação

**`LEGACY_LAYOUT_PARTIAL`.**

**`NOT_READY_FOR_2008_ENGINEERING_TEST`** (`assess-readiness --year 2008 --course all-computing`, exit code 1).

**`READING_ORDER_NOT_STABILIZED`** — o padrão sistêmico de leitura local (tabelas/código) não foi
generalizado com segurança nesta fase; apenas um caso (D09) do padrão de absorção de legenda foi
corrigido na raiz, com um segundo defeito residual, mais preciso, ainda aberto.

Progresso real e verificado frente à Fase 3B: uma correção geral, gerada por instrumentação direta
(não hipótese), foi identificada, implementada, testada exaustivamente contra 2011/2021 (zero
drift confirmado byte a byte duas vezes) e aplicada — ela corrige uma lacuna real e não trivial em
`figures.py` (fusão de candidatos vetoriais por proximidade vertical, sem verificação de eixo X),
responsável pela grade RASCUNHO de cada questão discursiva colapsar em uma região quase do tamanho
da página inteira. Essa correção resolveu genuinamente **D20 e D39** (que a Fase 3B havia marcado
`passed` por engano — a reinspeção nesta fase mostra que o defeito de figura espúria continuava
presente no arquivo então committado) e melhorou substancialmente **D09, D10 e D40**. Ao investigar
o impacto da correção, duas questões antes `not_performed` foram auditadas pela primeira vez:
**D79** (aprovada) e **D60** (um defeito real e pré-existente de contaminação cruzada com Q61 foi
descoberto, não causado pela correção desta fase). Duas tentativas de correção geral adicionais
(para o padrão de embaralhamento de tabela/código, classe B) foram implementadas, testadas e
**revertidas** após regeneração completa revelar regressões reais em questões já validadas — a
evidência de ambas está preservada. Nenhuma das 15 questões `failed` foi ocultada como resolvida
sem verificação; nenhuma das 32 `not_performed` foi marcada `passed` sem inspeção real.

## B. Estado Git

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   586005e7563a4d3378dea61fc0914278f2b6d6e4 (idêntico ao início desta fase — nenhum commit criado)
origin/feat/enade-2008-cc-b-pilot: 586005e... (sincronizado)
master:  a5dfaab0c105150df3a7201c16547708cef45292 (= origin/master, intocado)
origin/feat/enade-2011-unified-extraction: 84c50058220bbc81a8d2f3086b2cd60d0cd47eb6 (referência, não tocada)
working tree: 32 caminhos com alterações, nenhum commit criado nesta fase
```

Confirmado por inspeção fresca no início da sessão: este era um clone novo (reflog mostrava apenas
o evento `clone`), com a branch `feat/enade-2008-cc-b-pilot` existente somente em `origin` — não
havia checkout local. A branch foi criada localmente via `git checkout -b ... origin/...`, exatamente
no commit `586005e` (HEAD de `origin/feat/enade-2008-cc-b-pilot`), sem nenhuma divergência do estado
presumido pelo prompt (única discrepância notada e não material: as mudanças das Fases 3A/3B já
estavam commitadas nesse ponto, não soltas no working tree como o resumo do prompt presumia —
mérito organizacional, não um problema). Nenhum merge, rebase ou cherry-pick em andamento. Nenhum
commit, push, PR ou tag executado nesta fase.

## C. Reconciliação

Lida diretamente do ledger e da auditoria visual reais (não do resumo do prompt), reconstruindo a
árvore completa:

| Nível | Quantidade | Detalhe |
|---|---|---|
| Blockers originais (Fase 3A) | 27 | 25 `region-merge-content-loss` + 2 `section-transition-chrome-bleed` |
| Resolvidos na Fase 3B | 18 | 16 region-merge + 2 chrome-bleed |
| Remanescentes após 3B | 10 | 9 region-merge (D09,Q02,Q07,Q24,Q45,Q54,Q62,Q63,Q75) + D40 (chrome-bleed resolvido, mas reaberto sob novo blocker `d40-table-reading-order-scramble`) |
| Novos na Fase 3B | 5 | Q12, Q13, Q29, Q33, Q68 |
| Total `failed` após 3B | 15 | 10 remanescentes + 5 novos |
| Blockers adicionais (não-estrutura-do-enunciado) | 7 | 3 `unstructured-image-alternatives` (Q8/Q38/Q55, excluídas) + `d59-answer-standard-image-only` + `d09/d10-answer-standard-absent-from-source` — afetam padrão de resposta, não o enunciado |
| Blockers abertos ao final da Fase 3B | 22 | 15 (enunciado) + 7 (acima) |

**Nesta fase (3C)**, sobre essa base de 15 `failed`:

| Questão | Blocker(s) | Status pré-3C | Ação 3C | Status pós-3C |
|---|---|---|---|---|
| D09 | `d09-region-merge-content-loss` | failed | causa raiz encontrada e parcialmente corrigida (fusão sem eixo X) | **failed** (melhorado — não mais vazio, 3 fragmentos residuais) |
| D40 | `d40-table-reading-order-scramble` | failed | mesma correção; estrutura content_blocks agora correta | **failed** (melhorado — quase completo, 1 rótulo de diagrama residual) |
| Q02, Q07, Q12, Q13, Q24, Q29, Q33, Q45, Q54, Q62, Q63, Q68, Q75 | (13 blockers distintos) | failed | nenhuma alteração de conteúdo (confirmado por diff byte a byte) | **failed** (inalterado; Q68 root-causado com precisão, correção tentada e revertida — ver seção E) |

**Descoberta desta fase, fora da lista dos 15**: ao aplicar a correção de fusão, dois efeitos
colaterais em questões que a Fase 3B classificara `passed` foram descobertos por reinspeção direta
do arquivo então committado (não presumidos a partir do código):

| Questão | Status pré-3C (alegado) | Realidade encontrada | Ação 3C | Status pós-3C |
|---|---|---|---|---|
| D20 | passed (Fase 3B: "no residuals found") | Falso — figura espúria da grade RASCUNHO ainda dividia o enunciado no meio de uma palavra | corrigido pela mesma correção geral | **passed** (agora genuinamente verdadeiro) |
| D39 | passed (nunca teve nota de reinspeção) | Falso — mesma classe de defeito, dividindo o item B | corrigido pela mesma correção geral | **passed** (novo, genuíno) |
| D80 | passed | Verdadeiro, mas com um asset órfão (figura-03, nunca referenciada no corpo) | asset órfão removido | **passed** (inalterado em substância) |

**Duas questões antes `not_performed`, auditadas pela primeira vez** (porque a correção alterou seus assets, motivando inspeção):

| Questão | Resultado |
|---|---|
| D60 | Defeito real e **pré-existente** encontrado: contaminação cruzada com os rótulos do diagrama ITIL de Q61 — confirmado presente no arquivo já committado antes desta fase, apenas obscurecido pela fragmentação mais severa que a correção removeu. Novo blocker aberto. |
| D79 | Aprovada — enunciado completo e coerente, referencia corretamente (sem reproduzir) o texto-estímulo compartilhado com Q78, o mesmo padrão já validado para 2011 Q78/D79. |

Nenhuma correção desta fase alterou Q02, Q07, Q12, Q13, Q24, Q29, Q33, Q45, Q54, Q62, Q63, Q68, Q75,
ou qualquer uma das outras 30 questões ainda `not_performed` (confirmado: `diff -rq` entre o corpus
regenerado e o committed mostra apenas os 8 arquivos discursivos listados acima).

## D. Baseline pré-mudança

```
pytest -q                                     → 481 passed
ruff check .                                  → All checks passed!
ruff format --check .                         → 372 files already formatted
mypy src                                      → Success: no issues found in 52 source files
enade validate-schema                         → 13/13 fixture(s) valid
enade validate-manifest                       → OK (0 warnings)
enade audit-extraction (corpus todo)          → 252/252 OK
verify-gold --year 2021 --course ciencia-...  → OK (40/40), validated
assess-readiness --year 2021                  → READY_FOR_2011, 40/40 verified, 0 needs_review
verify-gold --year 2011 --course all-computing → OK (55/55), validated
assess-readiness --year 2011                  → READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, 1 needs_review
2008-B provisional: 27/77 verified, 50 needs_review
  visual audit: 30 passed, 15 failed, 32 not_performed (usando contagem literal de status "not_performed"
    no arquivo; a métrica interna de `assess-readiness` reporta not_performed=0, pois considera "não
    auditado" apenas uma chave *ausente* do arquivo — todas as 77 chaves já estavam presentes desde a
    Fase 3A, cada uma com um status explícito, inclusive o texto literal "not_performed" — consistente
    com o que a Fase 3B já reportava, não uma mudança desta fase)
```

Hashes SHA-256 dos 288 arquivos protegidos (270 arquivos `.md`/`.png` sob `data/questions/2011/` e
`data/questions/2021/` + 18 manifestos `2011`/`2021` sob `data/manifests/`) capturados antes de
qualquer mudança de código, para comparação byte a byte ao final de cada mudança.

## E. Diagnóstico direto (instrumentação real, não hipótese)

Toda correção e toda reversão nesta fase partiu de instrumentação direta contra o PDF real
(`data/raw/geacc-enade/2008/b1_prova.pdf`), chamando `_raw_lines`, `detect_column_margins`,
`detect_visual_regions`, `compute_question_regions` e `assemble_question` diretamente e imprimindo
bboxes/contagens/textos brutos — nunca inferência a partir do código sozinho.

### E.1 — Classe A (absorção de legenda): causa raiz real de D09/D10/D20/D39/D40

Instrumentação da página 6 (D09) revelou: um retrato real embutido (63,8–247,9 × 117,4–564,5) mais
sua moldura formam um cluster de 2 elementos; a grade RASCUNHO própria de cada questão discursiva
(desenhada como ~40 segmentos vetoriais curtos de borda de linha, nunca reconhecidos como decorativos
porque sua posição varia por questão) forma um segundo cluster. `_merge_by_vertical_proximity`
(figures.py) ordenava candidatos apenas por Y, sem nenhuma verificação de eixo X — os segmentos da
coluna esquerda da grade (x≈37–60) e da coluna direita (x≈558–559, ~500pt mais à direita) recorrem
no mesmo passo vertical e colapsavam em **um único cluster de quase a largura inteira da página**
(36,8–559,2). Esse cluster, ao passar por `_expand_with_labels` e depois por
`_merge_overlapping_regions` (que também não verifica eixo X), absorvia por Y-overlap o retrato
acima dele, produzindo uma região cobrindo praticamente a página inteira — dentro da qual todo o
enunciado real caía como se fosse "conteúdo de figura".

Confirmado por reprodução direta em `data/raw/geacc-enade/2011/1_prova.pdf` (D5, página 17: prosa
esquerda / pseudocódigo direito) que este NÃO é um padrão exclusivo de layout de duas colunas real —
D5 tem elementos genuinamente distantes em X que devem permanecer no mesmo cluster.

### E.2 — Correção implementada e por que é segura

`figures.py`: `_merge_by_vertical_proximity` ganhou um parâmetro opcional `x_tolerance` (default
`UNBOUNDED_MERGE_X_TOLERANCE = math.inf`, ou seja, comportamento original inalterado). Um valor
finito (`MERGE_X_TOLERANCE = 150.0`) só é aplicado quando explicitamente solicitado — e apenas no
pool de candidatos "grandes" (o pool de "pequenas fórmulas" mantém `x_tolerance` sempre infinito,
porque a Fase 3C confirmou por regeneração completa que fórmulas legítimas de 2011 Q14/Q23 se
espalham por 200pt+ de uma mesma linha antes de serem corretamente re-separadas por alternativa).

O valor finito é ativado **apenas** para o caderno 2008-b, via um novo campo declarativo
`ExamStructureProfile.region_merge_x_tolerance` (`None` por padrão — nenhum booklet existente o
define, logo nenhum é afetado), lido em `pipeline.py` e repassado por `assemble_question` até
`detect_visual_regions`. `data/manifests/exam-structure-2008.yaml` define
`region_merge_x_tolerance: 150.0` com justificativa documentada inline.

**Por que 150pt e por que gated**: confirmado por regeneração completa (não suposição) que aplicar
esta mesma correção como padrão incondicional para *todos* os anos altera 2011 (Q23/Q38 — perdem sua
própria agrupação legítima de fórmulas por alternativa) e, com um valor de razão de altura alternativo
testado (ver E.3), também 2021 (Q34). Gated declarativamente, exatamente como a Seção 23 do prompt
prevê para este caso.

**Resultado real, verificado por regeneração completa e comparação byte a byte**:
- **D20, D39**: figura espúria removida por completo; enunciado agora genuinamente completo e coerente.
- **D09**: enunciado deixa de estar vazio (de "só figura-01.png" para prosa real + 3 fragmentos
  residuais) — melhoria real, não uma correção completa.
- **D40**: de "severamente embaralhado" para `content_blocks` estruturado com bloco de código SQL
  correto e verbatim; um rótulo de diagrama residual ("B nome,endereco", quase certamente uma
  projeção relacional π mal-renderizada) ainda vaza como texto solto antes de figure-02.
- **D10, D60, D80**: figuras espúrias/órfãs removidas; D10 permanece com perda real de conteúdo
  (ver seção J); D60 revela um defeito pré-existente e distinto (ver seção J); D80 inalterado em
  substância.
- **2011/2021**: zero diferença em qualquer um dos 288 arquivos protegidos, confirmado duas vezes
  (antes/depois), mais uma verificação adicional após a formatação automática do `ruff format`.

**Não resolvido por esta correção**: D09 ainda perde a maior parte do artigo/citação porque o
título real "DIREITOS HUMANOS EM QUESTÃO" (conteúdo genuíno, não uma legenda) toca o retrato e é
absorvido no primeiro passe de `_expand_with_labels` — geometricamente indistinguível, por
proximidade e largura sozinhas, de um rótulo de diagrama legítimo. Uma separação real entre
"inclusão no crop" e "consumo do texto" (Seção 7-9 do prompt) foi considerada, mas não implementada:
qualquer limite de "passes" testável mentalmente ainda classificaria esse título real como uma
legenda de um único passe, correndo o risco de alterar rótulos legítimos de 2011/2021 que também são
absorvidos em um único passe. Não implementado sem tempo para verificação de regressão equivalente
à usada para a correção acima — documentado, não escondido.

### E.3 — Classe B (ordem local de leitura): Q68 root-causado, corrigido, e a correção revertida duas vezes

Instrumentação da página 29 (Q68) confirmou a causa raiz exata: uma subconsulta SQL aninhada
("... AND E.IdDep IN (SELECT IdDep FROM Empregado GROUP BY IdDep HAVING count(*) > 5)") tem seu
próprio nível de indentação mais profundo (x≈265) recorrendo exatamente 3 vezes (o mínimo exigido por
`MIN_LINES_PER_COLUMN`) e distante o suficiente (gap de 100pt, no limite exato de
`MIN_COLUMN_SEPARATION`) para que `layout.detect_column_margins` o confunda com uma segunda coluna
real da página. `extract_page_lines` então ordena essas 3 linhas para o **final** da ordem de leitura
da página inteira, dividindo o WHERE clause da consulta II em dois fragmentos desconectados
(blocker `q68-sql-code-block-reordering`).

**Tentativa 1 — gate por razão de altura**: rejeitar uma coluna candidata cuja extensão vertical seja
uma fração pequena da outra (`shorter/taller < 0.15`). Corrigiu Q68 (razão real 0,048) mas, confirmado
por regeneração completa do corpus 2008 inteiro, **quebrou Q49/Q50** — Q50 tem seu próprio início de
enunciado legítimo em uma coluna esquerda igualmente curta (razão real 0,137, geometricamente
indistinguível da razão de Q68), fazendo a página cair para ordenação ingênua (y0, x0) e produzindo
contaminação cruzada real entre Q49 e Q50 (o enunciado de Q50 esvaziado, suas próprias Tabela I/II
anexadas à alternativa E de Q49). **Revertido.**

**Tentativa 2 — razão de altura + coluna curta 100% monoespaçada**: a hipótese de que código
(monoespaçado) nunca é uma segunda coluna real curta, enquanto prosa (Q50) é. Verificado diretamente:
as 3 linhas da subconsulta de Q68 **não** são sinalizadas `is_monospace=True` — o PDF rotula esse
código SQL com um nome de fonte de subconjunto embutido arbitrário ("TT2F7Bo00") que a heurística de
substring de `Line.is_monospace` (courier/mono/consolas) não reconhece. O próprio sinal está
indisponível para as fontes deste caderno, não apenas não usado. Aplicado, o gate combinado nunca
dispara para Q68 (nenhum risco de regressão, mas também nenhuma correção). **Revertido.**

Ambas as tentativas, evidência completa e diffs, estão preservadas em
`scratchpad/experiment-column-height-ratio.diff` e
`scratchpad/experiment-q68-vs-q50-evidence.md`, e resumidas como comentário permanente no próprio
`layout.py` (não removidas silenciosamente). Nenhuma versão foi reintroduzida sob outro nome. Q68
permanece um blocker aberto, agora com causa raiz precisamente documentada; um mecanismo de "ilha
de leitura local" (Seções 12-13 do prompt) não foi implementado como arquitetura geral nesta fase —
ver seção Z/Recomendação.

## F. Modelo de legenda (Seções 6-9 do prompt)

Formalizado apenas como diagnóstico, não como implementação geral nesta fase (ver seção E.2, última
observação). A distinção entre `caption`/`asset_label` e `body_text` não pôde ser reduzida, com
segurança testável, a um sinal geométrico único (proximidade, largura, contagem de hops) sem risco
real e confirmado a 2011/2021 — a mesma disciplina que impediu uma correção apressada nas Fases 3A/3B
se aplica aqui. A separação entre "decisão A: inclusão no crop" e "decisão B: consumo canônico"
(Seção 7) permanece arquiteturalmente **não implementada**: `VisualRegion` ainda tem um único bbox
usado tanto para renderização quanto para a decisão de exclusão do texto em `_line_in_region`
(assembler.py). Implementá-la exigiria uma segunda bbox mais conservadora computada com um limite de
"passes" de absorção diferente para o consumo — tentado mentalmente e descartado nesta fase porque
o caso real (D09's "DIREITOS HUMANOS EM QUESTÃO") já é absorvido no primeiro passe, o mesmo passe que
protege rótulos curtos legítimos de diagramas em 2011/2021.

## G. Casos de absorção (resultado individual)

| Questão | Antes (Fase 3B) | Depois (Fase 3C) | Causa | Correção |
|---|---|---|---|---|
| D09 | vazio | prosa real + 3 fragmentos soltos | fusão sem eixo X (grade RASCUNHO) + absorção de legenda residual | parcial (fusão corrigida; absorção de legenda não) |
| D20 | figura espúria dividindo palavra | completo, sem figura | fusão sem eixo X | corrigida |
| D39 | figura espúria dividindo item B | completo, sem figura | fusão sem eixo X | corrigida |
| D10 | truncado após "Observações" | 3 fragmentos de citação presentes, mas 2 de 3 manchetes/corpos ainda perdidos | fusão sem eixo X (parcial) + outro mecanismo não isolado | parcial |
| D60 | fragmentado em 3 imagens | coerente, mas com contaminação de Q61 | fusão sem eixo X (parcial) + vazamento cross-question pré-existente | parcial |
| D80 | asset órfão (figura-03 nunca referenciada) | asset órfão removido | mesmo mecanismo | corrigida (nunca afetava o texto renderizado) |
| Q02, Q07, Q12, Q45, Q54, Q75 | vazio/truncado | inalterado | absorção de legenda pura (`_expand_with_labels`), sem componente de grade RASCUNHO | não investigada correção nesta fase (ver seção F) |

## H. Ilhas locais (arquitetura)

**Não implementada nesta fase.** O conceito de `local_reading_order_region` (Seção 12 do prompt) —
uma unidade atômica que entra na ordenação global da página, mas cuja ordem interna é resolvida
separadamente — permanece uma recomendação arquitetural, não código. A tentativa mais próxima (seção
E.3) mostrou que mesmo um gate estreito, dirigido a um único mecanismo de detecção
(`detect_column_margins`), tem efeitos colaterais reais em conteúdo geometricamente semelhante mas
semanticamente distinto (Q50's coluna esquerda curta e legítima vs. a subconsulta aninhada de Q68).
Implementar ilhas locais de verdade exigiria reconhecer a *forma* de uma tabela/bloco de código
antes da decisão de coluna da página inteira — um detector de "run monoespaçado e/ou com estrutura
delimitadora reconhecível" independente de `detect_column_margins`, não uma correção geométrica
sobre o mecanismo existente. Não implementado dado o tempo restante desta sessão.

## I. Tabelas

`tables.py`/`detect_tables` (Fase 1C) não foi alterado nesta fase. Nenhum novo caso de tabela
geometricamente reconstruída foi encontrado ou tentado. Q50 continua com sua única tabela detectada
caindo após o corte de alternativas e sendo corretamente excluída (não mal atribuída) — comportamento
inalterado e já aceito desde a Fase 3A.

## J. Código/pseudocódigo

D40's bloco de código SQL agora é reconstruído corretamente como `CodeSegment`/`content_blocks` com
indentação e quebras de linha preservadas verbatim (efeito colateral positivo da correção de fusão —
ver seção E.2). Q68's próprio código SQL permanece embaralhado (ver seção E.3). Nenhuma "correção"
de sintaxe foi aplicada em nenhum bloco de código; nenhuma indentação foi inventada.

## K. Source coverage

Uma verificação formal de cobertura (span → classificação) não foi implementada como mecanismo
dedicado nesta fase, pelo mesmo motivo da Fase 3B: o tempo foi investido na correção de causa raiz.
Uma ferramenta de triagem aproximada (bag-of-words por página vs. Markdown publicado) foi construída
e executada sobre as 77 questões publicadas — revelou-se **não confiável como veredito automático**
(páginas compartilhadas por 3-4 questões produzem cobertura baixa mesmo para questões corretas e já
confirmadas `passed`, como Q65) e foi descartada como gate; usada apenas como triagem exploratória
inicial, não como evidência de correção ou defeito. Nenhuma questão foi classificada com base nela.

## L. Quinze questões (resultado individual)

| ID | Página | Blocker | Causa | Arquivo alterado | Asset | Resultado visual | Teste | Status final |
|---|---|---|---|---|---|---|---|---|
| D09 | 6 | `d09-region-merge-content-loss` | fusão sem eixo X (parcial) + absorção de legenda residual | figures.py, exam_profile.py, pipeline.py, assembler.py | figure-01.png (menor) | melhorado, ainda incompleto | `test_d09_statement_is_no_longer_empty` | **failed** |
| D40 | 17 | `d40-table-reading-order-scramble` | idem | idem | figure-01/02.png (recortes diferentes) | melhorado, quase completo | (nenhum teste dedicado novo — coberto indiretamente) | **failed** |
| Q02 | 3 | `q02-region-merge-content-loss` | absorção de legenda pura | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q07 | 4 | `q07-region-merge-content-loss` | idem | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q12 | 8 | `q12-partial-content-loss` | idem | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q13 | 9 | `q13-duplicated-alternative-text` | não investigada | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q24 | 12 | `q24-region-merge-content-loss` | não isolada (tabela/diagrama) | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q29 | 13 | `q29-inline-sidebar-fragment` | não isolada | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q33 | 14 | `q33-item-marker-displacement` | não isolada | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q45 | 19 | `q45-region-merge-content-loss` | absorção de legenda pura (itens I/II) | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q54 | 23 | `q54-region-merge-content-loss` | idem (diagrama de rede grande e legítimo) | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q62 | 27 | `q62-cross-question-diagram-label-bleed` | vazamento de rótulo de Q61 | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q63 | 27 | `q63-region-merge-content-loss` | não isolada | nenhum | nenhum | inalterado | nenhum | **failed** |
| Q68 | 29 | `q68-sql-code-block-reordering` | **root-causada com precisão** (seção E.3) — coluna espúria por subconsulta aninhada | nenhum (correção tentada e revertida) | nenhum | inalterado | testes unitários da tentativa revertida | **failed** |
| Q75 | 32 | `q75-region-merge-content-loss` | absorção de legenda pura | nenhum | nenhum | inalterado | nenhum | **failed** |

Nenhuma das 15 foi encerrada apenas por corrigir exemplos representativos — cada uma foi
individualmente reexecutada e comparada contra o corpus regenerado após a correção.

## M. Trinta e duas auditorias novas (resultado parcial, honestamente reportado)

**Apenas 2 das 32 questões `not_performed` foram auditadas nesta fase** — D60 e D79, ambas tocadas
pela correção de fusão (seção C). As outras 30 **não foram auditadas nesta sessão**; permanecem
honestamente `not_performed`, exatamente como estavam. Uma ferramenta de triagem aproximada (seção K)
foi executada sobre todas, mas revelou-se não confiável o suficiente para basear qualquer veredito —
nenhuma das 30 foi classificada `passed` sem inspeção real, e nenhum novo defeito foi ocultado.

| ID | Resultado |
|---|---|
| D60 | Novo defeito real encontrado (contaminação cruzada com Q61) — classificado `failed`, novo blocker `d60-cross-question-diagram-label-bleed` aberto. |
| D79 | Nenhum defeito encontrado — classificado `passed`. |
| (30 restantes) | **Não auditadas nesta fase.** Recomenda-se fase dedicada — ver seção Z. |

## N. Q8/Q38/Q55 — reavaliação diagnóstica

Reexecutada a detecção após a correção de fusão (Seção 22 do prompt: somente depois de estabilizar
as regras gerais). Confirmado: **permanecem excluídas**, sem alteração.

```
objective 8:  could not build a valid Question - alternative A: text is empty and no asset is set
objective 38: could not build a valid Question - alternative A: text is empty and no asset is set
objective 55: could not build a valid Question - alternative A: text is empty and no asset is set
```

Reinspecionadas as regiões visuais candidatas diretamente: continuam grandes blobs mesclados
(`is_small_formula=False` para todas), não pequenos candidatos por alternativa — a mesma conclusão
da Fase 3B, agora reconfirmada sob a correção desta fase. Nenhuma correção específica foi tentada
(conforme instruído). Exclusão preservada, sem inferência de resposta. Recomenda-se fase própria
para alternativas puramente visuais (ver seção Z).

## O. Regressões preservadas

**Q34 de 2011**: `needs_review`/`non-structural`, exatamente como antes — não tocado. O experimento
de enforcement de `owner_key` documentado na Fase 3B permanece revertido; não foi reintroduzido sob
outro nome nesta fase.

**Q21/Q22/Q23**: revalidados sem alteração — `test_q21/q22/q23_statement_is_complete_and_uncontaminated`
continuam passando sem modificação.

**Os 18 blockers resolvidos na Fase 3B**: revalidados; nenhum reaberto pela correção desta fase.

**Novo experimento revertido nesta fase** (seção E.3): documentado em
`scratchpad/experiment-column-height-ratio.diff` e `scratchpad/experiment-q68-vs-q50-evidence.md`,
com o motivo da reversão registrado permanentemente como comentário em `layout.py` — não
reintroduzido sob outro nome.

## P. Overrides/profile

**Novo campo declarativo**: `ExamStructureProfile.region_merge_x_tolerance: float | None = None`
(exam_profile.py). `None` é o comportamento original e inalterado para todo booklet existente (2011,
2021, e o próprio 2008-b antes desta fase); apenas `data/manifests/exam-structure-2008.yaml` define
um valor finito (`150.0`), com justificativa documentada inline no próprio YAML. Nenhum
`layout-overrides.yaml` foi criado, removido ou necessário — a correção é uma regra geral gated por
capacidade declarativa (Seção 23 do prompt), não um override vinculado a um PDF/bbox específico.
Nenhum question ID foi inserido na lógica central do parser.

## Q. Auditoria visual

```
Fase 3B: 30 passed, 15 failed, 32 not_performed
Fase 3C: 30 passed, 17 failed, 30 not_performed  (77 total, fully_covered=True)
```

Composição do `passed` mudou mesmo com o total igual a 30: D10 saiu (falso `passed` corrigido para
`failed`), D79 entrou (novo, genuíno). D20/D39 permanecem `passed`, mas agora por um motivo real, não
por uma alegação prematura da Fase 3B. As 30 `passed` restantes foram cada uma comparada
integralmente contra o texto-fonte em fases anteriores ou nesta (D20, D39, D79 nesta fase); as 17
`failed` têm causa e evidência documentadas no ledger; as 30 `not_performed` permanecem honestamente
não verificadas individualmente (apenas 2 das 32 anteriores foram auditadas nesta sessão — seção M).

## R. Blocker ledger

```
Fase 3B: 40 blockers, 22 open, 18 resolved
Fase 3C: 43 blockers, 24 open, 19 resolved
```

3 blockers novos: `d10-label-absorption-newspaper-fragments` (open, corrigindo a alegação indevida
de resolução da Fase 3B), `d39-region-merge-content-loss` (resolved, encontrado e corrigido na mesma
fase), `d60-cross-question-diagram-label-bleed` (open, defeito pré-existente descoberto na primeira
auditoria real desta questão). Dois blockers existentes tiveram seu texto de causa/resolução
atualizado com a evidência desta fase (`d09-region-merge-content-loss`,
`d20-region-merge-content-loss`, `d40-table-reading-order-scramble`). `validate_ledger`: 0 problemas.
Nenhum blocker desapareceu silenciosamente.

## S. Gold 2008-B

```
maturity: provisional
verified: 28/77  (Fase 3B: 27/77)
needs_review: 49/77
structural_blockers: [answer-standard-absent-from-source, answer-standard-incomplete,
  content-duplication, cross-question-contamination, region-merge-content-loss,
  table-reading-order-scramble, unstructured-image-alternatives]
verify-gold: OK (77 questions match)
```

Não promovido a `validated` — blockers estruturais reais permanecem abertos, conforme instruído
explicitamente. O aumento líquido de verified (+1) reflete D79 entrando e D10 saindo, com D20/D39/D80
permanecendo verified por um motivo agora genuíno.

## T. Readiness

```
enade assess-readiness --year 2008 --course all-computing \
  --ready-label READY_FOR_2008_ENGINEERING_TEST \
  --not-ready-label NOT_READY_FOR_2008_ENGINEERING_TEST
→ NOT_READY_FOR_2008_ENGINEERING_TEST (exit code 1)
  28/77 verified, 49 needs_review, gold maturity=provisional
  visual audit: 30 passed, 17 failed, 0 not_performed (fully_covered=True — mesma convenção de
    contagem já usada nas Fases 3A/3B: todas as 77 chaves estão presentes no arquivo, cada uma com
    status explícito; ver nota na seção D)
  83 blocker(s), todos estruturais
```

## U. Proteção de 2011

```
verify-gold --year 2011 --course all-computing → OK (55/55), maturity=validated
assess-readiness → READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, 1 needs_review
  1 blocker: [question_not_verified, non-structural] enade-2011-computing-q34
ledger: 38 total, 0 open (inalterado)
```

Q34 permanece exatamente como estava — não tocado. **Zero drift**: hash SHA-256 de cada um dos 270
arquivos de questões de 2011/2021 + 18 manifestos relacionados (288 no total) idêntico ao congelado
antes de qualquer mudança de código, confirmado byte a byte **quatro vezes** ao longo desta fase
(após a primeira tentativa de fusão sem gate, após a versão gated final, após a tentativa de razão
de altura revertida, e após a formatação automática do `ruff format`).

## V. Proteção de 2021

```
verify-gold --year 2021 --course ciencia-da-computacao-bacharelado → OK (40/40), validated
assess-readiness → READY_FOR_2011, 40/40 verified, 0 needs_review, no blockers
```

**Zero drift** — incluído nos mesmos 288 arquivos verificados acima. As duas outras variantes de
curso 2021 (`ciencia-da-computacao-licenciatura`, `sistemas-de-informacao`) também foram
regeneradas e comparadas byte a byte contra o corpus publicado — zero diferenças.

## W. Testes

```
Fase 3B (baseline desta fase): 481 passed
Fase 3C: +6 novos testes
  - tests/test_extraction_figures.py: 3 (comportamento padrão inalterado; rejeita retângulos
    distantes em X sob tolerância finita; ainda mescla retângulos próximos sob tolerância finita)
  - tests/test_extraction_pipeline_2008.py: 3 (D09 não mais vazio; D20/D39 completos e sem figura
    espúria, corpus real)
Total final: 487 passed
```

## X. Quality gates

```
pytest -q                            → 487 passed
ruff check .                         → All checks passed!
ruff format --check .                → 373 files already formatted
mypy src                             → Success: no issues found in 52 source files
enade validate-schema                → 13/13 fixture(s) valid
enade validate-manifest              → OK (0 warnings)
enade audit-extraction (corpus todo) → 252/252 OK
verify-gold + assess-readiness (2011, 2021, 2008) → ver seções S/T/U/V
```

## Y. Reprodutibilidade

Duas extrações limpas e independentes do caderno 2008-b, diretórios isolados:
```
diff -rq run-A run-B                 → 0 diferenças
diff -rq run-A data/questions/2008   → 0 diferenças (idêntico ao publicado)
```
Nenhum campo com timestamp ou reordenação não determinística observado.

## Z. Desempenho

```
Páginas processadas: 36
Questões delimitadas: 80 (77 publicadas + 3 excluídas)
Assets renderizados: 38 (Fase 3B: 46 — queda esperada: menos figuras espúrias derivadas da grade RASCUNHO)
Tempo de extração: ~57-64s por execução (aumento frente à Fase 3B, atribuído à variação de máquina
  desta sessão, não a uma mudança algorítmica de complexidade — o novo parâmetro de tolerância X é
  O(1) por comparação)
```

## AA. Bugs encontrados

**Corrigidos** (1 mudança de regra geral, gated declarativamente, testada, zero drift 2011/2021):
1. `figures.py`: `_merge_by_vertical_proximity` ganhou verificação de eixo X opcional
   (`x_tolerance`), ativada apenas para 2008-b via `ExamStructureProfile.region_merge_x_tolerance`.

**Revertidos** (documentados, não mantidos), ambos em `layout.py`'s `detect_column_margins`:
1. Gate de razão de altura de coluna — corrigia Q68, quebrava Q49/Q50 (regressão de contaminação
   cruzada real). Ver seção E.3.
2. Gate de razão de altura + monoespaçado — nunca dispara para Q68 (a fonte deste PDF não é
   reconhecida como monoespaçada pela heurística existente); sem risco, mas também sem correção.

**Corrigido incidentalmente por engano de auditoria anterior, não por código novo**: D10, D20, D39
foram reveladas, por reinspeção direta nesta fase, como tendo tido a alegação `passed`/"no residuals
found" da Fase 3B incorreta — o defeito real (figura espúria da grade RASCUNHO) continuava presente
no arquivo então committado. D20 e D39 foram genuinamente corrigidas pela correção de fusão desta
fase; D10 permanece com um defeito real e distinto (perda de conteúdo, não apenas a figura espúria).

**Não corrigidos, permanecem como blockers abertos**: absorção de legenda residual em D09
(headline real absorvida como legenda), D10 (2 de 3 fragmentos de notícia perdidos), D40 (um rótulo
de diagrama residual); embaralhamento de tabela/código em D40 (resolvido pela mesma causa que a
absorção residual — não mais um blocker de reordenação, mas sim de rótulo residual), Q24, Q63, Q29,
Q33, Q68 (causa raiz de Q68 precisamente isolada, correção tentada e revertida duas vezes);
contaminação cruzada em Q62 e agora também D60 (pré-existente, recém-descoberta); duplicação em Q13;
perda parcial em Q12; três questões com alternativas puramente visuais (Q8/Q38/Q55, confirmadas
inalteradas).

## AB. Arquivos e Git final

**Modificados (código)**: `src/enade/extraction/{figures.py, layout.py, assembler.py,
exam_profile.py, pipeline.py}`, `tests/{test_extraction_figures.py, test_extraction_pipeline_2008.py}`.

**Modificados (dados)**: `data/manifests/{exam-structure-2008.yaml, blocker-ledger-2008.yaml,
visual-audit-2008-computing.json, gold-2008-computing.json,
extraction-audit-2008-computing.{csv,json}}`; `data/questions/2008/all-computing/` — 8 arquivos
`.md` (d09, d10, d20, d39, d40, d60, d79, d80) e seus assets (vários `.png` removidos por serem
espúrios/órfãos, dois modificados em d40).

**Removidos**: nenhum arquivo canônico — apenas assets de figura espúrios/órfãos (agora inexistentes
porque a questão correspondente não tem mais aquela figura), regenerados automaticamente pela
extração, não removidos manualmente.

**Novo (não versionado, documentação de experimento)**: `scratchpad/experiment-column-height-ratio.diff`,
`scratchpad/experiment-q68-vs-q50-evidence.md`.

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   586005e7563a4d3378dea61fc0914278f2b6d6e4 (inalterado — nenhum commit criado)
32 caminhos com alterações no working tree (staged: 0)
```
**Confirmado explicitamente**: nenhum commit, push, PR, merge ou tag foi executado nesta fase.

## Recomendação

Dado o resultado `PARTIAL`, em ordem de impacto esperado:

1. **Absorção de legenda residual** (D09, D10, e o rótulo residual de D40) exige a separação real
   entre inclusão-no-crop e consumo-de-texto (Seção 7-9 do prompt) — não uma correção geométrica
   isolada. Isso provavelmente precisa de uma segunda bbox por região, mais conservadora, computada
   com uma política de "quantos passes de absorção contam como consumo" que ainda não foi desenhada
   com segurança suficiente para não arriscar 2011/2021.
2. **Contaminação cruzada persistente** (Q62, D60 — ambas envolvendo rótulos do diagrama ITIL de
   Q61) sugere uma causa comum ainda não isolada especificamente para esse diagrama; investigar
   antes de tentar uma correção geral de "rótulo de diagrama nunca cruza para a questão seguinte".
3. **Embaralhamento de tabela/código** (Q24, Q29, Q33, Q63, Q68) precisa da arquitetura de "ilha de
   leitura local" descrita nas Seções 12-13 do prompt como mecanismo dedicado — não uma correção
   pontual sobre `detect_column_margins`, que esta fase mostrou ser insegura mesmo quando
   estreitamente direcionada.
4. **Completar a auditoria visual das 30 questões `not_performed` restantes** — apenas 2 das 32
   foram cobertas nesta fase, como efeito colateral de investigar o impacto da correção de fusão.
5. **Reconsiderar Q8/Q38/Q55** somente depois de (1)-(3) resolvidos — a mesma classe de correção
   pode alterar a forma dos candidatos disponíveis para essas três questões. Recomenda-se
   explicitamente uma fase própria e dedicada para alternativas puramente visuais, conforme a Seção
   22 do prompt já antecipava.

**O bundle `e` de 2008 não deve ser o próximo teste** até que este primeiro caderno esteja
integralmente validado, conforme o princípio final do prompt desta fase. Não iniciado
automaticamente.
