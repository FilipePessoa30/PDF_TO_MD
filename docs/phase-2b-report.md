# Fase 2B — Auditoria Visual Exaustiva e Fechamento do Corpus Unificado 2011

## A. Classificação final

**GENERALIZATION_PARTIAL**

**NOT_READY** (o `assess-readiness` gate, executado com
`--ready-label READY_FOR_LEGACY_LAYOUT_TEST`, retorna `NOT_READY` com 32
bloqueadores concretos e disclosed — ver Seção K).

Justificativa resumida (critérios do prompt, Seção 20):

- A auditoria visual das 55 questões canônicas está **completa**:
  `passed(37) + failed(18) + not_performed(0) = 55`, `not_performed=0`,
  sem duplicatas ou IDs inesperados (gate `assess_visual_audit_coverage`
  confirma `fully_covered=True`).
- O corpus 2021 permanece **byte-idêntico** ao estado já certificado
  (`verify-gold` para `ciencia-da-computacao-bacharelado`: 40/40 hashes
  batem; `git status` mostra zero diff nos arquivos rastreados) — validado
  repetidamente, após cada mudança de código desta fase.
- As 4 provas virtuais (35 objetivas + 5 discursivas = 40 por curso) são
  válidas e sem contaminação cruzada.
- Múltiplos defeitos reais e não-triviais foram encontrados, alguns
  corrigidos com fixes gerais/declarativos/auditáveis (nunca
  `if question_id==...` no núcleo do parser), mas **13 blocos de defeito
  estrutural permanecem sem correção**, afetando 18 das 55 questões
  (~33%) de forma que ainda **enganaria um leitor** que não consultasse o
  `visual-audit-2011-computing.json` (alternativas vazias, frações sem
  numerador, figuras erradas anexadas a outra questão). Isso é
  precisamente o que impede `GENERALIZATION_SUCCESS`: "defeitos resolvidos
  OU fielmente representados via fallback visual (nunca conteúdo
  enganoso)" não está satisfeito para esses 13 casos — eles estão
  **documentados com precisão**, não **corrigidos ou visualmente
  substituídos**.
- Por outro lado, nada indica `GENERALIZATION_FAILED`: a estrutura
  multi-curso funciona perfeitamente, 2021 não regrediu nenhuma vez,
  nenhum fix é um hack hardcoded por ID de questão, e a fidelidade de cada
  defeito remanescente está bem estabelecida (causa raiz identificada e
  documentada para praticamente todos os 18 casos `failed`).
- Gold do 2011 permanece `provisional` (correto e obrigatório dado o
  estado acima).

## B. Estado git

