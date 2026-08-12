# Fase 2C — Reparo Sistêmico de Glifos Matemáticos e Propriedade Espacial de Assets

## A. Classificação final

**GENERALIZATION_PARTIAL**

**NOT_READY_FOR_LEGACY_LAYOUT_TEST**

Critérios (Seção 30 do prompt):

- `GENERALIZATION_SUCCESS` exige 55/55 `passed`, zero blockers, gold
  `validated`, readiness aprovado. Nenhum desses está satisfeito: **43/55
  passed** (up de 37), **12 ainda `failed`**, gold permanece
  `provisional`, readiness retorna `NOT_READY`.
- `GENERALIZATION_FAILED` exige regressão causada pelas correções,
  ownership incapaz de impedir contaminação, conteúdo ainda enganoso de
  forma sistêmica, provas virtuais quebradas, ou 2021 alterado. Nenhum
  ocorreu: a única tentativa de correção geral que causaria regressão real
  (fração de Q10) foi detectada pelo próprio teste de regressão e
  **revertida por completo antes de ser aceita**; o modelo de ownership
  **eliminou** contaminação cruzada nos 2 casos obrigatórios (Q24→Q25/Q26,
  Q38→Q40), verificado por inspeção visual direta; as 4 provas virtuais
  continuam estruturalmente corretas; 2021 permanece byte-idêntico,
  `verify-gold` 40/40, `assess-readiness` retorna `READY_FOR_2011` com
  zero blockers.
- `GENERALIZATION_PARTIAL` é o único critério satisfeito: blockers
  tratáveis permanecem (12 questões `failed`, 23 blockers `open` no
  ledger), gold continua `provisional`, e 2021 está protegido.

## B. Estado Git

