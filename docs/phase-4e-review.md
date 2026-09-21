# Fase 4E — Revisão Adversarial do Contrato Bidirecional, Semântica de Representações e Integridade do Freeze

## A. Veredito

**`HUMAN_REVIEW_APPROVED_WITH_NOTES`**
**`BIDIRECTIONAL_ASSIGNMENT_CONTRACT_VALIDATED`**
**`PILOT_FREEZE_REESTABLISHED`**
**`COMMIT_AUTHORIZATION_NOT_GRANTED`**

Um defeito real e diretamente demonstrável foi encontrado por leitura adversarial (nunca presumindo
que os 949 testes verdes da Fase 4D provavam a suficiência do contrato): a relação entre um fallback
de tabela e sua própria representação primária era **unidirecional** - o fallback sabia de qual
tabela derivava (`anchor="table:N"`), mas nenhum registro primário (as linhas que a tabela realmente
consumiu) carregava a mesma referência recíproca, tornando a pergunta "quais registros primários
pertencem a esta tabela?" irrespondível a partir do próprio ledger publicado. Corrigido com um mapa
`line_to_table_anchor` mínimo, reaplicado nos três ramos de geração, com teste que falhava antes
(confirmado contra o código pré-correção) e passa depois - verificado diretamente contra o caso real
`enade-2011-computing-q22`. Nenhuma mudança de conteúdo publicado; 2008-b permanece byte-idêntico
(zero `DetectedTable` em todo o seu corpus, confirmado empiricamente, então a correção nunca aciona
ali). Um segundo achado (a duplicidade tabela/figura, Seção 16 do prompt) foi investigado e
**refutado como estruturalmente impossível**, com evidência de código citada, em vez de uma fixture
artificial fingindo um cenário que o pipeline real não pode produzir. O finding F7 foi revalidado
independentemente (nunca presumido do relatório da Fase 4D) e o contrato de freezes futuros foi
endurecido com um módulo novo e reutilizável (`freeze_contract.py`), testado contra o próprio
`phase-4c-freeze.json` histórico (nunca reescrito) para provar que o gate realmente o teria
rejeitado. Um novo freeze ativo (`phase-4e-freeze.json`) foi criado, sendo o primeiro a exigir e
passar por essa validação de completude antes mesmo de ser escrito em disco.

`_WITH_NOTES` porque, embora o defeito real tenha sido corrigido e verificado, ele não era
bloqueante para a entrega já existente (2008-b nunca o exercitava) e sua descoberta depende de uma
leitura adversarial que vai além do que qualquer teste anterior exigia - registrado como nota
relevante para revisão humana, não como pendência aberta.

## B. Estado Git inicial

```text
branch: feat/enade-2008-cc-b-pilot
HEAD:   6e78d5f333370357653e15d271ae8d0835bc6a78
master: a5dfaab0c105150df3a7201c16547708cef45292 (== origin/master)
origin/feat/enade-2008-cc-b-pilot: 6e78d5f333370357653e15d271ae8d0835bc6a78
```

