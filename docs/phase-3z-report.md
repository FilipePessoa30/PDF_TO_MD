# Fase 3Z — Política Formal de `source_unavailable`, Reconciliação de D09/D10 e Readiness Final de 2008-b

## A. Classificação

**`SOURCE_LIMITATION_POLICY_ESTABLISHED`**.

Justificativa: o pacote-fonte oficial de 2008-b foi formalizado (`SourcePackage`,
`data/manifests/source-availability-2008.yaml`); D09 e D10 foram revalidadas do zero nesta fase
(nunca reaproveitando a narrativa da Fase 3T sem reexecutar), com ausência agora comprovada não só
em texto/rawdict (evidência da Fase 3T) mas também em imagens, drawings e texttrace, nas 6 páginas
de `b3_padrao.pdf` — fechando exatamente a lacuna que, em D59, escondeu um answer standard real por
três fases; a política é machine-readable (`source_availability.py`, `is_confirmed_unavailable`,
`verify_source_hashes_match`), nunca confia no rótulo `availability_status` isoladamente, e recusa
a isenção sempre que qualquer evidência estiver incompleta; D59 permanece protegida como
contraexemplo positivo (não tocada, seu próprio asset e texto continuam intactos); o gold permanece
semanticamente correto (nenhum `needs_review` foi silenciosamente removido; `unresolved_question_ids`
continua `[D09, D10]`); o readiness agora é explicável (blockers acionáveis, limitações de fonte e
achados informativos aparecem separadamente, cada um com evidência própria); **zero blocker
acionável** restante em 2008-b; as duas limitações de fonte permanecem visíveis, nunca escondidas;
testes (23 novos) e quality gates estão limpos; zero drift no corpus publicado (2008-b, 2011, três
cursos de 2021); reprodutibilidade confirmada (duas execuções independentes, byte-idênticas).

O veredito real do gate (`enade assess-readiness --year 2008 --course all-computing`, com os labels
convencionais já usados desde a Fase 3T) é:

```text
READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS
```

— um novo label, literal, nunca inventado por estética (Seção Q): expressa exatamente "pronto como
teste de engenharia do extrator, mas com limitações documentais confirmadas e permanentes" — nunca
"corpus documentalmente completo". Reporto separadamente, como a Fase 3Z exige:

```text
ACTIONABLE_BLOCKERS = 0
SOURCE_LIMITATIONS = 2
INFORMATIONAL_FINDINGS = 0
```

Não declaro `GENERALIZATION_SUCCESS`, não declaro o corpus documentalmente completo, e não removo
D09/D10 de nenhum relatório — ambos continuam aparecendo, individualmente, no gold
(`unresolved_question_ids`) e no readiness (seção "source limitations").

## B. Estado Git inicial

```text
git status --short:        (árvore de trabalho limpa)
git branch --show-current: feat/enade-2008-cc-b-pilot
git rev-parse HEAD:         22e3e882046654193fedf21de296e5ae3c374cb3
git rev-parse master:       a5dfaab0c105150df3a7201c16547708cef45292
git rev-parse origin/master: a5dfaab0c105150df3a7201c16547708cef45292
git diff --stat:            (vazio)
git diff --check:           (vazio)
```

`HEAD` já incluía todo o trabalho acumulado das Fases 3A–3Y, commitado externamente antes do início
desta fase (`22e3e88`, "feat: Implement raster alternative region handling and verification" —
Fase 3Y). Confirmado: Q8 publicada (5 alternativas raster), Q38 publicada (circuito + 5 alternativas
vetoriais), D09/D10 representadas como `extraction_status: needs_review`/`answer_standard: null`
(limitação de fonte, não removidas). `master`/`origin/master` inalterados do início ao fim desta
fase. Nenhum commit, push, PR, merge ou tag foi criado.

## C. Baseline

```text
pytest:                    844 passed (confirmado por execução real)
ruff check .:               All checks passed!
ruff format --check .:      421 files already formatted
mypy src:                   Success: no issues found in 60 source files
enade validate-schema:      13/13 fixture(s) valid
enade validate-manifest:    OK (0 warning(s))
enade audit-extraction (2008-b/2011/2021 x3): 80/55/40/40/40 OK
```

