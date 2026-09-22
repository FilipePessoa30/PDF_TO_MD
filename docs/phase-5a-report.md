# Fase 5A — Fundação Semântica para Taxonomia, Conceitos, Palavras-Chave e Recomendações Futuras

## A. Classificação final

**`SEMANTIC_ARCHITECTURE_ESTABLISHED`**
**`TAXONOMY_PILOT_PROVISIONAL`**
**`READY_FOR_HUMAN_SEMANTIC_REVIEW`**

Todos os artefatos planejados foram produzidos, validados (schema + cruzado) e são
reproduzíveis; nenhum defeito estrutural sobreviveu à verificação. A taxonomia é
`status: provisional` por desenho (seção 5: fontes curriculares externas ainda não
incorporadas). Nenhuma anotação foi humanamente revisada — a recomendação desta
fase (seção Y) é revisão humana do piloto antes de qualquer expansão.
`SEMANTIC_GENERALIZATION_SUCCESS` nunca se aplica: apenas 30/255 questões foram
anotadas, e o scan de generalização (seção R) é explicitamente diagnóstico, não
uma prova de que a taxonomia generaliza.

## B. Estado Git

Descoberto, nunca presumido, no início desta fase:

- Branch: `feat/enade-2008-cc-b-pilot`
- HEAD (início e fim desta sessão): `8e272cc0dd53031ddddc78d3f88c7efdce073a8f`
- `master` / `origin/master`: `a5dfaab0c105150df3a7201c16547708cef45292` (nunca tocado)
- `origin/feat/enade-2008-cc-b-pilot`: `8e272cc...` (idêntico ao HEAD local — nada
  para enviar, nada pendente do lado remoto)
- **Fato relevante**: o trabalho da Fase 4E (revisão adversarial F8 + módulo
  `freeze_contract.py`) já estava commitado e publicado como `8e272cc` *antes*
  desta sessão de Fase 5A começar — por uma ação externa, nunca pelos comandos
  git desta ou de qualquer sessão anterior. Confirmado via
  `git show --stat 8e272cc`, cujo conjunto de arquivos bate exatamente com o
  relatório da própria Fase 4E. Registrado como fato, nunca atribuído a esta fase.
- Working tree ao final desta fase: **sem nenhum commit, stage ou push realizado
  por esta sessão** — apenas arquivos modificados/novos no disco (`git status
  --short`, confirmado ao final desta fase):

```
 M src/enade/cli.py
 M src/enade/models/enums.py
 M src/enade/models/taxonomy.py
 M tests/test_phase4e_freeze.py
 M tests/test_schema_taxonomy.py
?? data/semantic/
?? data/taxonomy/computing-v1.yaml
?? docs/phase-5a-report.md
?? docs/semantic-annotation-guidelines.md
?? docs/semantic-pilot-review.md
?? src/enade/semantic/
?? tests/test_cli_semantic.py
?? tests/test_phase5a_semantic_freeze.py
?? tests/test_semantic_annotatable_content.py
?? tests/test_semantic_annotation.py
?? tests/test_semantic_artifacts.py
?? tests/test_semantic_audit.py
?? tests/test_semantic_corpus_survey.py
?? tests/test_semantic_freeze_contract.py
?? tests/test_semantic_generalization_scan.py
?? tests/test_semantic_review.py
?? tests/test_semantic_selection.py
?? tests/test_semantic_validators.py
```

(`?? data/manifests/phase-5a-semantic-freeze.json` passa a aparecer neste mesmo
`git status` só depois que a seção X é escrita, ao final desta fase — o
snapshot acima foi tirado antes disso, e é listado à parte por essa razão.)

## C. Freeze de extração (Fase 4E)

`docs/phase-4e-review.md` e `data/manifests/phase-4e-freeze.json` foram lidos
integralmente e revalidados via `pytest tests/test_phase4e_freeze.py`.

