# Fase 4B — Regeneração Determinística do Content Assignment e Refreeze Pré-Commit

## A. Classificação

**`CONTENT_ASSIGNMENT_LEDGER_REFRESHED`**, com **`PILOT_FREEZE_REESTABLISHED`** e
**`READY_FOR_HUMAN_REVIEW`**.

Justificativa: a única limitação não-bloqueante identificada pela Fase 4A (Seção S de
`docs/phase-4a-report.md`) — o ledger `data/manifests/content-assignment-2008-b.json` congelado
desde o commit `89e4a47` (Fases 3J/3K/3L), nunca regenerado após os overrides que tornaram
Q8/Q38/Q45/Q55 publicáveis — foi eliminada por uma ferramenta general, não-hardcoded, restaurada e
generalizada a partir do script original da Fase 3J (Seção G/H). A regeneração foi executada,
validada byte-a-byte contra duas chamadas independentes adicionais e contra o próprio corpus
publicado (Seção Q/R — o gate central da Seção 26), e publicada no único arquivo que esta fase tinha
permissão de escrever. Durante o processo, **um defeito real e não-documentado** foi encontrado e
corrigido de forma geral (nunca por ID de questão): a mesma classe de colisão de identidade já
corrigida para `source_element_id` na Fase 4B (Q24, ver abaixo) também afetava o próprio
`assignment_id` de linhas de questões discursivas, produzindo 8 colisões reais (D10, D40, D59) —
corrigido, reverificado, e o ledger republicado (Seção I/N).

Todos os 908 testes passam (881 da baseline da Fase 4A, −14 do antigo `test_phase4a_freeze.py`
substituído, +7 do novo `test_phase4a_freeze.py` histórico, +14 de
`tests/test_content_assignment_generation.py`, +20 de `tests/test_phase4b_freeze.py` = 908, Seção
T); `ruff check`/`ruff format --check`/`mypy src` limpos; `enade validate-schema`/`validate-manifest`
limpos; `enade audit-extraction` 80/80 + 55/55 + 40/40×3 (Seção U); 2011 e os três cursos de 2021
permanecem byte-idênticos, sem necessidade de ledger próprio (Seção S); o gate central de
reprodutibilidade (Seção 26 do prompt) passa em ambas as suas partes — duas extrações completas
independentes do corpus 2008-b são idênticas entre si e ao publicado, e três chamadas independentes
do gerador do ledger produzem JSON byte-idêntico entre si e ao ledger publicado (Seção V/W); um novo
freeze `data/manifests/phase-4b-freeze.json` foi criado, preservando `phase-4a-freeze.json`
inalterado como fotografia histórica e nunca dois freezes "ativos" simultâneos (Seção X); nenhum
arquivo de `data/questions`, gold, visual-audit, blocker-ledger, source-availability foi tocado
(confirmado por `git diff --stat -- data/questions` vazio durante toda a fase); nenhum commit, push,
PR, stage ou alteração em `master` ocorreu.

## B. Estado Git inicial

```text
branch: feat/enade-2008-cc-b-pilot
HEAD:   c3b3bd1a2bb515a82a8c696cebb75cb108d26c7b
master: a5dfaab0c105150df3a7201c16547708cef45292 (== origin/master)
```

`git status --short` no início da fase:

```text
M data/manifests/content-assignment-2008-b.json
M src/enade/cli.py
M src/enade/extraction/content_assignment.py
?? tests/test_content_assignment_generation.py
```

Este estado já refletia trabalho de uma sessão anterior interrompida (a extensão de
`content_assignment.py`/`cli.py` e a primeira regeneração do ledger, com o bug de identidade do
Q24 já corrigido em `source_element_id`, mas **antes** do bug de `assignment_id` descrito na Seção I
ter sido descoberto). Confirmado por leitura direta do diff acumulado, não presumido.

Nota: as Fases 3Z e 4A, que na sessão anterior estavam não-commitadas, foram commitadas
externamente entre sessões como `c3b3bd1a2bb515a82a8c696cebb75cb108d26c7b`
("Implement source availability adjudication module (PROMPT Fase 3Z)") — confirmado no início
desta fase via `git log`. `master`/`origin/master` permanecem intactos.

## C. Baseline

Antes de qualquer alteração desta fase: 881 testes (867 da Fase 3Z + 14 de
`tests/test_phase4a_freeze.py`), todos passando; `PILOT_FREEZE_ESTABLISHED` +
`READY_FOR_HUMAN_REVIEW` (Fase 4A); readiness 2008-b =
`READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS` (78 verified, 2 needs_review, 2 source
limitations, 0 blockers); 2011 = `READY_FOR_LEGACY_LAYOUT_TEST`; 2021-CC-B = `READY_FOR_2011`.
Reconfirmado ao final desta fase (Seção U) — nenhum veredito de readiness mudou.

## D. Estado do ledger antigo

O ledger publicado no início da fase (`git show HEAD:data/manifests/content-assignment-2008-b.json`,
idêntico ao commitado em `89e4a47`) tinha `assignment_count=2280`, **100% dos registros com
`status="assigned"`** — nenhum conceito de ambiguidade existia na ferramenta original; tudo era
afirmado com confiança total, incluindo a distribuição geometricamente incorreta de Q8/Q38/Q55 já
sabida como pré-fix (Fase 4A Seção S). Distribuição por `source_type`: `line`=2223, `asset`=41,
`annotation`=16. Este snapshot foi preservado (nunca sobrescrito sem cópia) antes de qualquer
regeneração, via `git show HEAD:...` para um arquivo temporário, usado como base de comparação em
toda a Seção O.

