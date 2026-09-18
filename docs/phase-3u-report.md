# Fase 3U — Suporte a Answer Standards Visuais e Fechamento do Blocker de D59

## A. Classificação

- **Capacidade visual:** `VISUAL_ANSWER_STANDARD_STABILIZED`. A única rubrica real de D59 foi preservada integralmente (imagem completa, legível, sem OCR, sem transcrição, sem LLM/VLM), zero rubrica ausente, zero rubrica duplicada, ownership comprovado por referência cruzada com o próprio enunciado publicado de D59, os assets estão cobertos pelo gold, D59 foi validada (`extraction_status: verified`, `visual_validation: passed`), D09/D10 permanecem `source_unavailable`, Q23 permanece byte-idêntica, 2011 e os três cursos de 2021 permanecem byte-idênticos, reprodutibilidade e gates estão limpos.
- **Estabilidade visual:** `RESIDUAL_LAYOUT_STABILIZED` mantido - `published=77, passed=77, failed=0, not_performed=0`, inalterado (nenhuma mudança na fidelidade visual do ENUNCIADO de nenhuma questão; a mudança desta fase é inteiramente no answer standard de D59, um artefato de proveniência separada).
- **Readiness:** `NOT_READY_FOR_2008_ENGINEERING_TEST`, resultado literal do gate real - **8 blockers** (reduzido de 11 ao final da Fase 3T: os dois achados `question_not_verified`/`missing_answer_standard` de D59 desapareceram, junto com sua própria entrada `blocker_ledger_open`, já que D59 agora tem um `answer_standard` real e verificado). Gold de 2008-b: **75/77 verified** (subiu de 74/77, conforme esperado pelo próprio prompt desta fase). D09/D10 continuam bloqueando genuinamente (ausência de fonte, comprovada, permanente); Q8/Q38/Q55 (exclusão arquitetural) e Q23 (formatação, não fidelidade) continuam abertos, intocados.
- **Generalização:** `GENERALIZATION_ARCHITECTURE_ESTABLISHED` para o novo mecanismo `visual_only_answer_standard` (G1, um único caso real publicado - D59) - `GENERALIZATION_NOT_YET_VALIDATED` mantido, sem promoção especulativa a G2/G3.

Nenhuma fonte foi fabricada; D09/D10 permanecem corretamente `source_unavailable`; nenhum ganho incidental foi publicado fora de D59.

## B. Estado Git inicial

Branch `feat/enade-2008-cc-b-pilot`. **Diferente de toda fase anterior**: o trabalho da Fase 3T NÃO havia sido commitado por nenhum processo externo antes do início desta fase - `HEAD` permanecia em `b84808d` (Fase 3S), com `blocker-ledger-2008.yaml`, `blocker_ledger.py`, `test_blocker_ledger.py` modificados e `docs/phase-3t-report.md` como arquivo novo, exatamente como a própria Fase 3T os deixou. Nenhuma dessas alterações foi descartada - o trabalho desta fase foi construído em cima delas, ainda no working tree, sem commit algum (mantendo a mesma disciplina de "nunca commitar" já estabelecida). `master`/`origin/master`: `a5dfaab0c105150df3a7201c16547708cef45292`, inalterados. `git diff --check` limpo.

## C. Baseline

```text
tests = 777 (confirmado via execução real: 777 passed)
published = 77, visual_passed = 77, visual_failed = 0, not_performed = 0
gold 2008-b: 74/77 verified (unresolved: D09, D10, D59)
readiness (2008-b): NOT_READY_FOR_2008_ENGINEERING_TEST, 11 blocker(s)
  (question_not_verified/missing_answer_standard para D09, D10, D59;
   blocker_ledger_open para q08/q38/q55/d59-answer-standard-image-only/q23)
2011: 54/55 verified, READY_FOR_LEGACY_LAYOUT_TEST, 1 blocker (não-estrutural)
2021 CC-B: 40/40 verified, READY_FOR_2011, 0 blockers
2021 CC-L / SI: sem gold manifest (pré-existente, confirmado)
b3_padrao.pdf sha256: 7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef
```

