# Fase 5B — Auditoria Adversarial do Piloto, Reconciliação dos 12 Casos Não Propostos e Preparação da Adjudicação Humana

## A. Classificação

```text
SEMANTIC_PILOT_RECONCILED
TAXONOMY_COVERAGE_REFINED
READY_FOR_HUMAN_SEMANTIC_ADJUDICATION
FULL_CORPUS_ROLLOUT_NOT_AUTHORIZED
```

As 30 anotações do piloto foram revisadas adversarialmente: os 10 casos
`unclassifiable` e os 2 `needs_review` foram individualmente diagnosticados e
reconciliados (nenhum permanece sem classificação); as 18 `proposed` foram
auditadas (17 confirmadas sem defeito, 1 ganhou um concept adicional). Zero
`unclassifiable`/`needs_review` ao final **não** é apresentado como sucesso
por si só — é o resultado de (1) construir uma taxonomia genuinamente
separada para os 9 casos de formação geral/pedagogia (nunca absorvidos em
Computação) e (2) completar uma inspeção visual que a Fase 5A deveria ter
feito e não fez em 2 casos. `SEMANTIC_GENERALIZATION_SUCCESS` e
`READY_FOR_FULL_CORPUS_ROLLOUT` nunca se aplicam: apenas as mesmas 30
questões do piloto foram tratadas; a decisão de expandir pertence a uma
revisão humana ainda não realizada.

## B. Estado Git

Descoberto no início desta fase (nunca presumido):

- Branch: `feat/enade-2008-cc-b-pilot`
- HEAD (início e fim desta sessão): `4ca2a82be4e01188e09563f83e2bec1f2d0f3677`
- `master` / `origin/master`: `a5dfaab0c105150df3a7201c16547708cef45292` (nunca tocado)
- `origin/feat/enade-2008-cc-b-pilot`: idêntico ao HEAD local — nada a
  enviar, nada pendente do lado remoto.
- **Fato relevante**: o trabalho completo da Fase 5A (fundação semântica,
  taxonomia `computing-v1`, 30 anotações, freeze semântico) já estava
  commitado e publicado como `4ca2a82` *antes* desta sessão de Fase 5B
  começar — por uma ação externa, nunca pelos comandos git desta ou de
  qualquer sessão anterior. Confirmado via `git show --stat 4ca2a82`
  (37 arquivos, batendo exatamente com a lista de entregáveis do relatório
  da própria Fase 5A). Registrado como fato, nunca atribuído a esta fase.
- `git status`/`--short`/`--porcelain=v1` no início: working tree
  completamente limpo (`nothing to commit, working tree clean`).
- Working tree ao final desta fase: novos arquivos apenas (nenhum arquivo
  da Fase 5A foi modificado) — ver seção W para a lista completa.

## C. Preservação

Confirmado byte-a-byte (hash cruzado contra os valores que o próprio
`phase-5a-semantic-freeze.json` já registrou, nunca contra uma cópia local
presumida):

- `data/taxonomy/computing-v1.yaml`
- `data/semantic/pilot-selection-5a.json`
- `data/semantic/question-annotations-5a.json`
- `data/semantic/semantic-audit-5a.json`
- `data/semantic/generalization-scan-5a.json`
- `data/manifests/phase-5a-semantic-freeze.json`
- `data/manifests/phase-4e-freeze.json` (freeze terminal da extração)

Nenhum desses 7 arquivos foi reescrito. `pytest tests/test_phase5b_protection.py`
(novo gate desta fase) confirma isso programaticamente — 12/12 (1
skip antes do freeze 5B existir, depois 12/12).

## D. Baseline

Executado **antes** de qualquer alteração desta fase:

```text
pytest -q          → 1106 passed, 0 failed (20m58s) — confirma exatamente
                      a contagem final da Fase 5A, ponto de partida limpo.
```

Contagens 5A confirmadas por releitura integral (nunca só pelo resumo
herdado): 13 áreas / 35 tópicos / 18 conceitos em `computing-v1.yaml`; 30
anotações (18 `proposed`, 2 `needs_review`, 10 `unclassifiable`); 0
diagnósticos nos validadores; hashes dos 7 artefatos 5A conferidos (seção C).

## E. Ledger dos 12 casos