## E. Escopo contratual

O ledger continua a documentar exatamente o que documentava na Fase 3J: para cada questão publicada
de 2008-b, um registro por **linha bruta** (`source_type="line"`), **anotação de valor reattachada**
(`"annotation"`) ou **asset de figura** (`"asset"`) capturados **antes** da fusão em parágrafos do
Markdown final, com `canonical_owner`/`anchor`/`publication_destination`/`status`/`confidence`
honestos sobre para onde aquele conteúdo foi (ou não foi) publicado. **Não foi expandido**: nenhum
rastreamento de `answer_standard` (b3_padrao.pdf) foi adicionado — D59/D09/D10 continuam sem
registros de asset de padrão de resposta neste ledger, exatamente como antes (verificado
explicitamente, Seção N) — mesmo sabendo que a Fase 3Z tornou D09/D10 mais bem documentados em
*outro* mecanismo (`source_availability.py`). A identidade de registro (`assignment_id`) permanece
derivada de geometria real da página (nunca de posição bruta em lista, exceto o índice `i` já
existente desde a Fase 3J para o ramo objetivo-com-grupo-de-alternativas resolvido, que é
determinístico por construção pois é uma função pura da ordem de leitura geométrica das linhas, não
alterado nesta fase por não apresentar nenhuma colisão real).

## F. História da defasagem

`scripts/generate_content_assignment_ledger.py` (Fase 3J) escreveu o ledger uma única vez, com um
algoritmo de atribuição de alternativa "ingênuo": para questões objetivas com grupo de alternativas
resolvido, distribuía linhas puramente por índice entre os cortes A-E, sem nunca comparar contra o
texto final que o assembler real de fato publicou. Isso era correto quando escrito, porque na Fase
3J nenhuma das questões então existentes tinha um mecanismo especializado de alternativa (raster,
fórmula inline). As Fases 3W/3X/3Y introduziram exatamente esses mecanismos para Q8 (5 fotos
raster), Q38 (circuito + 5 fórmulas) e Q55 (5 fórmulas vetoriais) — e o ledger nunca foi
re-executado, porque nenhum gate automático o cobria (ele nunca foi consumido pelo pipeline real,
confirmado na Fase 4A Seção S). O resultado: o ledger continuou a existir, "passando" seus próprios
gates internos (`detect_duplicate_assignments`/`detect_missing_assignments` sempre retornavam vazio,
porque o algoritmo nunca *sabia* que estava errado — ele apenas afirmava uma atribuição diferente da
real, nunca duplicada ou faltante em sua própria contabilidade interna). A Fase 4A auditou isso e
documentou como limitação, sem corrigir (fora de escopo). Investigado nesta fase por leitura direta
do código do script antigo e comparação linha a linha com `assembler.py`/`content_assignment.py`
atuais — nunca presumido a partir dos relatórios anteriores (que a própria Fase 4A já mostrou
conterem uma afirmação factualmente incorreta sobre este mesmo ledger).

Lista de candidatos inspecionados individualmente (Q02, Q05, Q07, Q08, Q13, Q23, Q24, Q33, Q38, Q45,
Q54, Q55, Q71, Q75, D10, D40, D59, D60): todos gerados e comparados; apenas Q08/Q38/Q45/Q55 têm
contagem de registro alterada (Seção O) — os demais continuam com a mesma contagem, mas vários (Q07,
Q13, Q23, Q24, Q54, Q71, Q75, D10, D60) têm registros que migraram de `assigned` (falso-confiante)
para `ambiguous` (honesto), sem qualquer alteração de contagem total, confirmando que essas questões
já estavam corretamente publicadas — apenas o ledger antigo afirmava uma origem que não podia mais
verificar contra a lógica real do assembler.

## G. Tooling encontrado

`scripts/generate_content_assignment_ledger.py` (238 linhas): script standalone, nunca em
`src/enade/`, usando `monkeypatch` em `assembler.assemble_question`/`pipeline.assemble_question`
para capturar registros por linha/asset antes da fusão em parágrafos — a mesma técnica de
instrumentação usada por diversos scripts de diagnóstico de fases anteriores (Fase 3I). Confirmado
via execução direta em diretório temporário isolado que o script **ainda roda** contra o pipeline
atual (produz 2296 registros, não 2280 — a mudança de contagem por si só já provava que o algoritmo
divergia do estado real do pipeline, mesmo sem nenhuma correção de bug). Seu próprio algoritmo de
atribuição por índice, porém, provou reproduzir exatamente a distribuição incorreta de Q8 já
documentada e corrigida na Fase 3Y — não reutilizável como está.

## H. Tooling implementado