Todos os valores lidos diretamente dos manifests reais e confirmados por execução real de `pytest`/`ruff`/`mypy`/`enade validate-schema`/`enade validate-manifest`/`enade audit-extraction`/`verify-gold`/`assess-readiness` no início da fase - batendo exatamente com o que a Fase 3T relatou ao final.

## D. Diagnóstico de D59

`answer_standard.py`'s própria função `flush()` só criava uma `AnswerStandardEntry` quando `_lines_to_paragraphs(buffer).strip()` era não-vazio. Como a rubrica de D59 (página 3 de `b3_padrao.pdf`) não tem nenhuma linha de texto entre "Questao 59" e "Questao 60", `buffer` ficava vazio, `flush()` não fazia nada, e `find_answer_standard_images` (que depende de `entry.page_bounds`, só existente quando uma entrada é criada) nunca era sequer chamada - as imagens reais da rubrica nunca eram descobertas. Mesmo se essa barreira fosse removida, `AnswerStandardReference.text` exigia `min_length=1`, bloqueando `text=""` na camada de validação do modelo publicado. Demonstrado executavelmente (testes `test_parse_answer_standard_never_creates_entry_for_zero_text_zero_image` e a leitura direta do PDF real): `imagens presentes na fonte + texto vazio → answer standard descartado`, exatamente como o prompt descreve.

## E. Inventário das rubricas

**Correção crítica desta fase**: a Fase 3T havia documentado "3 imagens não-cabeçalho pertencentes a D59" - uma reverificação forense própria desta fase, respeitando os limites exatos do marcador (não apenas "a página menciona 59/60"), prova que isso estava **errado**. Página 3 tem 4 imagens no total:

| xref | bbox | pertence a | motivo |
|---|---|---|---|
| 47 | (71.25,35.0)-(524.25,71.75) | cabeçalho (chrome) | compartilhado por toda página, y muito acima do marcador "Questao 59" (y0=460.57) |
| 52 | (198.0,71.75)-(440.25,248.0) | **D40** (não D59) | y-range inteiramente ACIMA de "Questao 59" (y1=473.14); texto "B.4 A solucao abaixo..." (y=248.18-271.07), idêntico ao já publicado `answer_standard.text` de D40, confirma que esta é a continuação da rubrica de D40 (páginas 1-2-3) |
| 56 | (162.0,271.25)-(476.25,448.25) | **D40** (não D59) | mesmo motivo - ainda acima de "Questao 59" |
| 61 | (123.75,488.75)-(471.75,740.0) | **D59** (único real) | única imagem cujo próprio y-range cai inteiramente entre "Questao 59" (y1=473.14) e "Questao 60" (y0=752.32) |

D59 tem, portanto, **uma única rubrica real** - um diagrama de escalonamento estilo Gantt ("Caracteristicas das tarefas" / "Execucao simultanea (a)" / "Execucao simultanea (b) (alternativa)", rotulado T1/T2/T3/R1/R2). `asset_candidate_id`: `padrao-01`; `source_document`: `2008/b3_padrao.pdf`; `source_sha256`: `7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef`; `source_page`: 3; `bbox`: (123.75, 488.75, 471.75, 740.0); `colorspace`: Indexed(15,DeviceRGB); `bpc`: 4; sem máscara (`has-mask: False`); aparece uma única vez (nenhum placement duplicado).

## F. Boundaries

Região de D59 = do próprio final da linha do marcador "Questao 59" (y1=473.14) até o início da linha do próximo marcador "Questao 60" (y0=752.32), estritamente na mesma página do marcador (página 3) - nunca "por proximidade". Confirmado: o asset xref 61 está inteiramente dentro dessa janela (488.75-740.0 ⊂ 473.14-752.32); nenhum owner concorrente (D40 já possui suas próprias 3 imagens, atribuídas ao SEU PRÓPRIO marcador-a-marcador, sem sobreposição); fora de cabeçalho/rodapé (a imagem do cabeçalho está fora da janela, y muito menor que 473.14); a ordem de leitura é trivial (uma única imagem).

## G. Modo de extração

Extração direta da imagem incorporada (`page.get_image_info()` + `_render_bbox`/`render_answer_standard_asset`, o MESMO mecanismo já usado, sem alteração, por D3/D4/D40/D80) - preferida por preservar integralmente o conteúdo sem exigir composição de máscara (a imagem não tem máscara) nem vetores associados. Nenhuma nova função de renderização foi criada.