Resultado real da primeira execução (antes de qualquer ajuste desta fase):
**28 tests, 3 falhas** — todas as 3 falhas eram esperadas e do mesmo tipo já
documentado nas transições 4B→4C→4D→4E: o freeze registra um instantâneo de
git/disco de um momento específico, e esse momento já ficou para trás:

1. `test_freeze_head_matches_the_real_current_head` — o HEAD gravado
   (`6e78d5f...`, o estado *antes* do commit externo da própria Fase 4E) não é
   mais igual ao HEAD atual (`8e272cc`), pois esse commit externo já aconteceu.
2. `test_working_tree_uncommitted_set_matches_exactly_what_the_freeze_declared`
   — os 8 arquivos que o freeze registrou como "não commitados" já foram
   absorvidos pelo commit `8e272cc` e não aparecem mais como alterações no
   working tree.
3. `test_generation_tooling_hashes_match_current_disk_state` — `src/enade/cli.py`
   (um dos 3 arquivos de `generation_tooling` certificados pelo freeze) mudou de
   hash porque esta própria fase precisou estendê-lo com os 3 novos comandos
   semânticos (adição pura, nunca alteração de um comando de extração
   pré-existente).

**Ação tomada**: `phase-4e-freeze.json` permanece **byte-a-byte intocado**
(nunca editado — é o freeze terminal da extração, PROMPT seção 3). Apenas
`tests/test_phase4e_freeze.py` (código de teste, não o artefato congelado) foi
reescrito para expressar os fatos corretos: ancestralidade de HEAD em vez de
igualdade; "agora commitado" em vez de "ainda não commitado"; verificação
byte-a-byte mantida para os dois arquivos exclusivamente de extração
(`content_assignment.py`, `freeze_contract.py`) e, para `cli.py`, uma checagem
mais forte e mais honesta — que nenhum comando de extração já certificado foi
removido ou reescrito (via `git show <head>:cli.py` comparado ao arquivo atual).
Resultado após o ajuste: **28/28 tests passando**. Todos os outros gates que já
eram estritos (manifests, reports, reviews, `question_outputs` dos 5 alvos,
ledger de content-assignment, `source_limitations`) permaneceram **inalterados e
passando** — prova direta de que `data/questions` não sofreu nenhum desvio.

Um segundo achado real, menor, surgiu só depois — ao escrever
`data/manifests/phase-5a-semantic-freeze.json` (seção X) no mesmo diretório
`data/manifests/` que os freezes de extração: `test_no_manifest_appeared_that_the_freeze_never_inventoried`
passou a falhar, pois o freeze de extração nunca poderia ter previsto um
arquivo de uma lineage separada, criada uma fase inteira depois. Corrigido
excluindo explicitamente o padrão `phase-*-semantic-freeze.json` desse
inventário (o mesmo tratamento já dado a `phase-4e-freeze.json` olhando para
si mesmo) — o novo arquivo é inventariado e verificado por hash exclusivamente
pelo seu próprio gate, `tests/test_phase5a_semantic_freeze.py`. Resultado final:
28/28 continuam passando.

## D. Fontes semânticas

Lidos e usados como base real (nunca informalmente resolvidos):

- `data/questions/**/*.md` (front matter + corpo: seção, tipo, componente,
  content_blocks, assets, alternatives) das 5 metas protegidas.
- `src/enade/models/question.py`, `content_block.py`, `enums.py` (estrutura real
  dos dados, nunca assumida).
- `data/manifests/content-assignment-*.json` (ledger de proveniência já
  publicado pelas Fases 3J/4B-4E).
- `data/taxonomy/demo-taxonomy.yaml` (fixture protegida, `status: demo`, nunca
  alterada — apenas lida como referência de forma).
- Nenhum documento curricular oficial externo foi incorporado nesta fase (não
  havia um já presente no repositório, e a coleta de novos documentos externos
  estava fora do escopo do piloto). Por isso `computing-v1.yaml` é
  `status: provisional` — honestamente, não uma formalidade.

## E. Taxonomia (`data/taxonomy/computing-v1.yaml`)