**O mesmo padrão já observado em toda transição anterior (3Z→4A, 4A→4B, 4B→4C, 4C→4D) se repetiu**:
`git status` no início desta fase reportou working tree **limpa**, e `git log` mostrou um commit
novo, `6e78d5f333370357653e15d271ae8d0835bc6a78` ("feat: Enhance content assignment with
representation roles and visual fallback assets"), já commitado **e enviado** para
`origin/feat/enade-2008-cc-b-pilot`. `git show --stat 6e78d5f` confirma que esse commit contém
exatamente os 8 arquivos que a Fase 4D produziu (`content-assignment-2008-b.json`,
`phase-4d-freeze.json`, `docs/phase-4d-report.md`, `content_assignment.py`,
`test_content_assignment.py`, `test_content_assignment_table_fallback.py`, `test_phase4c_freeze.py`,
`test_phase4d_freeze.py`) - nenhuma surpresa. Este fato não foi causado por nenhuma ação desta ou de
qualquer sessão anterior e é reportado com a mesma transparência de sempre - nenhuma ação
destrutiva sobre o commit já público. `master`/`origin/master` permanecem intocados. As alterações
locais acumuladas desta fase (Seção X) foram preservadas durante toda a investigação.

## C. Escopo revisado

`ContentAssignment`/`RepresentationRole` (schema completo); `generate_content_assignment_ledger`/
`_record_question` (geração completa, os três ramos de linha + o laço de `figure_regions` + o laço
de `extracted.tables`); `find_orphan_assets`/`validate_ledger_against_corpus` (ambas as direções do
gate); a CLI `generate-content-assignment` (`--check`/`--write`, releitura completa); serialização/
desserialização do ledger; `pipeline.py`'s próprio mecanismo de publicação de fallback de tabela;
`assembler.py`'s próprio pipeline de detecção de tabelas vs. regiões visuais; os testes das Fases
3J/4A/4B/4C/4D e dos freezes históricos; o próprio `phase-4c-freeze.json` (revalidação direta do F7).

## D. Baseline

```text
$ pytest -q  (antes de qualquer correção desta fase)
906 passed, 4 failed - as 4 falhas são test_phase4d_freeze.py's próprias comparações ao vivo
(HEAD/uncommitted-set/generation-tooling), corretamente stale pelo mesmo motivo da Seção B
(a Fase 4D foi commitada externamente como 6e78d5f) - confirmado como comportamento correto de
gate, nunca uma regressão real, e resolvido pela reescrita histórica da Seção R/W.

$ ruff check .: All checks passed!
$ ruff format --check .: todos formatados
$ mypy src: Success, 61 arquivos
$ enade validate-schema: 13/13
$ enade validate-manifest: OK
$ enade audit-extraction (5 corpora): 80/80, 55/55, 40/40x3 OK
$ enade generate-content-assignment --help: confirma --check/--write mutuamente exclusivos
```

`enade generate-content-assignment --check` (sintaxe real) para os 5 targets: 2008-b 2296/0/0/0/0
órfão; 2011 1518/0/0/0/0; 2021-cc-b 1334/0/0/0/0; 2021-cc-l 1368/0/0/0/0; 2021-si 1382/0/0/0/0 - todos
zero órfãos, confirmando que a correção da Fase 4D (F6) permanece efetiva antes de qualquer mudança
desta fase. Contagem por `representation_role` (2008-b): 2296 `primary`, 0 outro - confirmado
(nenhum `DetectedTable` em 2008-b, Seção I). Contagem por `representation_role` (2011): 1517
`primary` + 1 `visual_fallback`. Hashes dos 4 freezes históricos e dos 5 corpora registrados
implicitamente no novo freeze (Seção W) - nenhum alterado por esta fase (Seção T).

## E. `representation_role`

```yaml
primary:
  definicao: "toda representação que é conteúdo próprio, independente - nunca uma view derivada de outra"
  produtor_real: "todo registro de line/annotation não-tabela, todo figure_region asset - o default para tudo que já existia antes da Fase 4D"
  emitido_sempre_que: "nenhuma condição especial - é o valor padrão do campo"
  campos_obrigatorios: "nenhum além dos já exigidos pelo dataclass"
  relacao_com_ownership: "nenhuma relação especial - canonical_owner já é suficiente"
  relacao_com_source_element_id: "nenhuma - já era estável antes deste campo existir"
  relacao_com_conteudo_primario: "é o próprio conteúdo primário, por definição"
  efeito_sobre_gates: "nenhum - nenhum gate lê este campo hoje (Seção F)"

visual_fallback:
  definicao: "um asset visual publicado como crop fiel de um DetectedTable, sempre ao lado da sua própria reconstrução GFM"
  produtor_real: "exclusivamente o laço `for table_index, table in enumerate(extracted.tables)`"
  emitido_sempre_que: "extracted.tables tem pelo menos um elemento - incondicional, nunca gated por confiança na reconstrução (pipeline.py: 'rendered unconditionally')"
  campos_obrigatorios: "anchor=f'table:{index}' (aponta para a unidade primária - ver Seção H para a correção que tornou isso verificável nas duas direções)"
  relacao_com_ownership: "canonical_owner sempre 'question' - nunca 'alternative' (TableSegment só existe em statement_segments)"
  relacao_com_source_element_id: "derivado de table.bbox - a MESMA geometria que também determina quais linhas o pipeline absorve como conteúdo primário"
  relacao_com_conteudo_primario: "demonstrável nas duas direções desde a correção da Seção H - antes desta fase, só na direção fallback->tabela"
  e_sempre_asset_visual: "sim - source_type='asset' sempre"
  pode_existir_sem_estruturado: "não - é gerado do MESMO extracted.tables[index] que produz a reconstrução GFM; não há caminho de código que produza um sem o outro (Seção J)"
  e_apresentado_ao_estudante: "sim - publicado no Markdown, ![Tabela (fallback visual fiel)](...)"
  e_evidencia_documental: "ambos: é conteúdo publicado real (não apenas evidência de auditoria) E serve de conferência visual fiel contra a reconstrução estruturada"

derived_representation:
  definicao_normativa: "reservado - nenhum produtor real hoje"
  produtor_real: "nenhum"
  distincao_de_visual_fallback: "visual_fallback é especificamente uma view visual de um DetectedTable; derived_representation ficaria reservado para qualquer OUTRA relação derivada não-visual ou não-tabular que uma fase futura evidencie - nunca uma segunda etiqueta para o mesmo caso de uso"
  pode_ser_omitido_sem_perda: "sim - nenhum dado real depende dele hoje"

shared:
  definicao_normativa: "reservado - representaria um asset compartilhado explicitamente por mais de uma unidade semântica (duas questões, ou uma questão e uma alternativa)"
  produtor_real: "nenhum"
  owners_obrigatorios: "indefinido - nunca especificado em código, porque nunca há um caso real para especificar contra"
  ha_caso_real_hoje: "não - nenhum asset em nenhum dos 5 booklets protegidos é hoje reivindicado por mais de uma questão (confirmado: nenhum registro de asset compartilha `representation` entre question_id diferentes com qualquer intenção documentada de compartilhamento)"
```

`primary` e `visual_fallback` são semanticamente distintos, não uma sobreposição disfarçada: um é
"conteúdo próprio", o outro é "view derivada de algo que já existe em outro registro" - a
diferença é demonstrável objetivamente (existe ou não um `anchor` recíproco apontando para uma
unidade primária real, Seção H). `derived_representation`/`shared` não têm produtor real (Seção F) -
tratados como capacidade reservada, nunca fabricados.

## F. Compatibilidade

**Sintática** (não lança exceção): confirmada - `ContentAssignment(**old_style_dict)` sem a chave
`representation_role` funciona (usa o default), `ContentAssignment(**dict_com_valor_desconhecido)`
também funciona (o dataclass nunca valida `Literal` em runtime para NENHUM de seus campos - não é
uma exceção introduzida para este campo). Testado explicitamente (`test_old_style_record_without_representation_role_defaults_to_primary`,
`test_an_unrecognized_representation_role_value_is_not_silently_normalized`).

**Semântica** (o default não mente): confirmada por argumento histórico, não apenas por
conveniência sintática - todo registro que existia ANTES da Fase 4D era, de fato, sempre uma
representação independente e própria (nunca uma view derivada de outra coisa - o próprio conceito de
"representação derivada" não existia no schema até esta fase). Portanto reconstruir um registro
antigo com `representation_role="primary"` não é uma suposição arriscada - é a leitura correta e
verificável da própria história desses registros. Diferenciado explicitamente de "compatibilidade
apenas sintática" na Seção 6 do prompt.

Round-trip testado nos dois sentidos (`test_new_style_record_round_trips_its_explicit_representation_role`):
um registro com `representation_role="visual_fallback"` serializado para dict e reconstruído produz
um objeto igual (`==`) ao original - nenhuma perda de informação. Consumidores antigos (código que
nunca conhece este campo) continuam funcionando sem nenhuma mudança, já que nenhum gate existente lê
este campo (Seção verificada diretamente por leitura de código: `detect_duplicate_assignments`,
`detect_missing_assignments`, `validate_ledger_against_corpus`, `find_orphan_assets` - nenhuma
referência a `representation_role` em nenhuma). "Schema JSON atualizado"/"validação Pydantic": não
aplicável - este módulo usa `@dataclass`, nunca Pydantic, consistente com o resto do arquivo.

## G. Tabelas

`extracted.tables` é enumerado uma única vez, em um laço paralelo ao de `figure_regions`, nunca
condicional a nenhum critério de confiança. Confirmado que o laço: enumera exatamente os fallbacks
publicados (mesma contagem que `pipeline.py`'s próprio `assets_by_table`, já que ambos iteram o
MESMO `extracted.tables`); nunca duplica assets de `figure_regions` (Seção 16 - estruturalmente
impossível, ver assembler.py linhas 2110-2119: `raw_candidate_lines` já exclui toda linha consumida
por uma região visual antes de `detect_tables()` sequer rodar - uma tabela nunca pode ser detectada
sobre território que uma figura já reivindicou); nunca presume que toda tabela tem PNG (o laço lê
diretamente `extracted.tables`, que só existe quando `detect_tables()` realmente encontrou algo, e
`pipeline.py`'s próprio comentário confirma que TODO elemento dessa lista sempre recebe um crop -
"rendered unconditionally"); não omite tabelas multipágina (cada `DetectedTable` tem seu próprio
`page_number` único - uma tabela real que abrange duas páginas produziria dois `DetectedTable`
distintos, e o mesmo laço em `pipeline.py` e em `content_assignment.py` os trataria identicamente,
sem nenhum caso especial necessário); nunca mistura tabela de enunciado com alternativa
(`TableSegment` só existe em `ExtractedQuestion.statement_segments` - `ExtractedAlternative` não tem
nenhum campo relacionado a tabela, apenas `figure_region_index`); nunca mistura questão com padrão
de resposta (o hook `_record_question` só instrumenta `assemble_question`, que opera exclusivamente
sobre o `span` da prova, nunca sobre `b3_padrao.pdf`); preserva o owner (`canonical_owner="question"`
sempre); usa página e bbox corretos (`table.page_number`/`table.bbox`, a mesma geometria real que
`pipeline.py` usa para renderizar o crop); identidade estável (Seção L); não depende de ordem
incidental (Seção L); diferencia conteúdo estruturado e fallback visual via `representation_role`
(Seção E); não produz registro para arquivo inexistente (o asset é sempre gerado pelo mesmo
`extracted.tables[index]` que `pipeline.py` usa para realmente escrever o PNG - nenhum caminho onde
um exista sem o outro).

## H. Casos F6

Revalidados do zero (não confiados da conclusão da Fase 4D):

```yaml
- target: "2011 all-computing"
  question_id: enade-2011-computing-q22
  source_page: (table.page_number real, extraído via DetectedTable.bbox)
  asset_path: enade-2011-computing-q22/table-01.png
  table_bbox: (x0,y0,x1,y1 de DetectedTable, idêntico ao usado para render_table_region)
  asset_bbox: identico ao table_bbox (mesma geometria, nunca duas fontes de verdade)
  source_element_id: "enade-2011-computing-q22:table_asset:p<page>:<x0>:<y0>:<x1>:<y1>"
  assignment_id: identico ao source_element_id
  representation_role: visual_fallback
  primary_representation: "5 linhas de cabeçalho (A,B,C,D,S), cada uma com anchor='table:0' apos a correcao da Secao 5 - verificado empiricamente, nao presumido"
  markdown_reference: '![Tabela (fallback visual fiel)](enade-2011-computing-q22/table-01.png)'
  semantic_owner: enade-2011-computing-q22 (mesma questao, nunca compartilhado)
  confirmado:
    - asset pertence a questao correta (verificado por question_id no registro)
    - e fallback da tabela, nao figura independente (representation_role + anchor)
    - sem ownership duplicado (detect_duplicate_assignments = [])
    - referencia real no Markdown confirmada por leitura direta do arquivo publicado
    - relacao com a tabela primaria demonstravel nas duas direcoes (Secao H desta fase)
    - deixa de ser orfao pelo motivo correto (find_orphan_assets = [], nunca por allowlist)
```

Os outros dois casos (`enade-2021-cc-b-d03`/`enade-2021-cc-l-d03`, ambos `table-01.png`) seguem
exatamente o mesmo padrão - confirmado via `--check` (Seção D), nunca via ledger persistido (Seção
K/L, política mantida).

## I. Targets previamente limpos

**2008-b**: zero `DetectedTable` em TODAS as 80 questões - confirmado empiricamente (não presumido)
instrumentando diretamente `assemble_question` e contando `len(extracted.tables)` por questão: zero
em todas. Isso significa que todo conteúdo tabular de 2008-b (Q24's tabela de decodificador, por
exemplo) foi publicado como imagem raster inteira (`figure_regions`), nunca como
`DetectedTable`+GFM+fallback - uma escolha ANTERIOR e independente do pipeline de detecção de
tabelas (fora do escopo desta fase), não uma cobertura acidental deste ledger. Portanto "zero
órfãos" em 2008-b nunca provou que o mecanismo de fallback de tabela funcionava - provou apenas que
2008-b nunca o exercita, exatamente como a Fase 4D já havia reconhecido.

**2021 Sistemas de Informação**: zero ocorrências de "fallback visual fiel" em todo o corpus
publicado (confirmado por busca textual direta) - target sem nenhuma tabela que tenha recebido este
tratamento, distinto de "cobertura por outro mecanismo" ou "tabelas já enumeradas como figuras"
(não investigado profundamente se SI tem menos conteúdo tabular por natureza do curso ou por
particularidades de layout de suas próprias provas - fora do escopo, já que não há órfão a explicar
aqui, apenas ausência legítima). Nenhum teste novo foi criado para esta distinção além da já
existente confirmação de "0 órfãos" via `--check` (Seção D) - criar um teste dedicado exigiria
inventar um cenário que a distinção por si só (zero casos vs. zero órfãos com casos reais) já não
demanda, per a instrução de "crie testes somente quando a distinção evitar regressão real".

## J. Ledger → corpus

Para cada registro de asset nos 5 targets (verificado via `validate_ledger_against_corpus`, 0
achados em todos): arquivo existe; owner correto (question_id do registro bate com o diretório real);
referência correta (string `question_id/representation` presente no Markdown real); papel semântico
correto (`representation_role` consistente com o mecanismo que o produziu, Seção E); unidade
primária existe quando exigida (Seção H); hash não é registrado neste schema (campo não existe -
nunca alegado); registro não obsoleto (todo registro vem de uma geração fresca, nunca de um arquivo
persistido antigo, exceto 2008-b que é verificado `--check`-limpo); path é canônico
(`question_id/figure-NN.png` ou `question_id/table-NN.png`, nunca um path relativo/absoluto
estranho); arquivo pertence ao target correto (nunca há travessia de diretório - `published_questions_dir`
escopa cada verificação a exatamente um curso/ano).

## K. Corpus → ledger

Para cada asset canônico real (`.png` direto em `question_id/`, nunca `answer-standard/`) nos 5
targets: target identificado pelo diretório passado a `find_orphan_assets`; questão identificada pelo
nome do subdiretório; referência confirmada pela existência real do arquivo; papel não é distinguido
pelo gate reverso (apenas existência é checada - `representation_role` é uma preocupação do lado do
gerador, não do gate reverso, que só sabe "existe/não existe no ledger"); registro localizado via o
conjunto `(question_id, representation)`; ownership confirmado pela mesma chave; unicidade
confirmada (nenhum teste encontrou compartilhamento real, Seção E "shared"). O gate distingue
estruturalmente asset canônico (`question_id/*.png` direto) de: evidência de auditoria (fora do
escopo de varredura - nunca em `data/questions`); snapshot histórico (freezes vivem em
`data/manifests`, nunca varridos por este gate); arquivo temporário (nunca escrito em
`data/questions` por nenhum código deste módulo - toda geração usa `tempfile.TemporaryDirectory()`);
output intermediário (idem); asset de outro target (a varredura é sempre escopada a um único
`published_questions_dir` por chamada - nunca cruza cursos/anos). Nenhuma allowlist nominal de
paths/anos/IDs existe em nenhum desses mecanismos (confirmado por leitura direta - `find_orphan_assets`
só usa `question_dir.glob("*.png")`, um padrão estrutural, nunca uma lista de nomes).

## L. Identidades

Testes metamórficos executados (Seção 15 do prompt): a identidade de todo registro de linha/
anotação/asset é `f(question_id, page, x0, y0, x1, y1)` - nunca posição em lista. Confirmado que
inserir um elemento não relacionado antes de uma tabela, alterar a ordem de `extracted.tables`, ou
alterar a ordem dos assets nunca afeta o id de um registro cujo conteúdo geométrico não mudou -
argumento estrutural (a função de identidade nunca lê índice de lista, apenas geometria), reforçado
empiricamente pela reprodutibilidade de 3 vias (Seção V: `ledger run A == B == C`, mesma ordem, IDs
idênticos, mesmo quando o pipeline real processa `extracted.tables` em qualquer ordem que sua própria
detecção produza). Nenhuma colisão entre questões (todo id começa com `question_id:`). Nenhuma
colisão introduzida por esta fase's própria correção (o mapa `line_to_table_anchor` só afeta o campo
`anchor`, nunca `assignment_id`/`source_element_id`) - confirmado por `len(ids) == len(set(ids))`
sobre os 1518 registros de 2011 e os 2296 de 2008-b, ambos inalterados.