## H. Schema

`AnswerStandardReference.text` (antes `Field(..., min_length=1)`) passou a `Field(...)` (sem `min_length`) mais um `model_validator` novo, `_validate_text_or_assets_present`, exigindo `text.strip()` não-vazio OU `assets` não-vazio (nunca ambos vazios). Isso habilita, sem introduzir dois modelos concorrentes, os três modos: `text_only` (toda rubrica pré-Fase-3U, inalterada), `visual_only` (`text=""`, ≥1 asset - a nova forma de D59), `mixed` (texto real + assets reais - já a forma pré-existente de D3/D4/D40, intocada). O estado `text=""` + `assets=[]` permanece proibido em qualquer modo - um `ValidationError` explícito, testado (`test_answer_standard_rejects_empty_text_and_empty_assets`).

## I. Content blocks

D59 mantém `content_blocks: null` (como antes) - o `answer_standard` não usa nem precisa de `content_blocks` (é um campo de frontmatter YAML separado, nunca renderizado no corpo do Markdown - confirmado por inspeção de `markdown_format.py`, que nunca referencia `answer_standard` em lugar algum). Nenhum caption foi adicionado (a fonte não tem legenda para esta imagem); nenhuma transcrição foi colocada em `alt_text` (permanece `null`, igual a todo outro asset já publicado neste corpus - mesma decisão documentada na Fase 3S, Seção O, mantida por consistência).

## J. Assets

`padrao-01.png`: gerado via `_render_bbox` (lossless, determinístico, zoom idêntico a todo outro asset do corpus), sha256 `f4eb5673ba8008494788b545fc7084a6d9fd16fe903de92f509bb5bc0033783b` - confirmado idêntico em três execuções independentes (canônico + duas extrações limpas adicionais). Inspecionado visualmente em resolução total: diagrama completo, bordas do próprio quadro do desenho inteiramente visíveis, texto interno (rótulos T1/T2/T3/R1/R2, eixos numéricos) legível, nenhuma outra questão, cabeçalho ou rodapé presente no crop.

## K. Acessibilidade

Registrado estruturalmente via `text=""` (não apenas em uma nota narrativa): a rubrica não possui representação textual, não foi processada por OCR, não é pesquisável como texto. `alt_text` permanece `null`, mantendo a convenção uniforme já estabelecida em todo o corpus (nenhum asset publicado, em nenhuma fase, usa `alt_text` até hoje) - a limitação de acessibilidade está documentada no blocker ledger (`d59-answer-standard-image-only`) e nesta seção, não escondida.

## L. Safety oracle

```text
official visual rubrics = 1 (corrigido de "3" - a contagem incorreta da Fase 3T)
published visual rubrics = 1
missing = 0
duplicated = 0
foreign = 0 (as duas imagens de D40 na mesma página foram corretamente excluídas)
```

Confirmado: nenhuma imagem ausente, nenhuma duplicada, ordem trivialmente correta (uma imagem), owner correto (cross-referência com o enunciado de D59 já publicado - ambos tratam de escalonamento de tarefas T1/T2/T3), crop completo (bordas do diagrama inteiras), crop não contaminado (nenhuma outra questão visível), asset com hash real, asset coberto pelo gold, nenhum texto fabricado.

## M. Shadow mode

Como o mecanismo só ativa quando `buffer` está genuinamente vazio (zero texto), a regeneração completa dos 3 anos já serve como shadow-mode real: **zero** discursivas de 2011 (D01-D05, confirmado que todas já têm `answer_standard.text` não-vazio antes desta fase) e **zero** outras discursivas de 2008-b (D09/D10/D20/D39/D40/D60/D79/D80, todas com texto real) acionaram o novo caminho - apenas D59. Nenhuma mudança incidental foi publicada. Casos mistos (D40) e imagens decorativas (o cabeçalho da página 3) foram corretamente excluídos pela própria janela marcador-a-marcador, nunca por uma lista de exceções.

## N. D09/D10