`data/semantic/unresolved-cases-ledger-5b.json` — 12 registros, cada um com
`phase5a_status/component/source_hash/candidate_cause/evidence_reviewed/
taxonomy_candidates/decision/resolution/remaining_ambiguity/
recommended_human_action`.

| Questão | Status 5A | Causa | Decisão |
|---|---|---|---|
| enade-2008-computing-d09 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1 |
| enade-2008-computing-q04 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1 |
| enade-2011-computing-q01 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1 |
| enade-2011-computing-q31 | unclassifiable | **cross_domain_question** | reclassify_to_general_education_v1 |
| enade-2011-computing-q33 | unclassifiable | **cross_domain_question** | reclassify_to_general_education_v1 |
| enade-2021-cc-b-d01 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1 |
| enade-2021-si-d01 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1 |
| enade-2021-cc-b-q01 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1 |
| enade-2021-si-d02 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1_with_context_tag |
| enade-2021-si-q05 | unclassifiable | general_education_outside_computing_taxonomy | reclassify_to_general_education_v1 |
| enade-2011-computing-q14 | needs_review | **annotation_error** | reclassify_within_computing_v1_1 |
| enade-2011-computing-q23 | needs_review | **insufficient_evidence** | confirm_and_upgrade_confidence |

As causas **não** são idênticas para todos os 10 `unclassifiable`: q31/q33
receberam `cross_domain_question` (pedagogia de Licenciatura), distinto dos
outros 8 (`general_education_outside_computing_taxonomy`) — decidido após
ler individualmente o front matter (`applicable_courses:
ciencia-da-computacao-licenciatura`, não o alias `all-computing`). Os 2
`needs_review` também receberam causas diferentes entre si: q14 foi um
**erro real de anotação** (tópico errado); q23 foi apenas **evidência
insuficiente** (tópico já certo, faltava confirmação visual).

## F. `unclassifiable` (resultado individual)

Todos os 10 foram lidos por completo (enunciado, alternativas, assets,
padrão de resposta quando presente — lido apenas para confirmar o domínio,
nunca usado como evidência da anotação) e reclassificados em
`general-education-v1` (nunca absorvidos em `computing-v1.1`):

| Questão | Novo tópico (general-education-v1) |
|---|---|
| enade-2008-computing-d09 | direitos-humanos-e-cidadania |
| enade-2008-computing-q04 | legislacao-e-direitos-sociais |
| enade-2011-computing-q01 | compreensao-e-interpretacao-textual |
| enade-2011-computing-q31 | curriculo-e-sociologia-da-educacao |
| enade-2011-computing-q33 | demografia-aplicada-ao-planejamento-educacional |
| enade-2021-cc-b-d01 / enade-2021-si-d01 | arte-cultura-e-liberdade-de-expressao |
| enade-2021-cc-b-q01 | mobilidade-social-e-desigualdade |
| enade-2021-si-d02 | sustentabilidade-e-desenvolvimento-urbano |
| enade-2021-si-q05 | saude-publica-e-populacoes-vulneraveis |

Nenhum permanece `unclassifiable` — mas nenhum foi absorvido em Computação:
todos vivem numa taxonomia estruturalmente separada (seção I).

## G. `needs_review` (resultado individual)

**enade-2011-computing-q14** — a Fase 5A classificou como
`conjuntos-relacoes-e-funcoes`/baixa confiança com base numa leitura
incompleta do enunciado fragmentado (nunca abriu as 7 imagens). A Fase 5B
inspecionou individualmente todos os 7 assets: figure-01 é um diagrama de
Venn com 3 conjuntos (região sombreada = XOR de X, Y, Z); figure-02 pede
explicitamente "poderia ser expressa pela função lógica f(x,y,z) ="; figure-03
a 07 são as 5 alternativas, todas expressões de álgebra booleana
(AND/OR/NOT). **Achado real: erro de anotação da Fase 5A**, não lacuna de
taxonomia — o tópico correto (`logica-proposicional`) já existia.
Reclassificado para `logica-proposicional` (primário) +
`conjuntos-relacoes-e-funcoes` (secundário) + novo concept
`expressao-booleana-de-regiao-de-conjuntos`; confiança elevada de `low`
para `high`; status de `needs_review` para `proposed`.