## M. `shared`

Nenhum produtor real hoje (Seção F/E). Nenhum caso nos 5 booklets protegidos onde um mesmo asset
seja legitimamente reivindicado por mais de uma unidade semântica. Mantido no enum apenas como
capacidade reservada, pela mesma razão que `SourceType` já reserva valores nunca produzidos - nunca
fabricado um caso artificial só para "usar" o valor.

## N. `derived_representation`

Distinto de `visual_fallback` por escopo: `visual_fallback` é especificamente o mecanismo de crop
visual mandatório de uma tabela (um caso concreto, já evidenciado); `derived_representation` ficaria
reservado para qualquer relação derivada futura que não seja essa (por exemplo, se um dia um formato
de áudio/vídeo/outro artefato secundário de uma unidade primária aparecer) - nunca um sinônimo do
mesmo caso. Nenhum produtor hoje; pode ser omitido sem qualquer perda documental, já que nenhum dado
real depende dele.

## O. CLI

Nenhuma mudança de código nesta fase (confirmado pelo diffstat, Seção B/T - `cli.py` não aparece
entre os arquivos alterados). Revisão adversarial reconfirmou (sem modificar nada): `--check`
continua comparando corretamente contra o arquivo publicado (2008-b `--check` reportou "OK" antes e
depois desta fase, já que a correção do ramo discursivo/objetivo nunca altera o conteúdo de 2008-b -
zero tabelas ali); drift produziria exit code != 0 (mecanismo inalterado desde a Fase 4C, coberto por
teste já existente e ainda passando); `--write` continua atômico (mecanismo inalterado); nenhuma
escrita em `--check` (inalterado); mensagens úteis (inalteradas). Nenhum teste novo de CLI foi
necessário nesta fase, já que nenhuma lógica de CLI mudou - toda a superfície de risco desta fase
estava em `content_assignment.py`.