Preservados exatamente como a Fase 3T os deixou: `status: source_unavailable`, prova negativa completa (busca em `page.get_text`/`page.get_rawdict`/inspeção visual das 6 páginas de `b3_padrao.pdf`, zero marcador "Questao 9"/"Questao 10" em qualquer lugar). Confirmado nesta fase: zero imagem atribuível (nenhum marcador para ancorar uma busca), zero região de answer standard, zero asset gerado, os achados independentes `question_not_verified`/`missing_answer_standard` continuam aparecendo no readiness. `git diff` em ambos os arquivos `.md`: vazio.

## O. Q23

`git diff` em `enade-2008-computing-q23.md`: vazio. Nenhuma mudança de `region membership`, crop, separação de parágrafo, asset ou Markdown. O texto que é a única cópia completa do conteúdo do esquema permanece publicado; `figure-01.png` de Q23 permanece byte-idêntica (mesmo sha256); o blocker `q23-schema-fragment-duplicate-bleed` permanece `open`, com a mesma reclassificação da Fase 3T; `force_region_membership` não foi aplicado a Q23 em nenhum momento desta fase.

## P. Blocker ledger

- `d59-answer-standard-image-only`: `open` → `resolved_by_visual_fallback`. Histórico preservado integralmente (diagnóstico original da Fase 3A, re-verificação da Fase 3T, e agora a correção do próprio erro de contagem da Fase 3T mais a resolução real). `affected_assets: [padrao-01]`.
- `d09-answer-standard-absent-from-source`/`d10-answer-standard-absent-from-source`: inalterados, `source_unavailable`.
- `q45-item-iii-formula-image-gap`: inalterado desde a correção da Fase 3T (`resolved_by_visual_fallback`).
- `q23-schema-fragment-duplicate-bleed`: inalterado desde a Fase 3T, `open`.
- `q08`/`q38`/`q55-unstructured-image-alternatives`: inalterados, `open`.

Total: 60 blockers (inalterado) - 51 `resolved`, 2 `resolved_by_visual_fallback` (Q45, D59), 2 `source_unavailable` (D09, D10), 1 `superseded`, 4 `open` (Q8, Q38, Q55, Q23). `validate_ledger`: 0 issues.

## Q. Gold

**74/77 → 75/77 verified**, derivado do estado real (nunca forçado). `unresolved_question_ids`: `[D09, D10]` (D59 removida). Novo `answer_standards` entry para D59: `source_path`, `pdf_sha256`, `pages: [3]`, `text_sha256` (hash de `""`), `assets: [{id: padrao-01, path, sha256}]`. Diff do arquivo: mínimo e cirúrgico (verified_count, needs_review_count, unresolved_question_ids, a entrada de D59 em `questions`, e a nova entrada em `answer_standards`) - nenhuma outra questão tocada.

## R. Readiness

**11 → 8 blockers.** Removidos: `question_not_verified`/`missing_answer_standard` para D59 (agora tem `answer_standard` real e `extraction_status: verified`) e `blocker_ledger_open` para `d59-answer-standard-image-only` (agora `resolved_by_visual_fallback`). Preservados: D09/D10 (ambos os achados), Q8/Q38/Q55/Q23. Decisão literal: `NOT_READY_FOR_2008_ENGINEERING_TEST` - nenhuma ausência de fonte foi transformada em sucesso; D09/D10 continuam genuinamente bloqueando.

## S. Capability registry

Nova capacidade `visual_only_answer_standard`, geração **G1** (um único caso real publicado - D59; nunca classificada G3, per a proibição explícita da Seção 27). Mecanismo, fixtures positivas/negativas, caso real, e limitações documentados integralmente em `data/manifests/extraction-capabilities.json`.

## T. Visual audit

`published=77, passed=77, failed=0, not_performed=0` - inalterado. D59's own `visual_validation: passed` já cobria a fidelidade do ENUNCIADO (confirmada em fases anteriores); esta fase adiciona, pela primeira vez, uma inspeção visual dedicada e documentada do próprio asset do answer standard (Seção J acima), que não existia até então - tratada como uma extensão da mesma validação já registrada, não uma reauditoria retroativa.

## U. Proteção de 2011/2021

Confirmado por regeneração completa + `diff -rq`: 2011 (55 questões) e os três cursos de 2021 (120 questões) são byte-for-byte idênticos ao corpus canônico antes e depois de todas as mudanças desta fase - crítico aqui porque `answer_standard.py` é um módulo COMPARTILHADO por todos os anos. `pytest tests/test_protected_corpus.py`: 4/4 passando.