**enade-2011-computing-q23** — a Fase 5A já havia classificado corretamente
(`teoria-da-computacao` + `compiladores-e-linguagens-formais` +
`automato-finito`), mas com confiança `medium` por não ter confirmado
visualmente o conteúdo. A Fase 5B inspecionou os 5 assets: figure-01 é a
gramática livre de contexto real (S→aS|bS|cS|abA, A→abA|abcB, B→aB|bB|cB|λ);
figure-02 é o diagrama de autômato finito real (6 estados, alfabeto
{a,b,c}). **A inspeção confirmou, não contradisse**, a classificação
original. Confiança elevada de `medium` para `high`; status de
`needs_review` para `proposed`.

Em nenhum dos dois casos o gabarito foi usado para decidir qual alternativa
é correta — apenas o *tópico* avaliado foi confirmado.

## H. Auditoria dos `proposed`

Todas as 18 anotações `proposed` da Fase 5A foram relidas por completo
(enunciado, alternativas, assets, quando aplicável o padrão de resposta
oficial só para confirmar o domínio) e testadas contra os 10 critérios da
seção 12 do prompt. **17 confirmadas sem defeito** (tópico realmente
avaliado; evidência sustenta a classificação; nenhum termo vem apenas de
alternativa isolada; source hash válido). **1 achado real**:
`enade-2021-si-q25` testa 5 afirmações (I-V), mas o concept original
(`principios-cid-confidencialidade-integridade-disponibilidade`) só cobria
a tríade clássica CID (itens I-III) — os itens IV (legalidade) e V
(autenticidade) ficavam sem cobertura conceitual própria, apesar do
próprio tópico já citar "autenticidade" em sua descrição. Adicionado um
concept de suporte (`legalidade-e-autenticidade-da-informacao`, papel
`supporting`, confiança `medium`) — o concept CID original permanece
`required`, inalterado.

Achado colateral não-semântico, registrado mas não corrigido nesta camada
(seção N): `enade-2008-computing-q55` tem uma fórmula ausente no meio do
enunciado (extração incompleta de uma equação inline) — não afeta a
classificação de tópico (o contexto textual ao redor já é suficiente), mas
é um defeito real de extração para registro futuro.

## I. Formação geral

Das 10 questões originalmente `unclassifiable`, **8 pertencem de fato ao
componente `formacao_geral`** do ENADE (confirmado pelo próprio front
matter: `section` com prefixo `formacao-geral-`) e **2 são componente
específico de Licenciatura em Ciência da Computação** cujo conteúdo é
pedagogia/ciências da educação, não Computação (`applicable_courses:
ciencia-da-computacao-licenciatura`, `section` com prefixo
`componente-especifico-`).

**Decisão arquitetural**: criada `data/taxonomy/general-education-v1.yaml`,
um documento de taxonomia **totalmente separado** (mesmo schema
`Taxonomy`/`Subject`/`Topic`/`Concept` já existente — zero mudança de
schema necessária), com 2 subjects:

- `formacao-geral` (7 tópicos, cobrindo as 8 questões de formação geral —
  o par compartilhado `cc-b-d01`/`si-d01` conta como 1 tópico)
- `pedagogia-e-formacao-de-professores` (2 tópicos, cobrindo as 2 questões
  de Licenciatura)

Nenhum id é compartilhado entre `computing-v1.1` e `general-education-v1`
(verificado programaticamente,
`test_no_id_is_shared_between_computing_and_general_education`). Nunca foi
"absorvida" formação geral dentro de uma área de Computação — as
alternativas descartadas (namespace dentro do mesmo documento, taxonomia
transversal já fundamentada) foram consideradas e preteridas em favor de um
documento genuinamente separado, mais simples de auditar e impossível de
confundir com o escopo de Computação. Dispatch entre as duas taxonomias é
feito pelo próprio campo `taxonomy_version` da anotação (uma string
totalmente qualificada, ex. `"general-education-v1@1.0.0-pilot"`) — nenhuma
mudança no modelo `QuestionAnnotation` foi necessária.

A decisão foi baseada no corpus real (9 questões concretas, cada uma
individualmente lida) e não em conveniência para reduzir a contagem de
`unclassifiable` — ver seção Y para a ressalva explícita sobre isso.

## J. Interdisciplinaridade

