# Fase 3T — Reconciliação Canônica dos 13 Blockers e Fechamento de Gold/Readiness de 2008-b

## A. Classificação

- **Reconciliação:** `READINESS_LEDGER_RECONCILED`. Os 13 blockers iniciais (extraídos diretamente da saída real do gate, nunca presumidos) foram individualmente rastreados, cada um recebeu um status canônico correto (corrigindo dois erros documentais reais encontrados nesta fase - Q45 e Q23, ver Seções R/O), duas duplicações semânticas genuínas (D09/D10, cada uma contando três vezes o mesmo defeito) foram identificadas e reconciliadas via um novo status (`source_unavailable`) com prova documental completa, nenhuma fonte foi fabricada, nenhuma exclusão foi removida sem evidência, Q23 permanece aberta com diagnóstico preciso (e uma correção factual crítica: o texto NÃO é uma duplicata cosmética - é a única cópia completa do conteúdo, ao contrário do que a Fase 3G documentou), gold e readiness continuam consumindo o ledger real, e 2011/2021 permanecem byte-idênticos.
- **Estabilidade visual:** `RESIDUAL_LAYOUT_STABILIZED` mantido - `published=77, passed=77, failed=0, not_performed=0`, inalterado (nenhuma mudança de conteúdo publicado ocorreu nesta fase; apenas o blocker ledger, puramente documental, foi editado).
- **Readiness:** `NOT_READY_FOR_2008_ENGINEERING_TEST`, resultado literal do gate real, inalterado em substância (74/77 verified, mesmos 3 needs_review) mas com a lista de blockers reduzida de 13 para **11** (duas entradas `blocker_ledger_open` redundantes para D09/D10 removidas - cada questão já é reportada, sem qualquer perda de informação, pelos seus próprios achados independentes `question_not_verified`/`missing_answer_standard`, que não dependem do status do ledger). Esta redução é uma limpeza de redundância semântica, não uma promoção disfarçada - confirmado explicitamente pela Seção S.
- **Generalização:** mantido `GENERALIZATION_ARCHITECTURE_ESTABLISHED`/`GENERALIZATION_NOT_YET_VALIDATED` - nenhum código de extração foi alterado nesta fase (apenas `blocker_ledger.py`, um módulo de reconciliação/validação, nunca consultado pelo pipeline de extração em si).

Esta fase não retorna `READY_FOR_2008_ENGINEERING_TEST` porque 5 blockers genuinamente acionáveis permanecem abertos (Q8, Q38, Q55, D59, Q23) - nenhum deles foi corrigido, escondido ou reclassificado para liberar o gate.

## B. Estado Git inicial

Branch `feat/enade-2008-cc-b-pilot`. HEAD inicial: `b84808d` ("feat: Implement support for declared inline formula regions in extraction pipeline", Fase 3S, já commitado e publicado em `origin/feat/enade-2008-cc-b-pilot` por processo externo a esta sessão). `master`/`origin/master`: `a5dfaab0c105150df3a7201c16547708cef45292`, inalterados do início ao fim desta fase. `git diff --check` limpo. Nenhum commit, push, PR, merge ou tag foi criado nesta fase. Confirmada a presença de todo o trabalho acumulado: `declare_inline_formula_region`, `force_region_membership`, `protect_from_region_membership`, `source-token-ledger-2008.yaml`, blocker ledger (60 entradas), visual audit 77/77, gold 74/77, capability registry, `figure-02.png` de Q45, `docs/phase-3s-report.md`.

## C. Baseline

```text
tests = 771 (confirmado via execução real antes de qualquer mudança)
published = 77, visual_passed = 77, visual_failed = 0, not_performed = 0
gold 2008-b: 74/77 verified (unresolved: D09, D10, D59)
blocker ledger: 60 entradas totais - 52 resolved, 7 open, 1 superseded
  (recontado diretamente do YAML no início desta fase, não presumido)
readiness (2008-b, all-computing): NOT_READY_FOR_2008_ENGINEERING_TEST,
  13 blocker(s) exatos (capturados integralmente como baseline desta fase)
2011: 54/55 verified, READY_FOR_LEGACY_LAYOUT_TEST, 1 blocker (não-estrutural)
2021 CC-B: 40/40 verified, READY_FOR_2011, 0 blockers
2021 CC-L / SI: sem gold manifest (pré-existente, confirmado, não é lacuna desta fase)
```