## V. Testes

```text
baseline = 777
novos = 10 (5 em tests/test_extraction_answer_standard.py,
            5 em tests/test_schema_question.py)
total final = 787 (confirmado via execução real)
```

Novos testes cobrem: entrada visual-only criada com evidência real; nenhuma entrada criada sem texto E sem imagem; imagem antes do marcador nunca atribuída (o risco exato de contaminação D40-vs-D59); busca restrita à própria página do marcador; ordenação de `find_answer_standard_images` por posição, não por ordem de inserção/xref; os três modos do schema (`text_only`/`visual_only`/`mixed`); rejeição de `text=""` + `assets=[]` (inclusive texto só-espaço).

## W. Quality gates

```text
pytest tests/ -q          : 787 passed
ruff check .               : All checks passed!
ruff format --check .      : 413 files already formatted
mypy src                   : Success: no issues found in 60 source files
enade validate-schema      : 13/13 fixture(s) valid
enade validate-manifest    : OK (0 warning(s))
enade audit-extraction (2008-b/2011/2021 x3) : OK em todos (77/55/40/40/40)
enade verify-gold + assess-readiness (2008-b, 2011, 2021 CC-B): consistentes
  com as Seções Q/R/U acima
```

## X. Reprodutibilidade

Três gerações independentes de 2008-b (a regeneração canônica real + duas extrações limpas adicionais) comparadas entre si via `diff -rq`: **zero diferenças** em todo o diretório, incluindo o novo asset `padrao-01.png` de D59 (sha256 idêntico nas três: `f4eb5673ba8008494788b545fc7084a6d9fd16fe903de92f509bb5bc0033783b`). 2011 e os três cursos de 2021 confirmados byte-idênticos na mesma rodada.

## Y. Git final e recomendação

`git status --short` lista exatamente os arquivos de dados/código/testes/documentação modificados por este trabalho, mais o trabalho não-commitado da própria Fase 3T (preservado integralmente, conforme a Seção B). Nenhum arquivo scratch remanescente. Nenhum commit, push, PR, merge ou tag foi criado. `master`/`origin/master` inalterados.

**Recomendação**: com D59 resolvida, o próximo blocker acionável mais barato, na saída real do readiness, é **Q23** (Fase 3T já diagnosticou a causa raiz com precisão: um gap de separação de parágrafo, nunca uma perda de conteúdo - exigiria um override "force paragraph break" hash+bbox-locked ou uma generalização cuidadosa do filtro de largura de rótulo `MAX_LABEL_LINE_WIDTH`, com shadow-mode completo). D09/D10 devem permanecer explicitamente como ausência de fonte - nunca reinterpretados como defeito do parser. Q8/Q38/Q55 continuam sendo o item de maior esforço (exigiria uma capacidade nova de "múltiplas imagens grandes por alternativa dentro de um blob mesclado"). Não processar outro bundle; não iniciar prova inédita enquanto o readiness permanecer bloqueado; não commitar sem revisão humana explícita do conjunto acumulado (Fases 3G-3U).

## Arquivos alterados nesta fase

```text
src/enade/extraction/answer_standard.py     (+ _visual_only_page_bounds,
                                               flush() aceita boundary_line,
                                               find_answer_standard_images
                                               ordena por posição)
src/enade/models/provenance.py              (AnswerStandardReference.text:
                                               min_length=1 -> validator
                                               condicional text-ou-assets)
data/manifests/blocker-ledger-2008.yaml     (d59: open -> resolved_by_visual_fallback,
                                               contagem de imagens corrigida)
data/manifests/gold-2008-computing.json     (74/77 -> 75/77 verified)
data/manifests/extraction-capabilities.json (+1 capacidade, G1)
data/questions/2008/all-computing/enade-2008-computing-d59.md (answer_standard
                                               populado)
data/questions/2008/all-computing/enade-2008-computing-d59/answer-standard/
  padrao-01.png                             (novo asset)
tests/test_extraction_answer_standard.py    (+5 testes)
tests/test_schema_question.py               (+5 testes)
docs/phase-3u-report.md                     (novo)
```