**Estado inicial** (confirmado no início desta fase): branch
`feat/enade-2011-unified-extraction`, `HEAD=4b22323` ("Refactor extraction
pipeline and introduce virtual exam functionality"), rastreando
`origin/feat/enade-2011-unified-extraction` (já publicado externamente
pelo usuário, fora desta sessão — mesmo padrão observado nas Fases 1C e
2A: nenhuma ação corretiva tomada, conforme orientação prévia do usuário
"Apenas confirmar e encerrar"). `master`/`origin/master` intocados.

**Trabalho desta fase**: nenhum commit foi criado. Todas as mudanças
(código, dados, docs, testes) permanecem no working tree, não staged, não
commitadas, não empurradas — conforme a não-autorização explícita do
prompt ("não faça commit, push, PR, tag ou altere master/2021-gold nesta
fase").

**Estado final** (ver Seção R para a listagem completa): 94 entradas em
`git status --short` — 72 modificados, 10 deletados (assets espúrios
removidos), 12 novos arquivos/diretórios (incluindo `layout_overrides.py`,
seu módulo de teste, e os manifests de extração 2021-L/2021-S, que já
eram artefatos não rastreados no início desta fase, não introduzidos por
ela).

## C. Reconciliação 54 vs 55

O relatório da Fase 2A continha um erro aritmético ("8 questões
auditadas" descrevendo na verdade 9 entradas) já identificado e corrigido
em `docs/phase-2a-report.md` no início desta fase, com nota explicativa.
Para eliminar essa classe de erro de forma estrutural, não apenas
prosa, foi usado (e agora reexecutado sobre o `visual-audit-*.json`
totalmente reescrito desta fase) o gate `assess_visual_audit_coverage`
(`src/enade/extraction/visual_audit.py`), que falha se
`passed+failed+not_performed != 55`, se `set(audit_ids) != set(canonical_ids)`,
ou se há chave JSON duplicada (via `object_pairs_hook`). Resultado atual:

```
passed=37 failed=18 not_performed=0 total=55
fully_covered=True unexpected_ids=frozenset() duplicate_ids=frozenset()
```

## D. Auditoria visual — tabela completa (55/55)

Os campos completos por questão (source_pages, automatic_validation,
visual_validation, visual_notes, defects, resolution) estão em
`data/manifests/visual-audit-2011-computing.json` (55 entradas, uma nota
detalhada por questão) — não duplicados aqui por extenso para evitar
divergência entre duas cópias da mesma informação. Resumo:

| Status | Contagem | Questões |
|---|---|---|
| `passed` | 37 | Q1-Q8, Q11, Q13, Q15-Q19, Q21, Q22, Q28-Q37, Q39, Q41, Q42, Q46, Q47, Q49, Q50, D1, D2, D4 |
| `failed` | 18 | Q9, Q10, Q12, Q14, Q20, Q23, Q24, Q25, Q26, Q27, Q38, Q40, Q43, Q44, Q45, Q48, D3, D5 |

Todas as 55 questões foram individualmente comparadas ao PDF-fonte
(`data/raw/geacc-enade/2011/1_prova.pdf`, todas as 32 páginas visualizadas
nesta fase) e, para D1-D5, também ao padrão de resposta
(`3_padrao.pdf`, 5 páginas). Nenhuma foi deixada como `not_performed`.

## E. Resolução dos 3 defeitos originais (Fase 2A)

1. **Q22 (tabela-verdade sem cabeçalho)** — **RESOLVIDO**. Duas correções
   gerais (Nível 1) tentadas e rejeitadas por regressão real no 2021
   certificado; corrigido com override Nível 3
   (`exclude_from_orphan_marker_merge`, hash-locked). Tabela completa
   (cabeçalho "A B C D S" + 16 linhas), verificada célula a célula.
   `tables_verified: true`.
2. **Q13 (figura espúria dividindo pseudocódigo)** — **RESOLVIDO**. Causa
   raiz: cadeia de absorção de labels ancorada em 3 imagens raster
   minúsculas (símbolos matemáticos inline de Q12) crescendo até englobar
   parte de Q11/Q12/Q13. Corrigido com `suppress_visual_region` (Nível 3).
   Q11 e Q12 também deixaram de exibir o aviso espúrio de "figura após o
   corte de alternativas".
3. **Q23 (notação matemática inline ausente)** — **PARCIALMENTE
   RESOLVIDO**. Causa raiz de dois efeitos combinados identificada
   (fragmentos de texto pós-símbolo elegíveis para absorção + as próprias
   imagens-símbolo re-ancorando o topo da região). Corrigido com 6
   overrides Nível 3 (3× `protect_from_label_absorption` + 3×
   `exclude_from_region_candidates`). Resíduo disclosed: os 3 símbolos
   (Σ={a,b,c}, Σ*, λ) continuam ausentes do texto/asset — a frase agora é
   gramaticalmente completa ao redor deles, mas os símbolos em si não são
   preservados. `status: failed` mantido intencionalmente (o resíduo é
   real, não cosmético).

## F. Novos defeitos encontrados durante a auditoria exaustiva

A auditoria não-amostral encontrou **15 defeitos adicionais** além dos 3
originais (18 `failed` no total). Dois padrões sistêmicos emergiram,
cada um afetando várias questões — não são 15 causas-raiz isoladas:

### Classe A — notação matemática/lógica inline não é texto extraível

Símbolos de conjunto, aritmética modular, frações empilhadas, gramáticas
BNF com símbolos, e álgebra booleana são renderizados como pequenas
sequências de glifos embutidos (fonte distinta do corpo do texto), que a
camada de texto do PyMuPDF não expõe como texto. Afetados: **Q9**
(propriedades de relação de equivalência, conjunto quociente, projeção
canônica, itens II-IV perdidos — nota: esta questão estava **rotulada
incorretamente como `passed` desde a Fase 2A**; a correção dessa etiqueta
é em si um resultado desta auditoria, ver Seção A), **Q10** (todas as 5
alternativas perdem o numerador da fração), **Q12** (nomes de símbolos e
todo o bloco de gramática BNF ausentes), **Q14** (as 5 alternativas
renderizam vazias), **Q38** (produções de gramática embaralhadas), **D3**
(fórmula de recorrência de Fibonacci ausente).

### Classe B — crop com largura de página inteira + absorção em cadeia atravessa questões não-relacionadas

`assets.py._render_bbox` alarga deliberadamente todo crop para a largura
de conteúdo da página (evitar cortar parágrafos largos ao lado de uma
figura estreita). Em página de duas colunas, isso alcança *ambas* as
colunas; combinado com a absorção em cadeia vertical de
`_expand_with_labels`, uma única região pode capturar visualmente
conteúdo de uma questão bem diferente (às vezes não-adjacente) sem que
esse conteúdo apareça no Markdown da questão correta. Confirmado por
inspeção direta dos assets: **Q25**'s `figure-01.png` contém os itens
I-IV completos de **Q24** + a imagem de cartas de **Q26** + o cabeçalho
"QUESTÃO 26"; **Q40**'s `figure-01.png` contém os estados de autômato
LR ausentes de **Q38**. Em ambos os casos a questão "receptora" não é
prejudicada, mas a dona original perde conteúdo real (não perdido da
extração — apenas mal-atribuído, sem rótulo, sob o cabeçalho errado).
Instâncias menores da mesma mecânica, sem a contaminação cruzada: **Q43**,
**Q44** (a maior perda de texto contínuo encontrada: 3 parágrafos + 2
equações), **Q45**, **Q48**, **Q20** (perda da segunda asserção/PORQUE).

### Outros

- **Q26**: perde sua própria imagem (5 cartas de baralho) — está presente
  no corpus, mas anexada a Q25 em vez de Q26 (ver Classe B).
- **Q27**: pseudocódigo preservado por completo mas achatado em uma frase
  contínua (fonte não-monoespaçada na fonte, mesma classe já aceita para
  Q46/D4 — severidade baixa, não é perda de conteúdo).
- **D3** (padrão de resposta): setas de atribuição `←` corrompidas para o
  glifo "Å" em todo o pseudocódigo (bug de mapeamento de glifo, distinto
  da Classe A embora relacionado).
- **D5** (padrão de resposta): as 3 tabelas de largura de bits (rótulo/
  linha/palavra) ausentes por completo — os números exatos que definem
  cada esquema de mapeamento, conteúdo central para a correção.

Nenhuma correção geral foi tentada para as Classes A/B nesta fase — ver
Seção H para o porquê (risco de regressão já demonstrado 3× nesta sessão
para mudanças mais estreitas na mesma maquinaria compartilhada) e
`docs/decisions.md`, ADR 28, para a análise completa.

## G. Q22 — aprofundamento

Ver Seção E.1 acima e `docs/decisions.md` ADR 21 para a investigação
completa (duas correções gerais tentadas e rejeitadas, override Nível 3
final). Nada mudou sobre Q22 nesta fase além da confirmação de que
`extraction_status=verified` permanece correto após todas as mudanças de
código subsequentes (reverificado: `git diff` do arquivo Q22 desde o
último `extract` mostra apenas re-render idêntico de `table-01.png`, sem
mudança de conteúdo).

## H. Inventário de overrides (Nível 3)

`data/manifests/layout-overrides.yaml`, 16 entradas ativas, todas
travadas ao SHA-256 exato do PDF-fonte (`eb3b497f...`):

| Regra | Questão | Qtd | Motivo (resumo) |
|---|---|---|---|
| `exclude_from_orphan_marker_merge` | Q22 | 1 | Cabeçalho de tabela confundido com marcador de alternativa |
| `suppress_visual_region` | Q13 | 1 | Região espúria de símbolos matemáticos minúsculos |
| `protect_from_label_absorption` | Q23 | 3 | Fragmentos de texto pós-símbolo inline |
| `exclude_from_region_candidates` | Q23 | 3 | As 3 imagens-símbolo inline em si |
| `protect_from_label_absorption` | Q6 | 5 | Legenda + 2 linhas finais do enunciado + 2 continuações de alternativa (cadeia de absorção, ver ADR 26) |

O override `force_single_column_page` (Q1, ADR 24) foi **removido** nesta
fase após ser superado por um fix geral (Nível 1) — ver Seção seguinte.

## I. Auditoria visual de D1-D5 (padrão de resposta)

Todos os 5 padrões de resposta (`3_padrao.pdf`, 5 páginas) foram
comparados integralmente ao campo `answer_standard.text` de cada questão
D1-D5:

- **D1**: passed — 10 vantagens da EaD, texto verbatim.
- **D2**: passed — 3 critérios de correção, texto verbatim (marcadores
  "•" preservados inline).
- **D3**: **failed** — setas de atribuição corrompidas (`←` → "Å") em
  todo o pseudocódigo iterativo e recursivo; formatação de código também
  achatada (mesma classe de baixa severidade do Q27, mas aqui composta
  com a corrupção de glifo, que é severa).
- **D4**: passed — pseudocódigo `CriaABP` completo incluindo marcadores
  de indentação `|`, ambas as notas "Qualquer notação..." presentes;
  nota cosmética de formatação achatada (mesma classe do Q27, sem perda
  de conteúdo).
- **D5**: **failed** — as 3 tabelas de largura de bits (mapeamento
  direto/totalmente associativo/associativo por conjunto) ausentes por
  completo; todo o texto explicativo ao redor está correto.

Nenhuma referência visual não endereçada ("conforme abaixo", "figura",
"tabela") foi encontrada além dessas duas.

## J. Provas virtuais (4 conjuntos)

Materializadas e validadas via `materialize_virtual_exam_set` +
`validate_virtual_exam_set` contra o corpus atual em
`data/questions/2011/all-computing/` (55 questões carregadas):

```
ciencia-da-computacao-bacharelado   obj=35 disc=5 total=40 issues=[]
ciencia-da-computacao-licenciatura  obj=35 disc=5 total=40 issues=[]
engenharia-da-computacao            obj=35 disc=5 total=40 issues=[]
sistemas-de-informacao              obj=35 disc=5 total=40 issues=[]
```

Zero problemas: sem contagem errada, sem duplicata, sem ordem incorreta,
sem contaminação cruzada entre cursos (`cross_course_contamination`
check). `all-computing` continua a nunca ser combinado com um código de
curso explícito (validador do Fase 0, inalterado).

## K. Gold 2011 e readiness

`enade build-gold --year 2011 --course all-computing --maturity provisional`,
com 13 `--structural-blocker` explícitos (um por classe/grupo de defeito
disclosed na Seção F). Maturidade: **`provisional`** — correta e
obrigatória, não alterada para `validated`.

`enade assess-readiness --year 2011 --course all-computing`:

```
assess-readiness: NOT_READY
  36/55 verified, 19 needs_review, gold maturity=provisional
  visual audit: 37 passed, 18 failed, 0 not_performed (fully_covered=True)
  32 blocker(s):
    - 13× recorded_structural_blocker (os 13 grupos de defeito documentados)
    - 19× question_not_verified (18 questões `failed` no audit visual +
      Q34, cujo aviso estrutural pré-existente - "figura após corte de
      alternativas" - é um falso positivo já disclosed, mas mantido
      needs_review por conservadorismo, não por engano)
```

Nenhum bloqueador é espúrio; todos rastreiam a um defeito real e
documentado, ou a uma política deliberadamente conservadora. O gate
nunca foi contornado ou relaxado para "passar" — sua saída é exatamente
o estado real do corpus.

## L. Proteção do 2021 — antes e depois

**Antes desta fase** (linha de base confirmada no início): `verify-gold
--year 2021 --course ciencia-da-computacao-bacharelado` → OK, 40/40,
`maturity=validated`.

**Depois de cada mudança de código nesta fase** (Y-overlap em
`detect_column_margins`; 5 overrides de `layout-overrides.yaml` para Q6;
redução de `x_tolerance` em `assembler.py`): reextração completa de 2021
para os 3 cursos localmente disponíveis
(`ciencia-da-computacao-bacharelado`, `ciencia-da-computacao-licenciatura`,
`sistemas-de-informacao`) seguida de `git status`/`verify-gold`. Resultado
em **todas** as verificações: zero diff para `ciencia-da-computacao-bacharelado`
(o único curso 2021 com gold travado em git) — byte-idêntico. Os cursos L
e S não têm gold travado nem estavam rastreados em git antes desta sessão
(estado pré-existente, não introduzido aqui); comparados apenas via
"Structure matches what was previously observed for this booklet" do
próprio extrator, sem diff disponível por falta de baseline commitada.

**Verificação final** (após todas as mudanças, nesta ordem): `verify-gold`
→ OK, 40/40, byte-idêntico. **2021 nunca regrediu, nenhuma vez, em nenhum
passo desta fase.**

## M. Testes

Suíte completa: **354 testes, 0 falhas** (era 352 no início desta
sessão; net +2 arquivos de teste totalmente novos herdados da Fase 2A/
início da 2B — `test_extraction_visual_audit.py`,
`test_layout_overrides.py` — mais os testes abaixo, adicionados nesta
sessão):

- `test_extraction_layout.py`: +2 testes para o fix geral de
  Y-overlap em `detect_column_margins` (rejeita ranges não-sobrepostos;
  aceita ranges genuinamente sobrepostos).
- `test_extraction_assembler.py`: +1 teste de integração (PDF sintético
  via pymupdf) para a redução de `x_tolerance` — verificado manualmente
  que falha com o valor antigo (15pt) e passa com o novo (5pt), provando
  que o teste de fato pega a regressão.
- `test_extraction_figures.py`: +1 teste modelando a cadeia de absorção
  de duas candidatas independentes de Q6 (bloquear uma não impede a
  outra de sozinha causar a mesma absorção).

Cobertura de auditoria: `assess_visual_audit_coverage` já tinha 7 testes
próprios (Fase 2B, seção anterior desta mesma fase) — não modificados,
ainda todos passando contra o `visual-audit-2011-computing.json`
totalmente reescrito.

## N. Quality gates (ambos os anos)

```
validate-manifest --corpus-root data/raw/geacc-enade   → OK (0 warnings)
audit-extraction --questions-dir .../2011/all-computing → 55/55 OK
audit-extraction --questions-dir .../2021/.../bacharelado → 40/40 OK
validate-schema                                          → 13/13 fixtures OK
mypy src/                                                 → Success, no issues (50 files)
ruff format . / ruff check .                              → All checks passed
pytest -q                                                  → 354 passed
verify-gold --year 2021 --course bacharelado              → OK, 40/40
assess-readiness --year 2011 --course all-computing       → NOT_READY (32 disclosed blockers)
```

## O. Reprodutibilidade

Duas extrações limpas e independentes de `data/questions/2011/all-computing`
(reexecutando `enade extract --year 2011 --course all-computing` duas
vezes em sequência, com um snapshot completo tirado após cada uma):
`files written: 0, unchanged: 55` em ambas as execuções; `diff -rq` entre
os dois snapshots: **zero diferenças**. O pipeline é determinístico.

## P. Performance

Extração completa do caderno 2011 unificado (32 páginas, 55 questões, ~24
assets renderizados): **~10-13s** por execução completa (medido
repetidamente ao longo desta fase, variando com carga do disco/cache do
PyMuPDF). Nenhuma mudança desta fase alterou a ordem de complexidade de
nenhum algoritmo (todos os fixes são checagens O(1)/O(n) adicionais sobre
estruturas já percorridas).

## Q. Arquivos alterados/criados nesta fase

**Código-fonte**: `src/enade/extraction/layout.py` (Y-overlap geral),
`src/enade/extraction/assembler.py` (x_tolerance geral),
`src/enade/extraction/figures.py`/`layout_overrides.py` (overrides Q6,
já existentes de antes desta sub-fase para Q13/Q22/Q23),
`data/manifests/layout-overrides.yaml` (5 novas entradas Q6, 1 removida
Q1).

**Dados/manifests**: `data/manifests/visual-audit-2011-computing.json`
(reescrito por completo, 9→55 entradas), `data/manifests/gold-2011-computing.json`
(reconstruído, `provisional`, 13 structural blockers), 47 arquivos
`.md`/assets em `data/questions/2011/all-computing/` regenerados (conteúdo
real mudou em Q1, Q2, Q6, Q7, Q15, Q16, D4; demais mudanças são apenas
metadados de frontmatter — `extraction_status`/`visual_validation` —
promovidos pelo próprio extrator ao ler o audit atualizado).

**Documentação**: `docs/decisions.md` (+4 ADRs: 26, 27, 28, e a nota de
supersedência no ADR 24), `docs/phase-2b-report.md` (este arquivo).

**Testes**: 3 arquivos estendidos (ver Seção M).

Nenhum arquivo do 2021 foi escrito por esta fase (apenas lido/reextraído
para verificação, com resultado sempre idêntico ao já commitado).

## R. Estado git final

Branch `feat/enade-2011-unified-extraction`, ainda em `HEAD=4b22323`
(nenhum commit criado nesta fase). `git status --short`: 94 entradas (72
modificadas, 10 deletadas — assets espúrios removidos por correções reais
— , 12 novas). `master`/`origin/master` intocados. Nada foi commitado,
staged intencionalmente, ou empurrado — todas as mudanças permanecem
apenas no working tree, exatamente como a não-autorização desta fase
exige.

## S. Recomendação

1. **Não promover** o gold 2011 para `validated` até que pelo menos as
   Classes A e B (Seção F) recebam investigação dedicada — cada uma afeta
   múltiplas questões e provavelmente compartilha uma causa raiz mais
   profunda ainda não totalmente isolada (para a Classe B, uma correção
   candidata é desacoplar a largura do crop renderizado do bbox lógico
   usado para exclusão de texto, ou tornar `_render_bbox` ciente de
   colunas; para a Classe A, um fallback visual obrigatório por segmento
   de alternativa não-extraível é a rota mais segura, análoga ao que já
   existe para tabelas).
2. **Não** iniciar o teste de layout legado (`READY_FOR_LEGACY_LAYOUT_TEST`)
   com o corpus 2011 atual como base de comparação — 33% das questões
   têm um defeito de fidelidade real e não-disclosed-apenas-em-prosa; um
   terceiro layout tornaria a already-taxada maquinaria de absorção/
   coluna ainda mais provável de regredir sem cobertura de teste
   dedicada para as Classes A/B.
3. A arquitetura de overrides Nível 3 (`layout_overrides.py`,
   hash-and-bbox-locked, com 5 tipos de regra) provou-se sólida e
   reutilizável ao longo de duas fases — deve continuar sendo o
   mecanismo padrão para exceções genuinamente documento-específicas,
   com fixes gerais (Nível 1) reservados a padrões confirmados em 2+
   ocorrências independentes (como aconteceu organicamente com Q1→D4 e
   Q16→Q7→Q15 nesta fase).
4. Antes de investir em correção das Classes A/B, vale medir o quanto
   cada uma se repete nos anos/cadernos ainda não tocados (2005, 2008) —
   se for um padrão geral do formato ENADE (não específico de 2011), a
   correção geral compensa o investimento; se for um artefato só deste
   PDF específico, overrides seguem sendo a rota mais barata.