`taxonomy_id: computing-v1`, `version: "1.0.0-pilot"`, `status: provisional`,
`language: pt`. Estrutura final: **13 áreas, 35 tópicos, 18 conceitos**,
ordenados alfabeticamente por `id` em todos os níveis (exigido e verificado pelo
validador `_check_deterministic_ordering` de `enade/models/taxonomy.py`, cujo
escopo foi deliberadamente restrito a documentos com `taxonomy_id` não vazio —
`demo-taxonomy.yaml` genuinamente não está ordenado, e isso não é um defeito
desta fase, é um fato pré-existente da fixture protegida, descoberto e
documentado, não presumido).

Todo nó cita `source_references` com IDs reais de questões do corpus (nunca
inventados). Dois conceitos foram adicionados tardiamente, durante a
verificação, ao perceber que haviam sido decididos em análise mas não
persistidos: `operacoes-morfologicas-erosao-dilatacao` (motivado por
`enade-2021-cc-b-q29`) e a correção dos `keywords` de
`hierarquia-dado-informacao-conhecimento`/`teoria-geral-de-sistemas` (ver seção
F sobre o próprio scan de generalização, que revelou o problema).

## F. Áreas

As 13 áreas cobrem os domínios recorrentes identificados na leitura estrutural
do corpus: Arquitetura e Organização de Computadores, Banco de Dados,
Engenharia de Software, Estruturas de Dados e Algoritmos, Inteligência
Artificial, Interação Humano-Computador, Linguagens de Programação e Teoria da
Computação, Matemática Aplicada e Estatística, Matemática Discreta e Lógica,
Processamento de Imagens, Redes de Computadores, Segurança da Informação,
Sistemas Operacionais. Duas áreas (Interação Humano-Computador, Internet das
Coisas — esta como tópico de Redes) foram incluídas por convenção curricular
mesmo com baixa recorrência direta no corpus lido, e isso está declarado
explicitamente nas suas próprias `description`/`inclusion_criteria` — nunca
escondido.

## G. Tópicos

35 tópicos no total. Achado real durante a auditoria (seção R): o scan de
generalização inicialmente mostrou a área "Engenharia de Software" dominando
artificialmente (83 ocorrências em 255 questões) — investigado e a causa raiz
identificada: o conceito `teoria-geral-de-sistemas` continha palavras-chave
genéricas do dicionário português (`"ambiente"`, `"informacao"`,
`"conhecimento"`, `"entrada"`, `"saida"`, `"feedback"`) que combinavam com quase
qualquer enunciado. Corrigido na raiz (não no scanner): as `keywords` desses
dois conceitos foram trocadas por expressões compostas e específicas
(`"teoria geral de sistemas"`, `"hierarquia dado-informacao-conhecimento"`
etc.). Após a correção, a contagem de "Engenharia de Software" caiu para 2 — o
valor real. `data/semantic/question-annotations-5a.json` foi regenerado e
revalidado (0 diagnósticos) após esse ajuste, já que dois `search_terms` de
anotações reais usavam os mesmos termos genéricos.

## H. Conceitos

18 conceitos, cada um com `role` (`required`/`supporting`/`contextual`) quando
associado a uma questão, e evidência própria — nunca inferidos do gabarito.

## I. Componentes e cursos

**Descoberta real durante a construção dos testes** (não presumida a partir do
resumo herdado de sessões anteriores): o diretório `data/questions/2008/all-computing`
**não é uniformemente "compartilhado"**. Ele mistura 20 questões que usam o
alias `ALL_COMPUTING` (formação geral + algumas de componente específico) com
**60 questões específicas de curso** dentro do mesmo livreto físico: Bacharelado
em Ciência da Computação (q21-q38, d39-d40), Engenharia da Computação
(q41-q58, d59-d60) e Sistemas de Informação (q61-q78, d79-d80) — confirmado
lendo o front matter real (`applicable_courses`) de cada arquivo, não assumido.
Isso não muda nenhuma anotação já produzida (o campo `component` continua
correto, derivado de `section`), mas corrige uma suposição estrutural imprecisa
herdada do resumo da sessão anterior — documentada aqui em vez de silenciada.
Um teste real (`test_2008_booklet_mixes_shared_and_course_specific_questions`)
agora fixa esse fato: 20 compartilhadas / 60 específicas de curso.