Um caso real de contexto vs. tópico principal foi tratado explicitamente:
`enade-2021-si-d02` (cidades inteligentes) menciona tecnologia (TIC) como
premissa ("uma cidade é considerada inteligente quando nela se utiliza a
tecnologia..."), mas os itens de fato avaliados pedem explicação de
sustentabilidade e uma proposta de intervenção social — nunca o mecanismo
técnico. Classificado com tópico primário
`sustentabilidade-e-desenvolvimento-urbano` (general-education-v1) e um
`context_tag` textual registrando a menção tecnológica sem promovê-la a
tópico — nunca `secondary_topic`, que exigiria evidência própria de
conhecimento avaliado. Contraste deliberado mantido com
`enade-2021-si-q34` (mesmo tema, mas avaliado tecnicamente — IoT,
heterogeneidade de dispositivos, TIC como o próprio objeto da questão),
que permanece em `computing-v1.1`.

Novo validador `validate_context_not_used_as_primary_topic` garante
estruturalmente que nenhuma anotação futura repita um id simultaneamente
como `context_tag` e como tópico primário/secundário — 0 diagnósticos
contra os dados reais.

## K. Taxonomia nova

**`computing-v1.1.yaml`** (sucessora aditiva/retrocompatível de
`computing-v1.yaml`, que permanece intocado): mesmo `taxonomy_id`
(`computing-v1`), `version` incrementada para `"1.1.0-pilot"`. Todos os 66
ids da v1.0 preservados com o mesmo `name`/significado (verificado
programaticamente por `validate_no_taxonomy_id_meaning_changed` — 0
diagnósticos). Duas adições, ambas motivadas por achados reais da auditoria
adversarial (nunca por conveniência):

1. `expressao-booleana-de-regiao-de-conjuntos` (novo concept, sob
   `logica-proposicional`) — motivado por `enade-2011-computing-q14`.
2. `legalidade-e-autenticidade-da-informacao` (novo concept, sob
   `principios-de-seguranca-da-informacao`) — motivado por
   `enade-2021-si-q25`.

13 áreas → 13 (inalterado); 35 tópicos → 35 (inalterado); 18 conceitos → 20
(+2). Classificação de versão: **minor** (novos nós compatíveis, PROMPT
seção 15) — nunca patch (mudança de significado zero) nem major (nada
incompatível).

**`general-education-v1.yaml`** (nova, primeira versão): 2 subjects, 9
tópicos, 0 conceitos (seção I).

## L. Migração

`data/semantic/migration-5a-to-5b.json` — 30 entradas, uma por questão,
cada uma com `previous_status/new_status/previous_topics/new_topics/
change_reason/taxonomy_change/evidence_change`. **17 questões marcadas
explicitamente `unchanged`** (auditadas, sem defeito, apenas bump de
versão de taxonomia) — provando que foram de fato revisadas, não apenas
omitidas do log. As 13 restantes têm razão de mudança individual e
específica (nunca um texto genérico copiado). `enade validate-semantic-migration`
confirma: nenhuma questão foi perdida entre 5A e 5B; toda entrada tem razão
não-vazia; nenhum id de taxonomia mudou de significado silenciosamente.

## M. Evidência

Toda evidência das 30 anotações 5B foi revalidada: texto excerto conferido
literalmente contra o arquivo `.md` real antes de serializar (`assert
excerpt in md_text` no script gerador); hash de cada asset citado
reaproveitado do próprio front matter publicado (nunca recalculado
livremente); `validate_evidence_integrity` re-lê os arquivos reais do disco
e não aponta nenhum "stale". Novo validador
`validate_primary_evidence_not_alternative_only` confirma que nenhuma
evidência primária das 30 anotações vem exclusivamente de dentro de "##
Alternativas" (0 diagnósticos). Evidência textual: 49 (5A) → 51 (5B, +2 de
q14); evidência visual: 5 (5A) → 9 (5B, +4 de q14/q23) — o aumento reflete
exatamente a inspeção visual que a Fase 5A não tinha feito.

## N. Distratores