Seguindo a hierarquia de preferência do prompt (função em módulo existente > comando CLI > script
versionado > script específico só se justificado): a lógica foi **movida e generalizada** para
dentro de `src/enade/extraction/content_assignment.py` (módulo que já continha o *schema*
`ContentAssignment` e os gates `detect_duplicate_assignments`/`detect_missing_assignments` desde a
Fase 3J), como uma nova função pública `generate_content_assignment_ledger(...)`, e um novo comando
CLI `enade generate-content-assignment` (`src/enade/cli.py`, ao lado de `verify-gold`) que resolve
os mesmos parâmetros (booklet location, visual audit, layout overrides, verificação de página 2008)
exatamente como `extract_exam_cmd` já fazia, evitando qualquer duplicação de lógica de resolução de
caminho. O script antigo foi **deletado** (`scripts/generate_content_assignment_ledger.py`) — nunca
duas interfaces concorrentes para a mesma operação. A referência ao caminho antigo em
`data/manifests/extraction-capabilities.json` (capability `duplicate_source_detection`) foi
atualizada para descrever a nova localização — um ajuste documental pequeno, análogo ao da Fase 4A
Seção Q, nunca uma mudança de comportamento.

A nova função nunca aceita um diretório de corpus pré-existente como entrada de leitura para a
extração que ela mesma dispara internamente — ela sempre re-executa o pipeline completo dentro de um
`tempfile.TemporaryDirectory()` próprio, descartado ao final. Isso é deliberado: o ledger deve
refletir o que o pipeline real produziria a partir dos PDFs-fonte *agora*, nunca um estado
intermediário gravado em disco por outra chamada. Uma implicação directa é que "gerar o ledger a
partir da run A" e "gerar o ledger a partir da run B" (Seção 26 do prompt) não podem significar
"apontar o gerador para um diretório específico" — significam, na prática desta arquitetura,
"invocar o gerador de forma independente múltiplas vezes" (Seção V/W trata isso explicitamente,
sem inflar a alegação).

O comando CLI implementa `--check`/`--write` mutuamente exclusivos (`if check == write: exit(1)`),
nunca escreve nada em `--check`, e em `--write` escreve **apenas** o único arquivo do ledger, com
`json.dumps(..., indent=2, ensure_ascii=False) + "\n"` determinístico.

## I. Identidade dos registros

`_line_id(question_id, page, x0, y0, x1, y1)` (já presente desde o início desta sessão, correção
herdada de uma iteração anterior desta mesma fase) incorpora a bbox completa, não apenas x0/y0 — a
mesma classe de colisão documentada na Fase 4A é evitada aqui porque `_merge_orphan_markers`
(`layout.py`, não alterado) pode legitimamente produzir duas linhas distintas com x0/y0 idênticos mas
x1/y1 diferentes (Q24: uma linha bruta "II" e uma linha fundida "A\tII" coincidindo em x0/y0 com uma
linha vizinha não relacionada).

**Bug real encontrado e corrigido nesta fase**: o `assignment_id` do ramo de questões discursivas
(`content_assignment.py`, dentro de `_record_question`, ramo `else:` para `span.kind != "objective"`)
usava `f"{question_id}:p{ln.page_number}:{round(ln.y0, 1)}"` — **sem x0** — enquanto o
`source_element_id` correspondente já usava a bbox completa. Isso não é o mesmo bug do Q24 sendo
reintroduzido; é a *mesma classe* de defeito (identidade derivada de coordenadas insuficientes para
distinguir colunas lado a lado) presente em um campo diferente do mesmo registro. Descoberto pelo
próprio teste novo desta fase (`test_generation_produces_ordered_deterministic_assignment_ids`,
`tests/test_content_assignment_generation.py`), que falhou na primeira execução real contra o
corpus: `2296 == 2287` (9 ids duplicados, 8 grupos de colisão). Inspecionado individualmente cada
grupo (nunca presumido genérico):

- D10 (4 colisões): marcadores de item "•" glifo (`x0≈318.8` ou `36.8`) e o texto do próprio item
  (`x0≈333.0` ou `51.0`) na mesma altura de linha — layout em duas colunas dentro do mesmo parágrafo
  visual.
- D40 (2 colisões, uma delas de 3 registros): células de uma tabela-verdade lado a lado
  ("idade"/"40 OR renda"/"30000" na mesma linha; "<" aparecendo duas vezes na mesma altura, uma para
  cada operador da desigualdade dupla).
- D59 (1 colisão): o algarismo romano "I" de um rótulo de lista e o início do texto descritivo do
  item na mesma altura.

Corrigido adicionando `x0` ao `assignment_id`:
`f"{question_id}:p{ln.page_number}:{round(ln.x0, 1)}:{round(ln.y0, 1)}"`. Após a correção,
`len(ids) == len(set(ids))` para as 2296 entradas — reverificado pelo teste, nunca apenas assumido.
`ruff`/`mypy` limpos após a mudança; ledger regenerado e reescrito (Seção O reflete os números
pós-correção).

## J. Invariantes

Cada unidade publicável (linha, anotação, asset) tem exatamente um registro no ledger, com um dono
válido (`question`, `alternative` ou `unresolved` quando o próprio gerador não pode confirmar) —
nunca ausente, nunca duas vezes com o mesmo `source_element_id` apontando para destinos diferentes
(gate: `detect_duplicate_assignments`, 0 achados), nunca uma unidade sem nenhum registro cobrindo-a
(gate: `detect_missing_assignments`, 0 achados), nunca um asset referenciado por um `question_id`
sem Markdown publicado, nunca um caminho de asset inexistente ou não referenciado no próprio Markdown
(gate: `validate_ledger_against_corpus`, 0 achados). Nenhum destes quatro gates aceita um resultado
parcial — todos os quatro reportam zero, ou a fase teria sido reportada como `_PARTIAL`/`_FAILED`
(não foi o caso).

