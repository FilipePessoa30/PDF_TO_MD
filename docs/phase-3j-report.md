# Fase 3J — Atribuição Canônica de Conteúdo, Duplicação de Alternativas e Anotações Associadas à Questão

## A. Classificação

- **`CONTENT_ASSIGNMENT_STABILIZED`** — Q13 está sem duplicação (confirmado por igualdade de string
  exata contra o texto real do PDF); D60 possui as três anotações de valor corretamente atribuídas ao
  seu próprio item; o assignment ledger (`data/manifests/content-assignment-2008-b.json`, 2280 registros)
  é válido e determinístico (duas execuções independentes produzem saída byte a byte idêntica); os gates
  de duplicação/ausência (`content_assignment.detect_duplicate_assignments`/`detect_missing_assignments`)
  retornam **zero** ocorrências ao rodar contra o ledger completo das 77 questões publicadas; o scan da
  Seção K não revelou nenhum outro caso da mesma classe de defeito (mesmo source em dois destinos, mesmo
  source em duas alternativas, asset compartilhado entre questões); 2011/2021 permanecem byte-idênticos;
  reprodutibilidade confirmada (run A = run B = corpus publicado). Ver Seção P para o escopo exato do
  ledger (tipos de source com identidade estável nesta fase: `line` e `asset`) — a classificação é
  honesta sobre esse escopo, não uma alegação de cobertura universal de todo tipo de source declarado no
  schema.
- **`RESIDUAL_LAYOUT_NOT_STABILIZED`** — 67/77 aprovadas na auditoria visual, 10/77 reprovadas (queda
  real de 12 para 10, auditada questão por questão).
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido. Quatro novas capacidades declarativas
  (`canonical_content_assignment`, `annotation_ownership`, `question_value_annotation`,
  `duplicate_source_detection`) registradas, G2/G3, seguindo o mesmo padrão das Fases 3C-3I.
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase. Nunca `GENERALIZATION_SUCCESS`.
- `NOT_READY_FOR_2008_ENGINEERING_TEST` (readiness) — confirmado (65/77 verified, 12 needs_review, Q8/
  Q38/Q55 seguem excluídas).
- Nenhum commit, push, PR, merge ou tag foi criado por este agente. `master` não foi tocado.

## B. Estado Git

- Branch: `feat/enade-2008-cc-b-pilot` (confirmada no início e no fim da fase).
- `HEAD` = `99dee9c` — este commit já existia no início da fase (o usuário commitou o trabalho da Fase 3I
  entre as sessões); nenhum commit novo foi criado por este agente durante a Fase 3J.
- `master` = `origin/master` = `a5dfaab` — intocado.
- `origin/feat/enade-2011-unified-extraction` = `84c5005` — não tocada.
- Nenhum merge, rebase ou cherry-pick em andamento. Working tree ao final: 4 arquivos modificados +
  2 questões modificadas (Q13, D60) + 2 arquivos-fonte/teste modificados + 6 arquivos novos legítimos —
  todos justificados nesta fase; nenhum arquivo inesperado; nenhum arquivo de scratch remanescente
  (`diag_q8_q38_q55.py`-style scripts usados durante a investigação foram deletados antes do encerramento;
  confirmado via `git status --short | grep "^??"` mostrando apenas os 6 arquivos novos legítimos).
- 2011 preservado (zero drift). 2021 preservado (zero drift, 3 cursos verificados).

## C. Baseline

Confirmado no início da fase (herdado do fim da Fase 3I, já commitado como `99dee9c`): `pytest` = 589
passed; 77 questões publicadas; auditoria visual = 65 passed / 12 failed / 0 not_performed; gold = 63
verified / 14 needs_review; Q8/Q38/Q55 excluídas; 2011/2021 byte-idênticos (hash SHA-256 dos 288 arquivos
protegidos confirmado); reprodutibilidade confirmada; nenhum commit/push desde `99dee9c`.

## D. Reconciliação: por que 65 ≠ 63 e 12 ≠ 14 (estado no início da fase)

Investigação direta (antes de qualquer alteração de código), comparando o campo `visual_validation` do
front matter de cada questão publicada com seu `extraction_status`:

```
enade-2008-computing-d09.md: visual_validation=passed extraction_status=needs_review
enade-2008-computing-d59.md: visual_validation=passed extraction_status=needs_review
```

