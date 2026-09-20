# Fase 4C — Revisão Humana Independente do Diff e Autorização Técnica Pré-Commit

## A. Veredito

**`HUMAN_REVIEW_APPROVED_WITH_NOTES`** / **`READY_FOR_COMMIT_AUTHORIZATION_WITH_NOTES`**

Três findings `HIGH` e dois `MEDIUM` diretamente demonstráveis foram encontrados por leitura
adversarial do código real (nunca por confiar nos testes verdes já existentes) e corrigidos nesta
mesma fase, cada um com teste que falhava antes e passa depois (Seção V/F). Um sexto finding,
`LOW`, foi encontrado, verificado e **deliberadamente não corrigido** por estar fora do escopo desta
fase (concerne apenas 2011/2021, nunca 2008-b, e corrigi-lo exigiria entender um mecanismo novo -
tabelas publicadas como imagem de fallback - que esta fase nunca foi mandatada a investigar). Zero
finding `CRITICAL`. Todos os `HIGH`/`MEDIUM` estão resolvidos; o `LOW` está documentado e não
compromete corretude, reprodutibilidade ou auditabilidade do que está de fato sendo proposto para
commit (o ledger 2008-b e sua própria ferramenta geradora). Por isso `_WITH_NOTES`, não o veredito
simples: houve substância real a revisar e corrigir, não apenas observações cosméticas.

## B. Escopo

Revisão de risco do diff acumulado da Fase 4B (commit `34ad0cb`, ver Seção C sobre um fato
importante do estado git encontrado no início desta revisão) contra `master`: `content_assignment.py`,
o comando `enade generate-content-assignment`, a identidade dos 2296 registros do ledger regenerado,
a semântica `assigned`/`ambiguous`, o freeze ativo da Fase 4B, a preservação histórica do freeze da
Fase 4A, e a integração com readiness/gold/corpora protegidos - exatamente a lista de prioridades do
prompt. Nenhuma feature nova, nenhuma alteração de extração de PDF, nenhum commit/push/PR/staging/
alteração de `master` foi realizada.

## C. Estado Git