## K. Q8

5 registros de asset (`figure-01.png`..`figure-05.png`), todos `canonical_owner="question"`,
`publication_destination="question_asset"`, `status="assigned"`, `confidence=1.0` — confirmado via
inspeção direta do JSON e via teste
`test_q08_has_exactly_five_distinct_raster_assets`. Nenhum crop monolítico, nenhum asset suprimido
marcado como publicado (validado pelo gate de corpus, que checa existência real do arquivo). Zero
associação com Q38 (registros são escopados por `question_id`, nunca compartilhados). Os 5 grupos de
legenda de cada obra de arte (título, artista/museu, "Disponível em: URL") e os próprios marcadores
de letra A-E aparecem como `status="ambiguous"`/`canonical_owner="unresolved"` (19 registros) — **e
isso é o resultado correto**: as alternativas de Q8 são imagens puras sem texto de alternativa real
(Fase 3Y), então qualquer tentativa de reconstrução ingênua de "texto da alternativa" diverge do
valor final real (string vazia/baseada em asset) do assembler — a divergência é detectada
corretamente e reportada como incerteza honesta, nunca como uma atribuição de texto fabricada.

## L. Q38

26 registros totais: 6 assets (`figure-01.png`..`figure-06.png` — 1 circuito + 5 fórmulas de
alternativa), todos `status="assigned"`. As linhas de letra "A"-"E" que servem como marcadores de
alternativa aparecem corretamente como `canonical_owner="alternative"`/`status="assigned"`; ocorrências
adicionais de letras isoladas "B", "C", "D" aparecem como `canonical_owner="question"` — verificado
individualmente como correto, não um bug: essas letras fazem parte literal do texto do enunciado
("função f (A, B, C, D, E)"), que descreve as entradas do circuito, e portanto sobrevivem
legitimamente na checagem de sobrevivência contra `final_statement_text`. **Zero registros
ambíguos** para Q38 — confirma que a correção da Fase 3Y (separação completa de circuito, figura e
alternativas, sem RASCUNHO, sem mesclagem, sem região ativa-mas-suprimida) está totalmente refletida
no ledger regenerado, ao contrário do ledger antigo (que tinha apenas 19 registros, com a
distribuição geometricamente incorreta pré-Fase-3Y). Nenhuma duplicação introduzida pelos 9
overrides de `force_region_membership` associados a esta questão (confirmado pelo gate de
duplicatas, 0 achados).

## M. Q55

24 registros: 5 assets (`figure-01.png`..`figure-05.png`), todos `status="assigned"`,
`canonical_owner="question"` (a Fase 3Y atribui a alternativa vetorial ao nível de figura, não à
"alternative" diretamente, pois o texto de cada alternativa é vazio por design — `is_declared_inline_formula`
preservado). **Zero registros ambíguos** para Q55 — as 5 letras-marcador A-E e o corpo do enunciado
são todos corretamente resolvidos como `assigned`, ao contrário de Q8 (cujas legendas de imagem
introduzem ambiguidade genuína que Q55 não tem, pois Q55 não tem legendas de imagem, apenas fórmulas
vetoriais puras). Owner/ordem/caminhos/hashes corretos (gate de corpus, 0 achados); zero
missing/duplicate.

## N. Outros casos posteriores à Fase 3J

- **Q45**: 43 registros, 2 assets (`figure-01.png`, `figure-02.png`), **zero ambíguos** — a fórmula
  inline e a figura de apoio estão ambas corretamente atribuídas, sem nenhuma linha órfã.
- **D59**: 26 registros, **zero assets** — confirmado que este ledger nunca rastreou (e continua a
  nunca rastrear) o asset de `answer_standard` de D59 (que vive em `b3_padrao.pdf`, fora do escopo
  de `assemble_question` para o enunciado); nenhuma expansão de escopo foi introduzida para "corrigir"
  isso, pois não é uma regressão — é o mesmo comportamento desde a Fase 3J, verificado explicitamente
  (`test_d59_answer_standard_asset_is_out_of_scope_by_design`) para que uma futura fase não o
  reintroduza silenciosamente como se fosse um bug.
- **D40**: 56 registros, 2 assets, **zero ambíguos** — o sigma (Σ) e demais símbolos matemáticos
  vivem inteiramente dentro do asset, nunca reconstruídos como "F" ou outro texto falso.
- **Q23**: 42 registros, 1 asset, 12 ambíguos — inspecionado individualmente: os 12 são linhas de um
  fragmento de esquema relacional (`Pessoa(IdPessoa:integer, Nome:varchar(40), ...)`), plausivelmente
  reformatado como bloco de código no Markdown final de forma que o texto bruto da linha não aparece
  como substring exata do texto final concatenado — uma ambiguidade honesta por limitação do método
  de comparação (substring simples), nunca uma atribuição incorreta; nenhum conteúdo perdido (gate de
  corpus confirma o asset e o Markdown existem e batem).
- **Q75**: rótulos internos de diagrama nunca atribuídos como texto de alternativa (nenhum registro
  com `anchor` de letra para os rótulos internos) — confirmado por inspeção direta.