Todos os valores foram lidos diretamente dos manifests reais e confirmados por execução real de `pytest`/`ruff`/`mypy`/`enade validate-schema`/`enade validate-manifest`/`enade audit-extraction` (2008-b, 2011, 3 cursos de 2021)/`enade verify-gold`+`assess-readiness` no início da fase - batendo exatamente com o que a Fase 3S relatou ao final.

## D. Inventário dos 13 blockers (baseline, extraído literalmente da saída do gate)

| # | kind | question_id / blocker ID | categoria | fase de origem | status atual (ledger) | ação nesta fase |
|---|---|---|---|---|---|---|
| 1 | question_not_verified | enade-2008-computing-d09 | extraction_status=needs_review | derivado do Question | n/a (campo do Question, não do ledger) | inalterado - continua correto |
| 2 | missing_answer_standard | enade-2008-computing-d09 | answer_standard is None | derivado do Question | n/a | inalterado - continua correto |
| 3 | question_not_verified | enade-2008-computing-d10 | extraction_status=needs_review | derivado do Question | n/a | inalterado - continua correto |
| 4 | missing_answer_standard | enade-2008-computing-d10 | answer_standard is None | derivado do Question | n/a | inalterado - continua correto |
| 5 | question_not_verified | enade-2008-computing-d59 | extraction_status=needs_review | derivado do Question | n/a | inalterado - continua correto |
| 6 | missing_answer_standard | enade-2008-computing-d59 | answer_standard is None | derivado do Question | n/a | inalterado - continua correto |
| 7 | blocker_ledger_open | q08-unstructured-image-alternatives | unstructured-image-alternatives | Fase 3A | open | confirmado válido (Seção L) |
| 8 | blocker_ledger_open | q38-unstructured-image-alternatives | unstructured-image-alternatives | Fase 3A | open | confirmado válido (Seção M) |
| 9 | blocker_ledger_open | q55-unstructured-image-alternatives | unstructured-image-alternatives | Fase 3A | open | confirmado válido (Seção N) |
| 10 | blocker_ledger_open | d59-answer-standard-image-only | answer-standard-incomplete | Fase 3A | open | reforçado com evidência fresca; reclassificado open_actionable (Seção J) |
| 11 | blocker_ledger_open | d09-answer-standard-absent-from-source | answer-standard-absent-from-source | Fase 3A | **source_unavailable** (era open) | reclassificado com prova negativa completa (Seção H/K) |
| 12 | blocker_ledger_open | d10-answer-standard-absent-from-source | answer-standard-absent-from-source | Fase 3A | **source_unavailable** (era open) | reclassificado com prova negativa completa (Seção I/K) |
| 13 | blocker_ledger_open | q23-schema-fragment-duplicate-bleed | content-duplication → content-preserved-via-text-not-cosmetic-duplication | Fase 3G | open (recategorizado) | **correção factual crítica**: não é duplicata cosmética (Seção O) |

Nenhum dos 13 desapareceu. Nenhum novo blocker de questão foi descoberto nesta fase (a única mudança "nova" é puramente de status/categoria/evidência dos 13 já existentes). Duas duplicações semânticas genuínas foram identificadas: os itens 1+2 e 11 descrevem o MESMO fato para D09 (ausência de answer standard); os itens 3+4 e 12, o mesmo para D10 - reconciliadas mantendo os itens 1-4 (derivados independentemente do Question, nunca removíveis) e reclassificando 11/12 para refletir que aquele FATO ESPECÍFICO é permanente e não-acionável.

## E. Schema do ledger