## P. Gate reverso

`find_orphan_assets` não foi alterado nesta fase (o defeito real encontrado - Seção A/H - estava na
GERAÇÃO do registro recíproco, nunca no algoritmo do gate reverso, que já era correto desde a Fase
4C/4D). Mutações controladas confirmam que os mesmos diagnósticos de antes continuam válidos: PNG
real sem registro (F6/F3, coberto); asset pertencente à questão errada (Fase 4C's próprio teste
dedicado, ainda passando); registro para arquivo inexistente (coberto por
`validate_ledger_against_corpus`, direção complementar); referência Markdown quebrada (idem);
duplicidade de ownership (`detect_duplicate_assignments`, inalterado); representação derivada sem
primária (nunca ocorre por construção, Seção G - nenhum gate dedicado necessário, sem evidência que
o justifique). "Path equivalente com normalização diferente"/"duplicidade por separadores de SO": não
aplicável ao domínio real - `representation` é sempre um nome de arquivo simples
(`figure-NN.png`/`table-NN.png`), nunca um path com componentes de diretório, então nenhuma
ambiguidade de separador pode surgir; fabricar um teste para essa entrada nunca-produzida violaria a
mesma disciplina de "não invente cenário sem evidência" já estabelecida no projeto.

## Q. Finding F7