Auditoria específica (seção 13 do prompt) sobre as 18 `proposed`: nenhum
concept foi encontrado apoiado apenas numa alternativa isolada — o caso
mais próximo de risco (`enade-2008-computing-q30`, cujas 5 alternativas
listam várias tecnologias de rede) tem o concept
`tecnicas-de-multiplo-acesso` grounded diretamente na frase do próprio
enunciado ("técnicas de múltiplo acesso que permitam..."), nunca só numa
alternativa. `enade-2011-computing-q49` foi verificado com atenção especial
por suas 5 alternativas serem palavras isoladas (ambiente/entrada/
feedback/processos/saída, o mesmo vocabulário do achado de palavra
genérica da Fase 5A) — mas o concept `teoria-geral-de-sistemas` está
grounded no enunciado ("trazido pela Teoria Geral de Sistemas", "sistema
aberto"), nunca numa alternativa isolada.

Achado de extração registrado, não corrigido (seção H):
`enade-2008-computing-q55` tem uma fórmula inline ausente no meio do
enunciado. `enade-2021-cc-b-q29` está oficialmente `annulled`
(`answer_validation_status`) — não afeta a classificação semântica (o
conteúdo de morfologia matemática é real independentemente da anulação),
mas é registrado aqui por transparência.

## O. Keywords genéricas

Novo validador `validate_taxonomy_keywords_are_not_bare_generic_terms`
(denylist explícita: sistema/processo/modelo/rede/estrutura/dados/
programa/funcao/servico/informacao/ambiente/entrada/saida/feedback — os
mesmos termos que a Fase 5A já havia corrigido, mais os outros exemplos
citados na seção 14 do prompt). **Achado real de bug no próprio
validador durante o desenvolvimento**: a primeira versão flagava qualquer
palavra-chave curta (<5 caracteres), o que teria marcado incorretamente
"SQL", "DER", "TDA", "SaaS", "CDMA", "CID" — acrônimos técnicos precisos,
exatamente o oposto de um termo genérico. Corrigido removendo o critério de
comprimento; o validador agora usa exclusivamente a denylist explícita, e
nunca penaliza um termo curto só por ser curto. Rodado contra
`computing-v1.1` e `general-education-v1`: **0 diagnósticos** em ambas —
nenhuma palavra-chave genérica sobrevive nas duas taxonomias atuais.

## P. Confiança

Critérios objetivos aplicados (nunca por impressão): `high` exige tópico
explícito + evidência direta + nenhuma hipótese concorrente plausível;
`medium` exige alguma interpretação/interdisciplinaridade; `low` exige
evidência parcial ou dependência de asset ambíguo. Distribuição: 26
`high`/3 `medium`/1 `low` (5A) → **28 `high`/2 `medium`/0 `low`** (5B). A
única `low` (q14) subiu para `high` porque a ambiguidade real foi resolvida
por evidência nova (inspeção visual), nunca por decisão arbitrária — a
confiança nunca foi elevada só porque um novo nó de taxonomia foi criado
(verificado caso a caso, seção G). Nenhuma das 10 questões
`unclassifiable`→`proposed` recebeu confiança incoerente: todas as 10 são
`high` porque, após a leitura completa, o domínio (formação geral/pedagogia)
era inequívoco em cada uma — não uma inflação artificial.

## Q. Habilidades cognitivas

Revalidadas nas 30 questões; vocabulário fechado mantido
(recall/interpret/apply/calculate/analyze/compare/evaluate/design/
justify). Nenhuma habilidade foi inferida automaticamente pela modalidade
(objetiva vs. discursiva) — cada questão discursiva de formação geral
recebeu `interpret`/`justify`/`evaluate` conforme a tarefa real pedida
(ex.: `enade-2011-computing-q31`/`q33`, objetivas, avaliam 4 afirmações →
`analyze`/`evaluate`, não apenas `interpret` por serem múltipla escolha).

## R. Termos de busca

Reavaliados; nenhum termo genérico sem contexto foi introduzido nas novas
anotações (seção O). Os termos de busca das 10 novas anotações
general-education derivam diretamente do próprio tópico atribuído (nunca
gerados a partir do texto completo da questão).

## S. Template humano

`data/semantic/human-adjudication-template-5b.json` — 30 entradas, campos
`human_decision`/`human_primary_topics`/`human_secondary_topics`/
`human_concepts`/`human_notes`/`reviewer`/`reviewed_at` **todos `null`**.
Modelo `HumanAdjudicationEntry` (`src/enade/semantic/adjudication.py`)
impõe estruturalmente: os três campos `human_decision`/`reviewer`/
`reviewed_at` só podem ser preenchidos juntos (nunca parcialmente); uma
decisão `reject`/`defer` nunca pode carregar uma lista de tópicos humanos
(contradição lógica). `enade build-human-adjudication` recusa sobrescrever
um arquivo que já tenha uma decisão humana real, a menos que `--force` seja
passado explicitamente.

## T. Pacote de revisão

`docs/semantic-pilot-review-5b.md` — para cada uma das 30 questões, mostra
lado a lado a classificação histórica da Fase 5A e a proposta técnica da
Fase 5B, o motivo da mudança, evidências, e separa claramente "proposta
técnica" (tudo calculado por esta fase) de "decisão humana pendente"
(caixas de seleção approve/correct/reject/defer, nunca preenchidas aqui —
a decisão real só pode ser registrada no template machine-readable). O
gabarito nunca aparece.

## U. Generalization scan

`data/semantic/generalization-scan-5b.json` rodado contra `computing-v1.1`
sobre as 255 questões dos 5 livretos — diagnóstico apenas, nenhuma
anotação automática publicada. Comparação com `generalization-scan-5a.json`:

| Métrica | 5A | 5B |
|---|---|---|
| sem candidato | 145 | 143 |
| `matematica-discreta-e-logica` (hits) | 5 | 7 |
| exigem evidência visual | 92 | 92 |
| compartilhadas | 55 | 55 |
| provavelmente precisam de revisão | 14 | 14 |

A única mudança real é o aumento de 5→7 em `matematica-discreta-e-logica`,
explicado exatamente pelas novas keywords do concept
`expressao-booleana-de-regiao-de-conjuntos` ("diagrama de venn", "expressão
booleana") passando a casar com mais 2 questões do corpus completo — um
efeito colateral esperado e coerente da correção da seção G, não um sinal
de scope creep. `general-education-v1` também foi rodado diagnosticamente
(205/255 sem candidato) — a heurística de substring simples não funciona
bem para tópicos de ciências sociais nomeados de forma ampla (ex.:
"Direitos Humanos e Cidadania" raramente aparece como frase literal no
enunciado de uma questão) - resultado honesto, não uma tentativa de fazer
funcionar adicionando palavras-chave genéricas (o que reintroduziria
exatamente o defeito da seção O).

## V. Testes

- Baseline (antes de qualquer alteração): **1106 passed, 0 failed**
  (seção D).
- Novos arquivos de teste desta fase: `tests/test_semantic_adjudication.py`,
  `tests/test_semantic_validators_5b.py`, `tests/test_cli_semantic_5b.py`,
  `tests/test_semantic_migration_5b.py`, `tests/test_semantic_ledger_5b.py`,
  `tests/test_semantic_general_education_taxonomy.py`,
  `tests/test_semantic_review_5b.py`, `tests/test_phase5b_protection.py`,
  `tests/test_semantic_freeze_contract_5b.py`,
  `tests/test_phase5b_semantic_freeze.py`.
- Suíte completa final (após todas as alterações desta fase, incluindo
  `tests/test_phase5b_semantic_freeze.py`, execução real antes do freeze
  ter seus valores preenchidos): **1224 passed, 1 failed** (19m39s) — a
  única falha era `test_quality_gates_pytest_entry_is_filled_in_and_passing`,
  esperada (o mesmo bootstrapping documentado na Fase 5A: o freeze ainda
  não sabia sua própria contagem final). Após preencher o campo
  `quality_gates.pytest` do freeze com o valor real (1225 = 1224 + o
  próprio teste do freeze, que passa a validar a si mesmo):
  **`pytest tests/test_phase5b_semantic_freeze.py`: 22/22 passed**;
  **total final: 1225 passed, 0 failed**.

## W. Proteção e reprodutibilidade

- `data/questions/**`: zero diff (255/255 `audit-extraction` OK;
  `test_phase5b_protection.py` confirma o hash agregado por alvo
  inalterado desde a Fase 4E).
- Gold/manifests: inalterados (hash cruzado contra `phase-4e-freeze.json`).
- Freezes 4E e 5A: byte-a-byte idênticos (seção C).
- Reprodutibilidade real, executada (não apenas planejada):
  - `enade validate-semantic-migration` × 2 → 0 diagnósticos em ambas.
  - `enade build-human-adjudication` × 2 (saídas separadas) → diff vazio.
  - `build_reconciliation_review_markdown` × 2 → resultado idêntico.
  - `scan_corpus` (generalização) × 2 → resultado idêntico.
  - Nenhum campo humano foi preenchido em nenhum artefato (100% `null`).
- Working tree final (novos arquivos desta fase, `git status --short`):

```
?? data/manifests/phase-5b-semantic-freeze.json
?? data/semantic/generalization-scan-5b.json
?? data/semantic/human-adjudication-template-5b.json
?? data/semantic/migration-5a-to-5b.json
?? data/semantic/question-annotations-5b.json
?? data/semantic/unresolved-cases-ledger-5b.json
?? data/taxonomy/computing-v1.1.yaml
?? data/taxonomy/general-education-v1.yaml
?? docs/phase-5b-report.md
?? docs/semantic-pilot-review-5b.md
?? src/enade/semantic/adjudication.py
?? tests/test_cli_semantic_5b.py
?? tests/test_phase5b_protection.py
?? tests/test_phase5b_semantic_freeze.py
?? tests/test_semantic_adjudication.py
?? tests/test_semantic_freeze_contract_5b.py
?? tests/test_semantic_general_education_taxonomy.py
?? tests/test_semantic_ledger_5b.py
?? tests/test_semantic_migration_5b.py
?? tests/test_semantic_review_5b.py
?? tests/test_semantic_validators_5b.py
 M src/enade/cli.py
 M src/enade/semantic/freeze.py
 M src/enade/semantic/review.py
 M src/enade/semantic/validators.py
```

Nenhum arquivo da Fase 5A ou anterior foi modificado. Nenhum commit,
staging ou push foi realizado nesta fase.

## X. Freeze 5B

`data/manifests/phase-5b-semantic-freeze.json` — sucessor da lineage
semântica, referenciando por hash tanto `phase-5a-semantic-freeze.json`
(`predecessor_semantic_freeze_reference`) quanto `phase-4e-freeze.json`
(`extraction_freeze_reference`, transitivamente, nunca tratando a extração
como se fosse deste mesmo nível). Novo contrato de completude
`validate_phase5b_freeze_completeness` (`src/enade/semantic/freeze.py`),
com forma própria (`taxonomy_computing`/`taxonomy_general_education`/
`annotations`/`unresolved_cases_ledger`/`migration_log`/
`human_adjudication_template`/`review_packet`) — testado para rejeitar a
forma antiga da Fase 5A quando aplicada incorretamente aqui
(`test_5a_style_artifact_keys_alone_do_not_satisfy_the_5b_shape`).
`semantic_maturity: "provisional_reconciled_pilot"`;
`human_review_status: "not_yet_reviewed"` — nunca `"reviewed"`/`"approved"`.
Gate próprio: `tests/test_phase5b_semantic_freeze.py`.

## Y. Recomendação

**Adjudicação humana das 30 questões (`data/semantic/human-adjudication-template-5b.json`,
apoiada por `docs/semantic-pilot-review-5b.md`) é o próximo passo
obrigatório antes de qualquer rollout.** Pontos específicos para o
revisor humano priorizar:

1. **A decisão arquitetural mais importante desta fase**: confirmar que
   `general-education-v1` como taxonomia separada (em vez de um namespace
   dentro de `computing-v1.1`, ou manter os 10 casos `unclassifiable`) é a
   escolha correta — e que os 2 subjects (`formacao-geral` vs.
   `pedagogia-e-formacao-de-professores`) fazem sentido como categorias
   distintas.
2. O achado mais significativo tecnicamente: `enade-2011-computing-q14`
   foi reclassificado depois de a Fase 5A ter cometido um erro real de
   leitura — confirmar a reclassificação.
3. `enade-2021-si-d02`: confirmar que o uso de `context_tag` (em vez de
   promover IoT/cidades inteligentes a tópico secundário) reflete
   corretamente o que a questão de fato avalia.
4. O concept adicional em `enade-2021-si-q25` (legalidade/autenticidade) -
   confirmar que "supporting" é o papel correto, não "required".
5. A fórmula ausente em `enade-2008-computing-q55` (seção N) - um achado
   de extração para investigação futura, fora do escopo desta camada
   semântica.

Esta fase **não** deve ser seguida por rollout completo do corpus (225
questões restantes). `FULL_CORPUS_ROLLOUT_NOT_AUTHORIZED` permanece válido
até que a adjudicação humana desta fase e da Fase 5A conclua. Reduzir a
quantidade de `unclassifiable` para zero não é, por si só, o critério de
sucesso desta fase — o critério real é que cada uma das 30 classificações
finais tenha tópico, papel e evidência demonstráveis, o que foi verificado
individualmente, questão a questão, nesta auditoria.