Nota sobre o comando literal do prompt: `enade verify-gold`/`assess-readiness --year 2008 --course
engenharia-da-computacao-bacharelado` **não se aplica** — `engenharia-da-computacao-bacharelado` não
existe como `CourseCode` (o valor real é `engenharia-da-computacao`, sem sufixo, e corresponde ao
caderno 2008-**e**, um bundle explicitamente fora de escopo desde a Fase 1). O caderno unificado
2008-b (Formação Geral + Componente Específico Comum de Computação, todas as Fases 3A-3Y) é
identificado pelo código real `all-computing`, exatamente como em todo relatório anterior (mesma
nota já registrada nas Fases 3T/3U). Usei `all-computing` em todos os comandos.

```text
enade verify-gold --year 2008 --course all-computing:
  OK (80 questions match); maturity=provisional verified=78 needs_review=2
enade assess-readiness --year 2008 --course all-computing
  --ready-label READY_FOR_2008_ENGINEERING_TEST
  --not-ready-label NOT_READY_FOR_2008_ENGINEERING_TEST:
  NOT_READY_FOR_2008_ENGINEERING_TEST
  78/80 verified, 2 needs_review, gold maturity=provisional
  visual audit: 80 passed, 0 failed, 0 not_performed (fully_covered=True)
  4 blocker(s):
    - [question_not_verified, structural] enade-2008-computing-d09: extraction_status=needs_review
    - [missing_answer_standard, structural] enade-2008-computing-d09
    - [question_not_verified, structural] enade-2008-computing-d10: extraction_status=needs_review
    - [missing_answer_standard, structural] enade-2008-computing-d10
enade verify-gold --year 2011 --course all-computing:
  OK (55 questions match); maturity=validated verified=54 needs_review=1
enade assess-readiness --year 2011 --course all-computing
  --ready-label READY_FOR_LEGACY_LAYOUT_TEST --not-ready-label NOT_READY_FOR_LEGACY_LAYOUT_TEST:
  READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, 1 blocker (não-estrutural, Q34)
2021 CC-B: verify-gold OK (40/40); assess-readiness READY_FOR_2011, 0 blockers
2021 CC-L / SI: sem gold manifest (pré-existente, confirmado, não é lacuna desta fase)
```

Hashes-fonte registrados (2008-b): `b1_prova.pdf`
`5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264` (36 páginas); `b2_gabarito.pdf`
`707a326330c6982a9368957c6d9af1563b886d32d6c6720319faeb71803f2425` (2 páginas); `b3_padrao.pdf`
`7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef` (6 páginas) — idênticos aos já
registrados desde a Fase 3T (o arquivo-fonte não mudou). Uma captura SHA-256 de todos os 143
arquivos de 2008-b, 97 de 2011 e 173 de 2021 (Markdown + assets) foi feita antes de qualquer edição,
para a verificação de zero-drift da Seção W.

## D. Reconciliação dos denominadores

Nenhuma inconsistência real foi encontrada — as contagens "77" (Fases 3T/3U/3V) e "78 verified + 2
needs_review" (Fase 3Y em diante) representam **universos diferentes, corretamente**, nunca
misturados no mesmo relatório:

- Até a Fase 3V (inclusive), 2008-b tinha **77** questões efetivamente publicadas em disco — Q8,
  Q38 e Q55 estavam excluídas inteiramente do corpus (nenhum arquivo `.md` existia para elas,
  `pipeline.py`'s próprio isolamento de `ValidationError` por questão). "published=77",
  "visual_audit=77 passed" e "gold=74→75→77 verified+needs_review" todos usavam esse mesmo
  denominador de 77 arquivos reais no disco.
- A Fase 3W resolveu Q55 (77→78 arquivos publicados), a Fase 3X resolveu Q38 (78→79), e a Fase 3Y
  resolveu Q8 (79→80). Ao final da Fase 3Y, **as 80 questões acadêmicas estão publicadas** (0
  excluídas) — um denominador maior e correto, não um erro.
- "gold = 78 verified + 2 needs_review" (78+2=**80**) e "visual audit = 80 passed" (confirmado nesta
  fase via `assess-readiness` real) já refletem esse novo denominador de 80 — perfeitamente
  consistentes entre si, apenas maiores que o "77" das fases anteriores porque o universo cresceu.
- As **duas** entidades `needs_review` são exatamente D09 e D10 (`unresolved_question_ids: [D09,
  D10]`, confirmado lendo `gold-2008-computing.json` diretamente).
- Os **quatro** achados que geram os blockers atuais são exatamente: `question_not_verified`
  (D09), `missing_answer_standard` (D09), `question_not_verified` (D10), `missing_answer_standard`
  (D10) — confirmado literalmente na saída real do gate (Seção C acima), nunca presumido.

Nenhuma correção de contrato foi necessária aqui — a "inconsistência" aparente era apenas a mesma
métrica, honestamente, em dois pontos diferentes de uma série temporal crescente.

## E. Quatro blockers iniciais

| finding_id | question_id | artifact_type | current_reason | current_status | blocking_effect | source_evidence | extractor_actionability | duplicate_of |
|---|---|---|---|---|---|---|---|---|
| question_not_verified:d09 | enade-2008-computing-d09 | Question.extraction_status | `needs_review` (nenhum answer standard correspondente encontrado no gabarito/padrão) | achado derivado, sem status próprio | estrutural (bloqueia) | ver Seção L | não-acionável (fonte ausente, comprovado) | mesma causa raiz de missing_answer_standard:d09 |
| missing_answer_standard:d09 | enade-2008-computing-d09 | Question.answer_standard | `None` | achado derivado, sem status próprio | estrutural (bloqueia) | ver Seção L | não-acionável | mesma causa raiz de question_not_verified:d09 |
| question_not_verified:d10 | enade-2008-computing-d10 | Question.extraction_status | `needs_review` | achado derivado | estrutural (bloqueia) | ver Seção M | não-acionável | mesma causa raiz de missing_answer_standard:d10 |
| missing_answer_standard:d10 | enade-2008-computing-d10 | Question.answer_standard | `None` | achado derivado | estrutural (bloqueia) | ver Seção M | não-acionável | mesma causa raiz de question_not_verified:d10 |

A composição real confirmada bate exatamente com a hipótese do prompt (D09/D10, cada um com
`question_not_verified`+`missing_answer_standard`) — nunca presumida sem consultar a saída real do
gate (Seção C). Classificação dos pares: **manifestações distintas (mecanismos de detecção
independentes: um lê `Question.extraction_status`, o outro `Question.answer_standard`) da mesma
limitação única** (ausência do answer standard oficial no pacote-fonte) — não são duplicações
semânticas a apagar (cada achado é computado por um caminho de código genuinamente diferente e
permanece útil de exibir separadamente), nem um blocker-e-consequência (nenhum dos dois causa o
outro; ambos são consequências independentes do mesmo fato de origem). Por isso a solução desta
fase preserva ambos os achados, aplicando a mesma isenção (não-estrutural) aos dois quando — e
somente quando — a limitação de origem estiver totalmente comprovada (Seção O/Q). A contagem final
nunca foi reduzida "artificialmente" para chegar a zero — ela chega a zero porque a **causa real**
(ausência confirmada, nunca um defeito) foi formalmente adjudicada com evidência completa.

## F. Pacote-fonte oficial

Formalizado em `data/manifests/source-availability-2008.yaml` (`source_packages`):

```yaml
source_package_id: 2008-b-computacao
documents:
  - path: 2008/b1_prova.pdf   (prova, 36 páginas)
  - path: 2008/b2_gabarito.pdf (gabarito, 2 páginas)
  - path: 2008/b3_padrao.pdf   (padrao, 6 páginas)
```

`coverage_claim`: o pacote oficial de 2008-b, tal como fornecido a este projeto (geacc/enade,
commit `a657632b97468c8a5eb3b433d1abb4a5511c5`) — três arquivos PDF, hash-locked. Uma conclusão
`source_unavailable_confirmed` é sempre relativa a **este** pacote exato — nunca uma alegação de que
o conteúdo nunca existiu em lugar nenhum, e nunca uma alegação sobre a incapacidade do extrator.

## G. Hashes e proveniência

| documento | papel | sha256 | páginas | proveniência |
|---|---|---|---|---|
| `2008/b1_prova.pdf` | prova | `5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264` | 36 | geacc/enade, commit `a657632b72b97468c8a5eb3b433d1abb4a5511c5` |
| `2008/b2_gabarito.pdf` | gabarito | `707a326330c6982a9368957c6d9af1563b886d32d6c6720319faeb71803f2425` | 2 | idem |
| `2008/b3_padrao.pdf` | padrao | `7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef` | 6 | idem |

Todos os três hashes re-verificados nesta fase batem exatamente com os já registrados desde a Fase
3T — o arquivo-fonte não mudou desde então.

## H. Marker inventory

`b3_padrao.pdf`, busca fresca via `page.get_text("rawdict")` + regex
`(?i)quest[aã]o\s+(?:discursiva\s+)?0*(\d+)\b`, todas as 6 páginas:

| # | marcador | página | bbox |
|---|---|---|---|
| 1 | Questão 20 | 1 | (89.25, 115.57)–(152.38, 128.13) |
| 2 | Questão 39 | 1 | (89.25, 411.82)–(155.38, 424.39) |
| 3 | Questão 40 | 1 | (89.25, 709.57)–(152.38, 722.14) |
| 4 | Questão 59 | 3 | (89.25, 460.57)–(155.38, 473.14) |
| 5 | Questão 60 | 3 | (71.25, 752.32)–(137.38, 764.89) |
| 6 | Questão 79 | 4 | (71.25, 616.57)–(140.38, 629.14) |
| 7 | Questão 80 | 5 | (106.5, 353.32)–(172.63, 365.89) |

Nunca "Questão 9"/"Questão 09"/"Questão 10" em nenhuma das 6 páginas. A página 1 começa
imediatamente em "COMPUTAÇÃO" (y0=72.4) seguido por "Questão 20" (y0=115.6) — sem capa, sem gap. A
página 6 (última) é a continuação textual de "Questão 80" (nenhum marcador novo) — o documento
termina exatamente onde a sequência de marcadores termina. Contagem de caracteres por página
(`page.get_text("text")`): 1123/626/176/2944/2643/321 — nenhuma página com zero texto (nenhuma
totalmente rasterizada).

## I. Forense textual

Métodos: `page.get_text("text")` (regex ancorado, nunca número isolado sozinho, conforme exigido);
`page.get_text("rawdict")` (linha a linha, char-level); `page.get_texttrace()` (confirma 100% dos
spans de texto como render-mode 0 — texto normal, visível, preenchido; zero span invisível/oculto
que um `get_text()` ingênuo pudesse perder de forma diferente). Resultado idêntico nos três métodos:
os 7 marcadores da Seção H, nunca 9/10. Ver `text_evidence` de ambos os registros em
`data/manifests/source-availability-2008.yaml` para o texto completo.

## J. Forense de imagens

`page.get_images(full=True)` + `page.get_image_info(xrefs=True)`, todas as 6 páginas: **15 imagens**
no total. Uma delas (cabeçalho recorrente, bbox 71.25,35.0–524.25,71.75, idêntica em todas as 6
páginas) é chrome, nunca conteúdo de rubrica. As 14 restantes foram **individualmente atribuídas**,
por posição Y estrita dentro da janela marcador-a-marcador (nunca por proximidade aproximada), a uma
das 7 discursivas realmente presentes (20, 39, 40, 59, 60, 79, 80) — nenhuma imagem órfã, nenhuma
caindo em uma janela "Questão 9"/"Questão 10" (indefinida por construção, já que esse marcador não
existe). Reconfirma, de forma independente, a atribuição já estabelecida na Fase 3U para a página 3
(D40 recebe as 2 imagens antes de "Questão 59"; D59 recebe a única imagem entre "Questão 59" e
"Questão 60"). Ver `image_evidence` no manifest para o detalhamento completo por xref/bbox.

## K. Forense de drawings

`page.get_drawings()`, todas as 6 páginas: **zero** em cada uma, sem exceção. Não há nenhum conteúdo
vetorial (diagrama desenhado, tabela com bordas vetoriais, fórmula desenhada) em nenhum lugar deste
documento — descartando a hipótese análoga a D59, mas via vetor em vez de raster.

## L. Evidência de D09

Ver tabela completa na Seção 20/consolidada abaixo. Resumo: artefato esperado (answer_standard),
documento esperado (`2008/b3_padrao.pdf`), hash confirmado, 6/6 páginas pesquisadas, marcador
"Questão 9"/"Questão 09"/"9" nunca encontrado, zero imagem/drawing atribuível a essa janela
(indefinida). `availability_status: source_unavailable_confirmed`, `review_status: reviewed`,
gate `is_confirmed_unavailable` = **True** (verificado programaticamente nesta fase, não apenas
lido do YAML).

## M. Evidência de D10

Idêntica a D09 (mesmo documento, mesma busca exaustiva, mesmo resultado negativo completo). Ver
`data/manifests/source-availability-2008.yaml`, registro `sa-2008-d10-answer-standard`.

## N. Contraexemplo D59

Confirmado intacto e **não tocado** nesta fase: `git diff` em `enade-2008-computing-d59.md` e em
`enade-2008-computing-d59/answer-standard/padrao-01.png`: vazio. Testes de pipeline
(`test_extraction_pipeline_2008.py -k "d59 or q45 or q55 or q08 or q38 or d40"`, 9 testes) passam
sem alteração. D59 nunca foi, e nunca poderia ser, classificada `source_unavailable_confirmed`
por este novo mecanismo: seu próprio registro exigiria `image_evidence`/`drawing_evidence`
documentando a IMAGEM REAL que de fato existe (o oposto de "ausente") — nenhum registro
`source_unavailable_confirmed` foi ou será criado para D59. A lição de D59 (um texto vazio não prova
ausência de fonte) é exatamente o que `is_confirmed_unavailable` agora impõe estruturalmente para
D09/D10: a exigência de `search_methods` cobrir imagens e drawings, com evidência não-vazia em
ambos, existe precisamente para nunca repetir o erro que esconderia um D59-like real.

## O. Modelo de disponibilidade

Novo módulo `src/enade/extraction/source_availability.py` (nunca reaproveitando `blocker_ledger.py`
como um campo booleano disfarçado): `SourcePackage`/`SourceDocument` (fronteira do pacote-fonte,
Seção F), `SourceAvailabilityRecord` (evidência estruturada por sujeito/artefato, com os 6 estados
distintos exigidos: `available_and_extracted`, `available_but_not_extracted`,
`source_unavailable_confirmed`, `source_ambiguous`, `source_not_checked`, `source_hash_mismatch` —
nunca um booleano), `SourceAvailabilityLedger` (coleção + loader tolerante a arquivo ausente, como
`visual_audit.py`). Dois gates, nunca confiando no rótulo isoladamente:

- `is_confirmed_unavailable(record, ledger) -> bool`: exige status literal
  `source_unavailable_confirmed`, `review_status="reviewed"`, pacote existente, o documento
  referenciado (`expected_source`) existente dentro do pacote, `pages_scanned` cobrindo **todas** as
  páginas do documento (nunca uma lista parcial — Seção 19), os 5 métodos de busca
  (`text`/`rawdict`/`texttrace`/`images`/`drawings`) presentes, e `text_evidence`/`image_evidence`/
  `drawing_evidence`/`evidence`/`source_hashes` todos não-vazios. Retorna `False` (nunca lança) para
  qualquer violação — o padrão seguro é sempre "continua bloqueando".
- `verify_source_hashes_match(record, ledger, corpus_root) -> issue | None`: re-hasheia o(s)
  documento(s) reais no disco agora e compara contra o que o registro declara — uma fonte
  substituída (mesmo nome, bytes diferentes) invalida a isenção automaticamente (Seção 18/19).

`data/manifests/source-availability-2008.yaml`: 1 pacote + 2 registros (D09, D10), ambos confirmados
`True` pelo gate (verificado nesta fase, Seção L/M).

## P. Política de gold

Decisão explícita (seguindo a mesma disciplina conservadora já estabelecida pela Fase 3T ao recusar
uma extensão elaborada do blocker ledger): **`gold.py`/`GoldManifest` não foi alterado**. Avaliação
em ordem, como o prompt exige:

1. **Status existente já suficiente?** Sim — `needs_review_count`/`unresolved_question_ids`
   (já existentes) permanecem a representação literal e honesta de "não verificado, ainda" no
   nível do `Question`; a *interpretação* de que essa não-verificação é uma limitação de fonte
   adjudicada, e não um defeito, já vive corretamente em `blocker-ledger-2008.yaml` (`status:
   source_unavailable`, desde a Fase 3T) e agora, com evidência completa, em
   `source-availability-2008.yaml`. `gold.py`'s próprio job (hash-lock, "algo mudou desde o
   último `build-gold`?") nunca precisou saber *por que* uma questão está `needs_review` — essa
   é exatamente a separação de responsabilidades que `readiness.py` já existe para prover
   (docstring do próprio módulo: "verify-gold only proves absence of drift... assess-readiness
   answers... is this course ready").
2. Não foi necessário adicionar metadado de limitação ao gold (a limitação já vive, de forma mais
   rica e re-verificável, em `source-availability-2008.yaml`).
3. Não foi criado nenhum novo `GoldMaturity`/status (`verified_with_source_limitation` não foi
   introduzido) — a maturidade de 2008-b permanece `provisional`, honestamente (nunca `validated`
   enquanto D09/D10 não tiverem seu próprio artefato, mesmo que a ausência seja comprovada e
   permanente).

O gold de 2008-b continua reportando, literal e corretamente: `verified=78, needs_review=2,
unresolved_question_ids=[D09, D10]` — nunca escondendo a ausência, nunca declarando completude
documental. `enade verify-gold`'s próprio output já nomeia o denominador (`"(80 questions match
...)"`) e separa `verified`/`needs_review` (Seção D).

## Q. Política de readiness

`src/enade/readiness.py` ganhou dois parâmetros novos e opcionais em `assess_readiness`
(`source_availability_path`, `corpus_root`) — comportamento 100% inalterado quando omitidos (todo
teste pré-existente passa sem modificação, Seção V). Quando fornecidos: um `subject_id` cujo
registro em `source-availability-<year>.yaml` passa `is_confirmed_unavailable` **e**
`verify_source_hashes_match` (hash ainda bate com o arquivo real no disco) tem seus achados
`question_not_verified`/`missing_answer_standard` marcados `structural=False` — exatamente o mesmo
padrão já usado por `accepted_non_material_difference` (Fase 2F), nunca escondido de
`report.blockers`, apenas excluído do cômputo de `ready`. Um registro `source_ambiguous`/
`source_not_checked` gera, ao contrário, um achado **sempre estrutural** (nunca uma isenção por
evidência incompleta). Um `source_hash_mismatch` detectado em tempo real também gera um achado
sempre estrutural, e a isenção correspondente nunca é concedida (Seção 18/19).

Novo campo `ReadinessReport.source_limitations: tuple[SourceAvailabilityRecord, ...]` — os registros
que efetivamente concederam uma isenção, para exibição separada (Seção S) — e uma nova propriedade
`source_completeness` ("complete"/"incomplete"), que **nunca** alimenta `ready`/`classification`
(Seção 11: as duas perguntas continuam sendo respondidas separadamente).

`enade assess-readiness` (CLI) ganhou `--corpus-root` (para o hash-check) e
`--ready-with-source-limitations-label` (default `READY_FOR_2011_WITH_SOURCE_LIMITATIONS`) — usado
apenas quando `report.ready and report.source_limitations`; caso contrário o comportamento e o
output são idênticos aos de antes desta fase (2011/2021 confirmados, Seção U).

## R. Blockers versus limitações

Distinção formalizada e aplicada: um **blocker acionável** (ex.: D59 antes da Fase 3U — imagem real
presente, extrator falhando em extraí-la) continua bloqueando incondicionalmente. Uma **limitação
externa não-acionável** (D09/D10, agora) nunca desaparece do registro (`status: source_unavailable`
permanece; nunca vira `resolved`), permanece visível no gold e no readiness, e deixa de bloquear o
teste de engenharia **somente** por esta política explícita, gated por evidência completa — nunca
como efeito colateral silencioso de qualquer outro mecanismo. Reabre automaticamente
(`verify_source_hashes_match`) se uma fonte válida aparecer (Seção 18, testado na Seção V).

## S. Explicabilidade da CLI

`enade assess-readiness` agora imprime três seções sempre separadas e sempre presentes (mesmo
quando vazias, `0`), nunca escondendo D09/D10 por terem deixado de bloquear:

```text
  actionable blockers: 0
  source limitations: 2
    - sa-2008-d09-answer-standard (enade-2008-computing-d09, answer_standard): expected 2008/b3_padrao.pdf [2008-b-computacao] - ...
    - sa-2008-d10-answer-standard (enade-2008-computing-d10, answer_standard): expected 2008/b3_padrao.pdf [2008-b-computacao] - ...
  informational findings: 0
```

Cada limitação mostra: ID (`source_availability_id`), questão (`subject_id`), artefato
(`artifact_type`), pacote-fonte (`source_package_id`), fonte esperada (`expected_source`) e efeito
(`impact`) — determinístico, sem caminhos temporários. Saída literal completa na Seção C/Y.

## T. Reversibilidade com nova fonte

Testado explicitamente (`test_source_hash_mismatch_reopens_blocking`,
`test_verify_source_hashes_match_detects_mismatch`): se `2008/b3_padrao.pdf` fosse substituído por
um arquivo com o mesmo nome mas conteúdo diferente (hash diferente), `verify_source_hashes_match`
detecta a divergência, a isenção não é concedida, um achado sempre-estrutural
`source_hash_mismatch` aparece, e os dois achados originais de D09/D10 voltam a bloquear
automaticamente — nenhum waiver antigo sobrevive a uma fonte nova. Um waiver antigo nunca é apagado
do histórico (o registro em `source-availability-2008.yaml` continua existindo, documentando a
adjudicação feita contra o hash antigo) — apenas deixa de se aplicar.

## U. Shadow mode

O mecanismo só é consultado quando `data/manifests/source-availability-<year>.yaml` existe —
verificado: **apenas** `source-availability-2008.yaml` existe; 2011 e os três cursos de 2021 não têm
arquivo correspondente, portanto `source_availability_path=None` é passado para
`assess_readiness`, e o novo código é estruturalmente inatingível para eles (nunca uma questão de
sorte/coincidência de dados). Confirmado por execução real:

```text
2011  --ready-label READY_FOR_LEGACY_LAYOUT_TEST --corpus-root data/raw/geacc-enade:
  READY_FOR_LEGACY_LAYOUT_TEST, source completeness: complete, actionable blockers: 0,
  source limitations: 0, informational findings: 1 (Q34, inalterado desde a Fase 3T)
2021 CC-B: READY_FOR_2011, source completeness: complete, source limitations: 0, 0 findings
```

Nenhuma outra ausência (2011/2021) foi convertida em limitação de fonte — o resultado é exatamente
"nada muda", nunca presumido, sempre confirmado pela execução real acima.

## V. Testes e quality gates

```text
baseline = 844
novos = 23 (14 em tests/test_source_availability.py, 9 em tests/test_readiness.py)
total final = 867 (confirmado via execução real: 867 passed)
ruff check .               : All checks passed!
ruff format --check .      : 423 files already formatted
mypy src                   : Success: no issues found in 61 source files
enade validate-schema      : 13/13 fixture(s) valid
enade validate-manifest    : OK (0 warning(s))
enade audit-extraction (2008-b/2011/2021 x3): 80/55/40/40/40 OK
enade verify-gold + assess-readiness (2008-b, 2011, 2021 CC-B): consistentes com as
  Seções C/Q/S acima
```

Cobertura dos 23 novos testes: disponibilidade de fonte (registro totalmente evidenciado,
método de busca faltando, evidência vazia estilo-D59, não revisado, status não-confirmado, pacote
ausente, páginas incompletas, hash batendo, hash divergente, arquivo/pacote ausente); readiness
(isenção de `missing_answer_standard`, isenção de `question_not_verified` sem duplicar o registro
de limitação, ausência de método de busca ainda bloqueia, evidência de imagem vazia ainda bloqueia,
hash divergente reabre o bloqueio, `source_ambiguous` sempre bloqueia, `corpus_root` omitido nunca
concede isenção, `source_availability_path` omitido não muda nada, `source_completeness`
"complete" quando não há limitações). Todos os testes pré-existentes de `test_readiness.py`
(20) e `test_blocker_ledger.py` (inalterado) continuam passando sem modificação.

## W. Reprodutibilidade e drift

Regeneração completa (2008-b/2011/2021 x3) comparada, byte-a-byte, contra o corpus canônico
(`diff -rq`) **e** contra a captura SHA-256 de 413 arquivos feita antes de qualquer edição
(Seção C): **zero diferença** em ambos os casos, para todos os anos/cursos. Duas execuções
independentes adicionais de `enade extract --year 2008 --course all-computing` (run A run B)
comparadas entre si: **zero diferença**. Duas execuções independentes de
`enade assess-readiness --year 2008 --course all-computing` (mesmos labels): saída textual
byte-idêntica. Nenhum campo com timestamp não-determinístico foi introduzido em nenhum manifest
novo ou modificado.

## X. Arquivos e estado Git final

Novos:
```text
src/enade/extraction/source_availability.py
data/manifests/source-availability-2008.yaml
tests/test_source_availability.py
docs/phase-3z-report.md
```

Modificados:
```text
src/enade/readiness.py               (+ source_availability_path/corpus_root em
                                        assess_readiness; + ReadinessReport.source_limitations/
                                        source_completeness)
src/enade/cli.py                     (assess-readiness: + --corpus-root,
                                        --ready-with-source-limitations-label; saída dividida em
                                        actionable/source limitations/informational)
src/enade/extraction/blocker_ledger.py (+ Blocker.source_limitation_id, opcional)
data/manifests/blocker-ledger-2008.yaml (D09/D10: evidência expandida com forense de
                                        imagens/drawings/texttrace; source_limitation_id
                                        cross-referenciando o novo ledger; resolution preenchido;
                                        visual_validation: failed -> passed, ver Seção Y)
tests/test_readiness.py              (+9 testes)
```

Nenhum arquivo removido. Nenhum arquivo scratch remanescente (nenhum script de diagnóstico
temporário foi deixado no repositório; todos os diretórios `/tmp/phase3z_*` usados durante a
investigação foram explicitamente apagados antes da conclusão da fase).

`git status --short` final:

```text
 M data/manifests/blocker-ledger-2008.yaml
 M src/enade/cli.py
 M src/enade/extraction/blocker_ledger.py
 M src/enade/readiness.py
 M tests/test_readiness.py
?? data/manifests/source-availability-2008.yaml
?? src/enade/extraction/source_availability.py
?? tests/test_source_availability.py
?? docs/phase-3z-report.md
```

Nenhum commit, push, PR, merge ou tag foi criado. `master`/`origin/master` inalterados
(`a5dfaab0c105150df3a7201c16547708cef45292`, confirmado idêntico ao início da fase).

## Y. Veredito e recomendação

**Tentativa rejeitada**: considerei inicialmente confiar apenas em `search_methods` (a lista
declarada de métodos usados) sem também exigir `pages_scanned` cobrir exatamente todas as páginas do
documento — rejeitada após reler a Seção 19 do prompt ("lista incompleta de páginas verificadas"
deve bloquear o waiver) e reconhecer que uma lista de páginas parcial, mesmo com os 5 métodos
"declarados", não prova busca exaustiva. Corrigido: `is_confirmed_unavailable` agora cruza
`pages_scanned` contra o `page_count` real do documento referenciado no pacote.

**Correção feita, fora do estritamente pedido, mas justificada por evidência**: `blocker-ledger-
2008.yaml`'s próprio campo `visual_validation` de D09/D10 estava `failed` desde a Fase 3T — uma
leitura ambígua (poderia sugerir "a verificação visual encontrou um problema", quando o fato real é
"a busca exaustiva confirmou corretamente a ausência"). Corrigido para `passed` nesta fase, já que a
Fase 3Z's própria auditoria visual/estrutural (texto+imagens+drawings) foi, ela mesma, bem-sucedida
em confirmar a ausência. Documentado aqui para transparência, nunca escondido como uma mudança
incidental.

**Nenhuma regressão encontrada.** D59, Q45, Q55, Q8, D40, Q38, 2011 e os três cursos de 2021
permanecem byte-idênticos e com o mesmo comportamento de readiness de antes desta fase (Seções N/U/W).

O veredito real e literal do gate, com os rótulos convencionais já usados desde a Fase 3T:

```text
assess-readiness --year 2008 --course all-computing:
  READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_LIMITATIONS
ACTIONABLE_BLOCKERS = 0
SOURCE_LIMITATIONS = 2
INFORMATIONAL_FINDINGS = 0
```

Este é um `READY_FOR_2008_ENGINEERING_TEST` qualificado — nunca `GENERALIZATION_SUCCESS`, nunca uma
alegação de completude documental. D09/D10 permanecem limitações documentais permanentes e visíveis
do pacote atual.

**Recomendação**: com o piloto de 2008-b agora `READY_FOR_2008_ENGINEERING_TEST_WITH_SOURCE_
LIMITATIONS`, recomendo revisão humana explícita de todo o trabalho acumulado (Fases 3A–3Z) antes de
qualquer commit — nenhuma destas fases commitou nada por conta própria (as poucas exceções já
documentadas em fases anteriores foram commits externos ao processo desta sessão, nunca desta
sessão em si). Considero o piloto de 2008-b, como teste de engenharia de layout legado, encerrado
nesta condição qualificada. D09/D10 devem permanecer, permanentemente, como limitações documentais
do pacote-fonte atual — nunca reabertas como defeito do parser, nunca "resolvidas" por fabricação.
Não iniciar automaticamente outro ano/bundle. Se uma fonte válida para os padrões de resposta de
D09/D10 aparecer no futuro, a política já criada nesta fase reabre a obrigação automaticamente
(Seção T) — não é necessário nenhum trabalho adicional de infraestrutura para esse dia, apenas
atualizar `source-availability-2008.yaml` com o novo hash/evidência e rodar `enade extract`
novamente.