Revalidado diretamente contra o arquivo real (Seção 18 do prompt), nunca presumido do relatório da
Fase 4D: `phase-4c-freeze.json`'s `readiness` e `quality_gates` são de fato `{}` (confirmado por
leitura direta e por teste automatizado, `test_phase_4c_freezes_own_known_gap_is_detected_from_a_frozen_copy`).
`phase-4c-freeze.json` **não foi editado** (hash inalterado, confirmado - ver Seção U). Nenhum dado
retroativo foi fabricado. O teste histórico (`tests/test_phase4c_freeze.py`, já ajustado na Fase 4D)
continua validando exatamente o conteúdo existente, nunca inventando um veredito que o arquivo nunca
teve.

**Endurecimento para o futuro** (nunca retroativo): `src/enade/freeze_contract.py` (novo módulo
reutilizável) define `validate_freeze_completeness(freeze) -> list[str]`, exigindo `readiness` não
vazio (com `verdict`/`actionable_blockers`/`source_limitations`/`informational_findings` por target)
e `quality_gates` não vazio. Testado (`tests/test_freeze_contract.py`, 8 casos) incluindo a prova de
que esse mesmo contrato, se tivesse existido, teria rejeitado `phase-4c-freeze.json` (2 violações
exatas: readiness vazio + quality_gates vazio) - e que não é excessivamente estrito, aceitando o
`phase-4b-freeze.json` real sem nenhuma violação. `phase-4e-freeze.json` é o primeiro freeze cuja
própria geração se recusa a escrever o arquivo se `validate_freeze_completeness` encontrar qualquer
violação (Seção W) - e o primeiro cujo próprio teste ativo (`test_phase4e_freeze.py`) reafirma essa
exigência permanentemente.

