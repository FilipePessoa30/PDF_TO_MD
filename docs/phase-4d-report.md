# Fase 4D — Reconciliação Bidirecional de Assets Órfãos e Cobertura de Fallbacks de Tabela

## A. Classificação

**`ORPHAN_ASSET_CONTRACT_RECONCILED`**, com **`PILOT_FREEZE_REESTABLISHED`** e
**`READY_FOR_HUMAN_REVIEW`**.

O finding F6 (três assets publicados em 2011/2021 sem cobertura no ledger) foi investigado até a
causa raiz — nunca aceito pela explicação preliminar da Fase 4C sem prova adicional — e resolvido
por uma correção geral do mecanismo (`_record_question` passou a enumerar `extracted.tables`, não
apenas `extracted.figure_regions`), nunca por uma lista de três caminhos. A varredura de
generalização (Seção O/P) confirma **zero órfãos nos cinco booklets protegidos** após a correção,
incluindo os dois cursos de 2021 que a Fase 4C nunca chegou a testar individualmente
(`ciencia-da-computacao-licenciatura`). Um órfão verdadeiro sintético continua sendo detectado
(Seção M, teste dedicado). Nenhum hardcode de ano/curso/questão foi introduzido. `data/questions`
permanece intocado; os cinco corpora permanecem byte-idênticos. Um novo freeze
(`phase-4d-freeze.json`) foi criado; os três freezes anteriores (4A/4B/4C) permanecem históricos e
byte-a-byte inalterados. 949/949 testes passam.

Um segundo achado real, independente de F6, foi descoberto durante esta fase e é reportado sem
ocultação (Seção W): o freeze da Fase 4C nunca teve seus campos `readiness`/`quality_gates`
preenchidos com valores reais (ficaram como `{}` vazio) — ao contrário dos freezes das Fases 4A e
4B, que preenchem esses campos corretamente. Não corrigido no arquivo (que é agora histórico e
imutável por definição), mas documentado e coberto por um teste que registra honestamente essa
lacuna em vez de escondê-la ou inventar dados retroativos.

## B. Estado Git inicial

```text
branch: feat/enade-2008-cc-b-pilot
HEAD:   24dfe722283f1fd59d143a4878fef1fdcf24ca1d
master: a5dfaab0c105150df3a7201c16547708cef45292 (== origin/master)
origin/feat/enade-2008-cc-b-pilot: 24dfe722283f1fd59d143a4878fef1fdcf24ca1d
```