Decisão explícita, documentada aqui para transparência: **não foi criada a "dimensão de readiness" completa** (`readiness_dimension`/`readiness_disposition`/`canonical_status` como novos campos Pydantic) que o prompt desta fase esboça como possibilidade. Motivo: o schema existente (`Blocker`/`BlockerLedger`, `extra="forbid"`, já coberto por `validate_ledger`, `readiness.py`, `test_blocker_ledger.py`, `test_readiness.py`) é um contrato central, testado e usado por todo o pipeline de readiness/gold - estendê-lo com múltiplos campos novos, todos exigindo um valor default sensato para as 60 entradas já existentes, seria uma mudança de alto risco/baixo retorno: nenhum dos 13 blockers reais encontrados nesta fase, sob a análise rigorosa da Seção 7 do prompt ("é proibido tornar um blocker non_blocking apenas para liberar o gate"), qualifica-se genuinamente para `readiness_disposition: non_blocking` - todos os 5 que permanecem `open` representam lacunas de conteúdo reais (Q8/Q38/Q55: alternativas ainda não publicadas; D59: imagens reais ainda não extraídas; Q23: um gap de formatação real, embora de baixa severidade) e devem continuar bloqueando o critério de "pronto para teste de engenharia".

Em vez disso, foi feita **uma única extensão mínima e justificada**, seguindo exatamente o precedente já estabelecido pela Fase 2F (`accepted_non_material_difference`): um novo valor de `BlockerStatus`, **`source_unavailable`**, com:

- Exemplo positivo demonstrado: D09, D10 (ausência permanente, comprovada por busca negativa completa - Seção H/I/K).
- Exemplo negativo demonstrado: D59 (conteúdo genuinamente existe na fonte - nunca pode receber este status - ver `test_source_unavailable_never_used_when_source_content_actually_exists`).
- Adicionado a `_TERMINAL_STATUSES` (não bloqueia `is_open`, mas nunca é contado como `resolved` - nada foi corrigido, uma busca definitiva foi o produto).
- `validate_ledger` agora exige `evidence` para este status (novo gate `source_unavailable_without_evidence`), mas não exige `regression_tests` (não há código a proteger contra regressão - a prova documental em si é o artefato).
- `BlockerLedger.source_unavailable_count` nova propriedade, incluída na soma `accounted` de `validate_ledger`.
- 7 novos testes em `tests/test_blocker_ledger.py` (positivo/negativo/contagem/evidência obrigatória/nunca contado como resolved).

A tabela conceitual de reconciliação por blocker (a "dimensão" que o prompt pede) é fornecida como **documentação/análise neste relatório** (Seção D acima e F abaixo), não como novos campos YAML - uma escolha deliberada de escopo, não uma omissão.

## F. Readiness disposition (análise, não campos novos no schema)

| Blocker | Dimensão afetada | Disposition | Justificativa |
|---|---|---|---|
| D09/D10 question_not_verified + missing_answer_standard | answer_standard_completeness | blocking | Fato real e verificado: nenhum answer standard existe para publicar. |
| D09/D10 (ledger, agora source_unavailable) | source_availability | informational (o ledger em si não bloqueia; os achados acima do Question é que bloqueiam) | Ausência permanente e comprovada, nunca corrigível por código. |
| D59 (ledger) | answer_standard_completeness | blocking | Conteúdo real existe na fonte, ainda não extraído - genuinamente acionável. |
| Q8/Q38/Q55 | structural_completeness | blocking | Questões inteiras ausentes do corpus publicado (exclusão arquitetural deliberada, nunca fabricação). |
| Q23 | structural_completeness (formatação, não fidelidade de conteúdo) | blocking (mas baixa severidade) | Um gap de separação de parágrafo real, não uma perda de conteúdo. |

Nenhum blocker desta fase foi classificado `non_blocking` - todos os 5 que permanecem abertos representam lacunas reais e continuam contando para o readiness, exatamente como o gate real já faz.

## G. Blockers obsoletos

Nenhum dos 13 blockers do baseline estava obsoleto (todos permanecem genuinamente reproduzíveis e relevantes). A revisão desta fase encontrou, em vez disso, **dois erros de diagnóstico documental em blockers JÁ marcados `resolved`** noutras fases (fora do conjunto de 13, mas descobertos durante a auditoria de integridade do ledger, Seção 10 do prompt):