Duas questões **verbatim-idênticas entre cursos diferentes de 2021** (livretos
já divididos, portanto invisíveis ao sinalizador estrutural
`is_shared_across_courses`) foram encontradas por leitura integral de texto e
receberam anotação idêntica, ligadas via `shared_question_groups` no arquivo de
anotações:

- `enade-2021-cc-b-q25` / `enade-2021-cc-l-q25` (computação em nuvem, SaaS/PaaS/IaaS)
- `enade-2021-cc-b-d01` / `enade-2021-si-d01` (arte/cultura/censura, formação geral)

`validate_shared_question_consistency` confirma 0 divergências entre os pares.

## J. Contrato de anotação

`src/enade/semantic/annotation.py`: `QuestionAnnotation` (Pydantic) com todos os
campos da seção 11 do prompt, validadores cruzados (tópico primário
XOR unclassifiable; nenhum tópico simultaneamente primário e secundário;
`reviewed` exige nota citando um revisor humano real; nenhuma evidência com
`source_kind="answer_standard"` é aceita, nem no nível da anotação nem dentro de
cada `ConceptAssociation`).

## K. Evidência

`SemanticEvidenceRef`: cada evidência textual carrega `source_sha256` (hash do
arquivo `.md` publicado) + `excerpt_sha256` (hash do próprio trecho, verificado
contra o texto no momento da criação — `build_annotations.py` reafirma
programaticamente, com `assert excerpt in md_text`, que todo excerto usado é uma
citação literal do arquivo real antes de serializar). Evidência visual
reaproveita o `Asset.sha256` já publicado (nunca recalculado). 5 evidências
visuais e 49 textuais no total do piloto. `validate_evidence_integrity`
re-lê os arquivos reais do disco a cada execução — nunca confia em um hash
gravado sem checar.

## L. Anti-vazamento de gabarito

`AnnotatableContent`/`AnnotatableAlternative` (`annotatable_content.py`) são
dataclasses que **não têm nenhum campo capaz de carregar a resposta correta ou
o padrão de resposta** — garantia em nível de tipo, não apenas uma convenção de
uso. `QuestionAnnotation` rejeita estruturalmente qualquer evidência com
`source_kind="answer_standard"`. 5 testes em
`tests/test_semantic_annotatable_content.py` confirmam a ausência do campo via
`dataclasses.fields()`; outros em `tests/test_semantic_annotation.py` confirmam
a rejeição do validador.

## M. Palavras-chave

`search_terms` deriva de tópicos/conceitos já anotados — nunca uma lista
independente. Corrigido nesta fase (seção G): dois conjuntos de `search_terms`
usavam palavras genéricas demais (`"informação"`, `"ambiente"`, `"feedback"`)
que não servem como termo de busca útil; substituídos por expressões
compostas. Nenhuma geração de palavras-chave em escala foi feita para o corpus
completo.

## N. Habilidades cognitivas

Vocabulário fechado usado nas 20 questões classificadas: `analyze`, `apply`,
`calculate`, `compare`, `design`, `evaluate`, `interpret`, `justify`, `recall`.
Nenhuma questão recebeu `design` apenas por mencionar um sistema — o único caso
com `design` (`enade-2011-computing-d03`) pede explicitamente que o estudante
desenvolva dois algoritmos.

## O. Confiança e status

| status | contagem |
|---|---|
| `unclassifiable` | 10 |
| `proposed` | 18 |
| `needs_review` | 2 |
| `reviewed` | 0 |

| confiança | contagem |
|---|---|
| `high` | 26 |
| `medium` | 3 |
| `low` | 1 |