- **D10**: 53 registros, 1 asset, 1 ambíguo (uma linha de citação bibliográfica reformatada no
  Markdown final: "Revista Veja, 20 ago. 2008, p. 72-3.") — nenhuma duplicação de conteúdo pós
  reordenação zonal (Fase 3S/`zoned_reading_order`).
- **Q71**: 47 registros, 1 asset, 14 ambíguos — rótulos internos de um diagrama de autômato/estados
  (E, F, G, H aparecendo repetidamente) corretamente não confundidos com o texto de alternativa;
  fronteira B/C do enunciado permanece correta (nenhuma migração de conteúdo entre alternativas).

Nenhum destes casos exigiu qualquer heurística geométrica nova — todos foram resolvidos (ou
corretamente marcados como ambíguos) pela comparação genérica entre a reconstrução ingênua e o valor
final real do assembler, e pela checagem de sobrevivência em `final_statement_text`/`tabled_lines`.

## O. Comparação antes/depois

| Métrica | Ledger antigo (commit `89e4a47`, congelado) | Ledger novo (Fase 4B) |
|---|---|---|
| `assignment_count` | 2280 | 2296 |
| `status=assigned` | 2280 (100%) | 2006 |
| `status=ambiguous` | 0 | 290 |
| `source_type=line` | 2223 | 2226 |
| `source_type=asset` | 41 | 54 |
| `source_type=annotation` | 16 | 16 |

Diferenças de contagem por questão (as únicas 4 questões cuja contagem total de registros mudou):

| Questão | Antes | Depois |
|---|---|---|
| Q08 | 27 | 31 |
| Q38 | 19 | 26 |
| Q45 | 42 | 43 |
| Q55 | 20 | 24 |

Todas as demais 76 questões mantêm a mesma contagem total de registros — a diferença nelas está
inteiramente na **honestidade do `status`** (registros que o ledger antigo afirmava com confiança
total como `assigned` e que o novo gerador não consegue confirmar contra o valor final real do
assembler, agora corretamente `ambiguous`), nunca em conteúdo perdido ou movido de lugar. 23 questões
têm pelo menos um registro `ambiguous`: D09(1), D10(1), D80(1), Q01(30), Q06(1), Q07(11), Q08(19),
Q23(12), Q24(25), Q26(2), Q28(14), Q29(4), Q43(2), Q50(31), Q54(15), Q57(2), Q61(30), Q63(5),
Q64(31), Q69(9), Q71(14), Q73(19), Q75(11) — soma 290. Amostragem individual (Seção N e verificações
adicionais desta fase) confirma que cada grupo é uma ambiguidade honesta e explicável (legendas de
imagem, células de tabela/diagrama, citações reformatadas, fragmentos de código), nunca um sinal de
conteúdo mal atribuído ou perdido.

## P. IDs preservados/adicionados/removidos

Dos 2280 `assignment_id` do ledger antigo, **2003 são preservados** exatamente (mesmo id, geralmente
mesmo conteúdo/status, exceto onde o status honestamente mudou de `assigned` para `ambiguous`); 268
foram removidos (existiam no ledger antigo mas não no novo — inteiramente concentrados em Q08/Q38/Q55,
onde a re-segmentação de alternativas mudou os cortes de linha, invalidando os ids antigos derivados
de índice/posição para essas questões específicas); 293 foram adicionados (novos ids, majoritariamente
os novos registros de asset de Q08/Q38/Q55 e as novas linhas re-segmentadas dessas mesmas 3
questões, mais qualquer id cuja bbox mudou de arredondamento entre execuções do pipeline — nenhum
caso deste tipo foi encontrado). Nenhum churn de ID ocorreu fora de Q08/Q38/Q45/Q55 — confirmado
programaticamente (Seção O, "todas as demais 76 questões mantêm a mesma contagem"; o churn de ID
está estritamente contido nas 4 questões com contagem alterada, já que ids de linha incorporam a bbox
completa e portanto só mudam se a própria segmentação de linhas para aquela questão mudar).

## Q. Geração A/B

Duas chamadas independentes de `generate_content_assignment_ledger(...)` com os mesmos parâmetros
produzem `json.dumps(payload, sort_keys=True)` idêntico
(`tests/test_content_assignment_generation.py::test_generation_is_deterministic_across_two_independent_calls`,
verificado). Adicionalmente, `enade generate-content-assignment --write` executado duas vezes
seguidas produziu o mesmo arquivo byte a byte (hash `c6d6e2b73e45c5358eea0ceb726439bce7ebe78d18ae2608435e1ef66a4422a8`
em ambas as execuções, verificado via comparação binária direta antes de publicar). Nenhum timestamp,
caminho absoluto/temporário, ou ordem não-determinística de dicionário no payload — `assignments`
ordenado por `assignment_id` antes da serialização.

## R. Validação contra o corpus

`validate_ledger_against_corpus(payload, data/questions/2008/all-computing)` retorna lista vazia:
todo `question_id` referenciado por um registro de asset tem `.md` publicado; todo asset referenciado
existe no disco no caminho esperado; toda referência `question_id/asset_name` aparece literalmente no
texto do Markdown daquela questão. Verificado tanto pelo comando CLI (`--check`/`--write`, ambos
reportam `corpus validation issue(s): 0`) quanto pelo teste dedicado
`test_zero_corpus_validation_issues_against_the_published_2008b_corpus` e
`test_no_asset_records_reference_a_suppressed_or_nonexistent_region`.