**Causa raiz, não um bug**: `extraction_status='verified'` exige **os dois** critérios simultaneamente
(`models/question.py`, validador Pydantic): `automatic_validation='passed'` (um conjunto de checagens
puramente mecânicas — schema, sequência de alternativas, contagem de assets, vínculo de resposta — feitas
por `validator.py`) **e** `visual_validation='passed'` (uma comparação humana/documentada contra o PDF
renderizado, registrada em `visual-audit-2008-computing.json`). São dois gates ortogonais, medindo coisas
diferentes: um mede fidelidade textual (o texto extraído corresponde à fonte?), o outro mede completude
mecânica (a questão tem tudo que precisa para ser publicada como um registro confiável e completo?).

D9 e D59 passam no critério de fidelidade visual (o texto extraído já foi confirmado correto) mas falham
no critério mecânico por uma razão **genuinamente não relacionada à extração**: `enade audit-extraction`/
`extraction-audit-2008-computing.json` mostra a mensagem `"no corresponding answer-key/answer-standard
entry found"` para ambas — o próprio `b3_padrao.pdf` não contém um padrão de resposta para essas duas
questões (D9) ou contém um padrão sem texto de rubrica algum, só imagens (D59) — ambos já documentados
como blockers abertos e pré-existentes (`d09-answer-standard-absent-from-source`,
`d59-answer-standard-image-only`/`answer-standard-incomplete`), não relacionados a Q13/D60 e fora do
escopo desta fase.

**Reconciliação numérica completa** (estado do início da fase): 65 passed + 12 failed = 77 (0
not_performed). Dos 65 aprovados visualmente: 63 são também `automatic_validation=passed` → `verified`;
2 (D9, D59) são `automatic_validation=failed` → `needs_review`. Dos 12 reprovados visualmente: todos os
12 são `needs_review` (uma reprovação visual sozinha já força `needs_review`, independente do resultado
mecânico). Total needs_review = 2 + 12 = **14**. Total verified = **63**. `63 + 14 = 77`. ✓ — a
divergência está completamente explicada; **nenhuma contagem foi alterada apenas para fazê-las coincidir**,
e nenhum status `verified` jamais coexiste com um blocker aberto (D9/D59 corretamente nunca aparecem como
`verified` enquanto seus próprios blockers de padrão-de-resposta permanecerem abertos).

## E. Modelo de atribuição

`src/enade/extraction/content_assignment.py` define `ContentAssignment` com exatamente os campos do
Section 6 do PROMPT (`assignment_id`, `source_element_id`, `source_type`, `source_page`, `source_bbox`,
`canonical_owner`, `anchor`, `publication_destination`, `representation`, `reason`, `evidence`,
`confidence`, `status`), mais `question_id` (agrupamento, não parte do schema original) e
`duplication_mode` (Seção 8, mirror autorizado — `None` para todo registro real produzido nesta fase, já
que nenhum caso real de mirror documentado existe neste corpus). `SourceType`/`Owner`/`Destination` são
`Literal`s declarando **todos** os valores que o PROMPT enumera como possíveis — mas apenas `line` e
`asset` (os dois tipos de source com identidade estável na pipeline atual) são realmente produzidos pelo
gerador do ledger; os demais (`char`, `span`, `fragment`, `visual_region`, `caption`,
`alternative_marker`) existem para extensibilidade futura, não como capacidade fabricada sem evidência
(ver módulo docstring e `docs/generalization-contract.md` seção 1.1).

## F. Separação owner / âncora / destino

Aplicada de forma concreta nas duas correções: para Q13, o **owner** de cada linha vem exclusivamente do
`AlternativeGroup.accepted` já validado (Fase 3I) — nunca recomputado; a **âncora** é a própria posição de
leitura da linha dentro de `content_lines` (`assembler._reading_order_index`); o **destino** (`statement`
vs `alternative_text`) é derivado diretamente do owner, nunca de uma comparação geométrica independente
que poderia divergir dele. Para D60, o **owner** de cada anotação de valor é o item cujo próprio intervalo
vertical real (página + y0) a contém — nunca o vizinho mais próximo na ordem de leitura (que é exatamente
o que causava o bug: proximidade após a mistura de colunas não é evidência de posse); a **âncora** é a
posição real de cada item (não a da própria anotação); o **destino** é a posição reordenada dentro da
lista de linhas, imediatamente após seu próprio item.