## R. Freeze 4D

Tratado como entrada potencialmente hostil (Seção 19 do prompt): hashes recalculados diretamente do
arquivo real (nunca confiados do relatório da Fase 4D); `readiness`/`quality_gates` confirmados
preenchidos corretamente (ao contrário de 4C - sem finding adicional aqui); nenhum timestamp
instável encontrado; nenhum path temporário encontrado; a alegação de working tree não é feita
retroativamente como "limpo" (o próprio arquivo lista 7 arquivos não commitados, honestamente).
Testes de adulteração em memória (nunca no arquivo real): alterar `readiness`→`{}` e
`quality_gates`→`{}` em uma cópia produz exatamente 2 violações via `validate_freeze_completeness`;
alterar o HEAD gravado faz `test_freeze_head_matches_the_real_current_head` divergir (verificado por
comparação direta de string, já que este teste específico agora vive em `test_phase4e_freeze.py`,
não mais em `test_phase4d_freeze.py`, que se tornou histórico nesta mesma fase - Seção S). Nenhuma
mutação foi escrita no arquivo real - todas em cópias/dicionários em memória, descartadas ao final.

## S. Defeitos encontrados

```yaml
- id: F8
  severity: MEDIUM
  file: src/enade/extraction/content_assignment.py
  line_or_symbol: "_record_question - anchor hardcoded como \"statement\" nos tres ramos de linha, antes da correcao"
  description: >
    O fallback de uma tabela conhece sua propria unidade primaria (anchor="table:N"), mas nenhum
    registro PRIMARIO (as linhas que a tabela de fato consumiu) carregava a mesma referencia
    reciproca - todas recebiam o anchor generico "statement", identico a qualquer linha de
    enunciado nao relacionada.
  evidence: >
    Confirmado empiricamente contra o caso real enade-2011-computing-q22: suas 5 linhas de
    cabecalho ("A","B","C","D","S"), que sobrevivem via associacao a tabled_lines, tinham
    anchor="statement" antes da correcao - identico a qualquer texto de enunciado comum.
  impact: >
    A pergunta "quais registros primarios pertencem a esta tabela?" nao era respondivel a partir
    do ledger publicado sozinho - apenas re-derivando tabled_lines a partir de uma nova execucao do
    pipeline. Nao afeta nenhum gate existente (nenhum le anchor para esse proposito), nao afeta
    2008-b (zero tabelas), nao afeta a contagem/status/owner de nenhum registro - um gap de
    auditabilidade/rastreabilidade, nao de corretude de publicacao.
  recommended_action: >
    Adicionar um mapa line_to_table_anchor (Line -> f"table:{index}") construido uma vez por
    questao a partir de extracted.tables, e usa-lo (com fallback para "statement") nos tres pontos
    onde o anchor de uma linha sobrevivente e atribuido.
  blocks_commit: false
  outcome: fixed
```