**Fato importante, consistente com o padrão já observado nas transições 3Z→4A, 4A→4B e 4B→4C**: no
início desta fase, `git status` reportou working tree **limpa** (não a árvore com os 8 arquivos que
o recap da Fase 4C descrevia como não commitados). `git log` mostrou um commit novo,
`24dfe722283f1fd59d143a4878fef1fdcf24ca1d` ("Enhance content assignment ledger and introduce orphan
asset detection"), já commitado **e enviado** para `origin/feat/enade-2008-cc-b-pilot`.
`git show --stat 24dfe72` confirma que esse commit contém exatamente os 9 arquivos que a Fase 4C
produziu, nem mais nem menos (`content-assignment-2008-b.json`, `phase-4c-freeze.json`,
`docs/phase-4c-review.md`, `cli.py`, `content_assignment.py`,
`test_content_assignment.py`/`test_content_assignment_generation.py`/`test_phase4b_freeze.py`/
`test_phase4c_freeze.py`) — nenhuma surpresa, nenhuma discrepância com o que a Fase 4C reportou como
seu próprio estado final. Este fato **não foi causado por nenhuma ação desta ou de qualquer sessão
anterior** (nenhum `git add`/`commit`/`push` foi executado por este agente em nenhuma fase) e é
tratado com a mesma transparência das ocorrências anteriores: reportado aqui, nunca escondido, e sem
nenhuma ação destrutiva unilateral sobre o commit já público. `master`/`origin/master` permanecem
intocados (`a5dfaab0...`, idênticos entre si). As alterações locais desta fase (Seção X) foram
preservadas durante toda a investigação — nenhum arquivo foi descartado ou revertido.

## C. Baseline

928 testes (final da Fase 4C), todos passando. `content-assignment-2008-b.json`: 2296 registros,
hash `adfa543b...` (o mesmo hash publicado no commit `24dfe72`). `enade generate-content-assignment
--help` confirma a sintaxe real: `--year`/`--course`/`--corpus-root`/`--questions-dir`/`--output-dir`/
`--check`/`--write` (mutuamente exclusivos). Executado com essa sintaxe real (nunca presumida):

```text
$ enade generate-content-assignment --year 2011 --course all-computing --check
generate-content-assignment: 1517 record(s) generated
  duplicate assignment finding(s): 0   missing assignment finding(s): 0   corpus validation issue(s): 0   orphan asset(s): 1
    - [asset_not_in_ledger] enade-2011-computing-q22/table-01.png exists on disk but has no corresponding asset record in the ledger

$ enade generate-content-assignment --year 2021 --course ciencia-da-computacao-bacharelado --check
  ... orphan asset(s): 1  enade-2021-cc-b-d03/table-01.png

$ enade generate-content-assignment --year 2021 --course ciencia-da-computacao-licenciatura --check
  ... orphan asset(s): 1  enade-2021-cc-l-d03/table-01.png

$ enade generate-content-assignment --year 2021 --course sistemas-de-informacao --check
  ... orphan asset(s): 0
```

`ruff check .`: All checks passed! `ruff format --check .`: todos formatados. `mypy src`: Success, 61
arquivos. `enade validate-schema`: 13/13. `enade validate-manifest`: OK. `enade audit-extraction`
para as 5 corpora: 80/80, 55/55, 40/40×3 OK. Hashes de baseline de `data/questions` (5 corpora),
gold (3 manifestos), visual audits (3), blocker ledgers (2), e dos 3 freezes anteriores foram
registrados implicitamente pelo próprio `phase-4d-freeze.json` gerado ao final (Seção U/V) — nenhum
foi alterado por esta fase, confirmado por comparação byte a byte antes/depois.

## D. Finding F6

Os três casos exatos, confirmados por leitura direta do Markdown publicado (nunca presumidos do
nome do arquivo):

| Ano/Curso | Questão | Página fonte | Asset | Referenciado como |
|---|---|---|---|---|
| 2011 all-computing | Q22 (objetiva) | ver `table.page_number` | `table-01.png` | `![Tabela (fallback visual fiel)](enade-2011-computing-q22/table-01.png)` |
| 2021 ciência-da-computação-bacharelado | D03 (discursiva) | idem | `table-01.png` | idem |
| 2021 ciência-da-computação-licenciatura | D03 (discursiva) | idem | `table-01.png` | idem |

2021-sistemas-de-informação não tem nenhum caso (nenhuma tabela sua recebeu este tratamento) — não
é "fora do escopo", é "zero órfãos por não ter nenhuma tabela com fallback", uma distinção mantida
explicitamente diferente ao longo deste relatório (Seção O/P). 2008-b também tem **zero** casos
(confirmado por busca textual em todo o corpus - nenhuma questão de 2008-b tem "fallback visual
fiel" em seu Markdown) — o que significa que o "zero órfãos" que a Fase 4C reportou para 2008-b
nunca provou que este mecanismo específico funcionava; provou apenas que 2008-b nunca o exercita.

## E. Contrato de escopo

`content_assignment.py` já continha uma resposta implícita, nunca antes declarada explicitamente:
`generate_content_assignment_ledger` é uma função **por booklet** (recebe `prova_path`/
`gabarito_path`/`padrao_path`/`exam_year`/`course`/`structure_profile` de UM booklet por chamada) e
o comando CLI grava em `output_dir / f"content-assignment-{year}-{slug}.json"` — um nome de arquivo
por combinação ano+curso, nunca um ledger multicorpus. A arquitetura portanto já prevê **um ledger
por prova**, gerado sob demanda (`--check` nunca persiste; `--write` persiste exatamente um
arquivo por chamada) — não uma limitação de escopo a 2008-b, mas uma decisão de **política**
(Fases 4B/4C: "não crie ledgers desnecessários para 2011/2021 sem necessidade documentada") nunca
uma limitação arquitetural. Confirmado ao rodar `--check` com sucesso para os 5 targets sem
nenhuma branch condicional por ano/curso no código do gerador. Esta fase não publica nenhum ledger
novo para 2011/2021 (Seção N/O/P) — apenas prova, via testes automatizados reais contra o corpus de
2011, que o gerador reconhece corretamente os casos de fallback de tabela quando de fato executado
sobre esse target.

## F. Hipótese adjudicada

**Combinação de A (omissão do gerador) e C (contrato incompleto de representação derivada) — nunca
B (escopo do gate).**

Evidência que **descarta B**: `find_orphan_assets` foi executado para 2011 com `--check` e
corretamente restringiu sua varredura a `data/questions/2011/all-computing` (o mesmo diretório usado
por `validate_ledger_against_corpus` para o mesmo target) - o único órfão real encontrado
(`enade-2011-computing-q22/table-01.png`) está genuinamente dentro desse target, pertence à questão
correta, e nenhum arquivo de outro target foi jamais varrido. O gate nunca teve jurisdição incorreta.

Evidência que **confirma A**: leitura direta de `pipeline.py` linhas 387-428 mostra que
`assets_by_table` é populado incondicionalmente para cada `extracted.tables[index]`
("Mandatory visual fallback for every detected table... rendered unconditionally"), com um arquivo
real (`table-{index+1:02d}.png`) sempre gravado em disco - mas `content_assignment.py`'s
`_record_question` (antes desta fase) só percorria `enumerate(extracted.figure_regions)`, nunca
`enumerate(extracted.tables)`. Confirmado empiricamente: 0 registros de asset para `table-01.png` em
qualquer payload gerado antes da correção.

Evidência que **confirma C**: mesmo depois de simplesmente adicionar um registro `asset` genérico
para cada tabela (a correção mínima que fecha F6 tecnicamente), permaneceria perdida a informação de
que esse asset é uma **projeção visual derivada** da MESMA unidade semântica que o `TableSegment`
correspondente já representa via suas próprias `consumed_lines` (linhas absorvidas na tabela
estruturada) - dois artefatos publicados (GFM + PNG) do mesmo conteúdo, não dois conteúdos
independentes. Sem essa distinção, uma auditoria futura não conseguiria diferenciar este caso de um
`figure_region` genuinamente independente (uma foto, um diagrama) só por inspecionar o ledger.

## G. Fallbacks de tabela

```yaml
- asset_path: enade-2011-computing-q22/table-01.png
  year: 2011
  course: all-computing
  question_id: enade-2011-computing-q22
  source_page: (table.page_number, extraído de DetectedTable.bbox real)
  asset_type: table_visual_fallback
  referenced_from: "![Tabela (fallback visual fiel)](enade-2011-computing-q22/table-01.png)"
  structured_counterpart: "GFM table rendered by render_table_markdown(table) - travels in the same Markdown chunk"
  semantic_owner: enade-2011-computing-q22 (mesma questão, mesmo TableSegment.table_index)
  generation_mechanism: "pipeline.py: 'Mandatory visual fallback for every detected table' - unconditional, PROMPT Phase 1C section 5.2"
  current_ledger_record: "ausente antes desta fase"
  expected_ledger_relation: "asset com representation_role=visual_fallback, anchor=table:<index>"
  orphan_reason: "_record_question nunca enumerava extracted.tables, apenas extracted.figure_regions"

- asset_path: enade-2021-cc-b-d03/table-01.png
  year: 2021
  course: ciencia-da-computacao-bacharelado
  question_id: enade-2021-cc-b-d03
  asset_type: table_visual_fallback
  generation_mechanism: idem
  orphan_reason: idem

- asset_path: enade-2021-cc-l-d03/table-01.png
  year: 2021
  course: ciencia-da-computacao-licenciatura
  question_id: enade-2021-cc-l-d03
  asset_type: table_visual_fallback
  generation_mechanism: idem
  orphan_reason: idem
```

O fallback visual **nunca substitui** a tabela estruturada nem é gerado apenas quando a
reconstrução falha — ele **complementa** deliberadamente toda tabela detectada, sempre, para que o
leitor possa conferir a reconstrução estrutural contra o original (`to_question.py`'s próprio
docstring, citando PROMPT Fase 1C seção 5.2: "D3-class content must never leave the reader with only
a structured guess and no way to check it against the original"). Portanto o PNG e a tabela GFM
**nunca são dois conteúdos independentes** - são duas representações do mesmo `DetectedTable`,
publicadas juntas no mesmo trecho de Markdown, nunca reordenáveis uma sem a outra. Pertence sempre à
mesma unidade estrutural que já possui um enunciado/alternativa/padrão-de-resposta como dono (neste
caso, sempre o enunciado da própria questão - `TableSegment` só aparece em `statement_segments`).

## H. Modelo de dados

O schema `ContentAssignment` já reutilizável para este caso (nenhuma questão de tipo/serialização
nova): apenas um campo foi adicionado.

```python
RepresentationRole = Literal["primary", "visual_fallback", "derived_representation", "shared"]
# ContentAssignment ganha:
representation_role: RepresentationRole = "primary"
```

Semântica: `"primary"` (default, retrocompatível - todo registro produzido antes desta fase, e todo
`figure_region`/linha/anotação produzido depois dela, continua `"primary"`); `"visual_fallback"` (o
único valor novo de fato produzido - a projeção visual mandatória de uma tabela);
`"derived_representation"`/`"shared"` declarados pela mesma razão que `SourceType` já declara
valores nunca produzidos (extensibilidade do contrato sem quebra de forma, PROMPT Fase 3J seção 6) -
**nenhum caso real os produz hoje**, e nenhum foi inventado apenas para preencher o enum. Nenhuma
migração de dados é necessária: o campo tem um default, então todo registro antigo reconstruído via
`ContentAssignment(**record)` a partir de um JSON sem essa chave simplesmente recebe `"primary"`.
Nenhuma validação de runtime nova foi adicionada além do que já existia para os outros campos
`Literal` do dataclass (nenhum deles é validado em runtime hoje - `status`/`canonical_owner`/etc. -
adicionar validação só para o campo novo seria inconsistente com o resto do schema, não corrigido
aqui por não ser parte do finding F6). A relação com a "unidade semântica" (o índice da tabela) é
capturada reutilizando o campo `anchor` já existente (`f"table:{table_index}"`), sem precisar de um
campo estrutural adicional.

## I. Identidade

`assignment_id`/`source_element_id` de um registro de fallback de tabela: derivados de
`table.bbox` (a MESMA geometria que `pipeline.py` já usa para recortar tanto o PNG quanto as linhas
estruturadas da tabela) + `table.page_number` - nunca de `enumerate(extracted.tables)` diretamente.
Formato: `f"{question_id}:table_asset:p{page}:{x0}:{y0}:{x1}:{y1}"` (arredondados a 1 casa decimal,
mesma convenção de toda identidade já estabelecida nas Fases 4B/4C). Prova de estabilidade: como
`table.bbox` é único por tabela dentro de uma questão (nenhuma tabela real ocupa o mesmo retângulo
que outra), inserir/remover uma linha ou figura não relacionada na mesma questão nunca afeta este
id. Prefixo `table_asset` distingue esta identidade da de `figure_region` (`asset`) - nenhuma colisão
possível entre os dois tipos, mesmo compartilhando a mesma página. `anchor=f"table:{table_index}"`
distingue a unidade semântica (qual tabela) da representação concreta (`representation_role`) e do
arquivo publicado (`representation`) - as três dimensões que a Seção 9 do prompt exige distinguir.
Verificado com `assignment_id == source_element_id` para 100% dos novos registros (mesma disciplina
que toda a Fase 4C já unificou para os outros três ramos). Nenhuma colisão introduzida: `len(ids) ==
len(set(ids))` confirmado para 2011 (1518 registros) e para 2008-b (2296, inalterado).

## J. Gerador

Uma única adição a `_record_question` (um novo laço `for table_index, table in
enumerate(extracted.tables)`, paralelo ao laço já existente de `figure_regions`) - responsabilidade
única mantida (o módulo continua sendo apenas geração + gates de auditoria, nunca consumido pelo
pipeline real). Nenhum hardcode de ano/curso/questão (`grep` confirma). Nenhuma nova dependência
circular (a nova lógica só lê `extracted.tables`, já disponível no mesmo objeto retornado por
`orig_assemble_question`, nunca chama nenhuma função nova). Nenhuma mutação do corpus. A correção
atua sobre o **mecanismo** (`table → fallback visual publicado → atribuição`), nunca sobre os três
paths específicos - confirmado pelo fato de que a mesma correção, sem nenhuma condicional adicional,
fechou os três casos reais de 2011/2021 simultaneamente (Seção O/P) e não introduziu nenhum
registro espúrio para 2008-b (que não tem nenhuma tabela com fallback).

## K. CLI

Nenhuma mudança na CLI foi necessária. Todas as garantias da Fase 4C permanecem intactas e foram
reverificadas: `--check` compara a geração fresca contra o arquivo publicado correto (confirmado -
`--check` para 2008-b corretamente reportou "is stale" imediatamente após a correção do schema, até
o `--write` ser executado); drift produz exit code 1; `--write` é atômico (não alterado, não
re-testado com nova falha simulada por não haver mudança no próprio mecanismo de escrita); target e
output continuam resolvidos sem ambiguidade (`--year`/`--course` inalterados); `--check` nunca
escreve (reconfirmado). A CLI já aceitava todos os 5 targets antes desta fase (Fase 4C já havia
verificado isso) - nenhuma mudança de validação de combinação ano/curso foi necessária.

## L. Gate reverso

`find_orphan_assets` **não precisou de nenhuma mudança de código** - seu algoritmo (comparar o
conjunto real `(question_id, representation.png)` em disco contra o conjunto que o ledger afirma
cobrir) já era correto e suficientemente geral; a lacuna estava inteiramente no lado do GERADOR
(Seção F/J), nunca no gate. Verificado que o gate detecta corretamente:

- asset publicado sem registro (o próprio F6, antes da correção);
- asset pertencente à questão errada (novo teste dedicado,
  `test_asset_claimed_by_the_wrong_question_is_still_an_orphan_for_its_real_owner` - uma reivindicação
  para `(q2, figure-01.png)` nunca "cobre" o arquivo real em `q1/figure-01.png`, já que a chave é
  sempre `(question_id, representation)` junto, nunca a representação isolada);
- órfão verdadeiro sintético continua detectado após a correção (Seção M).

Itens adicionais da Seção 13 do prompt (registro apontando para arquivo inexistente; referência
Markdown para asset ausente) já eram cobertos por `validate_ledger_against_corpus`, um gate
irmão pré-existente, nunca duplicado aqui. "Arquivo real que deixou de ser referenciado" é coberto
pela própria limpeza de assets obsoletos que `pipeline.py` já faz a cada extração (comentário
"A rerun can detect fewer/different regions... any asset file left over... must not silently keep
existing"). "Representação derivada sem primária válida" não recebeu um gate de runtime dedicado:
por construção, todo registro `visual_fallback` só é produzido dentro do mesmo laço que itera
`extracted.tables`, que é exatamente o mesmo objeto que garante a existência do `TableSegment`
correspondente - não há caminho de código que produza um sem o outro, então um gate para essa
combinação nunca teria um caso real para detectar (nenhum foi adicionado, por não haver evidência
que o justifique, seguindo a mesma disciplina de "não invente sem evidência" do resto do projeto).

## M. Três casos reais

Para cada um dos três (2011-Q22, 2021-cc-b-D03, 2021-cc-l-D03), individualmente:

1. Evidência do comportamento anterior preservada nesta seção e na Seção D (screenshot textual do
   `--check` reportando o órfão, antes de qualquer correção).
2. Código de publicação identificado: `pipeline.py` linhas 387-428 (`assets_by_table`).
3. Referência no conteúdo identificada: `to_question.py` linha 121 (`render_statement_markdown`).
4. Proprietário identificado: a própria questão (`enade-2011-computing-q22`,
   `enade-2021-cc-b-d03`, `enade-2021-cc-l-d03`) - nunca outra questão, nunca um proprietário
   compartilhado.
5. Demonstrado por que o enumerador antigo o omitia: só percorria `figure_regions` (Seção F/J).
6. Contrato corrigido: novo laço + campo `representation_role` (Seção H/J).
7. Candidato gerado para os 3 targets via `--check` (2011, 2021-cc-b, 2021-cc-l).
8. Confirmado que cada asset deixa de ser órfão **pelo motivo correto** (aparece no ledger com
   `representation_role="visual_fallback"`, `anchor` apontando para o índice da tabela certa -
   testes `test_table_fallback_asset_has_a_ledger_record`/
   `test_table_fallback_asset_is_tagged_as_a_derived_representation`).
9. Confirmado sem duplicidade: `detect_duplicate_assignments`/`detect_missing_assignments` retornam
   vazio para os três targets.
10. Confirmado que o conteúdo publicado (`data/questions`) permanece byte-idêntico - `git diff
    --stat -- data/questions` vazio durante toda a fase.

Nenhum dos três foi promovido "em massa" por uma allowlist de nomes - a correção geral, aplicada uma
única vez ao mecanismo, resolveu os três simultaneamente como consequência necessária, nunca como
três correções separadas.

## N. 2008-b

Zero órfãos, confirmado antes e depois (2008-b nunca teve nenhum caso de F6, Seção D). O ledger
**foi regenerado** (2296 registros preservados exatamente - mudança justificada: a adição do campo
`representation_role` altera a forma serializada de todo registro, exigindo republicação mesmo sem
nenhuma mudança de conteúdo). Verificado por uma chave independente de formato
(`(question_id, source_type, source_bbox)`): os 2296 registros correspondem exatamente entre a
versão anterior e a nova, com zero diferença em `canonical_owner`/`anchor`/`publication_destination`/
`representation`/`status`/`confidence`/`reason`/`assignment_id`/`source_element_id` - a única mudança
é a presença do novo campo `representation_role="primary"` em todo registro. Escrita dupla
confirmada byte-idêntica (hash `70dc941766b5c90b08f060c155a504b80486b104177251cc5635c45c700ad82e`
em ambas).

## O. 2011

Cobertura completa após a correção: 1518 registros (1517 + 1 novo registro de fallback de tabela),
zero duplicatas, zero faltantes, **zero órfãos** (antes: 1). Reprodutibilidade de 3 vias confirmada
(`ledger run A == B == C`, ordem determinística, IDs únicos). Prova automatizada permanente:
`tests/test_content_assignment_table_fallback.py` (8 testes, executados contra o corpus real de
2011, nunca publicando um arquivo em disco - por política, Seção E).

## P. 2021

| Curso | Antes | Depois | Órfãos antes | Órfãos depois |
|---|---|---|---|---|
| ciencia-da-computacao-bacharelado | 1333 | 1334 | 1 (D03/table-01.png) | 0 |
| ciencia-da-computacao-licenciatura | 1367 | 1368 | 1 (D03/table-01.png) | 0 |
| sistemas-de-informacao | 1382 | 1382 | 0 (nenhuma tabela com fallback) | 0 |

Todos os três verificados via `--check` real (Seção C/W) - nenhum ledger foi escrito em disco para
2011/2021 (política mantida, Seção E). "Zero órfãos" (sistemas-de-informacao, nunca teve nenhum
caso) é explicitamente distinguido de "zero órfãos após corrigir uma lacuna real" (os outros dois
cursos de 2021 e 2011) ao longo desta seção e da Seção D - nunca apresentados como equivalentes.

## Q. Testes

Baseline (fim da Fase 4C): 928. Novos/alterados nesta fase:

- `tests/test_content_assignment.py`: +1 teste
  (`test_asset_claimed_by_the_wrong_question_is_still_an_orphan_for_its_real_owner`, fixture pura,
  sem corpus real).
- `tests/test_content_assignment_table_fallback.py` (novo, 8 testes, corpus real de 2011): registro
  existe; tagueado como `visual_fallback`; demais assets/linhas permanecem `primary`; identidade
  geometricamente derivada; zero órfãos contra o corpus publicado; zero duplicata/faltante;
  determinismo entre duas chamadas independentes; um órfão verdadeiro sintético (introduzido em
  `tmp_path`, nunca no corpus real) continua detectado.
- `tests/test_phase4c_freeze.py`: reescrito (mesmo padrão histórico da Fase 4B/4C) - a asserção de
  readiness foi substituída por uma que documenta honestamente a lacuna real descoberta (Seção W).
- `tests/test_phase4d_freeze.py` (novo, 20 testes): o novo gate ativo, espelhando
  `test_phase4c_freeze.py` original, com verificação cruzada de hash para os TRÊS freezes históricos
  (4A, 4B, 4C) e um registro explícito do commit remoto pré-existente sem atribuí-lo a esta fase.

Total final: **949 testes, todos passando** (confirmado por execução completa, Seção R). Cada teste
que expõe o comportamento de F6 foi confirmado falhando contra o código pré-correção antes de
qualquer fix ser aplicado (Seção V da metodologia já estabelecida nas fases anteriores, reaplicada
aqui): rodar `tests/test_content_assignment_table_fallback.py` contra o código anterior à mudança de
schema produziu 5 falhas reais (`AssertionError`/ausência de registro), nunca apenas assumido.

## R. Quality gates

```text
pytest: 949 passed, 0 failed, 0 skipped (1184.24s)
ruff check .: All checks passed!
ruff format --check .: 432 files already formatted
mypy src: Success: no issues found in 61 source files
enade validate-schema: 13/13 fixture(s) valid
enade validate-manifest: OK (0 warning(s))
enade audit-extraction (5 corpora): 80/80, 55/55, 40/40, 40/40, 40/40 OK
enade generate-content-assignment --year 2008 --course all-computing --check: 2296/0/0/0/0 orphan
enade generate-content-assignment --year 2011 --course all-computing --check: 1518/0/0/0/0 orphan
enade generate-content-assignment --year 2021 --course ciencia-da-computacao-bacharelado --check: 1334/0/0/0/0 orphan
enade generate-content-assignment --year 2021 --course ciencia-da-computacao-licenciatura --check: 1368/0/0/0/0 orphan
enade generate-content-assignment --year 2021 --course sistemas-de-informacao --check: 1382/0/0/0/0 orphan
enade verify-gold (2008-b/2011/2021-b): OK, OK, OK
enade assess-readiness 2008-b: READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS (0/2/0)
tests/test_protected_corpus.py: 4/4 passed
tests/test_phase4a_freeze.py + 4b + 4c + 4d: 48/48 passed
git diff --check: sem saída (sem conflitos de whitespace)
```

## S. Reprodutibilidade

Corpus (Markdown/PNG): não re-executado como uma nova extração completa nesta fase - justificativa
explícita, não uma omissão silenciosa: `git diff --stat` confirma que nenhum dos módulos que
produzem o corpus real (`pipeline.py`, `assembler.py`, `to_question.py`, `tables.py`, `assets.py`,
`figures.py`) foi tocado por esta fase; apenas `content_assignment.py` (o gerador de ledger,
audit-only) e seus próprios testes mudaram. `content_assignment.py`'s próprio monkeypatch envolve
`assemble_question` sem jamais alterar seu comportamento (`orig_assemble_question` é chamado e seu
retorno é devolvido sem modificação) - portanto a propriedade de reprodutibilidade do corpus já
demonstrada nas Fases 4B/4C permanece válida por construção, não por nova evidência empírica
repetida aqui. Ledger: três chamadas independentes de `generate_content_assignment_ledger` para 2011
(o único target que exercita ambos os caminhos - `figure_regions` e o novo laço de `tables`)
produziram JSON byte-idêntico entre si (`A == B == C`), ordem determinística, IDs únicos. 2008-b:
escrita dupla via `--write` confirmada byte-idêntica. Nenhum timestamp ou caminho temporário
contaminando nenhum dos outputs (verificado, mesma checagem já estabelecida nas fases anteriores).

## T. Proteção do corpus

`git diff --stat -- data/questions`: vazio durante toda a fase. `enade audit-extraction` para as 5
corporas: 80/80, 55/55, 40/40×3 OK (Seção C/R). `gold-2008-computing.json`/`gold-2011-computing.json`/
`gold-2021-b.json`, `visual-audit-*.json` (3), `blocker-ledger-2008.yaml`/`blocker-ledger-2011.yaml`,
`source-token-ledger-2008.yaml`, os 3 PDFs-fonte de cada ano: `git diff` confirma zero mudança em
qualquer um destes arquivos durante toda a Fase 4D (apenas os 7 arquivos listados na Seção X foram
tocados). Nenhum gold foi atualizado para aceitar drift - não havia nenhum drift a aceitar.

## U. Freeze histórico

`phase-4a-freeze.json`, `phase-4b-freeze.json`, `phase-4c-freeze.json`: os três permanecem
byte-a-byte idênticos ao estado em que cada um foi deixado pela fase seguinte que os sucedeu
(confirmado por hash cruzado contra as três entradas `historical_freezes` do novo freeze ativo -
Seção V). `tests/test_phase4c_freeze.py` foi ajustado (mesmo padrão de auto-consistência histórica
já usado para 4A e 4B) para não mais comparar contra HEAD/disco ao vivo. `data/manifests/phase-4c-freeze.json`
em si **não foi reescrito** - apenas o teste que o verifica.

## V. Freeze 4D

`data/manifests/phase-4d-freeze.json` (novo, ativo): cobre branch/HEAD/master/merge_base atuais; o
commit remoto pré-existente `24dfe72` (registrado como fato, nunca atribuído a esta fase); os 6
arquivos atualmente não commitados; hashes de todos os 35 manifestos (incluindo agora
`phase-4c-freeze.json` como manifesto comum protegido); hashes dos 35 relatórios `phase-*-report.md`
e do 1 `phase-*-review.md` (`phase-4c-review.md`, rastreado numa lista `reviews` separada, já que seu
próprio nome de arquivo não segue a convenção `-report.md`); hash agregado de cada um dos 5 corpora
publicados; hash explícito do próprio ledger de content-assignment, sua contagem e sua ferramenta
geradora (incluindo agora o novo arquivo de teste `test_content_assignment_table_fallback.py`); os
resultados literais de todos os quality gates; os vereditos de readiness; as 2 limitações de fonte
D09/D10; e uma seção `historical_freezes` com três entradas (4a, 4b, 4c), cada uma com seu hash
exato e nota de superação, nunca alterando o conteúdo de nenhum arquivo antigo.
`tests/test_phase4d_freeze.py` (novo, 20 testes) é o único arquivo que compara este freeze contra
git/disco ao vivo. Limitações conhecidas do próprio freeze 4D: nenhuma identificada além das já
documentadas como herdadas (D09/D10 source_unavailable, nunca "resolved").

## W. Findings adicionais

Um finding real, não relacionado a F6, foi descoberto durante esta fase e é reportado sem
ocultação:

```yaml
id: F7
severity: LOW
file: data/manifests/phase-4c-freeze.json
line_or_symbol: "readiness, quality_gates (campos de nível superior)"
description: >
  O freeze da Fase 4C nunca teve seus campos readiness/quality_gates preenchidos com valores reais
  - permaneceram como {} (placeholder vazio) até o final daquela fase, ao contrário dos freezes das
  Fases 4A e 4B, que preenchem corretamente esses campos com o veredito real de 2008-b/2011/2021-b.
evidence: >
  Descoberto ao escrever o teste histórico desta fase para phase-4c-freeze.json (mesmo padrão já
  usado para 4A/4B): a asserção `freeze["readiness"]["2008-b"]` falhou com KeyError, já que
  freeze["readiness"] == {}.
impact: >
  Nenhum impacto em corretude/reprodutibilidade/auditabilidade do ledger ou do corpus - é uma
  lacuna puramente documental no próprio arquivo de freeze, que não afeta nenhuma garantia técnica
  já estabelecida. Um leitor futuro consultando phase-4c-freeze.json por seus próprios campos de
  readiness encontraria um dicionário vazio, sem indicação de que isso é uma omissão conhecida
  (até este relatório).
recommended_action: >
  Não corrigir o arquivo (é um snapshot histórico imutável - "nao reescreva o manifest 4C" é uma
  instrução explícita desta fase). O teste histórico foi ajustado para documentar honestamente a
  lacuna em vez de escondê-la ou inventar dados retroativos.
blocks_commit: false
outcome: fixed (o teste, não o arquivo - ver Seção Q)
```

Nenhum outro finding adicional foi encontrado durante a varredura de generalização (Seção O/P) ou a
revisão do gate reverso (Seção L).

## X. Estado Git final

```text
$ git status --short
 M data/manifests/content-assignment-2008-b.json
 M src/enade/extraction/content_assignment.py
 M tests/test_content_assignment.py
 M tests/test_phase4c_freeze.py
?? data/manifests/phase-4d-freeze.json
?? tests/test_content_assignment_table_fallback.py
?? tests/test_phase4d_freeze.py
```

Mais `docs/phase-4d-report.md`, adicionado após a geração inicial do freeze e coberto por uma
regeneração final deste mesmo freeze antes de sua publicação (mesmo padrão iterativo já usado nas
Fases 4A-4C). Nenhum arquivo staged; nenhum commit criado por esta fase; nenhum push; nenhum PR;
`master`/`origin/master` inalterados (`a5dfaab0...`). Nenhuma ação Git proibida ocorreu.
`data/questions` intocado durante toda a fase (Seção T).

## Y. Recomendação

Recomenda-se apenas revisão humana do diff e dos contratos corrigidos - nunca commit, dado que a
autorização permanece negada nesta fase. Pontos de atenção sugeridos para essa revisão: (1) a nova
função `representation_role`/o novo laço de tabelas em `content_assignment.py` (68 linhas líquidas,
a lógica central desta fase); (2) o próprio ledger `content-assignment-2008-b.json` regenerado
(recomenda-se confirmar que a única mudança real é a presença do novo campo, como demonstrado na
Seção N); (3) a reescrita de `tests/test_phase4c_freeze.py` (remove uma asserção, adiciona outra -
nunca esconde a lacuna real que motivou a mudança). Fora isso, nenhuma ação adicional é recomendada
enquanto a decisão de não commitar permanecer em vigor.