## G. Duplicação: gate, provenance e mirrors autorizados

`detect_duplicate_assignments` (Seção 11) agrupa estritamente por `source_element_id` — nunca por texto
(Seção 9, testado explicitamente: `test_identical_text_from_different_sources_is_never_flagged`, duas
alternativas com o mesmo texto literal nunca são sinalizadas). Um grupo com mais de um `destination`/
`owner`/`anchor` de alternativa é reportado, a menos que todo o grupo declare o **mesmo**
`duplication_mode` não nulo (mirror autorizado, Seção 8) — testado com um caso de mirror autorizado
(`test_authorized_mirror_is_not_flagged`) e um caso de modos incompatíveis, ainda sinalizado
(`test_mismatched_mirror_modes_are_still_flagged`). O gate nunca decide qual destino é o correto — apenas
relata (Seção 11: "não corrija a duplicação apagando arbitrariamente a segunda ocorrência"). Rodado contra
o ledger real das 77 questões: **zero** duplicações encontradas.

## H. Q12/Q13 — antes, causa, correção, depois, validação

**Antes**: `enade-2008-computing-q13.md` — enunciado terminava em `"...qual opção corresponde a uma
partição desse conjunto? E	{{1, 2}, {2, 3}, {3, 4}, {4, 5}, {5, 6}}"` (texto da alternativa E colado ao
final do enunciado), e a mesma string aparecia corretamente sob `## Alternativas` como `E. {{1, 2}, {2,
3}, {3, 4}, {4, 5}, {5, 6}}` — o mesmo source span publicado em dois destinos.

**Causa** (confirmada linha a linha contra `b1_prova.pdf` página 8, via `layout.extract_page_lines`): a
alternativa E de Q13 genuinamente transborda para o topo da coluna seguinte da mesma página (não coube
abaixo de D na coluna esquerda de Q13) — sua própria posição de leitura (`extract_page_lines`, ordem
coluna-esquerda-depois-coluna-direita) é a **última** de todo o span de Q13, mesmo seu y0 bruto (142.9)
sendo menor que o de A/B/C/D (706-746) na mesma página, por estar fisicamente no topo da página, não no
fundo. `assembler.assemble_question`'s antigo corte do enunciado comparava `(página, y0)` como um proxy
para "antes da primeira alternativa em ordem de leitura" (`_position_key`) — um proxy que funciona sempre
que y0 bruto e posição de leitura andam juntos, e falha silenciosamente exatamente quando não andam (uma
linha de transbordo de coluna). O grupo de alternativas (`alternative_groups.find_alternative_group`,
Fase 3I) já classificava E corretamente — o bug nasce apenas na fatia do enunciado, não na detecção de
alternativas.

**Correção**: novo `assembler._reading_order_index(lines, target)` localiza a posição real (por
identidade de objeto, nunca por igualdade estrutural) da linha de corte dentro de `content_lines`; o
enunciado passa a ser `content_lines[:cutoff_index]` — um corte por índice de ordem de leitura, nunca por
comparação geométrica. Generaliza para toda questão, não apenas Q13: o enunciado e cada fatia de
alternativa vêm agora da mesma lista, na mesma ordem, e não podem mais se sobrepor por construção.

**Depois** (verificado por igualdade de string exata contra o PDF):
```
Considerando o conjunto A = {1, 2, 3, 4, 5, 6}, qual opção corresponde a uma partição desse conjunto?
```
Alternativa E: `{{1, 2}, {2, 3}, {3, 4}, {4, 5}, {5, 6}}` (só, sem contaminação do enunciado).

**Validação**: `tests/test_extraction_pipeline_2008.py::test_q13_statement_no_longer_duplicates_alternative_e`
(nova); regeneração completa mostra apenas Q13/D60 alterados; scan das 77 (Seção K) confirma zero outras
ocorrências dessa classe.

**Não regressão Q12**: `git diff` confirma `enade-2008-computing-q12.md` **inalterado** nesta fase (a
correção de Q13 não toca Q12 de forma alguma — Q12 fica em página/span totalmente diferente). Diagrama
presente, alternativas completas, nenhum asset duplicado, owner correto — confirmado por comparação
direta (arquivo idêntico byte a byte ao estado herdado da Fase 3H/3I).