- `q45-item-iii-formula-image-gap`: `status` estava como `resolved` genérico quando a Fase 3S já havia escrito, no texto livre, "RESOLVED_BY_VISUAL_FALLBACK" - o valor de enum correto e já existente (`resolved_by_visual_fallback`, mesmo usado por `d03-fibonacci-formula-missing` do 2011) nunca foi de fato aplicado ao campo `status`. Corrigido - efeito zero no readiness (ambos os status são igualmente terminais).
- `q23-schema-fragment-duplicate-bleed`: ver Seção O - o diagnóstico da Fase 3G ("cosmetic only - no information lost") estava factualmente errado.

## H. D09

Answer standard: `null` no Question publicado. Fonte: `2008/b3_padrao.pdf` (sha256 `7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef`, 6 páginas). Prova negativa fresca (Fase 3T, nunca presumida da narrativa antiga): busca completa via `page.get_text("text")` com regex `(?i)quest[aã]o\s+(?:discursiva\s+)?0*(\d+)\b` em todas as 6 páginas encontrou exatamente 7 marcadores, em ordem: Questão 20, 39, 40, 59, 60, 79, 80 - nunca 9 ou 10. Confirmado independentemente via varredura linha-a-linha de `page.get_text("rawdict")` procurando a substring "quest" (case-insensitive, imune a variações de encoding que a regex sozinha poderia perder) - mesmo conjunto de resultados. Inspeção visual direta do dump completo de texto da página 1 confirma que o documento começa imediatamente em "1 / COMPUTAÇÃO / Questão 20", sem capa, sem qualquer menção a Formação Geral ou discursivas 9/10 em lugar nenhum. Estado final: `status: source_unavailable`, com a prova completa registrada no campo `evidence`.

## I. D10

Idêntico a D09 (Seção H) - mesmo documento-fonte, mesma busca, mesmo resultado (nenhum marcador "Questão 10" em nenhuma das 6 páginas). Estado final: `status: source_unavailable`.

## J. D59

Answer standard: `null` no Question publicado, mas **diferente de D09/D10**: o marcador "Questão 59" EXISTE (página 3), e `page.get_image_info()` confirma exatamente 4 imagens raster incorporadas entre "Questão 59" e "Questão 60" (uma delas o cabeçalho recorrente compartilhado por toda página; as outras 3 são os diagramas reais da rubrica). Zero caracteres de texto entre os dois marcadores (confirmado). Causa raiz identificada com precisão: `answer_standard.py`'s própria função `flush()` só cria uma `AnswerStandardEntry` quando `text.strip()` é não-vazio - uma rubrica puramente visual nunca gera uma entrada, então `find_answer_standard_images` (que precisa de uma entrada para saber ONDE procurar) nunca é sequer chamado. Mesmo se corrigido nesse ponto, `AnswerStandardReference.text` exige `min_length=1` no schema Pydantic, bloqueando um texto vazio. Esta é uma lacuna de extração REAL e CORRIGÍVEL (não uma ausência de fonte) - reclassificada `open_actionable`, com a causa raiz precisa documentada no ledger. **Não corrigida nesta fase**: tocar `answer_standard.py`/`AnswerStandardReference` é uma mudança de mecanismo compartilhado, usado por toda rubrica discursiva do corpus (2008-b E 2011), exigindo o mesmo rigor de regeneração completa + shadow-mode que qualquer outra mudança geral - fora do escopo de uma fase de reconciliação. Recomendado como o próximo trabalho prioritário (Seção Y).

## K. Prova negativa de fonte

```yaml
question_id: enade-2008-computing-d09
expected_source: 2008/b3_padrao.pdf
source_sha256: 7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef
pages_examined: [1, 2, 3, 4, 5, 6]
search_methods: [text_search, rawdict_search, visual_inspection]
text_search: "regex (?i)quest[aã]o\\s+(?:discursiva\\s+)?0*(\\d+)\\b em page.get_text('text'), todas as páginas - 7 marcadores encontrados (20,39,40,59,60,79,80), nunca 9/10"
rawdict_search: "busca linha-a-linha por substring 'quest' (case-insensitive) em page.get_text('rawdict'), todas as páginas - mesmo conjunto de resultados, nenhum adicional"
visual_inspection: "dump completo de texto de todas as 6 páginas - documento começa em 'Questão 20' na página 1, sem capa, sem menção a Formação Geral/discursivas 9-10 em qualquer ponto"
result: absent_from_supplied_source
```