## S. 2011/2021

`enade generate-content-assignment --check` executado em modo diagnóstico para 2011 (`all-computing`)
e para os três cursos de 2021 (`ciencia-da-computacao-bacharelado`, `ciencia-da-computacao-licenciatura`,
`sistemas-de-informacao`): todos os quatro rodam sem erro e reportam zero duplicatas/faltantes/issues
de corpus (1517, 1333, 1367 e 1382 registros gerados, respectivamente — números puramente
informativos do modo diagnóstico, nunca escritos em disco). Nenhum ledger novo foi criado para
nenhum desses quatro booklets — não há necessidade documentada de um ledger de auditoria para eles
nesta fase (nenhuma limitação equivalente à de 2008-b foi relatada para eles em nenhuma fase
anterior), e a ferramenta comprovadamente funciona para eles sem qualquer branch específica de
booklet, confirmando a generalidade da implementação. `tests/test_protected_corpus.py` (4/4)
confirma que 2011/2021 permanecem byte-idênticos ao seu estado protegido durante toda esta fase.

## T. Testes

908 testes totais (antes: 881). Novos/alterados:

- `tests/test_content_assignment_generation.py` (novo, 14 testes): 3 testes puros de
  `_naive_alternative_text`; determinismo de geração; ordenação e unicidade de `assignment_id`
  (o teste que primeiro capturou o bug da Seção I); zero duplicate/missing findings; zero corpus
  validation issues; Q8 (5 assets distintos, owner/destination corretos); Q38 (6 assets); Q55 (5
  assets); Q45 (≥1 asset); D59 (zero assets, por design); zero asset ausente; nenhum registro
  `ambiguous` com `confidence` diferente de 0.0 (nunca "ambíguo mas confiante").
- `tests/test_phase4b_freeze.py` (novo, 20 testes, 5 deles parametrizados): espelha a estrutura do
  antigo `test_phase4a_freeze.py` como o novo gate *ao vivo* — branch/HEAD/master atuais; o freeze
  declara suceder o da Fase 4A; o hash gravado para `phase-4a-freeze.json` bate com o arquivo real
  (prova de que não foi silenciosamente editado); hash do ledger de content-assignment bate com o
  disco atual; **a mudança do ledger de fato invalidou a entrada correspondente no freeze antigo**
  (prova de que o refresh não foi cosmético); hashes da ferramenta de geração e dos testes de geração
  batem; conjunto de arquivos não commitados bate exatamente com o declarado; cobertura de regressão
  explícita, determinística (blob sintético, independente do estado real do repo) para a classe de
  defeito "primeiro caractere do caminho truncado por `.strip()` no blob inteiro" da Fase 4A.
- `tests/test_phase4a_freeze.py` (reescrito, 14→7 testes): não compara mais contra estado *ao vivo*
  (HEAD atual, disco atual) — apenas contra o conteúdo gravado do próprio arquivo (uma fotografia
  histórica) e contra o hash que o novo freeze da Fase 4B registrou para ele, provando que não foi
  silenciosamente editado. Ver Seção X para a justificativa completa desta mudança.

## U. Quality gates

```text
pytest: 908 passed, 0 failed, 0 skipped (499.68s)
ruff check .: All checks passed!
ruff format --check .: 427 files already formatted
mypy src: Success: no issues found in 61 source files
enade validate-schema: 13/13 fixture(s) valid
enade validate-manifest: OK (0 warning(s))
enade audit-extraction --questions-dir data/questions/2008/all-computing: 80/80 OK
enade audit-extraction --questions-dir data/questions/2011/all-computing: 55/55 OK
enade audit-extraction --questions-dir data/questions/2021/ciencia-da-computacao-bacharelado: 40/40 OK
enade audit-extraction --questions-dir data/questions/2021/ciencia-da-computacao-licenciatura: 40/40 OK
enade audit-extraction --questions-dir data/questions/2021/sistemas-de-informacao: 40/40 OK
enade verify-gold --year 2008 --course all-computing: OK (80 questions), maturity=provisional, verified=78, needs_review=2
enade verify-gold --year 2011 --course all-computing: OK (55 questions), maturity=validated, verified=54, needs_review=1
enade verify-gold --year 2021 --course ciencia-da-computacao-bacharelado: OK (40 questions), maturity=validated, verified=40, needs_review=0
enade assess-readiness --year 2008 --course all-computing: READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS (0 actionable blockers, 2 source limitations, 0 informational)
enade assess-readiness --year 2011 --course all-computing: READY_FOR_LEGACY_LAYOUT_TEST (0 actionable blockers, 0 source limitations, 1 informational: enade-2011-computing-q34 needs_review)
enade assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado: READY_FOR_2011 (0/0/0)
enade assess-readiness --year 2021 --course ciencia-da-computacao-licenciatura: no gold manifest (gold-2021-l.json não existe - divergência pré-existente, documentada em todas as fases anteriores, não corrigida aqui por estar fora de escopo)
enade assess-readiness --year 2021 --course sistemas-de-informacao: no gold manifest (gold-2021-s.json não existe - mesma divergência pré-existente)
enade generate-content-assignment --year 2008 --course all-computing --check: 2296 record(s), 0 duplicate, 0 missing, 0 corpus_validation_issue
enade generate-content-assignment --year 2011 --course all-computing --check: 1517 record(s), 0/0/0 (diagnóstico apenas)
enade generate-content-assignment --year 2021 --course ciencia-da-computacao-bacharelado --check: 1333 record(s), 0/0/0
enade generate-content-assignment --year 2021 --course ciencia-da-computacao-licenciatura --check: 1367 record(s), 0/0/0
enade generate-content-assignment --year 2021 --course sistemas-de-informacao --check: 1382 record(s), 0/0/0
tests/test_protected_corpus.py: 4/4 passed
```