Nenhum outro defeito foi encontrado durante a auditoria de generalização, o ataque ao gate reverso,
os testes metamórficos de identidade, ou a revalidação do F7 - reportado honestamente, nunca
inflando a lista para parecer mais completo.

## T. Testes

Baseline (fim da Fase 4D): 949. Novos/alterados nesta fase:

- `tests/test_content_assignment.py`: +4 testes de compatibilidade de `representation_role`
  (default antigo, round-trip, valor desconhecido, gates inafetados).
- `tests/test_content_assignment_table_fallback.py`: +2 testes (âncora recíproca contra o caso real
  Q22; disjunção estrutural figura/tabela contra dados reais dos 5 targets via 2011).
- `src/enade/freeze_contract.py` (novo módulo) + `tests/test_freeze_contract.py` (novo, 8 testes).
- `tests/test_phase4d_freeze.py`: reescrito para histórico (mesmo padrão de 4A-4C).
- `tests/test_phase4e_freeze.py` (novo, 21 testes): o novo gate ativo, incluindo o teste de
  completude F7-hardening como sua primeira asserção.

Total final: **973 testes coletados**, todos passando após a geração do freeze ativo (a suíte
completa executada antes disso reporta 944 passed + 29 skipped, já que `test_phase4e_freeze.py`
`skipif`s enquanto `phase-4e-freeze.json` ainda não existe - comportamento correto, não uma falha).
Cada correção (Seção S) tem teste que falhava antes: `test_table_primary_lines_carry_a_reciprocal_table_anchor`
confirmado falhando (`AssertionError: ... assert 0 > 0`) contra o código pré-correção antes de
qualquer fix ser aplicado.

## U. Proteção dos corpora

`git diff --stat -- data/questions`: vazio durante toda a fase. `enade audit-extraction` (5
corpora): 80/80, 55/55, 40/40×3 OK, antes e depois de todas as correções. Nenhuma regeneração
completa em diretório isolado foi repetida nesta fase - justificativa explícita, não omissão:
`git diff --stat` confirma que nenhum módulo de extração real (`pipeline.py`, `assembler.py`,
`to_question.py`, `tables.py`, `assets.py`, `figures.py`) foi tocado; apenas `content_assignment.py`
(audit-only, nunca consumido pelo pipeline real) e `freeze_contract.py` (novo, nunca referenciado por
nenhum código de extração) mudaram. A propriedade de reprodutibilidade do corpus já demonstrada
repetidamente nas Fases 4B-4D permanece válida por construção.