## I. Anotações: taxonomia, candidatos e associação

`src/enade/extraction/annotations.py`: `AnnotationType` declara os 9 tipos do PROMPT (Seção 16) — apenas
`question_value` tem lógica de detecção real (`_VALUE_ANNOTATION_RE`,
`r"^\(valor:\s*[\d.,]+\s*pontos?\)$"`, case-insensitive), backed por um caso positivo real (D60, quebrado)
e vários casos negativos reais (D9/D10/D20/D39/D40/D59/D79/D80, todos já corretos). `DocumentAnnotation`
registra `owner_item_letter`/`reattached`/evidência. Candidatos de item (`_find_item_markers`) reusam a
mesma forma textual de `_ALTERNATIVE_LINE_RE` (letra maiúscula isolada + conteúdo) mas **nunca** invocam a
máquina de `alternative_groups` (conceito estruturalmente distinto: um item julgado discursivo não é uma
alternativa de múltipla escolha, mesmo compartilhando a forma). Associação: contenção geométrica de
intervalo (página + y0) contra a posição real de cada item — nunca proximidade na ordem de leitura, nunca
o texto da própria anotação além de confirmar sua própria forma (Seção 17, explicitamente testado:
`test_ordinary_prose_is_never_reordered_when_no_value_annotation_exists`).

## J. D60 — antes, causa, correção, depois, validação

**Antes**: item C terminava em `"...Justifique. (valor: 3,0 pontos)"` (valor de A, não o próprio de C),
seguido por dois parágrafos órfãos `"(valor: 3,0 pontos)"` e `"(valor: 4,0 pontos)"` no fim do enunciado.

**Causa** (confirmada via `extract_page_lines` na página 26): as três anotações `"(valor: X pontos)"` são
tipografadas em sua própria coluna estreita, à direita dos itens A/B/C e de seus próprios rótulos
"RASCUNHO" — não em linha com o texto corrido de cada item. A ordem de leitura coluna-major de
`extract_page_lines` (correta para as duas colunas reais da página) coloca essa coluna estreita **depois**
de toda outra coluna da página — as três anotações terminam juntas no fim da lista de linhas da questão,
na sua própria ordem relativa correta (A, depois B, depois C) mas geometricamente desconectadas de seus
próprios itens. `assembler._build_statement_segments`'s heurística de junção de parágrafo por gap então
computa um "gap" espúrio (negativo) entre a última linha real de C e a primeira anotação órfã, colando-as
(publicando C com o valor de A), e deixa as outras duas como parágrafos órfãos.

**Correção**: novo módulo `annotations.py`, `reattach_value_annotations` — cada anotação é realocada para
o item cujo próprio intervalo vertical real (página + y0, geometria própria de cada item, nunca
adjacência na ordem de leitura) genuinamente a contém.

**Depois** (verificado contra a página 26): item A termina em `"(valor: 3,0 pontos)"`; item B termina em
`"(valor: 3,0 pontos)"`; item C termina em seu próprio `"(valor: 4,0 pontos)"` real — batendo exatamente
com o layout visual da página (as anotações de A e B ficam logo acima de seus próprios rótulos RASCUNHO;
a de C, logo acima do seu).