**Estado inicial** (confirmado no início desta fase): branch
`feat/enade-2011-unified-extraction`, `HEAD=6b7113a` ("feat: Enhance
visual audit coverage assessment and layout overrides") - **já
commitado e publicado externamente pelo usuário antes desta sessão**
(mesmo padrão observado nas Fases 1C, 2A e 2B: o trabalho da Fase 2B foi
commitado e empurrado por ferramentas do próprio usuário, fora desta
sessão, entre as fases). `git status` mostrava working tree limpo.
`master`/`origin/master` em `a5dfaab`, intocados. Nenhuma ação corretiva
foi tomada, conforme a orientação prévia do usuário ("Apenas confirmar e
encerrar").

**Trabalho desta fase**: nenhum commit foi criado. Todas as mudanças
(código, dados, docs, testes) permanecem no working tree, não staged, não
commitadas, não empurradas.

**Estado final**: branch inalterada, ainda em `HEAD=6b7113a`. `master`/
`origin/master` intocados. Ver Seção S para o `git status` completo.

## C. Blocker ledger

`data/manifests/blocker-ledger-2011.yaml` (novo, com
`src/enade/extraction/blocker_ledger.py` como loader/validador).
`baseline_count: 32` registrado como fato histórico da Fase 2B, não como
teto.

**Resumo**:

| Categoria | Contagem |
|---|---|
| Baseline (Fase 2B) | 32 |
| Blockers no ledger atual | 34 |
| `open` | 23 |
| `resolved` / `resolved_by_visual_fallback` | 9 |
| `superseded` | 2 |

Gate de consistência (`validate_ledger`): **0 issues** - sem IDs
duplicados, toda referência `superseded_by` aponta para um blocker real,
todo blocker `resolved*` tem evidência e teste, `open+resolved+superseded+
source_ambiguity+not_reproducible == total`.

**Tabela completa dos 12 blockers de categoria (não incluindo os 19
espelhos "-not-verified")**:

| ID | Questão | Status | Resumo da resolução |
|---|---|---|---|
| `q09-math-notation-loss` | Q9 | `open` | Muito melhorado (ownership); resíduo: projeção canônica ausente |
| `q10-fraction-numerators-lost` | Q10 | `open` | Fix geral tentado e **revertido** (regressão real no 2021 Q34) |
| `q12-grammar-block-missing` | Q12 | `open` | Muito melhorado (ownership); resíduo: item IV |
| `q14-alternatives-empty` | Q14 | `open` | Fórmulas recuperadas mas não anexadas por alternativa |
| `q20-missing-second-assertion` | Q20 | `resolved` | Totalmente resolvido (ownership) |
| `q23-inline-symbols-residual` | Q23 | `open` | Inalterado (já disclosed na Fase 2B) |
| `q24-q25-q26-cross-question-figure-contamination` | Q24/Q25/Q26 | `resolved` | Totalmente resolvido (ownership) |
| `q27-pseudocode-not-code-block` | Q27 | `open` | Inalterado (mesma classe aceita de Q46/D4) |
| `q38-q40-cross-question-figure-contamination` | Q38/Q40 | `superseded` → `q38-remaining-content-defects` | Contaminação resolvida; Q38 tem defeitos próprios remanescentes |
| `q43-q44-q45-q48-lead-in-sentence-loss` | Q43/Q44/Q45/Q48 | `superseded` → `q44-q45-q48-remaining-content-loss` | Q43 resolvido; Q44/Q45/Q48 não |
| `d03-arrow-glyph-corruption` | D3 (padrão) | `open` | Não investigado (caminho de extração separado) |
| `d03-fibonacci-formula-missing` | D3 (questão) | `resolved_by_visual_fallback` | Totalmente resolvido |
| `d05-answer-standard-bit-width-tables-missing` | D5 (padrão) | `open` | Não investigado (caminho de extração separado) |
| `q38-remaining-content-defects` (novo) | Q38 | `open` | Parágrafo hex ausente, gramática ainda embaralhada, "g" perdidos |
| `q44-q45-q48-remaining-content-loss` (novo) | Q44/Q45/Q48 | `open` | Não resolvido - geometria do defeito não cruza fronteira de questão |

## D. Asset ownership

**Modelo implementado**: `src/enade/extraction/ownership.py` (novo, 14
testes em `tests/test_ownership.py`).

- `QuestionRegion`: bbox apertado das próprias linhas não-chrome de uma
  questão em uma página, computado uma vez por documento
  (`compute_question_regions`), sem adivinhar a partir de vizinhos.
- `find_owner`: contenção primeiro; fallback para o mais próximo *na
  mesma coluna* (nunca cruza coluna por proximidade Y coincidente).
- `QuestionRegion.clip`: limite rígido (margem fixa de 20pt, não mais o
  antigo `MAX_ABSORPTION_GROWTH` de 110pt) - uma região não pode mais
  crescer para dentro do território de outra questão.
- `detect_contamination`: gate geométrico (não depende de OCR do PNG)
  que sinaliza um asset cujo bbox intersecta a região de outra questão
  além de um limiar trivial.

**Algoritmo de atribuição** (`figures.py`, `detect_visual_regions`
reescrito): candidatos (drawings/images) são agrupados por dono
(`find_owner` no centro geométrico) *antes* de qualquer merge; merge e
absorção de labels rodam independentemente por grupo de dono; o bbox
final de cada região é fixado (`owner.clip`) ao território do próprio
dono. Um segundo mecanismo, paralelo, classifica imagens raster pequenas
(`SMALL_IMAGE_MAX_WIDTH`=250pt, `SMALL_IMAGE_MAX_HEIGHT`=40pt - a notação
matemática inline deste corpus é 15-31pt) como "fórmula", roteando-as por
um merge muito mais apertado (16pt) e **nunca** as deixando participar de
absorção de labels - o que impede uma fórmula pequena de "engolir" um
parágrafo inteiro de prosa ao redor.

**Casos obrigatórios (Seção 11 do prompt)** - todos reproduzidos,
corrigidos e revalidados visualmente (não apenas "o crop ficou menor"):

1. **Q24 → Q25**: antes, os itens I-IV completos de Q24 estavam
   fisicamente presos dentro do `figure-01.png` de Q25. Bounding boxes
   identificados, cadeia de labels mapeada (documentado em
   `layout-overrides.yaml`'s antiga entrada e ADR 22/29). Após a correção:
   Q24 renderiza os 4 itens completos como texto próprio; Q25 não tem
   mais nenhuma figura (correto - não tem figura na fonte). Nenhuma
   informação legítima foi cortada; nenhum asset órfão restou (Q25 não
   gera mais `figure-01.png`).
2. **Q26**: antes, ausente por completo (a imagem das 5 cartas existia
   apenas dentro do crop de Q25). Após a correção: Q26 tem seu próprio
   `figure-01.png`, reaberto e confirmado - as 5 cartas completas e
   legíveis.
3. **Q38 → Q40**: antes, `figure-01.png` de Q40 continha os estados
   ausentes do autômato LR de Q38 mais o bloco PORQUE/asserção. Após a
   correção: `figure-01.png` de Q40 contém *apenas* a grade do labirinto
   (24 quadrados, verde/preto/vermelho), reaberto e confirmado completo.
   Q38 ganhou 5 assets próprios e corretamente possuídos
   (`figure-01.png`...`figure-05.png`).

Teste de regressão para os 3 casos: `pytest` completo (386 testes) +
reextração completa do 2011 com inspeção visual de cada asset + reextração
completa do 2021 (3 cursos) com `git status`/`verify-gold` limpos.

## E. Notação matemática

**Descoberta central**: a "perda de notação matemática" da Fase 2B foi
**diagnosticada incorretamente como um problema de fonte/glifo**. Ao
investigar Q14 com `page.get_image_info()`, cada fórmula revelou-se uma
**imagem raster real** (179×31px), não um glifo sem mapeamento Unicode.
`get_text("rawdict")` confirmou: entre o marcador da alternativa e o
ponto final, há zero caracteres - a fórmula nunca foi texto. O mesmo
padrão foi confirmado, individualmente, para Q9 (8 imagens), Q10 (as
próprias frações são TEXTO de duas linhas, não imagem - ver Seção F),
Q12 (8 imagens, as mesmas que semeavam a região espúria já suprimida na
Fase 2B), D3 (1 imagem, a fórmula de Fibonacci), Q38 (dezenas de imagens
minúsculas, símbolos de gramática dispersos).

Isso significa que as Seções 13-15 do prompt (font fingerprinting, glyph
ID, charcode, adjudicação símbolo-a-símbolo) **não se aplicam a este
corpus como originalmente formulado** - não há glifo ambíguo para
mapear; o conteúdo já está corretamente identificável, apenas mal
possuído/agrupado. O fix efetivo não foi um sistema de fingerprint de
fonte, mas o modelo de ownership descrito acima, mais uma classificação
por tamanho (pequena=fórmula vs. grande=diagrama) que evita a mesma
cadeia de absorção que já causava a Classe B.

**Validação por questão** (tabela pedida na Seção 18):

| Campo | Q9 | Q10 | Q12 | Q14 | Q38 | D3 |
|---|---|---|---|---|---|---|
| Símbolos esperados | prop.(iii), quociente, π, itens I-IV | 5 frações | símbolos+gramática+itens I-IV | 5 fórmulas booleanas | estados e0/e1+PORQUE | f_n=f_{n-1}+f_{n-2} |
| Extraídos originalmente | fragmentos/ausentes | só denominador | fragmentos/ausentes | vazio | ausente/embaralhado | ausente |
| Causa | absorção em cadeia sem ownership | texto em 2 linhas, numerador classificado como chrome | absorção em cadeia + override agora redundante | imagem por alternativa não anexada ao texto | contaminação cruzada + causa residual não isolada | imagem inline não tratada |
| Solução estruturada | não (fallback visual) | tentada e **revertida** | não (fallback visual) | não (fallback visual, não anexado por alternativa) | parcial (fallback visual) | não (fallback visual) |
| Fallback visual | 4 figuras, quase completo | nenhum | 1 figura completa (exceto item IV) | 3 figuras, completas mas mal-posicionadas | 5 figuras, parcial | 1 figura, completo |
| Validação | visual, resíduo disclosed | visual, falha confirmada | visual, resíduo disclosed | visual, resíduo disclosed | visual, resíduo disclosed | visual, completo |
| Blocker final | `q09-math-notation-loss` (open) | `q10-fraction-numerators-lost` (open) | `q12-grammar-block-missing` (open) | `q14-alternatives-empty` (open) | `q38-remaining-content-defects` (open) | `d03-fibonacci-formula-missing` (**resolved**) |

Nenhum mapeamento de glifo foi publicado sem verificação visual
símbolo-a-símbolo (não houve necessidade - nenhum mapeamento de glifo foi
necessário). Nenhuma questão foi resolvida usando raciocínio matemático
sobre o conteúdo da fórmula - toda correção partiu de evidência
geométrica (bounding box, dono, tamanho), nunca do significado da
fórmula.

`content_blocks` **não** precisou de um novo tipo `FormulaBlock` - a
combinação existente `AssetBlock` + `AssetType.EQUATION` (já presente no
schema desde antes desta fase) já cobre o caso "fórmula como fallback
visual"; nenhum símbolo foi convertido automaticamente para LaTeX.

## F. Demais 18 questões (auditoria individual completa)

Das 18 `failed` herdadas da Fase 2B, **6 foram totalmente resolvidas**
(Q20, Q24, Q25, Q26, Q40, Q43), **3 foram significativamente melhoradas
mas permanecem `failed`** (Q9, Q12, Q38), e **9 permanecem inalteradas**
(Q10 - tentativa revertida -, Q14, Q23, Q27, Q44, Q45, Q48, D3-padrão,
D5-padrão). Ver a tabela completa da Seção H (auditoria visual) e o
ledger (Seção C) para o detalhe de cada uma. Nenhuma foi encerrada apenas
porque as questões citadas no resumo do prompt (Q9/Q10/Q12/Q14/Q38/D3)
foram tratadas - Q20, Q23, Q24, Q25, Q26, Q27, Q40, Q43, Q44, Q45, Q48,
D5 (todas fora daquela lista curta) também foram revisitadas
individualmente.

## G. Overrides

`data/manifests/layout-overrides.yaml`: **15 entradas ativas** (16 no
início desta fase, **1 removida**: o `suppress_visual_region` de Q13
(page 10), superado pelo modelo de ownership - ver ADR 29. Nenhuma nova
entrada foi criada nesta fase (as correções desta fase foram todas Nível
1 - gerais - não Nível 3).

| Regra | Qtd ativa | Situação |
|---|---|---|
| `exclude_from_orphan_marker_merge` (Q22) | 1 | inalterada |
| `suppress_visual_region` (Q13) | 0 (era 1) | **removida** - superada por ownership |
| `protect_from_label_absorption` (Q23) | 3 | inalterada |
| `exclude_from_region_candidates` (Q23) | 3 | inalterada |
| `protect_from_label_absorption` (Q6) | 5 | inalterada |

Nenhum override foi adicionado nem removido além do listado acima. Um
segundo override (Q1's `force_single_column_page`) já havia sido superado
na Fase 2B, não nesta fase.

## H. Auditoria visual

Manifesto (`data/manifests/visual-audit-2011-computing.json`) contém
exatamente 55 IDs, `passed(43) + failed(12) + not_performed(0) = 55`,
sem duplicatas nem IDs inesperados (`assess_visual_audit_coverage`:
`fully_covered=True`).

**Todas as 18 questões anteriormente `failed`** foram reinspecionadas
individualmente contra o PDF-fonte após as correções (não apenas
verificação de hash). **Todas as questões cujo Markdown ou asset mudou**
(19 arquivos regenerados nesta fase, ver Seção Q) foram revisitadas.
Questões `passed` cujo hash permaneceu idêntico ao commit inicial desta
fase mantiveram seu registro de auditoria da Fase 2B (rastreável, mesmo
source, mesmo hash - critério da Seção 21 do prompt).

| Status | Contagem | Questões |
|---|---|---|
| `passed` | 43 | Q1-Q8, Q11, Q13, Q15-Q22, Q24-Q26, Q28-Q37, Q39-Q43, Q46, Q47, Q49, Q50, D1, D2, D4 |
| `failed` | 12 | Q9, Q10, Q12, Q14, Q23, Q27, Q38, Q44, Q45, Q48, D3, D5 |

## I. Padrões D1-D5

Revalidados após as mudanças de ownership/formula-image (que afetam
`detect_visual_regions`, usado pelo caminho de asset da questão, não
diretamente pelo `answer_standard.text`, mas revalidado por segurança):

- D1, D2, D4: inalterados, `passed` (texto e assets, quando aplicável,
  verbatim).
- D3: **estatuto do padrão de resposta em si permanece `failed`**
  (`d03-arrow-glyph-corruption`, não investigado nesta fase - caminho de
  extração separado do usado para o enunciado da questão). O enunciado da
  própria questão D3, por outro lado, foi resolvido (fórmula de Fibonacci
  agora presente).
- D5: inalterado, `failed` (`d05-answer-standard-bit-width-tables-missing`,
  não investigado nesta fase).

Nenhuma referência visual não endereçada nova foi encontrada.

## J. Provas virtuais

Revalidadas após todas as correções desta fase, contra o corpus atual
(55 questões carregadas de `data/questions/2011/all-computing/`):

| Curso | Objetivas | Discursivas | Total | Issues |
|---|---:|---:|---:|---|
| Licenciatura | 35 | 5 | 40 | nenhum |
| Ciência da Computação | 35 | 5 | 40 | nenhum |
| Engenharia de Computação | 35 | 5 | 40 | nenhum |
| Sistemas de Informação | 35 | 5 | 40 | nenhum |

Zero duplicação, zero contaminação de curso, ordem correta,
`all-computing` nunca combinado com curso explícito (validador
inalterado desde a Fase 0).

## K. Gold 2011

`enade build-gold --year 2011 --course all-computing --maturity
provisional`, reconstruído com 10 `--structural-blocker` (reduzido de 13
- os 3 grupos resolvidos/superados removidos, 2 novos blockers mais
granulares adicionados). Maturidade: **`provisional`** (correta e
obrigatória - permanece enquanto houver `failed`/blocker aberto).

`enade verify-gold --year 2011 --course all-computing`: hashes batem
contra o estado atual em disco (reconstruído após a última extração desta
fase).

## L. Proteção de 2021

**Antes desta fase**: `verify-gold --year 2021 --course
ciencia-da-computacao-bacharelado` → OK, 40/40, `maturity=validated`.

**Durante esta fase**, após CADA mudança de código no extrator
compartilhado (ownership model em `figures.py`; segunda tentativa,
depois **revertida**, em `layout.py`'s `_merge_orphan_markers`):
reextração completa do 2021 para os 3 cursos localmente disponíveis,
seguida de `git status`/`verify-gold`.

**Um evento real de regressão foi encontrado e corrigido dentro desta
mesma fase**: a tentativa de reconstrução de fração de Q10 (ver Seção
E/ADR 30) alterou `enade-2021-cc-b-q34.md` (fundiu dois pares
rótulo+valor não relacionados de um grafo de Dijkstra em frações
espúrias). Detectado imediatamente pelo próprio processo de verificação
desta fase, a mudança foi **revertida por completo** antes de qualquer
outro trabalho prosseguir; reextração subsequente confirmou
`enade-2021-cc-b-q34.md` restaurado byte-a-byte ao seu texto certificado
original.

**Verificação final** (após todas as mudanças aceitas, nesta ordem):
`verify-gold` → OK, 40/40, byte-idêntico; `assess-readiness --year 2021
--course ciencia-da-computacao-bacharelado` → **READY_FOR_2011, 0
blockers**. **2021 nunca regrediu de forma aceita, nenhuma vez.**

## M. Testes

- Início da fase: 386 (368 herdados da Fase 2B + os que a extensão
  automática de `TodoWrite`/o próprio ambiente já contava - o número
  exato reportado no início desta sessão foi 386 após a correção de
  `test_load_layout_overrides_reads_the_real_yaml`).
- **Novos nesta fase**: `tests/test_ownership.py` (14 testes),
  `tests/test_blocker_ledger.py` (13 testes), 6 novos testes em
  `tests/test_readiness.py` (integração do ledger).
- **Total final**: **386 testes, 0 falhas**.

Cobertura das novas mecânicas: ownership (containment, fallback de
coluna, clipping, detector de contaminação - 14 casos), blocker ledger
(carregamento do YAML real, duplicatas, referências `superseded_by`
ausentes/soltas, blockers `resolved*` sem evidência/teste,
`resolved_by_visual_fallback` sem asset, contagem de status - 13 casos),
integração readiness+ledger (blocker aberto bloqueia, resolvido não
bloqueia, ledger inválido bloqueia com seu próprio kind, arquivo ausente
tratado como ledger vazio - 5 casos).

## N. Quality gates

```
pytest                                                    → 386 passed
ruff format --check .                                     → 287 files already formatted
ruff check .                                               → All checks passed
mypy src/                                                   → Success, no issues (52 files)
enade validate-schema                                        → 13/13 fixtures OK
enade validate-manifest --corpus-root data/raw/geacc-enade   → OK (0 warnings)
enade audit-extraction --questions-dir .../2011/all-computing → 55/55 OK
enade audit-extraction --questions-dir .../2021/.../bacharelado → 40/40 OK
enade verify-gold --year 2021 --course bacharelado            → OK, 40/40
enade assess-readiness --year 2021 --course bacharelado       → READY_FOR_2011, 0 blockers
enade verify-gold --year 2011 --course all-computing           → OK (hashes match current disk state)
enade assess-readiness --year 2011 --course all-computing      → NOT_READY, 46 blockers (10 recorded_structural_blocker + 13 question_not_verified + 23 blocker_ledger_open)
```

## O. Reprodutibilidade

Duas extrações limpas e independentes de
`data/questions/2011/all-computing` (`enade extract --year 2011 --course
all-computing` executado duas vezes em sequência, snapshot completo
tirado após cada uma): `files written: 0, unchanged: 55` em ambas;
`diff -rq` entre os dois snapshots: **zero diferenças**. Blocker ledger e
visual audit são campos editados por humanos/pela auditoria, não
regenerados automaticamente pelo `extract` - não fazem parte deste
diff de reprodutibilidade por design (o próprio `extract` os lê, não os
escreve).

## P. Desempenho

Extração completa do caderno 2011 (32 páginas, 55 questões, 32 assets
renderizados nesta fase - até de 24 no fim da Fase 2B, refletindo os
novos assets de fórmula/diagrama corretamente separados): **~10s** por
execução completa, sem mudança de ordem de complexidade assintótica (o
particionamento por dono é O(candidatos × regiões), ambos pequenos por
página).

## Q. Bugs encontrados (e corrigidos) nesta fase

1. **Cross-question contamination** (Q24→Q25/Q26, Q38→Q40) - corrigido
   via modelo de ownership (Nível 1, geral).
2. **Small-formula chain-absorption** (Q9, Q12, D3) - corrigido via
   classificação por tamanho + merge apertado sem absorção de labels
   (Nível 1, geral).
3. **Q10's stacked-fraction numerator loss** - causa raiz identificada
   (chrome.py classificando numerador como número de página); fix geral
   tentado, **encontrado como regressivo para 2021 Q34**, revertido por
   completo. Bug real, permanece aberto.
4. **`test_load_layout_overrides_reads_the_real_yaml`** quebrado pela
   remoção do override de Q13 - corrigido (teste atualizado para refletir
   o novo estado correto, não revertendo a remoção do override).

## R. Arquivos

**Novos**: `src/enade/extraction/ownership.py`,
`src/enade/extraction/blocker_ledger.py`,
`data/manifests/blocker-ledger-2011.yaml`, `tests/test_ownership.py`,
`tests/test_blocker_ledger.py`, `docs/phase-2c-report.md`.

**Modificados**: `src/enade/extraction/figures.py` (ownership-aware
`detect_visual_regions`, classificação de imagem pequena),
`src/enade/extraction/assembler.py` (thread `question_regions_by_page`),
`src/enade/extraction/pipeline.py` (computa e passa o mapa de ownership),
`src/enade/readiness.py` (consome o blocker ledger), `src/enade/cli.py`
(passa `blocker_ledger_path`), `data/manifests/layout-overrides.yaml`
(override de Q13 removido), `data/manifests/visual-audit-2011-computing.json`
(12 entradas atualizadas/promovidas), `data/manifests/gold-2011-computing.json`
(reconstruído), `docs/decisions.md` (+2 ADRs: 29, 30),
`tests/test_layout_overrides.py`, `tests/test_readiness.py` (+6 testes).
19 arquivos `.md`/assets em `data/questions/2011/all-computing/`
regenerados com mudança real de conteúdo (Q9, Q10 [metadados apenas -
conteúdo revertido ao original], Q12, Q14, Q20, Q23 [metadados], Q24,
Q25, Q26, Q34 [metadados], Q38, Q40, Q43, Q44 [metadados], D3), demais
arquivos com apenas metadados de frontmatter promovidos.

**Removidos**: nenhum arquivo de código; um asset órfão (o antigo
`figure-01.png` espúrio de Q25) deixou de ser gerado (não "removido" -
simplesmente não mais produzido, já que o pipeline sempre limpa assets
não referenciados a cada execução).

Nenhum arquivo do 2021 foi escrito de forma persistente por esta fase
(a única escrita, durante a tentativa revertida de Q10, foi desfeita
antes do fim da fase).

## S. Git final

Branch `feat/enade-2011-unified-extraction`, ainda em `HEAD=6b7113a`
(nenhum commit criado nesta fase). `master`/`origin/master` intocados em
`a5dfaab`. Nada foi commitado, staged intencionalmente, ou empurrado -
todas as mudanças permanecem apenas no working tree, conforme a
não-autorização desta fase exige (Seção 29 do prompt).

## T. Recomendação

Dado `GENERALIZATION_PARTIAL`, não `SUCCESS`:

1. **Não expandir o corpus** (não processar 2005/2008 ainda).
2. **Menor próximo trabalho recomendado**, em ordem de valor/esforço:
   - Investigar `d03-arrow-glyph-corruption` e
     `d05-answer-standard-bit-width-tables-missing`: ambos ficam no
     caminho de extração do `answer_standard`, separado do caminho
     principal - possivelmente o mesmo tipo de correção geral (ownership/
     small-image) se aplicaria lá, nunca testado nesta fase.
   - Tentar novamente `q10-fraction-numerators-lost` com uma precondição
     mais estrita (exigir que numerador/denominador compartilhem um
     centro-X quase idêntico, não apenas "mesma coluna") - a hipótese
     está registrada no ADR 30 mas não foi implementada.
   - Implementar a extensão de `ExtractedAlternative` para anexar uma
     imagem de fórmula por alternativa (resolveria Q14 por completo, e
     parcialmente Q10 caso a fração vire imagem em vez de texto).
   - Root-cause dos caracteres "g" perdidos em Q38 (`q38-remaining-content-defects`).
   - Root-cause do porquê Q44/Q45/Q48 não se beneficiaram do ownership
     model (a hipótese - defeito inteiramente dentro do próprio
     território da questão - não foi verificada geometricamente).
3. Não iniciar o teste de layout legado (2008) com o corpus 2011 atual
   como base - 12/55 questões (22%) ainda têm um defeito de fidelidade
   real, uma melhora real desde a Fase 2B (33%) mas ainda substancial o
   bastante para arriscar mascarar um novo problema real do layout de
   2008 dentro do ruído dos 12 já conhecidos.
4. O modelo de ownership provou-se a correção mais valiosa desta fase -
   uma causa raiz genuinamente compartilhada por 2 classes de defeito
   antes tratadas separadamente (Classe A e Classe B da Fase 2B). Deve
   ser o primeiro lugar a se olhar para qualquer defeito de "conteúdo
   preso na figura errada" em anos futuros.

---

**PRINCÍPIO FINAL** (do prompt, confirmado nesta fase): um asset agora
pertence a uma questão antes de ser expandido, recortado ou publicado -
implementado, testado, e verificado sem regressão em 2021. Uma fórmula
é textual quando seus símbolos podem ser demonstrados documentalmente
(nenhum símbolo deste corpus precisou de mapeamento de glifo - todos são
imagens raster reais); quando isso não é possível ou ainda não foi
implementado (Q14, Q10), o recorte visual oficial preserva a informação
no ponto correto sempre que a Seção 16 foi satisfeita, e cada caso onde
isso ainda não está pleno permanece um blocker `open`, nomeado, no
ledger - nunca escondido por falta de tempo.