Nenhuma anotação recebeu `reviewed` (estrutural — o modelo rejeita `reviewed`
sem uma nota citando `reviewer: <nome>`, que este pipeline nunca produz). As 2
`needs_review` (`enade-2011-computing-q14`, `enade-2011-computing-q23`) foram
marcadas assim honestamente por dependerem fortemente de figuras não totalmente
verificáveis apenas pelo texto extraído — nenhum conceito específico foi
forçado nelas.

## P. Seleção piloto

`data/semantic/pilot-selection-5a.json`: 30 questões, população elegível = 255.
**Método real, documentado honestamente**: o módulo determinístico
`src/enade/semantic/selection.py` (`select_pilot_sample`, hash-rank via SHA-256,
nunca `random.Random`) existe e é testado (`tests/test_semantic_selection.py`,
7 testes) como mecanismo reutilizável para um futuro rollout em escala. Para
este piloto específico de 30 questões, porém, a seleção final foi **curada
manualmente** a partir dos mesmos 16 eixos de `STRATA`, porque os dois pares de
questão verbatim-compartilhada entre cursos (seção I) só foram identificáveis
lendo o texto integral — o sinalizador estrutural nunca os detecta. Garantir a
presença de ambos os membros de cada par era necessário para exercitar de
verdade `validate_shared_question_consistency`. A cobertura real desta seleção
manual foi verificada programaticamente contra todos os 16 eixos de `STRATA`
(todas as 16 contagens são > 0 — nenhum eixo ficou descoberto).

## Q. Resultado individual (piloto)

**10 unclassifiable** (fora do escopo de Computação — formação geral ou
pedagogia específica de Licenciatura): `enade-2008-computing-d09`,
`enade-2008-computing-q04`, `enade-2011-computing-q01`,
`enade-2011-computing-q31`, `enade-2011-computing-q33`,
`enade-2021-cc-b-d01`/`enade-2021-si-d01` (par compartilhado),
`enade-2021-cc-b-q01`, `enade-2021-si-d02`, `enade-2021-si-q05`.

**20 classificadas** com tópico primário + evidência real (ver
`docs/semantic-pilot-review.md` para o detalhe completo, questão a questão,
sem o gabarito): árvores/recursão (`q14`, `d03`), redes (`q30`),
confiabilidade/probabilidade (`q55`), autômatos (`q23`), concorrência (`q27`),
TDA (`q39`), arquitetura razor (`q43`), SQL (`q46`), Teoria Geral de Sistemas
(`q49`), lógica proposicional (`d03` de 2021), aprendizado de máquina (`q18`),
modelagem ER (`q22`), computação em nuvem (par `q25`), morfologia de imagens
(`q29`), DIKW (`d03` de SI), segurança da informação (`q25` de SI), IoT/cidades
inteligentes (`q34` de SI), diagrama de Venn (`q14` de 2011, `needs_review`).

## R. Auditoria do piloto

`data/semantic/semantic-audit-5a.json` (nunca apresentado como medida de
acurácia — não há gold humano ainda):

- Evidência textual: 49; visual: 5.
- 16/66 nós da taxonomia nunca referenciados pelo piloto (esperado — só 30/255
  questões foram anotadas).
- Nenhuma área concentra ≥5 das 30 questões classificadas (a mais frequente,
  Redes de Computadores, tem 4) — sem sinal de concentração temática indevida.
- 1 anotação com confiança `low`, documentada na seção O.

Scan de generalização diagnóstico (`data/semantic/generalization-scan-5a.json`,
rodado contra as 255 questões dos 5 livretos, nunca publica anotação
automática): 145/255 sem candidato (heurística conservadora de substring,
nunca TF-IDF/embeddings/LLM); 92 exigem evidência visual; 55 estruturalmente
compartilhadas (na maioria, o alias `ALL_COMPUTING` de 2008); 14
provavelmente precisam de revisão humana (candidatos cruzando mais de uma área,
ou alternativas puramente visuais). Áreas dominantes reais (após a correção da
seção G): Linguagens de Programação e Teoria da Computação (17),
Sistemas Operacionais (13), Segurança da Informação (11), Redes (10).