**Validação**: `tests/test_annotations.py` (14 testes unitários/metamórficos);
`tests/test_extraction_pipeline_2008.py::test_d60_value_annotations_are_attached_to_their_own_item`
(nova, contra o pipeline real); `test_d60_no_longer_contaminated_by_q61_diagram` (Fase 3E, pré-existente)
continua passando sem alteração (a asserção `d60.statement.rstrip().endswith("(valor: 4,0 pontos)")`
permanece verdadeira, agora pela razão certa — C's own real value, not an orphaned line).

## K. Scan das 77 — duplicações, ausências, misattachments e novos blockers

Executado via `scripts/generate_content_assignment_ledger.py` (re-execução real e completa do pipeline
2008-b, com instrumentação somente-leitura sobre `assemble_question`, escrevendo para um diretório
temporário — nunca sobre o corpus publicado) + `content_assignment.detect_duplicate_assignments`/
`detect_missing_assignments` contra os 2280 registros resultantes:

- **Duplicações**: 0 encontradas (nenhuma linha em dois destinos, nenhuma linha em duas alternativas,
  nenhum asset — por bbox — reutilizado entre questões diferentes).
- **Ausências**: 0 encontradas (nenhum source sem destino, nenhuma anotação sem owner, nenhum asset sem
  owner dentre os registros efetivamente produzidos).
- **Nenhum novo blocker foi necessário.**

Uma verificação estática complementar (hash SHA-256 de todo asset PNG publicado em 2008-b) confirma
adicionalmente **zero grupos de hash duplicado** entre questões diferentes — reconfirmando
`owner_exclusion_gate` (Fase 3F) intacto.

**Limite honesto do scan**: cobre os tipos de source com identidade estável hoje (`line`, `asset`); não
fabrica uma checagem para `char`/`span`/`fragment`/`visual_region`/`caption`/`alternative_marker` sem
exemplo real de defeito ou de necessidade — ver Seção E.

## L. Alternative group — proteção de Q28/Q29/Q52/Q71

Confirmado por leitura direta do Markdown publicado (inalterado nesta fase): Q28 preserva as cinco
alternativas do layout horizontal/grade (`1, 1 e 2` .. `1, 1 e 1`); Q29 preserva as cinco alternativas da
questão de gramática; Q52 preserva as cinco alternativas textuais completas; Q71 preserva a fronteira B/C
corrigida na Fase 3I, sem duplicação, sem asset duplicado, sem alternativa perdida. Nenhum desses arquivos
aparece no `git status --short` desta fase.

## M. Fragment reconstruction — proteção de Q07/Q12/Q25/Q63

`fragment_reconstruction.py` não foi tocado. Q12/Q25/Q63 seguem `resolved` no blocker ledger, com o mesmo
conteúdo da Fase 3H/3I (confirmado - nenhum desses arquivos muda nesta fase). Q07 segue com sua própria
melhoria parcial da Fase 3H, categoria `region-merge-content-loss`, ainda aberta por um resíduo não
relacionado a fragmentação (não tocado nesta fase).

## N. D10 — blocker preservado

`detect_column_margins`/`wrong_column_order` não foram tocados. O ledger mostra
`d10-newspaper-collage-reading-order-scramble` ainda `open`, mesma descrição herdada; D10 segue reprovada
na auditoria visual pela mesma razão pré-existente, não relacionada a atribuição de conteúdo. Nenhum
código de `layout.py`/coluna foi modificado nesta fase.

## O. Q8/Q38/Q55 — exclusão preservada

Nenhuma tentativa de recuperação. `enade extract` continua reportando as três exclusões explícitas
("could not build a valid Question - alternative A: text is empty and no asset is set"), nunca
silenciosas. O assignment ledger não foi usado para forçar associação para essas três questões — elas
simplesmente não aparecem no ledger, porque nunca chegam a ser publicadas (`assemble_question` levanta
`ValidationError` antes que qualquer `ContentAssignment` seja produzido para elas).

## P. Source coverage

Integração parcial e honesta: o assignment ledger cobre `line` e `asset` (os únicos tipos com identidade
estável hoje) para as 77 questões publicadas; `enade audit-extraction` (schema + proveniência de
asset/hash) segue sendo o mecanismo de cobertura mais amplo e já existente (Fase 1C), rodado com sucesso
(77/77, 55/55, 40/40). Nenhum gap relevante detectado bloqueou nenhuma questão nesta fase.

## Q. Blocker ledger

Distribuição final (51 blockers totais): **33 resolved** (antes 31), **17 open** (antes 19), **1
superseded** (inalterado). `validate_ledger`: 0 issues.

| Categoria | open | resolved | superseded |
|---|---|---|---|
| alternative-boundary-misparse | 0 | 1 | 0 |
| answer-standard-absent-from-source | 2 | 0 | 0 |
| answer-standard-incomplete | 1 | 0 | 0 |
| content-duplication | 1 | 1 | 0 |
| cross-question-contamination | 0 | 3 | 0 |
| region-merge-content-loss | 6 | 22 | 1 |
| same-question-diagram-label-bleed | 1 | 0 | 0 |
| section-transition-chrome-bleed | 0 | 2 | 0 |
| table-reading-order-scramble | 3 | 3 | 0 |
| unstructured-image-alternatives | 3 | 0 | 0 |
| word_fragmentation | 0 | 1 | 0 |

Resolvidos nesta fase: `q13-duplicated-alternative-text` (categoria `content-duplication`, um outro
membro — `q23-schema-fragment-duplicate-bleed` — segue aberto, não relacionado); `d60-valor-annotation-
misattachment` (categoria `table-reading-order-scramble`, outros três membros — D10, D40, Q33 — seguem
abertos, não relacionados). A lista de categorias estruturais abertas no gold **não mudou** (ambas as
categorias têm outros membros abertos), então `enade build-gold` foi executado com exatamente as mesmas
sete categorias de antes.

## R. Gold e auditoria visual — reconciliação por ID (estado final)

Auditoria visual: **67 passed / 10 failed / 0 not_performed** (antes: 65/12). Gold: **65 verified / 12
needs_review** (antes: 63/14). A mesma divergência de 2 (D9, D59) persiste, agora entre 67 e 65 em vez de
entre 65 e 63 — exatamente como a Seção D previu (Q13/D60 saíram do grupo "visualmente reprovado" e
entraram no grupo "verified", sem afetar a divergência D9/D59, que é de uma classe de causa
completamente diferente). Nenhum status `verified` coexiste com um blocker aberto, gap de source coverage,
duplicação ou ownership inválido - confirmado.

## S. Capability registry

Quatro novas entradas em `data/manifests/extraction-capabilities.json` (18 capacidades totais, antes 14),
`runtime_ai_dependency: "none"`, `introduced_phase: "3J"`, validadas por
`tests/test_generalization_architecture.py` (9/9):

1. **`canonical_content_assignment`** (G2) — `assembler._reading_order_index`, o corte do enunciado por
   posição de leitura real em vez de comparação geométrica.
2. **`annotation_ownership`** (G2) — `annotations.reattach_value_annotations`, a reassociação geral de
   anotações a itens por contenção de intervalo geométrico.
3. **`question_value_annotation`** (G2) — o padrão textual concreto `"(valor: X pontos)"`, a única
   instância de `AnnotationType` com evidência real nesta fase.
4. **`duplicate_source_detection`** (G3, seguindo o precedente de `source_coverage_audit`) —
   `content_assignment.detect_duplicate_assignments`/`detect_missing_assignments`, uma auditoria
   independente, nunca integrada ao pipeline de extração em si.

## T. Generalização

25 testes novos (14 em `tests/test_annotations.py`, 11 em `tests/test_content_assignment.py`) mais 2 novos
testes de integração em `tests/test_extraction_pipeline_2008.py`. Metamórficos: invariância por translação
e por escala das anotações de valor, mudança de página entre itens, ordem do content stream divergente da
geometria real. Nenhum teste depende de question ID/ano/página/coordenada real do PDF. Limitação
explicitamente reconhecida: `_find_item_markers`, isoladamente, tem a mesma forma-armadilha textual já
conhecida de `alternative_groups` (uma frase começando com letra maiúscula isolada) — a segurança vem do
próprio `reattach_value_annotations` nunca sequer chamar essa função quando nenhuma anotação de valor
existe no span (verdadeiro no-op para a esmagadora maioria das questões, testado explicitamente).

## U. Runtime sem IA

`test_core_extraction_modules_import_no_network_or_llm_library` e
`test_declared_runtime_dependencies_contain_no_llm_or_network_client`: PASS. `annotations.py` e
`content_assignment.py` usam apenas geometria (`page_number`/`x0`/`y0`), `re` e `collections.defaultdict`
da stdlib — nenhuma dependência nova.

## V. Proteção de 2011/2021

Confirmado **zero drift** em cada uma das quatro rodadas de mudança de código desta fase (fix de Q13, fix
de D60, adição de `value_annotations` ao `ExtractedQuestion`, atualização do capability registry):
`git status --short data/questions/2011 data/questions/2021` vazio e `sha256sum -c` contra os 288 arquivos
protegidos com exit 0, em cada rodada. 2011 (`verify-gold`/`assess-readiness`) = `READY_FOR_LEGACY_LAYOUT_TEST`,
54/55, 1 blocker não-estrutural pré-existente (Q34). 2021 (3 cursos regenerados) = `READY_FOR_2011`, 40/40,
0 blockers.

## W. Testes e quality gates

- 589 testes existentes (fim da Fase 3I) → **616 testes** ao final desta fase (+27: 14 em
  `test_annotations.py`, 11 em `test_content_assignment.py`, 2 em `test_extraction_pipeline_2008.py`).
- `pytest -q`: 616 passed.
- `ruff check .`: All checks passed.
- `ruff format --check .`: limpo (duas correções de formatação puramente cosméticas aplicadas e
  reconfirmadas).
- `mypy src/enade`: Success, 57 source files.
- `enade validate-schema`: 13/13.
- `enade validate-manifest`: 0 warnings.
- `enade audit-extraction`: 2008 77/77, 2011 55/55, 2021 (ciencia-da-computacao-bacharelado) 40/40.
- `enade verify-gold`/`assess-readiness`:
  - 2008 (`all-computing`): `verify-gold` OK (77/77); `assess-readiness` →
    `NOT_READY_FOR_2008_ENGINEERING_TEST`, 65/77 verified, 12 needs_review, 39 blocker(s).
  - 2011 (`all-computing`): `verify-gold` OK (55/55); `assess-readiness` → `READY_FOR_LEGACY_LAYOUT_TEST`,
    54/55, 1 blocker não-estrutural.
  - 2021 (`ciencia-da-computacao-bacharelado`): `verify-gold` OK (40/40); `assess-readiness` →
    `READY_FOR_2011`, 40/40, 0 blockers.
- Gates específicos da Fase 3J: assignment ledger (2280 registros, determinístico); duplication gate (0
  achados); missing-assignment gate (0 achados); `annotation_ownership`/`question_value_annotation` (14
  testes); `canonical_content_assignment` (scan de 77, 0 achados); capability registry (9/9).

## X. Reprodutibilidade

Duas execuções completas e independentes de `enade extract --year 2008 --course all-computing` (run A,
run B), diretórios de saída isolados: `diff -rq run_a run_b` → idêntico byte a byte (exit 0). `diff -rq
run_a/all-computing data/questions/2008/all-computing` → idêntico byte a byte ao corpus publicado (exit
0). O gerador do assignment ledger também foi executado duas vezes de forma independente: saída JSON
byte a byte idêntica (`diff` exit 0), confirmando o requisito de determinismo da Seção 10.

## Y. Bugs encontrados

1. **Bug real corrigido (Q13)**: comparação geométrica `(page, y0)` usada como proxy de ordem de leitura
   no corte do enunciado — falha silenciosamente para uma linha de transbordo de coluna genuína. Corrigido
   via `assembler._reading_order_index`.
2. **Bug real corrigido (D60)**: anotações de valor tipografadas em coluna própria, reordenadas para o
   fim da lista de linhas pela ordem de leitura coluna-major, causando colagem com o item errado e
   parágrafos órfãos. Corrigido via `annotations.reattach_value_annotations`.
3. **Regressão evitada durante o desenvolvimento (não publicada)**: a primeira versão do fix de D60
   registrava um aviso (`warnings.append`) a cada reanexação bem-sucedida - `evaluate_extraction`
   (validator.py) trata **qualquer** aviso não vazio como `automatic_validation=failed`
   (`extraction_status=needs_review`), então D60 continuaria `needs_review` mesmo depois de corrigido.
   Precedente já estabelecido por `fragment_reconstruction.py` (Fase 3H): uma correção geral, determinística
   e bem evidenciada não deve, por si só, penalizar a questão — carrega seu próprio traço
   (`value_annotations: list[DocumentAnnotation]`, mesmo padrão de `fragment_merges`) em vez de um aviso
   genérico. Corrigido antes de qualquer regeneração do corpus publicado; nunca chegou a ser commitado ou
   reportado como comportamento real.
4. **Quase-incidente evitado (não publicado)**: a primeira versão de
   `scripts/generate_content_assignment_ledger.py` reconstruiu manualmente os parâmetros de
   `extract_exam` em vez de reusar a resolução real do `cli.py` - omitiu `visual_audit`,
   `answer_key_parser` (usando o parser padrão em vez de `parse_flat_item_gabarito`, exigido pelo formato
   do caderno unificado 2008-b) e `layout_overrides`, e escreveu diretamente sobre
   `data/questions` (o diretório publicado real). Uma única execução regenerou as 77 questões com
   `correct_answer=null`, `answer_validation_status=unknown` e `visual_validation=not_performed` em
   **todas** elas. Detectado imediatamente por `git status --short` (parte da disciplina padrão desta
   série de fases) antes de qualquer commit; revertido via `git checkout -- data/questions/2008`;
   corrigido reutilizando `cli._resolve_booklet_location` e escrevendo para um diretório temporário
   (`tempfile.TemporaryDirectory`), nunca mais tocando o corpus publicado. Re-executado com sucesso,
   `git status --short data/questions` vazio após a correção. Documentado aqui, não escondido, porque o
   PROMPT exige exatamente isso ("se um problema permanecer, registre-o tecnicamente").
5. Nenhum bug foi encontrado nos mecanismos protegidos (`alternative_groups.py`, `fragment_reconstruction.py`,
   `owner_exclusion_gate`) - todos permanecem exatamente como a Fase 3I os deixou.

## Z. Arquivos e Git final

Novos: `src/enade/extraction/annotations.py`, `src/enade/extraction/content_assignment.py`,
`scripts/generate_content_assignment_ledger.py`, `data/manifests/content-assignment-2008-b.json`,
`tests/test_annotations.py`, `tests/test_content_assignment.py`, `docs/phase-3j-report.md`.
Modificados: `src/enade/extraction/assembler.py` (`_reading_order_index`, integração de
`reattach_value_annotations`, campo `value_annotations` em `ExtractedQuestion`),
`tests/test_extraction_pipeline_2008.py` (2 testes novos), `data/manifests/blocker-ledger-2008.yaml`,
`data/manifests/visual-audit-2008-computing.json`, `data/manifests/extraction-capabilities.json`,
`data/manifests/gold-2008-computing.json`, `data/manifests/extraction-audit-2008-computing.{csv,json}`,
`data/questions/2008/all-computing/enade-2008-computing-q13.md`,
`data/questions/2008/all-computing/enade-2008-computing-d60.md`. Nenhum arquivo de `data/questions/2011`
ou `data/questions/2021` foi tocado. Nenhum arquivo de scratch remanescente. **Nenhum commit, push, PR,
merge ou tag foi criado.** `master` permanece intocado. Branch: `feat/enade-2008-cc-b-pilot`, HEAD ainda
em `99dee9c`.

## Recomendação

Q13 e D60 estão estabilizadas, com uma arquitetura geral (single-source-ownership no corte enunciado/
alternativas; reassociação geométrica de anotações por contenção de intervalo) que generaliza para toda a
classe de defeito, não apenas os dois casos nomeados - confirmado por um scan real e completo das 77
questões publicadas, sem nenhum outro achado. Recomenda-se:

1. **Não avançar para `wrong_column_order` de D10** nesta ou na próxima fase isoladamente - o próprio
   PROMPT desta fase excluiu isso do escopo, e a Fase 3H/3I já haviam recomendado uma fase própria e
   isolada dado o alto raio de impacto (afeta toda página de todo caderno).
2. Dos 10 casos restantes na auditoria visual, o maior cluster residual continua sendo
   `region-merge-content-loss` (6 abertos: Q02, Q05, Q07, Q24, Q45, Q54) - candidato natural para a
   próxima fase de estabilização de conteúdo, já que a maioria já tem causa raiz parcialmente
   diagnosticada nas Fases 3D/3G/3H.
3. Não recuperar Q8/Q38/Q55 antes de estabilizar as 77 publicadas - a causa raiz (associação de asset a
   alternativas quando a única região próxima é um blob grande/mesclado) continua sendo um mecanismo novo
   e de risco moderado, fora do escopo desta fase.
4. Não processar o bundle `e`. Não processar outro ano.
5. Não declarar generalização validada - G4 continua exigindo prova inédita com código congelado.
6. Expandir o assignment ledger para cobrir `2011`/`2021` apenas como uma auditoria read-only adicional
   (nunca escrevendo sobre esses corpora) se uma fase futura precisar de evidência equivalente para
   candidatar um novo defeito de duplicação/ownership nesses anos - não é necessário agora, já que nenhum
   defeito dessa classe foi reportado para 2011/2021 nesta fase.