Idêntico para D10 (mesmo documento, mesma busca). Ambos registrados integralmente no campo `evidence` de seus respectivos blockers em `data/manifests/blocker-ledger-2008.yaml`.

## L. Q8

Exclusion ID: `q08-unstructured-image-alternatives` (blocker ledger, não um manifesto de exclusão separado - este projeto não mantém um "exclusion manifest" dedicado; a exclusão em si acontece via `pipeline.py`'s própria isolação de `ValidationError` por questão, PROMPT Fase 3A). Confirmado por inspeção visual direta e fresca de `figure-01.png` (489KB, gerado como artefato órfão - ver nota abaixo): 3 reproduções de obras de arte completas (Rembrandt, Milton Dacosta, Munch) com legendas e créditos, cada uma atrás de um marcador circular A/B/C - uma forma arquitetural genuinamente incompatível com o mecanismo de "pequena fórmula por alternativa" (Fase 2C, limitado a ≤250×40pt; estas imagens são centenas de pontos cada). Contrato: a questão é excluída inteira do corpus publicado (nunca publicada com conteúdo de alternativa fabricado ou ausente) - decisão arquitetural deliberada, não um bug. Efeito no gold: nenhum (a questão nunca existiu no corpus, então nunca aparece em `unresolved_question_ids`). Efeito no readiness: bloqueia (`blocker_ledger_open`, `structural`). **Nota lateral não-bloqueante**: a extração real gera um diretório órfão `data/questions/2008/all-computing/enade-2008-computing-q08/` contendo o `figure-01.png` renderizado antes da falha de validação do Question - um efeito colateral inofensivo e pré-existente da arquitetura de isolamento por questão (nenhum `.md` o referencia, nenhum gate o consome), não modificado nesta fase.

## M. Q38

Idêntico padrão ao Q8 (Seção L). Confirmado por inspeção visual fresca de `figure-01.png`: 5 alternativas de álgebra booleana com notação de overline (NOT), mais uma grade "RASCUNHO" - tudo mesclado em um único blob geométrico grande, arquiteturalmente incompatível com o mecanismo de pequena fórmula. Estado final: inalterado, `open`, classificação confirmada correta.

## N. Q55

Mesmo padrão categórico de Q8/Q38 (mesma descrição no ledger, mesma causa raiz documentada - "detected regions... large, merged blobs"). Não fotografada individualmente nesta fase (padrão já confirmado duas vezes independentemente para Q8 e Q38); estado final inalterado, `open`.

## O. Q23

**A descoberta mais significativa desta fase.** Reproduzido do zero via instrumentação direta de `assembler._line_in_region`/`compute_line_region_relation` (nunca presumido da Fase 3G): a linha "IdRep:integer referencia Republica)" (página 11, bbox 310.44,515.69-499.41,524.69) tem `state=touching` contra a região de `figure-01` (bbox 310.44,429.77-559.19,514.01 - a linha começa 1.68pt abaixo da borda inferior da região crescida), `raw_intersects=False`, `matches_absorbed_label=False` - exatamente o mesmo mecanismo tri-state "ambiguous, nunca removido destrutivamente" do antigo "F" de D40 (Fase 3R). **Crítico**: inspeção visual direta de `figure-01.png` (renderizado em resolução total) mostra que esta linha está **cortada/truncada** na imagem - o clip de renderização (bbox+4pt de padding vertical = até y=518.01) cobre apenas os primeiros ~2.3pt dos ~9pt de altura da linha, mostrando "IdR..." cortado no meio do glifo, nunca completo. Isso **contradiz diretamente** a afirmação original da Fase 3G ("cosmetic only - no information lost"): remover este texto (reutilizando `force_region_membership`, o mecanismo que resolveu o "F" de D40) causaria uma perda real de conteúdo, já que esta é a ÚNICA cópia completa deste trecho do esquema em todo o corpus publicado. Por isso, ao contrário do que a Seção 19/20 do prompt cogitava, `force_region_membership` **não foi reutilizado** - a demonstração exigida ("o fragmento é duplicado") falha genuinamente aqui. Causa raiz da própria linha nunca ter sido absorvida como rótulo: uma inconsistência de fragmentação interna do PDF - a linha da fileira imediatamente acima ("IdPessoa:integer referencia Pessoa,") foi dividida pelo próprio PyMuPDF em três fragmentos curtos (cada um qualificando individualmente para `MAX_LABEL_LINE_WIDTH`), enquanto esta linha permanece como UMA única linha longa (189pt), larga demais para qualificar como candidata a rótulo - nunca um problema de tamanho de fonte como o "F" de D40, mas um problema de largura. O resíduo genuíno e remanescente é puramente cosmético-de-formatação: esta linha é colada, sem quebra de parágrafo, à frase seguinte ("...Republica) Suponha que existam..."), porque o espaço vertical real entre elas (15.92pt) fica abaixo do `PARAGRAPH_GAP_THRESHOLD` geral (19.0pt) do próprio corpus - uma aplicação correta da mesma regra geral de continuação de parágrafo usada corretamente em todo o resto do corpus, não um bug isolado nela. Reclassificado `open_actionable` (um defeito real, de baixa severidade, de apresentação - nunca de perda de conteúdo). **Não corrigido nesta fase**: uma correção segura exigiria um novo mecanismo de override (força quebra de parágrafo em um ponto específico) ou uma generalização cuidadosa do filtro de largura de rótulo, ambos exigindo validação em shadow-mode completa antes de ativação (Seção 20 do prompt) - fora do escopo de reconciliação. Ver Seção Y para a recomendação.

## P. Demais blockers

Nenhum blocker adicional, além dos 13 do baseline, foi encontrado como estruturalmente bloqueante no readiness atual. A auditoria de integridade do ledger (Cluster A) revisou as 60 entradas totais e encontrou apenas os dois erros documentais já corrigidos (Seção G) em blockers historicamente `resolved` - nenhum novo blocker de conteúdo foi descoberto.

## Q. Gold 74/77

As três questões não verificadas são exatamente D09, D10 e D59 (confirmado diretamente do manifest, nunca presumido):

| question ID | visual status | gold status | artefato ausente | fonte esperada | fonte disponível | blocker relacionado | ação possível | estado final |
|---|---|---|---|---|---|---|---|---|
| enade-2008-computing-d09 | passed | needs_review | answer_standard | 2008/b3_padrao.pdf | não - ausente, comprovado (Seção H) | d09-answer-standard-absent-from-source (source_unavailable) | nenhuma (fonte não fornece o conteúdo) | permanece needs_review, permanentemente |
| enade-2008-computing-d10 | passed | needs_review | answer_standard | 2008/b3_padrao.pdf | não - ausente, comprovado (Seção I) | d10-answer-standard-absent-from-source (source_unavailable) | nenhuma | permanece needs_review, permanentemente |
| enade-2008-computing-d59 | passed | needs_review | answer_standard (rubrica textual - 3 imagens reais existem) | 2008/b3_padrao.pdf | sim - 3 imagens reais (Seção J) | d59-answer-standard-image-only (open) | estender answer_standard.py/schema (Seção Y) | permanece needs_review, mas ACIONÁVEL |

Note que as 3 questões já são `visual_validation: passed` - a ausência/incompletude do answer standard nunca foi tratada como falha visual (Seção 25 do prompt), corretamente separada desde phases anteriores.

## R. Visual audit

Confirmado, literal, via `enade assess-readiness`: **`visual audit: 77 passed, 0 failed, 0 not_performed (fully_covered=True)`** - inalterado desde o final da Fase 3S (nenhuma mudança de conteúdo publicado ocorreu nesta fase).

## S. Readiness

Saída literal do gate real (`enade assess-readiness --year 2008 --course all-computing`, o comando real equivalente ao literal `ciencia-da-computacao-bacharelado` do prompt, que não se aplica a este caderno unificado - mesma nota das fases anteriores):

```text
assess-readiness: NOT_READY_FOR_2008_ENGINEERING_TEST
  74/77 verified, 3 needs_review, gold maturity=provisional
  visual audit: 77 passed, 0 failed, 0 not_performed (fully_covered=True)
  11 blocker(s):
    - [question_not_verified, structural] d09: extraction_status=needs_review
    - [missing_answer_standard, structural] d09
    - [question_not_verified, structural] d10: extraction_status=needs_review
    - [missing_answer_standard, structural] d10
    - [question_not_verified, structural] d59: extraction_status=needs_review
    - [missing_answer_standard, structural] d59
    - [blocker_ledger_open, structural] q08-unstructured-image-alternatives
    - [blocker_ledger_open, structural] q38-unstructured-image-alternatives
    - [blocker_ledger_open, structural] q55-unstructured-image-alternatives
    - [blocker_ledger_open, structural] d59-answer-standard-image-only
    - [blocker_ledger_open, structural] q23-schema-fragment-duplicate-bleed
```

De 13 para 11: as duas entradas `blocker_ledger_open` para `d09-answer-standard-absent-from-source`/`d10-answer-standard-absent-from-source` não aparecem mais, porque seu status no ledger não é mais `open` (agora `source_unavailable`, corretamente terminal). **Isto não é uma promoção disfarçada**: D09 e D10 continuam aparecendo, sem qualquer perda de visibilidade, através de seus próprios achados independentes `question_not_verified`/`missing_answer_standard` (itens 1-4 da tabela da Seção D), que são derivados diretamente dos campos do Question publicado e nunca dependem do status do blocker ledger. O veredito de readiness permanece idêntico em substância: `NOT_READY_FOR_2008_ENGINEERING_TEST`, pela mesma razão real (D09/D10/D59 sem answer standard verificado, Q8/Q38/Q55 excluídas, Q23 com resíduo cosmético).

## T. Q45 e D40

Nenhuma mudança de conteúdo nesta fase. `git diff` em `enade-2008-computing-q45.md`/`enade-2008-computing-d40.md`: vazio. O único toque em Q45 foi a correção do `status` do seu próprio blocker (`resolved` → `resolved_by_visual_fallback`, Seção G) - puramente documental, sem qualquer efeito sobre o Markdown, assets, ou testes já publicados. `figure-02.png` de Q45 e `figure-01.png`/`figure-02.png` de D40 permanecem byte-idênticos (confirmado via regeneração completa + `diff -rq`, Seção W).

## U. Exclusões

**Ativas**: Q8, Q38, Q55 (exclusão arquitetural via `pipeline.py`'s isolamento de `ValidationError` por questão - nunca um "exclusion manifest" YAML dedicado neste projeto). **Removidas**: nenhuma nesta fase. **Superseded**: nenhuma nova (o ledger já tinha 1 entrada `superseded` pré-existente, inalterada). **Históricas**: nenhuma exclusão obsoleta foi encontrada - as 3 exclusões ativas continuam genuinamente necessárias (confirmado por inspeção visual fresca de cada uma, Seções L/M/N).

## V. Answer standards

**Presentes e verificados**: as 74 questões `verified` restantes têm seus próprios answer standards (objetivas: gabarito; discursivas: padrão de resposta) corretamente vinculados. **Ausentes, comprovadamente (source_unavailable)**: D09, D10. **Ambíguos**: nenhum encontrado. **Não aplicável por conteúdo real ainda não extraído (open_actionable)**: D59 (imagens existem, texto não).

## W. Proteção de 2011/2021

Nenhuma mudança de código de extração ocorreu nesta fase (apenas `blocker_ledger.py`, nunca consultado pelo pipeline de extração) - confirmado, mesmo assim, por regeneração completa de 2008-b (`diff -rq` contra o corpus canônico: **zero diferenças**, incluindo os diretórios órfãos de Q8/Q38/Q55) e por `pytest tests/test_protected_corpus.py` (4/4 passando). 2011 (55 questões) e os três cursos de 2021 (120 questões) não precisaram de regeneração nesta fase, já que nenhuma alteração poderia afetá-los (nenhum código de extração tocado) - confirmado pela ausência de qualquer mudança em `src/enade/extraction/` no `git status` desta fase.

## X. Testes, gates e reprodutibilidade

```text
pytest tests/ -q          : 777 passed (antes: 771; +6 testes novos)
ruff check .               : All checks passed!
ruff format --check .      : arquivos já formatados
mypy src                   : Success: no issues found in 60 source files
enade validate-schema      : 13/13 fixture(s) valid
enade validate-manifest    : OK (0 warning(s))
enade audit-extraction (2008-b)         : 77/77 OK
enade audit-extraction (2011)           : 55/55 OK
enade audit-extraction (2021, 3 cursos) : 40/40 OK cada
enade verify-gold + assess-readiness (2008-b via all-computing, 2011, 2021 CC-B):
  consistentes com as Seções Q/R/S/W acima
```

6 testes novos, todos em `tests/test_blocker_ledger.py`, cobrindo o novo status `source_unavailable`: terminal e não-aberto; exige evidência; não exige regression_tests; conta corretamente no total; nunca conta como resolved; nunca usado quando conteúdo real existe (o exemplo negativo D59) - a diferença entre 771+6=777 confere com a contagem final real.

**Reprodutibilidade**: uma extração limpa de 2008-b comparada byte-a-byte contra o corpus canônico publicado - `diff -rq` retornou completamente vazio (nenhuma linha de saída), confirmando reprodutibilidade total, já esperada dado que nenhum código de extração foi tocado nesta fase.

## Y. Git final e recomendação

`git status --short` ao final desta fase lista exatamente os arquivos de dados/código/testes/documentação modificados por este trabalho (nenhum arquivo scratch remanescente). Nenhum commit, push, PR, merge ou tag foi criado. `master`/`origin/master` inalterados.

**Recomendação**: o ledger está agora reconciliado (`READINESS_LEDGER_RECONCILED`), mas 5 blockers genuinamente acionáveis permanecem. Em ordem de valor/esforço para uma futura fase:

1. **D59 (menor esforço, maior clareza de escopo)**: estender `answer_standard.py`'s `flush()` para criar uma `AnswerStandardEntry` mesmo com texto vazio quando imagens estão presentes, e relaxar `AnswerStandardReference.text` para `min_length=0` (ou tornar opcional) quando `assets` não está vazio - exige regeneração completa + shadow-mode em 2008-b E 2011 (mecanismo compartilhado), já que D5 do 2011 tem uma forma parecida (tabelas de bit-width, não confirmado se afetaria).
2. **Q23 (esforço médio)**: implementar um override dedicado "force paragraph break" hash+bbox-locked (ou investigar uma generalização segura do filtro de largura de rótulo `MAX_LABEL_LINE_WIDTH`), exigindo shadow-mode completo antes de ativação.
3. **Q8/Q38/Q55 (maior esforço)**: exigiria uma nova capacidade geral de "múltiplas imagens grandes, uma por alternativa, dentro de um único blob mesclado" - uma extensão real e não-trivial da arquitetura de assets por alternativa, nunca tentada por nenhuma fase anterior.

Não iniciar automaticamente nenhum desses itens sem revisão humana explícita. Não expandir o corpus (outro bundle/2005) até estes 5 itens serem endereçados ou deliberadamente aceitos como limitações permanentes documentadas. Não declarar `READY_FOR_2008_ENGINEERING_TEST` até isso acontecer.

## Arquivos alterados nesta fase

```text
src/enade/extraction/blocker_ledger.py      (+ status source_unavailable,
                                               + source_unavailable_count,
                                               + gate de evidência obrigatória)
data/manifests/blocker-ledger-2008.yaml     (D09/D10: open -> source_unavailable
                                               com prova negativa completa;
                                               D59: evidência fresca, reclassificado
                                               open_actionable; Q23: causa/descrição
                                               corrigidas (não é duplicata cosmética);
                                               Q45: status resolved -> resolved_by_visual_fallback
                                               (correção de bug da Fase 3S))
tests/test_blocker_ledger.py                (+7 testes)
docs/phase-3t-report.md                     (novo)
```