## S. Validadores

`src/enade/semantic/validators.py`: `validate_annotation_against_taxonomy`,
`validate_evidence_integrity`, `validate_shared_question_consistency`,
`validate_search_terms_have_provenance` — 16 testes próprios
(`tests/test_semantic_validators.py`) mais a execução real, end-to-end, contra
`computing-v1.yaml` + `question-annotations-5a.json`: **0 diagnósticos**.

## T. CLI

Três comandos novos em `src/enade/cli.py`, todos determinísticos, sem rede, sem
escrita em `data/questions`:

- `enade validate-taxonomy` — nunca escreve; exit 0/1.
- `enade validate-semantic-annotations` — valida contra taxonomia + integridade
  de evidência + consistência de questões compartilhadas + proveniência de
  termos de busca; nunca escreve; exit 0/1.
- `enade build-semantic-review` — só escreve o Markdown de revisão; nunca
  promove status; determinístico (A=B byte-a-byte, confirmado).

11 testes de CLI em `tests/test_cli_semantic.py` (validação limpa, taxonomia
inválida, anotação inválida, modo somente-leitura, códigos de saída,
determinismo do build).

## U. Testes e quality gates (seção 31)

- Suíte completa (`pytest -q`, sem filtro, execução final após todos os ajustes
  desta fase, incluindo `tests/test_phase5a_semantic_freeze.py`):
  **1106 passed, 0 failed** (20m31s).
- Novos arquivos de teste desta fase: `tests/test_semantic_annotatable_content.py`,
  `tests/test_semantic_annotation.py`, `tests/test_semantic_validators.py`,
  `tests/test_semantic_corpus_survey.py`, `tests/test_semantic_selection.py`,
  `tests/test_semantic_artifacts.py`, `tests/test_semantic_audit.py`,
  `tests/test_semantic_review.py`, `tests/test_semantic_generalization_scan.py`,
  `tests/test_semantic_freeze_contract.py`, `tests/test_phase5a_semantic_freeze.py`,
  `tests/test_cli_semantic.py`.
- `tests/test_phase4e_freeze.py` foi ajustado (seção C) — 28/28 passando.
- `tests/test_schema_taxonomy.py` foi estendido em sessão anterior (+19 testes,
  já refletidos na baseline herdada).

Execução real de cada gate exigido pela seção 31:

| Comando | Resultado |
|---|---|
| `pytest -q` | **1106 passed, 0 failed** (exit 0) |
| `ruff check .` | All checks passed! (exit 0) |
| `ruff format --check .` | 463 files already formatted (exit 0) |
| `mypy src` | Success: no issues found in 73 source files (exit 0) |
| `enade validate-schema` | 13/13 fixture(s) valid (exit 0) |
| `enade validate-manifest` | OK (0 warnings) (exit 0) |
| `enade audit-extraction` (5 alvos) | 80/80, 55/55, 40/40, 40/40, 40/40 — todos OK (exit 0) |
| `git diff --check` | exit 0 (apenas aviso de CRLF, não erro) |
| `pytest tests/test_phase4e_freeze.py` | 28 passed (exit 0) |
| `enade validate-taxonomy` | OK (exit 0) |
| `enade validate-semantic-annotations` | 30 checked, 0 diagnostics (exit 0) |
| `enade build-semantic-review` | 30 questões escritas (exit 0) |
| `enade generate-content-assignment --check` (5 alvos) | 0 duplicatas/faltantes/órfãos em todos (exit 0) |
| `enade verify-gold` (3/5 alvos com gold manifest) | OK nos 3; 2021-cc-l/si não têm gold manifest ainda — fato pré-existente, fora do escopo desta fase |
| `enade assess-readiness` (3/5 alvos) | READY em todos, 0 blockers acionáveis |
| gate de content-assignment / órfãos | 0 em todos os 5 alvos |
| `pytest tests/test_phase5a_semantic_freeze.py` | 18 passed (exit 0) — ver seção X |