## V. Reprodutibilidade do corpus

Duas extrações completas e independentes de 2008-b (`extract_exam`, cada uma em seu próprio
diretório temporário isolado, nunca escrevendo em `data/questions`) foram comparadas: run A vs run
B, run A vs publicado, run B vs publicado — **0 diferenças em todos os três pares** (mesmo conjunto
de arquivos, mesmo conteúdo byte a byte, para todos os `.md` e `.png` de 2008-b). Uma primeira
tentativa desta comparação relatou "1 diferença" (na verdade, um conjunto inteiro de arquivos
"diferentes") — investigado e confirmado como um bug no próprio script de comparação (o diretório
temporário usado como raiz de `questions_output_dir` legitimamente contém um prefixo `2008/all-computing/`
que o caminho já-resolvido `data/questions/2008/all-computing` não tem — comparação de bases
diferentes, não uma divergência real do corpus), corrigido no script de comparação (nunca no
pipeline) e re-executado com a base correta, confirmando 0 diferenças reais.

## W. Reprodutibilidade do ledger

Três chamadas independentes de `generate_content_assignment_ledger(...)` (cada uma re-executando o
pipeline completo internamente, ver Seção H sobre por que "apontar para run A/B" não se aplica a esta
arquitetura) produziram `json.dumps(..., sort_keys=True)` idêntico entre si e idêntico ao
`content-assignment-2008-b.json` publicado (`call1 == call2 == call3 == published`, todas `True`,
verificado programaticamente). Esta é a segunda metade do gate central da Seção 26 do prompt; ambas
as metades passam.

## X. Freeze reestabelecido

O freeze da Fase 4A (`data/manifests/phase-4a-freeze.json`) certificava um estado específico
(HEAD `22e3e882...`, 13 arquivos não commitados, o ledger *antigo*) que deixou de ser o estado atual
por dois motivos legítimos: seu HEAD foi superado quando aqueles 13 arquivos foram commitados
externamente como `c3b3bd1...` entre sessões, e o próprio ledger que ele protegia foi regenerado
nesta fase. Um freeze cujas próprias comparações "ao vivo" falham para sempre por motivos já
entendidos deixa de ser um gate útil — continuar a exigir que ele bata com o estado atual apenas
sinalizaria uma regressão que não existe.

Optou-se pela abordagem de freezes versionados (a segunda opção oferecida pelo prompt da Seção 24):
`data/manifests/phase-4b-freeze.json` foi criado como o novo freeze **ativo**, cobrindo: branch/HEAD/
master/merge_base atuais; os 8 arquivos atualmente não commitados (path/tipo/hash); hashes de todos
os 33 manifestos em `data/manifests/` (incluindo, pela primeira vez, `phase-4a-freeze.json` como um
manifesto comum — protegido, não mais especial); hashes dos 34 relatórios `docs/phase-*-report.md`
(agora incluindo este); hash agregado de cada um dos 5 corpora publicados; **o hash explícito do
próprio ledger de content-assignment, sua contagem de registros e sua ferramenta geradora**
(`content_assignment.py`, `cli.py`) e seus testes (`test_content_assignment.py`,
`test_content_assignment_generation.py`) — um campo que o freeze da Fase 4A não tinha, porque o
ledger não era o foco daquela fase; os resultados literais de todos os quality gates (Seção U); os
vereditos de readiness; as 2 limitações de fonte D09/D10; e uma seção `historical_freezes` com uma
única entrada apontando para `phase-4a-freeze.json`, seu hash exato, e uma nota explícita
("superseded", "superseded_by": "4b") — nunca alterando o conteúdo do arquivo antigo, apenas
documentando seu novo status a partir do freeze novo.

`data/manifests/phase-4a-freeze.json` permanece **byte-a-byte inalterado** no disco — confirmado por
hash cruzado em ambas as direções (`tests/test_phase4b_freeze.py::test_historical_freeze_entry_hash_matches_the_real_phase_4a_file_unedited`
e `tests/test_phase4a_freeze.py::test_freeze_was_never_silently_edited_after_being_superseded`).
`tests/test_phase4a_freeze.py` foi reescrito para não mais afetar HEAD/disco atuais — apenas
verifica que o arquivo existe, é JSON válido, seu HEAD gravado é um commit ancestral real do HEAD
atual (nunca igual a ele), suas afirmações internas sobre D09/D10/readiness permanecem consistentes,
e que ele foi corretamente marcado como superado pelo freeze novo. Nunca dois freezes "ativos"
simultaneamente: apenas `tests/test_phase4b_freeze.py` compara qualquer coisa contra o estado ao
vivo do git/disco.