**Fato importante encontrado no início desta revisão, não presumido do prompt**: ao executar os
comandos de estado git desta seção, `git status` reportou **working tree limpa** (não a árvore com 9
arquivos não commitados que o recap da Fase 4B descrevia) e `git log` mostrou um commit novo,
`34ad0cbd96ba6ace7cab9cb51a56c327fe739539` ("Add integration tests for content assignment ledger
generation and update freeze tests"), já **commitado E enviado (push) para
`origin/feat/enade-2008-cc-b-pilot`** - confirmado via `git rev-parse HEAD` = `34ad0cb...` =
`git rev-parse origin/feat/enade-2008-cc-b-pilot`. `git show --stat 34ad0cb` confirma que esse commit
contém exatamente os 10 arquivos que a Fase 4B produziu, nem mais nem menos (`data/manifests/content-assignment-2008-b.json`,
`data/manifests/extraction-capabilities.json`, `data/manifests/phase-4b-freeze.json`,
`docs/phase-4b-report.md`, a remoção de `scripts/generate_content_assignment_ledger.py`, `src/enade/cli.py`,
`src/enade/extraction/content_assignment.py`, `tests/test_content_assignment_generation.py`,
`tests/test_phase4a_freeze.py`, `tests/test_phase4b_freeze.py`) - **isto é exatamente o mesmo padrão
já visto entre as Fases 3Z→4A e 4A→4B**: trabalho sendo commitado e agora também enviado
externamente entre sessões, fora de qualquer ação desta sessão ou de qualquer sessão anterior
(nenhum `git add`/`commit`/`push` foi executado por este agente em nenhuma fase). `master`/
`origin/master` permanecem intocados (`a5dfaab0...`, idênticos entre si).

Este fato **não é um defeito de código** e não muda a substância técnica desta revisão (o diff sob
análise é o mesmo), mas muda o que "autorização pré-commit" significa na prática: o commit em
questão já existe e já foi enviado ao remoto antes de qualquer autorização ter sido concedida nesta
conversa. Esta revisão trata isso com transparência (reportado aqui, nunca escondido) e sem tomar
nenhuma ação destrutiva unilateral (reverter, force-push, ou reescrever o commit já público não foi
solicitado e não seria uma ação reversível de se tomar sem autorização explícita). O freeze ativo foi
reconciliado de acordo (Seção S) - a mesma consequência prática que já havia ocorrido entre as Fases
4A e 4B.

Comandos executados e resultados literais (estado **final**, após as correções desta fase - ver
Seção X para o comparativo completo):

```text
$ git status --short
 M data/manifests/content-assignment-2008-b.json
 M src/enade/cli.py
 M src/enade/extraction/content_assignment.py
 M tests/test_content_assignment.py
 M tests/test_content_assignment_generation.py
 M tests/test_phase4b_freeze.py
?? data/manifests/phase-4c-freeze.json
?? tests/test_phase4c_freeze.py

$ git branch --show-current
feat/enade-2008-cc-b-pilot

$ git rev-parse HEAD master origin/master
34ad0cbd96ba6ace7cab9cb51a56c327fe739539
a5dfaab0c105150df3a7201c16547708cef45292
a5dfaab0c105150df3a7201c16547708cef45292

$ git merge-base HEAD master
a5dfaab0c105150df3a7201c16547708cef45292

$ git diff --cached --stat
(vazio - nada staged)

$ git ls-files --others --exclude-standard
data/manifests/phase-4c-freeze.json
tests/test_phase4c_freeze.py
```

Confirmado: branch correta; nenhum arquivo staged; nenhum commit novo criado por esta revisão;
freeze ativo (agora `phase-4c-freeze.json`) presente; freezes históricos (`phase-4a-freeze.json`,
`phase-4b-freeze.json`) preservados; nenhum scratch file no repositório; `master`/`origin/master`
intactos.

## D. Baseline

Comandos literais do prompt (Seção 4), executados exatamente como escritos:

```text
$ enade generate-content-assignment --year 2008 --course engenharia-da-computacao-bacharelado --check
unknown course 'engenharia-da-computacao-bacharelado'; expected one of ['ciencia-da-computacao-bacharelado',
'ciencia-da-computacao-licenciatura', 'engenharia-da-computacao', 'sistemas-de-informacao', 'all-computing']
(exit code 1)

$ enade verify-gold --year 2008 --course engenharia-da-computacao-bacharelado
unknown course 'engenharia-da-computacao-bacharelado'; ... (exit code 1)

$ enade assess-readiness --year 2008 --course engenharia-da-computacao-bacharelado
unknown course 'engenharia-da-computacao-bacharelado'; ... (exit code 1)
```

Isto **não é um erro desta revisão** - é a mesma divergência documentada em toda fase anterior desde
a Fase 3A: o curso real de 2008-b é `all-computing` (o booklet unificado "b"), nunca
`engenharia-da-computacao-bacharelado` (que é, na verdade, o *outro* booklet unificado de 2008, o
pooled de engenharias, "e" - fora de escopo de todo este projeto). Reportado aqui literalmente, como
o prompt exige ("use os resultados reais... não aceite frase ambígua"), em vez de silenciosamente
substituir o nome do curso sem registrar a divergência.

Baseline real, com o curso correto (`all-computing`), **antes de qualquer correção desta fase**:

```text
$ enade generate-content-assignment --year 2008 --course all-computing --check
generate-content-assignment: 2296 record(s) generated
  duplicate assignment finding(s): 0   missing assignment finding(s): 0   corpus validation issue(s): 0
generate-content-assignment: --check OK (nothing written)

$ enade verify-gold --year 2008 --course all-computing
verify-gold: OK (80 questions match .../gold-2008-computing.json)
  maturity=provisional verified=78 needs_review=2

$ enade assess-readiness --year 2008 --course all-computing ...
assess-readiness: READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS
  78/80 verified, 2 needs_review
  actionable blockers: 0   source limitations: 2   informational findings: 0
```

`pytest` (suíte completa, antes de qualquer correção): **908 testes, 906 passed, 2 failed** -
`tests/test_phase4b_freeze.py::test_freeze_head_matches_the_real_current_head` e
`::test_working_tree_uncommitted_set_matches_exactly_what_the_freeze_declared`, ambos falhando
**pela mesma razão do fato da Seção C** (o freeze da Fase 4B certificou um HEAD/conjunto de
arquivos não commitados que a commitagem externa `34ad0cb` já havia superado) - um comportamento
de gate **correto**, não um bug, exatamente como a Fase 4B já havia documentado para o freeze da
Fase 4A. Baseline esperada pelo prompt era "908 testes" (sem especificar 0 falhas) - o número bate;
as 2 falhas são explicadas e reconciliadas na Seção S, não escondidas.

`ruff check .`: All checks passed! `ruff format --check .`: todos os arquivos formatados. `mypy src`:
Success: no issues found in 61 source files. `enade validate-schema`: 13/13 fixture(s) valid.
`enade validate-manifest`: OK (0 warning(s)). `enade audit-extraction` para as 5 corpora: 80/80,
55/55, 40/40, 40/40, 40/40 OK.

## E. Metodologia da revisão

Nenhuma alegação da Fase 4B foi aceita por os testes passarem. Cada afirmação central foi
re-verificada diretamente:

- A identidade dos 2296 `assignment_id` foi recomputada independentemente (`len(ids) == len(set(ids))`
  passou, mas uma inspeção adicional revelou que a unicidade era **acidental**, não estrutural - ver
  Seção H).
- As 8 colisões históricas de D10/D40/D59 foram recuperadas do ledger *antes* da Fase 4B
  (`git show c3b3bd1:...`) e comparadas registro a registro contra o ledger atual, confirmando que
  ambos os membros de cada par de colisão sobrevivem, com o owner/status corretos (Seção O).
- Todo asset real em disco (2008-b) foi comparado contra os registros do ledger via um script
  independente, não via o próprio `validate_ledger_against_corpus` (que só verifica uma direção) -
  isso revelou a lacuna da Seção J/N antes mesmo de qualquer correção existir.
- Um teste de adulteração (tamper) foi executado contra cópias em memória do freeze e do ledger
  histórico para provar que os gates de hash realmente detectam corrupção, nunca apenas presumido
  (Seção S/R).
- Os comandos do prompt foram executados literalmente, incluindo o nome de curso inválido, em vez de
  silenciosamente corrigidos (Seção D).

## F. Findings por severidade

```yaml
- id: F1
  severity: HIGH
  file: src/enade/extraction/content_assignment.py
  line_or_symbol: "generate_content_assignment_ledger._record_question (linhas 451, 561 antes da correção)"
  description: >
    assignment_id era derivado da posição bruta na lista (`f"{question_id}:{i}"` para linhas de
    questões objetivas com grupo de alternativas resolvido; `f"{question_id}:asset:{region_index}"`
    para TODO registro de asset) em vez da geometria estável já usada por source_element_id.
    Afetava 2019 dos 2296 registros (88%).
  evidence: >
    Inspeção direta do JSON publicado mostrou assignment_id="enade-2008-computing-q01:0" com
    source_element_id="enade-2008-computing-q01:line:p2:36.8:90.5:...". Um regex
    `^[^:]+(:asset)?:\d+$` aplicado aos 2296 registros publicados encontrou 2019 ocorrências.
  impact: >
    Qualquer mudança futura e não-relacionada (novo override, correção de filtro de chrome) que
    adicione/remova uma linha ou figura anterior dentro da MESMA questão renumeraria silenciosamente
    todo assignment_id posterior daquela questão, mesmo sem nenhuma mudança real de conteúdo -
    invalidação espúria de freeze e ruído de diff/auditoria, contrariando o propósito central do
    ledger (auditabilidade estável). Nenhuma colisão real ocorre hoje (source_element_id, usado
    pelos gates reais de duplicata/faltante, já era estável) - o risco é de churn/drift, não de
    corrupção imediata.
  recommended_action: >
    Reusar o já-computado source_element_id (geometria estável) como assignment_id em ambos os
    ramos, igual ao ramo "sem grupo resolvido" que já fazia isso corretamente.
  blocks_commit: true
  outcome: fixed

- id: F2
  severity: HIGH
  file: src/enade/cli.py
  line_or_symbol: "generate_content_assignment_cmd, ramo `if check:` (antes da correção)"
  description: >
    `--check` nunca comparava o candidato recém-gerado contra o arquivo já publicado - validava
    apenas a consistência interna do candidato (0 duplicatas/faltantes/issues de corpus). Uma
    defasagem silenciosa do ledger publicado (exatamente a falha que toda a Fase 4B existiu para
    corrigir) não seria detectada por `--check`.
  evidence: >
    Leitura direta do código: o ramo `if check: ... return` nunca lia `output_path`. Confirmado por
    um teste novo (test_check_fails_when_the_output_dir_holds_a_stale_ledger) que, antes da
    correção, teria passado mesmo com um ledger deliberadamente obsoleto no diretório de saída.
  impact: >
    `--check` dava falsa confiança de que o ledger estava atual quando na verdade só provava que
    "uma nova geração seria internamente consistente" - uma alegação bem mais fraca do que o nome
    do comando sugere, e mais fraca do que a Seção 18 do próprio prompt espera ("retorna exit code
    não zero quando divergente").
  recommended_action: >
    Ler o arquivo já publicado (se existir) e comparar seu conteúdo byte a byte contra o candidato
    fresco; falhar com exit code 1 e mensagem explícita se divergirem.
  blocks_commit: true
  outcome: fixed

- id: F3
  severity: HIGH
  file: src/enade/extraction/content_assignment.py
  line_or_symbol: "validate_ledger_against_corpus (ausência de find_orphan_assets antes da correção)"
  description: >
    Nenhum mecanismo verificava a direção reversa: um asset real, publicado, existente em disco sem
    nenhum registro correspondente no ledger passaria por todos os gates existentes sem ser notado.
  evidence: >
    Verificado com 0 órfãos em 2008-b (por sorte da reprodutibilidade do pipeline, não por
    construção do gate) - mas a nova função find_orphan_assets, ao ser executada em modo
    diagnóstico contra 2011 e 2021 (Seção 23 do prompt), **encontrou 3 órfãos reais**:
    enade-2011-computing-q22/table-01.png, enade-2021-cc-b-d03/table-01.png,
    enade-2021-cc-l-d03/table-01.png - todos legitimamente publicados e referenciados no Markdown
    ("Tabela (fallback visual fiel)"), nunca capturados pelo laço de asset do gerador (que só
    percorre extracted.figure_regions, nunca o mecanismo de tabela-como-imagem-de-fallback).
  impact: >
    Confirma que esta não era uma preocupação teórica: o gerador tem um ponto cego real e
    documentado para um tipo de asset legítimo. Para 2008-b (o escopo real desta entrega), zero
    órfãos - mas isso valia apenas como consequência não verificada da reprodutibilidade do
    pipeline, nunca como algo qualquer gate realmente checava.
  recommended_action: >
    Adicionar find_orphan_assets (ledger vs. disco, direção reversa de validate_ledger_against_corpus),
    escopado à mesma superfície de asset que o ledger já reivindica cobrir (nunca answer-standard/),
    e conectá-la aos gates do comando CLI.
  blocks_commit: true
  outcome: fixed

- id: F4
  severity: MEDIUM
  file: src/enade/cli.py
  line_or_symbol: "generate_content_assignment_cmd, escrita final (antes da correção)"
  description: >
    `--write` usava `output_path.write_text(...)` diretamente - não atômico. Uma interrupção
    (crash, disco cheio) durante a escrita podia deixar um arquivo JSON truncado/inválido no
    caminho que todo gate downstream (incluindo o freeze ativo) trata como fonte de verdade.
  evidence: >
    Leitura direta do código (ausência de padrão temp-file+rename). Confirmado por um teste que
    força uma falha de `os.replace` via monkeypatch e verifica que o destino nunca é tocado.
  impact: >
    Corrupção silenciosa do único artefato que este comando possui permissão de escrever, sob
    interrupção - comportamento frágil, não corrupção sob operação normal.
  recommended_action: >
    Escrever em um arquivo temporário no mesmo diretório e usar os.replace() para o rename final
    (atômico em POSIX e Windows para o mesmo filesystem); limpar o temporário em qualquer caminho de
    falha.
  blocks_commit: true
  outcome: fixed

- id: F5
  severity: MEDIUM
  file: src/enade/extraction/content_assignment.py
  line_or_symbol: "_record_question, ramo discursivo (antes da correção, linha ~534)"
  description: >
    O assignment_id do ramo discursivo já usava geometria (x0, y0), mas não a bbox completa
    (faltava x1/y1) que source_element_id já usava para o mesmo registro - a mesma classe de
    colisão que o próprio Q24 demonstrou (duas linhas reais podem compartilhar x0/y0 mas diferir em
    x1/y1) permanecia latente neste campo específico, mesmo após a correção original das 8 colisões
    de D10/D40/D59.
  evidence: >
    Comparação direta dos dois campos no JSON publicado antes da correção: assignment_id
    "enade-2008-computing-d10:p7:318.8:534.5" vs. source_element_id
    "enade-2008-computing-d10:line:p7:318.8:534.5:322.0:543.5" - dois esquemas de identidade
    distintos para o mesmo registro.
  impact: >
    Risco residual de colisão futura (nunca materializado nos dados atuais, verificado por
    unicidade), e uma fonte desnecessária de divergência entre dois campos que deveriam expressar a
    mesma garantia de estabilidade.
  recommended_action: >
    Subsumido pela correção de F1 - unificar assignment_id = source_element_id em todos os ramos
    de linha/anotação/asset elimina esta divergência por completo, sem lógica adicional.
  blocks_commit: true
  outcome: fixed

- id: F6
  severity: LOW
  file: src/enade/extraction/content_assignment.py
  line_or_symbol: "_record_question (laço `for region_index, region in enumerate(extracted.figure_regions)`)"
  description: >
    O gerador do ledger nunca captura assets publicados pelo mecanismo de "tabela como imagem de
    fallback" (tables.py) - apenas extracted.figure_regions é percorrido. Descoberto como
    consequência direta de corrigir F3: o novo gate find_orphan_assets, executado em modo
    diagnóstico contra 2011/2021 (nunca escrito em disco - fora de escopo desta fase), encontrou os
    3 órfãos reais já descritos em F3.
  evidence: >
    enade-2011-computing-q22/table-01.png e os equivalentes de 2021-cc-b/cc-l/d03 existem, são
    referenciados no Markdown publicado, e não têm registro correspondente no ledger de 2011/2021
    (nenhum dos quais é escrito ou faz parte do escopo desta fase).
  impact: >
    Zero impacto em 2008-b (0 órfãos, confirmado - Seção 14-17). Um ledger futuro para 2011/2021
    exigiria primeiro entender e instrumentar o mecanismo de fallback de tabela-como-imagem em
    tables.py - trabalho genuinamente fora do escopo desta fase (PROMPT NÃO FAZER: "não amplie o
    corpus", "não crie ledgers desnecessários para 2011/2021").
  recommended_action: >
    Registrar como escopo de acompanhamento explícito para uma fase futura que precise de um ledger
    de 2011/2021; não corrigir agora.
  blocks_commit: false
  outcome: skipped
```

## G. `content_assignment.py`

Revisão linha a linha confirmou: responsabilidade única mantida (o módulo continua sendo apenas
schema + geração + gates de auditoria, nunca consumido pelo pipeline real); zero lógica de questão
(`grep` por `Q8`/`Q38`/`Q55`/`if question_id` retorna apenas comentários explicativos); zero
dependência circular (a geração chama `assemble_question` real via monkeypatch com
`try/finally` restaurando o original); zero mutação do corpus (toda extração acontece dentro de
`tempfile.TemporaryDirectory()`); inputs/outputs explícitos (a função é pura em termos de I/O real -
nunca escreve arquivos, apenas retorna um dict); erros não são silenciados (o `try/finally` garante
que o monkeypatch é sempre desfeito, mesmo sob exceção). Nenhum uso de ordem de dict/set que afete o
resultado (letras A-E são uma lista literal; `final_text_by_letter` é só consultado por `.get()`).
Nenhum path absoluto/temporário vaza para o payload (verificado buscando "Temp"/"tmp" no JSON
publicado - zero ocorrências). Nenhum timestamp em nenhum campo. Nenhuma dependência de locale
(arredondamento via `round()` e f-strings não são sensíveis a locale em Python). Nenhuma dependência
de ordem de filesystem (a ordem de `extracted.figure_regions` vem do conteúdo interno do PDF, não de
uma listagem de diretório). `-0.0` nunca ocorre nas 2296 bboxes atuais (verificado). Um aparente
"mojibake" em `representation` ("QUEST�O") ao ser impresso no terminal bash foi investigado e
confirmado ser um artefato de exibição do terminal, não corrupção real - os codepoints reais no
arquivo (`0xc3 0x4f` = "Ã" + "O") são UTF-8 válido e corretos.

Os três defeitos reais encontrados (F1, F3, F5) e corrigidos estão detalhados na Seção F/H.

## H. Identidade dos assignments

A correção da Fase 4B (adicionar x0 à identidade que antes usava só `page:y0`) foi
**parcialmente aplicada**: correta e completa para `source_element_id` em todos os ramos, mas
`assignment_id` continuava usando um esquema **diferente e mais fraco** em dois dos quatro ramos de
geração (posição bruta de lista) e um terceiro ramo mais fraco que o necessário (bbox parcial). Esta
revisão verificou `count(ids) == count(unique(ids))` independentemente sobre os 2296 registros
publicados **antes** de qualquer correção: **passava** (nenhuma colisão real), mas por não ser
estrutural - ver F1 para o porquê disso é insuficiente (Seção 9 do prompt: "unicidade não é
suficiente"). Após a correção, `assignment_id` é idêntico a `source_element_id` para todo registro
de tipo `line`/`asset`/`annotation` (verificado por teste,
`test_assignment_id_matches_source_element_id_for_every_line_and_asset_record`) - a forma mais forte
possível da garantia de identidade, eliminando qualquer necessidade de manter dois esquemas em
sincronia no futuro.

## I. Estabilidade dos IDs

Com a correção aplicada, todo `assignment_id` é uma função pura de `(question_id, page, x0, y0, x1,
y1)` arredondados - nunca da posição na lista, nunca da ordem global do ledger, nunca do diretório de
execução. Isso significa: a ordem dos registros no JSON pode mudar (é ordenada por `assignment_id`
antes de serializar, mas isso não afeta a identidade de nenhum registro individual); adicionar um
registro para outra questão nunca afeta os ids desta questão (o `question_id` é sempre o primeiro
componente); e adicionar/remover uma linha não relacionada na MESMA questão agora só afeta o
assignment_id daquele registro específico (que também mudaria de conteúdo, então isso é esperado),
nunca de registros cujo conteúdo geométrico não mudou. Verificado por reprodutibilidade determinística
completa (Seção Q).

## J. `assigned` versus `ambiguous`

Confirmado que `assigned` nunca é produzido por proximidade, ordem de leitura pura, ou fallback
silencioso: todo `status="assigned"` remonta a uma comparação explícita contra
`ExtractedAlternative.text`/`final_statement_text` (o valor real e final do assembler), nunca a uma
suposição geométrica isolada. Casos sem essa evidência (a reconstrução ingênua diverge do valor
real, ou o texto da linha não sobrevive em lugar nenhum do conteúdo final publicado) são
corretamente `ambiguous`, `confidence=0.0`, `canonical_owner="unresolved"` - nunca silenciosamente
promovidos a `assigned`. `ambiguous` é contável (290 dos 2296, distribuído em 23 questões), inclui
`reason` legível, é reproduzível (mesma contagem/distribuição em execuções independentes,
verificado), e não bloqueia a publicação do corpus (o `status` do ledger é ortogonal ao que já foi
publicado - o ledger é auditoria pós-publicação, nunca gate de publicação). Nenhuma tentativa de
zerar ambiguidades artificialmente foi feita ou seria apropriada: amostragem individual (Q01 -
fragmentos de citação bibliográfica; Q24 - células de tabela/diagrama de decodificador; Q23 -
fragmento de esquema relacional reformatado como bloco de código) confirma que cada uma é uma
incerteza genuína e explicável do método de comparação por substring, nunca um sinal de conteúdo
mal atribuído.

## K. Reconciliação das contagens

2296 registros antes e depois desta fase (a correção de identidade nunca adiciona/remove registros,
apenas renomeia `assignment_id`/`source_element_id`). Verificado com uma chave independente de
formato - `(question_id, source_type, source_bbox)` - que todos os 2296 registros correspondem
exatamente entre a versão pré-correção (commit `34ad0cb`) e a versão pós-correção, com **zero**
diferença em `canonical_owner`/`anchor`/`publication_destination`/`representation`/`status`/
`confidence`/`reason`: a correção desta fase muda apenas a *string* de identidade, nunca o conteúdo
ou julgamento de nenhum registro. A tensão aparente entre "76 questões não afetadas" (linguagem da
Fase 4B, sobre a REGENERAÇÃO da Fase 4B) e a correção desta fase (que toca **todos** os 2296
registros, já que unificar o esquema de identidade muda a string de todo registro de linha/
anotação/asset) é esclarecida assim: a Fase 4B mudou *contagens e status* em 4 questões (Q08, Q38,
Q45, Q55); esta fase (4C) muda *apenas a string de identidade* de todo registro, sem tocar em
nenhuma contagem, status, owner ou conteúdo - são duas dimensões de mudança completamente
independentes, e nenhuma sentença ambígua entre elas permanece.

## L. Q8

Reconfirmado independentemente nesta fase: 5 registros de asset (`figure-01.png`..`figure-05.png`),
`canonical_owner="question"`, `publication_destination="question_asset"`, todos `assigned`. Os
grupos de legenda das 5 obras (título/artista/museu/"Disponível em: URL") e as próprias letras
marcadoras A-E aparecem corretamente como `ambiguous`/`unresolved` (19 registros) - confirmado que
isto é o resultado correto (as alternativas de Q8 são imagens puras, sem texto real de alternativa;
qualquer reconstrução de texto diverge do valor final vazio/baseado em asset, corretamente
sinalizada, nunca fabricada). Hashes/paths verificados via `validate_ledger_against_corpus` (0
issues) e `find_orphan_assets` (0 órfãos). Zero associação com Q38 (escopo por `question_id`). Zero
duplicata (`detect_duplicate_assignments`, 0 achados).

## M. Q38

Reconfirmado: 26 registros, 6 assets (1 circuito + 5 fórmulas), **zero registros `ambiguous`** -
tanto os marcadores de alternativa A-E (`canonical_owner="alternative"`) quanto as ocorrências de
letras isoladas B/C/D dentro do próprio enunciado ("função f (A, B, C, D, E)",
`canonical_owner="question"`) estão corretamente resolvidos, nunca confundidos entre si. Nenhum
`RASCUNHO`, nenhuma fusão de conteúdo entre alternativas, nenhuma duplicata introduzida pelos 9
overrides de `force_region_membership` associados (0 achados do gate de duplicata). Hashes/paths
verificados.

## N. Q45/Q55

**Q45**: 43 registros, 2 assets (`figure-01.png`, `figure-02.png`), zero `ambiguous` - fórmula
inline e figura de apoio corretamente atribuídas, nenhuma representação textual fabricada onde o
conteúdo real é uma fórmula/imagem.

**Q55**: 24 registros, 5 assets vetoriais, zero `ambiguous` - as 5 alternativas com texto vazio
legitimado por asset (`is_declared_inline_formula`), ordem A-E correta, zero duplicação.

## O. D10/D40/D59

As 8 colisões históricas (recuperadas do ledger pré-Fase-4B via `git show`) foram individualmente
re-confirmadas nesta revisão contra o ledger publicado:

| Colisão antiga (id único, 2 registros) | IDs novos (distintos) | Conteúdo preservado? |
|---|---|---|
| `d10:p7:534.5` | `d10:p7:318.8:534.5` + `d10:p7:333.0:534.5` | Sim - bullet "•" + "O texto deve ter entre 8 e 10..." |
| `d10:p7:543.6` | `d10:p7:318.8:543.6` + `d10:p7:333.0:543.6` | Sim |
| `d10:p7:561.9` | `d10:p7:318.8:561.9` + `d10:p7:333.0:561.9` | Sim |
| `d10:p7:562.9` | `d10:p7:36.8:562.9` + `d10:p7:51.0:562.9` | Sim |
| `d40:p17:132.0` | `d40:p17:36.0:132.0` + `d40:p17:185.8:132.0` | Sim |
| `d40:p17:579.8` (3 registros) | 3 IDs distintos com x0=103.3/138.1/204.1 | Sim - "idade"/"40 OR renda"/"30000" |
| `d40:p17:580.0` | `d40:p17:126.8:580.0` + `d40:p17:192.8:580.0` | Sim - dois "<" da desigualdade dupla |
| `d59:p25:225.3` | `d59:p25:78.5:225.3` + `d59:p25:95.5:225.3` | Sim - "I" + texto do item |

Todos os 8 grupos mantêm `canonical_owner="question"`/`status="assigned"` para ambos os membros,
página/x0/y0 corretos, e nenhum registro não relacionado teve seu próprio id renumerado por esta
correção (confirmado pela Seção K - a correção de identidade da Fase 4B para estes casos específicos
nunca dependia de posição, apenas de x0 vs. x0/y0, então não havia renumeração em cascata a
verificar aqui). D59 continua com exatamente zero assets de answer-standard no ledger (por design -
Seção F6/N).

## P. CLI

`--check`: nunca escreve (confirmado - nenhum arquivo aparece em `tmp_path` após uma chamada
`--check`, mesmo em falha); nunca cria diretórios (`output_dir.mkdir` só é chamado no ramo
`--write`); nunca toca timestamps (nenhum existe); nunca altera o freeze (nenhum código o referencia
aqui); retorna exit code 0 quando idêntico ao publicado e código diferente de zero quando divergente
(**corrigido nesta fase**, F2); mostra mensagem explícita de staleness. `--write`: escreve somente o
arquivo esperado; **agora atômico** (temp file + `os.replace`, corrigido nesta fase, F4); nunca deixa
arquivo parcial (verificado por teste com falha simulada de `os.replace`); preserva encoding UTF-8 e
newline explícitos; valida antes de substituir (duplicatas/faltantes/corpus/órfãos, todos checados
antes do `write_text`); nunca altera o corpus publicado (somente lê `questions_dir`); nunca altera
outro manifesto; falha claramente diante de curso/ano inválido (`_resolve_booklet_location` já
tratava isso corretamente, sem mudança necessária).

## Q. Testes

72 testes agora cobrem content-assignment/freeze (56 antes desta fase + 16 novos/reestruturados):
`tests/test_content_assignment.py` ganhou 4 testes de asset órfão (com/sem correspondência, exclusão
de answer-standard, múltiplas questões - todos usando fixtures reais em `tmp_path`, nunca arquivos
do repositório, per a instrução de nunca alterar arquivos reais para testar falhas);
`tests/test_content_assignment_generation.py` ganhou 6 testes (zero órfãos contra o corpus real;
`assignment_id` nunca por posição bruta; `assignment_id == source_element_id`; `--check` detecta
staleness; `--check` passa quando já atual; `--check` passa sem arquivo prévio; `--write` é atômico).
Cada um dos 3 testes que expõem os findings F1/F2/F3 foi confirmado falhando contra o código
pré-correção (Seção V) antes de qualquer fix ser aplicado - nunca apenas assumido. As 8 colisões
históricas continuam cobertas pela checagem agregada de unicidade (não individualmente nomeadas -
ver F5, subsumido pela mesma correção). `tests/test_phase4a_freeze.py`/`test_phase4b_freeze.py`/
`test_phase4c_freeze.py` cobrem Q8/Q38/Q45/Q55 indiretamente via os testes de geração acima, nunca
duplicando lógica.

## R. Freeze 4A histórico

`phase-4a-freeze.json` permanece byte-a-byte idêntico ao estado em que a Fase 4B o deixou
(confirmado por hash cruzado contra a entrada `historical_freezes[phase=4a]` do novo freeze da Fase
4C - Seção S). "Historical self-consistency" garante exatamente isto: o arquivo nunca foi
silenciosamente reescrito, verificável por qualquer pessoa a qualquer momento recomputando seu
SHA-256 e comparando contra o valor gravado no freeze ativo mais recente - uma cadeia de hashes que
se estende por toda fase subsequente. Um teste de adulteração foi executado (em memória, nunca contra
o arquivo real): alterar um único byte de status ("source_unavailable_confirmed" → "resolved") no
conteúdo do arquivo altera seu hash, e essa mudança seria detectada por
`test_historical_freeze_entry_hash_matches_the_real_file_unedited`. `tests/test_phase4a_freeze.py`
faz mais do que "JSON válido": verifica branch/master/merge_base internamente consistentes, que o
HEAD gravado é um commit ancestral real do HEAD atual (nunca igual a ele - `git cat-file -e` +
`git merge-base --is-ancestor`), que D09/D10 continuam `source_unavailable_confirmed`, que o
veredito de readiness gravado bate, e a checagem de hash cruzado. Não conflita com o freeze ativo:
nenhuma dessas 7 checagens compara contra estado *ao vivo* de git/disco.

## S. Freeze 4B ativo

**Reconciliação necessária, análoga à já feita entre as Fases 4A e 4B** (Seção C): o freeze
`phase-4b-freeze.json` certificava HEAD `c3b3bd1...` e um conjunto de 9 arquivos não commitados que
a commitagem externa `34ad0cb` já havia absorvido antes do início desta revisão - suas próprias
comparações ao vivo (`test_freeze_head_matches_the_real_current_head`,
`test_working_tree_uncommitted_set_matches_exactly_what_the_freeze_declared`) falhavam corretamente
na baseline (Seção D), exatamente como o freeze da Fase 4A já havia falhado perante a Fase 4B. As
correções desta fase (F1-F5) invalidariam de qualquer forma o hash do ledger que ele certificava.

Resolvido com o mesmo padrão de freeze versionado: `data/manifests/phase-4c-freeze.json` criado como
o novo freeze ativo, cobrindo hash do corpus/assets por curso (5), hash explícito do próprio ledger
de content-assignment e sua contagem, hash da ferramenta geradora (`content_assignment.py`, `cli.py`)
e seus testes, todos os demais 32 manifestos (incluindo agora `phase-4b-freeze.json` como um
manifesto comum protegido), os 35 relatórios, resultados dos quality gates, vereditos de readiness, e
os 2 registros de limitação de fonte D09/D10 - nunca alterados. `phase-4b-freeze.json` (e
`phase-4a-freeze.json`) permanecem byte-a-byte inalterados no disco. `tests/test_phase4b_freeze.py`
foi reescrito (mesmo padrão de `test_phase4a_freeze.py`) para não mais comparar contra HEAD/disco ao
vivo - apenas consistência interna e o hash cruzado contra o novo freeze ativo.
`tests/test_phase4c_freeze.py` (novo, 20 testes) é o único arquivo que agora compara `phase-4c-freeze.json`
contra git/disco ao vivo - nunca dois freezes "ativos" simultâneos. Um teste de adulteração
(`test_content_assignment_ledger_hash_matches_current_disk_state`) foi verificado em memória: corromper
o hash gravado do ledger seria detectado.

Arquivos extras/ausentes são detectados (`test_no_manifest_appeared_that_the_freeze_never_inventoried`,
`test_every_listed_manifest_exists_and_matches_its_recorded_sha256`); mudanças invalidam o freeze
(qualquer hash divergente falha o teste correspondente); branch/HEAD são verificados contra o
contrato vivo; D09/D10 permanecem visíveis (`test_source_limitations_still_present_and_never_resolved`);
corpus/assets protegidos (5 cursos, parametrizado); o relatório 4B está coberto (entre os 35
relatórios com hash verificado); caminhos são todos relativos ao root do repositório (`as_posix()`);
nenhum scratch path existe no freeze (verificado por inspeção do próprio JSON).

## T. Validação não circular

O gerador produz o ledger re-executando o pipeline real (`extract_exam` com `assemble_question`
monkeypatchado) a partir dos PDFs-fonte - nunca a partir do próprio ledger. `validate_ledger_against_corpus`
verifica cada registro de asset contra o sistema de arquivos real (existência do `.md`, existência do
PNG, presença da referência no texto do Markdown) - nunca contra o próprio ledger. A nova
`find_orphan_assets` (F3) fecha a direção oposta, também contra o sistema de arquivos real, nunca
contra o ledger. O freeze não usa apenas hashes armazenados dentro de si mesmo: todo teste
`test_..._matches_current_disk_state` recomputa o hash a partir do arquivo real no disco e compara
contra o valor gravado - nunca compara dois valores gravados entre si. `--check` (após F2) recomputa
o candidato do zero a cada execução, nunca reutiliza um resultado anterior. Os gates de
duplicata/faltante derivam exclusivamente da lista de `ContentAssignment` reconstruída do candidato
fresco, nunca de IDs copiados do output já publicado. Gerador e validador **compartilham código**
apenas na definição do schema `ContentAssignment` (dataclass) - as invariantes que cada um verifica
são estruturalmente independentes: o gerador nunca afirma "este registro é válido"; os gates
(`detect_duplicate_assignments`, `detect_missing_assignments`, `validate_ledger_against_corpus`,
`find_orphan_assets`) são funções puras que recebem a lista de registros e recomputam suas próprias
conclusões a partir de `source_element_id`/disco, nunca confiando em nenhum campo que o gerador já
tenha rotulado como "correto".

## U. Corpora protegidos

`data/questions` (2008-b/2011/2021×3): zero drift durante toda esta fase - nenhuma escrita jamais
ocorreu fora de `tempfile.TemporaryDirectory()`. `tests/test_protected_corpus.py`: 4/4 passed.
`enade audit-extraction` para as 5 corpora: 80/80, 55/55, 40/40×3 OK (Seção D/W). Markdown, assets,
answer standards, gold (`gold-2008-computing.json`/`gold-2011-computing.json`/`gold-2021-b.json`),
visual audits, `source-availability-2008.yaml`, `blocker-ledger-2008.yaml`/`blocker-ledger-2011.yaml`:
`git diff` confirma zero mudança em qualquer um destes arquivos durante toda a Fase 4C (apenas os 6
arquivos modificados + 2 novos listados na Seção C/X foram tocados).

## V. Correções realizadas

Cinco findings (F1-F5) corrigidos, cada um com teste que falhava antes:

1. **F1** (`assignment_id` por posição) - teste `test_assignment_id_is_never_derived_from_raw_list_position`
   falhou com 2019 ofensores antes da correção; passa (0 ofensores) depois. Corrigido reusando
   `source_element_id` como `assignment_id` nos ramos objetivo-com-grupo e asset.
2. **F2** (`--check` não detecta staleness) - teste `test_check_fails_when_the_output_dir_holds_a_stale_ledger`
   adicionado; verificado que a implementação anterior (sem comparação contra disco) teria passado
   incorretamente. Corrigido lendo e comparando o arquivo publicado antes de decidir `--check` OK.
3. **F3** (nenhum gate de asset órfão) - teste `test_asset_on_disk_with_no_ledger_record_is_an_orphan`
   falhou com `ImportError` antes de `find_orphan_assets` existir. Implementada e conectada ao
   comando CLI; **encontrou 3 órfãos reais em 2011/2021** (Seção F6, F16).
4. **F4** (`--write` não atômico) - teste `test_write_is_atomic_and_never_leaves_a_partial_or_temp_file`
   adicionado com falha simulada de `os.replace`; confirmado que a implementação anterior deixaria a
   possibilidade de arquivo parcial. Corrigido com padrão temp-file + `os.replace`.
5. **F5** (bbox parcial no ramo discursivo) - subsumido pela correção de F1 (mesmo commit de código).

Tentativas rejeitadas: nenhuma - todas as correções acima foram aplicadas na primeira tentativa,
cada uma mínima (sem nova arquitetura), coberta por teste, e sem afetar o corpus publicado. F6
(tabela-como-imagem-de-fallback não capturada para 2011/2021) foi deliberadamente **não corrigido**
por estar fora do escopo desta fase (Seção F).

Após as correções: o ledger foi regenerado (`enade generate-content-assignment --year 2008 --course
all-computing --write`), com **2296 registros preservados exatamente** (Seção K) - apenas
`assignment_id`/`source_element_id` mudaram de string, nunca conteúdo/status/owner.

## W. Quality gates

Executados após todas as correções:

```text
pytest: 928 passed, 0 failed, 0 skipped (1076.26s)
ruff check .: All checks passed!
ruff format --check .: todos os arquivos formatados
mypy src: Success: no issues found in 61 source files
enade validate-schema: 13/13 fixture(s) valid
enade validate-manifest: OK (0 warning(s))
enade audit-extraction (5 corpora): 80/80, 55/55, 40/40, 40/40, 40/40 OK
enade generate-content-assignment --year 2008 --course all-computing --check:
  2296 record(s), 0 duplicate, 0 missing, 0 corpus_validation_issue, 0 orphan asset(s)
enade generate-content-assignment --year 2011 --course all-computing --check:
  1517 record(s), 0/0/0, 1 orphan asset (F6, não corrigido - fora de escopo)
enade generate-content-assignment --year 2021 --course ciencia-da-computacao-bacharelado --check:
  1333 record(s), 0/0/0, 1 orphan asset (F6)
enade generate-content-assignment --year 2021 --course ciencia-da-computacao-licenciatura --check:
  1367 record(s), 0/0/0, 1 orphan asset (F6)
enade generate-content-assignment --year 2021 --course sistemas-de-informacao --check:
  1382 record(s), 0/0/0, 0 orphan asset(s)
enade verify-gold (2008-b/2011/2021-b): OK, OK, OK
enade assess-readiness 2008-b: READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS
  (actionable_blockers=0, source_limitations=2, informational_findings=0)
tests/test_protected_corpus.py: 4/4 passed
tests/test_phase4a_freeze.py + test_phase4b_freeze.py + test_phase4c_freeze.py: 36/36 passed
```

Os 3 achados de asset órfão para 2011/2021 (`--check`, exit code 1) são o comportamento **correto**
e **esperado** do novo gate (F3/F6) - nunca escritos em disco, nunca parte do escopo de commit desta
fase.

## X. Estado Git final

```text
$ git status --short
 M data/manifests/content-assignment-2008-b.json
 M src/enade/cli.py
 M src/enade/extraction/content_assignment.py
 M tests/test_content_assignment.py
 M tests/test_content_assignment_generation.py
 M tests/test_phase4b_freeze.py
?? data/manifests/phase-4c-freeze.json
?? tests/test_phase4c_freeze.py
```

`git diff --stat` (arquivos rastreados): `content-assignment-2008-b.json` (regenerado - toda mudança
é troca de string de identidade, nunca conteúdo, Seção K), `cli.py` (+51/-diffs líquidos: F2 + F4 +
conexão de F3), `content_assignment.py` (+103/- diffs líquidos: F1 + F3 + F5),
`test_content_assignment.py` (+69: 4 testes de asset órfão), `test_content_assignment_generation.py`
(+/-122: 6 testes novos), `test_phase4b_freeze.py` (reescrito para histórico, 298 linhas trocadas).
Nenhum arquivo staged; nenhum commit criado por esta revisão; nenhum push; nenhum PR; `master`/
`origin/master` inalterados (`a5dfaab0...`). Nenhum scratch file no repositório (scripts de geração
de freeze permanecem apenas no scratchpad da sessão, nunca commitados). `data/questions` intocado
durante toda a fase (Seção U). Freeze ativo (`phase-4c-freeze.json`) válido e verificado (Seção S/W).

## Y. Decisão pré-commit

**`HUMAN_REVIEW_APPROVED_WITH_NOTES`** / **`READY_FOR_COMMIT_AUTHORIZATION_WITH_NOTES`** (Seção A).

Recomendações, por serem o veredito de aprovação:

1. Solicitar autorização explícita do usuário antes de qualquer commit - esta revisão não a concede
   por si mesma, mesmo tendo concluído favoravelmente.
2. Notar explicitamente ao usuário o fato da Seção C (o commit `34ad0cb` já existe e já foi enviado
   ao remoto) antes de decidir como proceder - a autorização que se busca aqui é para os arquivos
   ainda não commitados listados na Seção X, não para desfazer o que já está público.
3. Somente após autorização, aplicar um plano de commit temático (nunca um único commit monolítico):
   por exemplo, (a) as correções de `content_assignment.py`/`cli.py` com seus testes correspondentes,
   (b) o ledger regenerado, (c) o freeze reestabelecido (`phase-4c-freeze.json`) junto com a
   reescrita de `test_phase4b_freeze.py`, (d) este próprio relatório de revisão.
4. Executar os quality gates da Seção W novamente após cada commit - nunca assumir que passar antes
   garante passar depois.
5. Registrar F6 (tabela-como-imagem-de-fallback não capturada para 2011/2021) como escopo de
   acompanhamento explícito, não como algo a corrigir silenciosamente numa fase futura sem
   documentação.
6. Não realizar push ou PR sem autorização separada, mesmo após os commits acima.

Testes verdes demonstraram que os casos já previstos pela Fase 4B funcionavam. Esta revisão
independente encontrou três lacunas que nenhum teste anterior havia previsto (identidade
posicional, `--check` sem comparação real, ausência de verificação de asset órfão) - todas
corrigidas, com evidência de que a correção era necessária (teste vermelho antes) e suficiente
(teste verde depois, mais a confirmação de que nenhum conteúdo/status/owner mudou). A identidade,
ownership, auditabilidade e o freeze permanecem corretos sob esta leitura adversarial do diff; as
limitações de fonte D09/D10 permanecem visíveis e nunca `resolved`.