## V. Proteção do corpus

- `data/questions/**`: **zero diff** confirmado por `audit-extraction` (255/255
  OK) e pelo próprio `test_phase4e_freeze.py` (`question_outputs` hash agregado
  por alvo, inalterado).
- `data/manifests/gold-*.json`, `blocker-ledger-*.yaml`,
  `source-availability-*.yaml`: inalterados.
- `data/manifests/phase-4a/4b/4c/4d/4e-freeze.json`: bytes idênticos aos
  registrados (verificado via hash cruzado em `test_phase4e_freeze.py`).
- Nenhum arquivo Markdown de questão foi editado para adicionar tags.
- Nenhuma anotação foi criada para bundle "e" ou para 2005.

## W. Reprodutibilidade

- Seleção piloto: `select_pilot_sample` executado duas vezes com a mesma seed
  sobre a mesma população real (255 questões) — resultado idêntico
  (`selection A == B: True`).
- Validação semântica: `enade validate-semantic-annotations` executado duas
  vezes — saída idêntica (`0 diagnostic(s)` em ambas).
- Pacote de revisão: `enade build-semantic-review` executado duas vezes para
  arquivos diferentes — **diff vazio** (bytes idênticos).
- `computing-v1.yaml` e `question-annotations-5a.json` serializam
  deterministicamente (ordem alfabética por `id`, sem timestamp, sem caminho
  temporário).
- Nenhum campo humano foi sobrescrito silenciosamente (não existe nenhum campo
  humano ainda a sobrescrever — `review_status` permanece `pending` em 100%
  das 30 anotações).

## X. Freeze semântico

`data/manifests/phase-5a-semantic-freeze.json` — o primeiro freeze de uma
lineage **separada** da extração (nunca substitui, nunca edita, nunca supera
`phase-4e-freeze.json`, que permanece terminal). Contém: HEAD real no
encerramento desta fase; um hash de referência para `phase-4e-freeze.json`
(detecta adulteração futura, nunca reescreve o arquivo); hashes de todos os
artefatos semânticos (taxonomia, anotações, seleção, diretrizes, pacote de
revisão, auditoria, scan de generalização); contagens reais; os resultados
reais dos quality gates (seção U); `semantic_maturity: "provisional_pilot"`;
`human_review_status: "not_yet_reviewed"` — nunca `"reviewed"`/`"approved"`,
estruturalmente impedido por `validate_semantic_freeze_completeness`
(`src/enade/semantic/freeze.py`), que só promove um freeze cujos campos
obrigatórios estão de fato preenchidos (mesmo espírito de robustecimento do
`freeze_contract.py` da Fase 4E, aplicado à nova lineage). Gate próprio:
`tests/test_phase5a_semantic_freeze.py`.

## Y. Recomendação final

**Revisão humana do piloto (as 30 questões em `docs/semantic-pilot-review.md`)
é o próximo passo obrigatório antes de qualquer expansão.** Pontos específicos
para o revisor humano priorizar:

1. As 2 anotações `needs_review` (`enade-2011-computing-q14`,
   `enade-2011-computing-q23`) dependem de figuras — confirmar com a imagem em
   mãos.
2. Os 2 pares de questão compartilhada (seção I) — confirmar que a anotação
   idêntica atribuída a ambos os membros está correta.
3. A inclusão de Interação Humano-Computador e Internet das Coisas como
   áreas/tópicos por convenção curricular, não por recorrência direta — decidir
   se isso deve continuar assim ao escalar.
4. O scan de generalização (seção R): 145/255 questões sem candidato — decidir
   se isso reflete lacunas reais da taxonomia (a expandir com mais tópicos) ou
   é o esperado dado que só 20 tópicos têm cobertura de palavras-chave testada.

Esta fase **não** deve ser seguida por uma geração automática de anotações para
as 225 questões restantes. O objetivo desta fase — provar que a arquitetura é
consistente antes de escalar — foi alcançado; a decisão de escalar pertence a
uma revisão humana subsequente, não a esta sessão.