Nova cobertura de regressão explícita para a classe de defeito "bug do primeiro caractere do
caminho" (Fase 4A Seção X): um teste determinístico usando um blob porcelain sintético fixo
(independente do estado real do repositório) prova que `.strip()` no blob inteiro corrompe
exatamente o primeiro caminho listado, enquanto dividir em linhas primeiro nunca o faz — a mesma
lição já registrada no relatório da Fase 4A, agora também codificada como teste permanente, não
apenas como prosa.

## Y. Estado Git final e recomendação

```text
branch: feat/enade-2008-cc-b-pilot
HEAD:   c3b3bd1a2bb515a82a8c696cebb75cb108d26c7b   (inalterado - nenhum commit criado)
master: a5dfaab0c105150df3a7201c16547708cef45292   (inalterado, == origin/master)
```

`git status --short`:

```text
 M data/manifests/content-assignment-2008-b.json
 M data/manifests/extraction-capabilities.json
 D scripts/generate_content_assignment_ledger.py
 M src/enade/cli.py
 M src/enade/extraction/content_assignment.py
 M tests/test_phase4a_freeze.py
?? data/manifests/phase-4b-freeze.json
?? docs/phase-4b-report.md
?? tests/test_content_assignment_generation.py
?? tests/test_phase4b_freeze.py
```

(10 linhas de `git status --short`; o próprio freeze `phase-4b-freeze.json` exclui apenas a si mesmo
de sua lista de `uncommitted_changes` — nunca pode conter o próprio hash — portanto declara 9
arquivos, que é exatamente esta lista menos ele mesmo. Este relatório, por ser texto descrevendo o
estado do repositório, inevitavelmente passa a fazer parte desse mesmo estado assim que é escrito;
isso é esperado, não uma inconsistência, e o freeze foi regenerado uma última vez após este arquivo
existir, precisamente para que sua própria contagem de relatórios (35, incluindo este) e o conjunto
de arquivos não commitados batessem com a realidade final, não com um instantâneo anterior a si
mesmo.)

`git diff --stat -- data/questions`: vazio (nenhuma linha) — corpus publicado nunca tocado.
`git diff --stat` (tracked): `content-assignment-2008-b.json` (regeneração de dados, não patch
manual — 14694 linhas trocadas, todas geradas pela ferramenta, nenhuma edição manual),
`extraction-capabilities.json` (+1/−1, ajuste documental de caminho), `cli.py` (+120, novo comando),
`content_assignment.py` (+/−491, nova função de geração + a correção da Seção I),
`test_phase4a_freeze.py` (reescrita, Seção X). Nenhum arquivo staged (`git diff --cached` vazio,
implícito por não ter sido usado `git add` em nenhum momento). Nenhum arquivo de scratch remanescente
— o script antigo do Fase 3J e todas as cópias temporárias de investigação usadas nesta sessão
(`scratchpad/test_gen_ledger.py`, `scratchpad/gen_freeze.py` permanece como histórico da Fase 4A,
não removido pois pertence àquela fase, não a esta) foram removidos do diretório de scratchpad da
sessão; nenhum arquivo temporário de investigação desta fase permanece fora do repositório em
`C:/Users/Filipe/AppData/Local/Temp/`.

**Recomendação**: revisão humana antes de qualquer commit. Arquivos de maior risco relativo para
revisão prioritária: `content_assignment.py` (491 linhas líquidas — a lógica de divergência
naive-vs-real e a correção de identidade da Seção I merecem leitura linha a linha, não apenas
confiança nos testes) e o próprio `content-assignment-2008-b.json` regenerado (recomenda-se abrir
o diff completo pelo menos para Q08/Q38/Q45/Q55, mesmo já tendo sido individualmente verificados
nesta fase — ver Seções K-N). `cli.py` e `test_phase4a_freeze.py` são de risco mais baixo (o
primeiro é aditivo; o segundo remove asserções ao vivo mas não lógica de negócio). Após aprovação
explícita, aplicar o plano de commit temático já estabelecido pela Fase 4A (agrupando por
mecanismo/artefato, nunca um único commit monolítico), re-executando os quality gates da Seção U após
cada commit — nunca assumindo que passar antes do commit garante passar depois. Push/PR só devem ser
considerados após esse ciclo completo, nunca iniciados automaticamente por esta fase.

## NÃO FAZER (confirmação de conformidade)

Nenhuma edição manual pontual em Q8/Q38/Q55 foi feita — toda mudança nesses registros veio da
regeneração determinística da ferramenta geral. Nenhum ID de questão hardcoded no gerador (buscado
explicitamente: `grep` por `Q8`/`Q38`/`Q55`/`if question_id` em `content_assignment.py` retorna
apenas comentários explicativos, nunca lógica condicional por ID). O ledger nunca foi conectado ao
pipeline de extração real (`assemble_question` real nunca foi modificado; apenas monkeypatchado
temporariamente, com restauração garantida por `try/finally`, dentro da própria função geradora).
Nenhuma mudança em `data/questions`, gold, visual-audit, D09/D10 (status permanece
`source_unavailable`, nunca `resolved`). Nenhuma expansão do corpus. Nenhum ledger novo criado para
2011/2021 sem necessidade documentada. O freeze antigo não foi silenciosamente deletado nem teve sua
semântica alterada — apenas seu papel de gate ao vivo foi transferido, de forma explícita e
documentada, para o freeze novo. Nenhum commit, push, PR, `git add`, ou alteração em `master` foi
executado em nenhum momento desta fase.