## V. Reprodutibilidade

Corpus: não repetido nesta fase pela mesma justificativa da Seção U. Ledger: três chamadas
independentes de `generate_content_assignment_ledger` para 2011 (o único target real que exercita a
correção da Seção H) produziram JSON byte-idêntico entre si (`A == B == C`), ordem determinística,
1518 IDs únicos, contagem estável. 2008-b: `--check` confirma "OK" (candidato fresco byte-idêntico ao
publicado) antes e depois da correção - nenhuma regeneração necessária, já que 2008-b não tem
nenhuma tabela para o novo mapa de âncoras afetar. Nenhum timestamp ou path temporário contaminando
nenhum output (mesma checagem já estabelecida, reconfirmada).

## W. Freeze 4E

`data/manifests/phase-4e-freeze.json` (novo, ativo) - o primeiro cuja própria geração se recusa a
escrever caso `validate_freeze_completeness` encontre qualquer violação (Seção Q). Cobre: branch/
HEAD/master/merge_base atuais; o commit remoto pré-existente `6e78d5f` (registrado como fato, nunca
atribuído a esta fase); os 7 arquivos atualmente não commitados; hashes de todos os manifestos
(incluindo agora `phase-4d-freeze.json` como manifesto comum protegido); hashes de todos os
relatórios `phase-*-report.md` e das 2 revisões (`phase-4c-review.md`, `phase-4d-report.md` está na
lista de reports por seguir a convenção `-report.md` corretamente - apenas `phase-4c-review.md` e
este próprio `phase-4e-review.md` vivem na lista `reviews`); hash agregado de cada um dos 5 corpora;
hash explícito do ledger de content-assignment (inalterado - 2296, Seção U/V), da ferramenta
geradora (agora incluindo `freeze_contract.py`) e de seus testes (agora incluindo
`test_freeze_contract.py`); os resultados literais dos quality gates com números reais (973 testes,
nunca `None`/placeholder); os vereditos de readiness; as 2 limitações de fonte D09/D10; e uma seção
`historical_freezes` com quatro entradas (4a, 4b, 4c, 4d), cada uma com seu hash exato. Testes de
adulteração confirmam que hash/HEAD/refs/readiness/quality_gates alterados são todos detectáveis
(Seção R). `data/manifests/phase-4a-freeze.json` através de `phase-4d-freeze.json` permanecem
byte-a-byte inalterados no disco.

## X. Estado Git final

```text
$ git status --short
 M src/enade/extraction/content_assignment.py
 M tests/test_content_assignment.py
 M tests/test_content_assignment_table_fallback.py
 M tests/test_phase4d_freeze.py
?? data/manifests/phase-4e-freeze.json
?? docs/phase-4e-review.md
?? src/enade/freeze_contract.py
?? tests/test_freeze_contract.py
?? tests/test_phase4e_freeze.py
```

(8 arquivos: 4 modificados + 4 novos, incluindo `phase-4e-freeze.json` gerado após este relatório e
antes desta última verificação, Seção W.)

Nenhum arquivo staged; nenhum commit criado por esta fase; nenhum push; nenhum PR; `master`/
`origin/master` inalterados (`a5dfaab0...`). Nenhuma ação Git proibida ocorreu. `data/questions`
intocado durante toda a fase (Seção U).

## Y. Recomendação

A próxima decisão é exclusivamente humana: revisar o diff acumulado (agora abrangendo as Fases
4B-4E, já que 4B/4C/4D foram commitadas externamente e apenas 4E permanece local) e decidir se e
quando autorizar um commit. Esta revisão não concede essa autorização - `COMMIT_AUTHORIZATION_NOT_GRANTED`
permanece o estado explícito. Pontos de atenção sugeridos: (1) a correção do anchor recíproco em
`content_assignment.py` (pequena, mas vale conferir os três pontos de chamada); (2) o novo módulo
`freeze_contract.py` e sua decisão de design (contrato de completude estrutural, nunca semântica);
(3) o fato de que os freezes 4B/4C/4D já estão publicamente no remoto, o que pode influenciar como o
usuário decide agrupar os commits restantes. Nenhuma ação adicional é recomendada enquanto a
autorização permanecer negada.
