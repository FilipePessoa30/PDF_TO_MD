# Fase 3S — Preservação Visual Estruturada de Fórmulas Vetoriais Inline e Fechamento de Q45

## A. Classificação

- **Inline vector formula preservation:** `INLINE_VECTOR_FORMULA_PRESERVATION_STABILIZED`. O grupo vetorial de 9 elementos que forma "f(x) = √x" (item III de Q45) foi identificado documentalmente (nunca por inferência semântica), um novo asset (`figure-02.png`, `type: equation`) foi derivado diretamente do PDF-fonte com recorte apertado e legível, o posicionamento ficou correto (entre "o gráfico de" e "e as retas x = 0 e x = 2.", exatamente onde o gap existia), `structured_content`/`canonical_representation` permanecem ausentes, nenhuma transcrição não comprovada foi publicada, Q45 é agora visualmente fiel, D40 permanece byte-idêntica, nenhuma outra questão mudou, 2011 e os três cursos de 2021 permanecem byte-idênticos, todos os testes/gates estão limpos, e a reprodutibilidade foi confirmada (duas execuções independentes + o corpus canônico: hashes idênticos).
- **Visual global (2008-b):** `RESIDUAL_LAYOUT_STABILIZED` — `published=77, passed=77, failed=0, not_performed=0`, confirmado via `enade assess-readiness` real, não deduzido manualmente. Esta é uma consequência da fidelidade documental alcançada, não uma meta perseguida às custas de qualquer atalho (nenhum conteúdo foi removido, nenhuma fórmula foi fabricada, nenhum blocker foi escondido para forçar esse número).
- **Generalização:** `GENERALIZATION_ARCHITECTURE_ESTABLISHED` para o mecanismo `declare_inline_formula_region` (documentado, hash+page+bbox-travado, com verificação estrutural obrigatória via `verify_drawings_present`, G1) — `GENERALIZATION_NOT_YET_VALIDATED`: um único caso real (Q45) foi resolvido; nenhuma regra geral de detecção automática de "isto é uma fórmula" foi construída ou ativada em qualquer lugar do pipeline. Mantido mesmo com 77/77, conforme exigido pelo próprio prompt desta fase - validação em prova genuinamente inédita ainda não ocorreu.
- **Readiness:** `NOT_READY_FOR_2008_ENGINEERING_TEST`, reportado literalmente pelo gate real (`enade assess-readiness`) - 74/77 verified (subiu de 73/77), gold maturity=provisional, 13 blockers estruturais remanescentes, todos pré-existentes e não relacionados à fidelidade visual: D09/D10 (padrão de resposta ausente da fonte), D59 (padrão de resposta apenas em imagens), Q8/Q38/Q55 (alternativas com imagens não estruturadas, excluídas do corpus publicado), Q23 (vazamento cosmético textual não relacionado). Nenhum desses foi tocado, corrigido ou escondido nesta fase.

Nenhuma classificação usa sucesso pleno indevido: a estabilização *visual* de 2008-b (77/77) é real e verificada, mas não implica que o corpus esteja pronto para engenharia (readiness continua honestamente `NOT_READY`, por motivos genuinamente não-visuais).

## B. Estado Git inicial

Branch `feat/enade-2008-cc-b-pilot`. HEAD inicial: `d83c4cc` ("Implement force_region_membership override and related tests", Fase 3R, commitado e já publicado em `origin/feat/enade-2008-cc-b-pilot` por processo externo a esta sessão, entre as fases - mesmo padrão observado em toda fase anterior). `master`/`origin/master`: `a5dfaab0c105150df3a7201c16547708cef45292`, inalterados do início ao fim desta fase. `git diff --check` limpo. Nenhum commit, push, PR, merge ou tag foi criado nesta fase. Confirmada a presença de todo o trabalho acumulado das Fases 3G-3R: `force_region_membership`/`protect_from_region_membership` (ambos em `layout_overrides.py`), `source-token-ledger-2008.yaml` (4 entradas no início), `alternative_content_assignment.py`, `same_row_ordering.py`, `reading_zones.py`, `fragment_reconstruction.py`, `content_assignment.py`, blocker/capability registries atualizados, `docs/phase-3r-report.md`.

## C. Baseline

```text
tests = 750 (confirmado via execução real: 750 passed)
published = 77
visual_passed = 76, visual_failed = 1 (Q45), not_performed = 0
gold 2008-b: 73/77 verified, maturity=provisional
overrides: 63 (confirmado via leitura direta do YAML)
blockers: 60 (52 resolved, 9 open, 1 superseded no início - recontado
  diretamente do YAML, não presumido)
288 arquivos protegidos (2011: 55, 2021: 120 em 3 cursos): confirmados via
  test_protected_corpus.py e por regeneração completa + diff -rq
```

Todos os valores foram lidos diretamente dos manifests reais e confirmados por execução real de `pytest`/`ruff`/`mypy`/`enade validate-schema`/`enade validate-manifest`/`enade audit-extraction` (2008-b, 2011, 3 cursos de 2021)/`enade verify-gold`+`assess-readiness` (2008-b via `--course all-computing`, o comando real equivalente ao literal `ciencia-da-computacao-bacharelado` do prompt, que não se aplica a este caderno unificado; 2011; 2021 CC-B) no início da fase - batendo exatamente com o que a Fase 3R relatou ao final.

## D. Escopo

Trabalho exclusivo em Q45, seu novo asset visual e os manifests diretamente derivados (source-token-ledger, blocker-ledger, visual-audit, gold, capability registry). D40 não foi tocada em nenhum aspecto: confirmado `git diff` vazio em `enade-2008-computing-d40.md`, `figure-01.png` de D40 byte-idêntico (mesmo sha256), o override `force_region_membership` da Fase 3R inalterado, o operador σ de D40 preservado exatamente como a Fase 3R o deixou. O sibling "F"/"B" (o par de símbolos de operador de D40, citado na Fase 3R) não foi tocado - nenhum override novo referencia D40 ou sua página 17. Nenhum outro bundle, ano ou questão (Q8/Q38/Q55 inclusive) foi processado.

## E. Evidência textual negativa

`page.get_text("rawdict")` e `page.get_texttrace()` para a página 19, na faixa x=404.97-443.97/y=481.9-493.4 (a lacuna entre "eixo x, o grafico de" e "e as retas x = 0 e x = 2."), não reportam nenhum bloco/linha/span/char - zero conteúdo textual utilizável nessa região. Confirmado por execução direta desta fase (não apenas herdado do relatório da Fase 3Q): as duas linhas vizinhas têm bboxes reais (318.6,483.28)-(404.97,493.33) e (443.97,483.28)-(550.79,493.33), com a lacuna entre `x1=404.97` e `x0=443.97` inteiramente vazia de texto.

## F. Evidência vetorial

`page.get_drawings()` para a mesma página/faixa reporta exatamente 9 elementos de path, todos tipo `"fs"` (fill+stroke), contornos em forma de glifo para: "f", "(", "x", ")", "=", o radical ("sqrt", formado por um checkmark + barra superior), e um segundo "x". União dos bounding boxes: `(406.679, 481.919, 442.919, 493.439)` - coincide, a menos de arredondamento de ponto flutuante, com o bbox já documentado pela Fase 3Q. Todos os 9 elementos têm `fill=(0,0,0)`, `color=(0,0,0)`, `width≈0.12pt` - traços finos e sólidos, consistentes com texto matemático tipográfico desenhado como vetor (nunca como fonte, já que nenhuma fonte cobre este intervalo de x/y). Renderizando esta faixa da página via `page.get_pixmap()` (o mesmo mecanismo que já produz todo asset deste corpus) confirma visualmente "f(x) = √x", com o radical, os parênteses e o sinal de igual completos e legíveis.

## G. Agrupamento

Os 9 elementos foram tratados como uma única unidade visual pelo critério mais simples e mais seguro disponível: todos foram individualmente re-confirmados, na hora da extração real (não apenas na hora da investigação), como sobrepostos ao bbox declarado no override (`figures.verify_drawings_present`, tolerância de 2pt) - nenhum agrupamento por proximidade/heurística de crescimento foi necessário, já que o bbox alvo já era conhecido e documentado desde a Fase 3Q. Nada fora dessa faixa foi incorporado: a verificação de `page.get_text`/`get_texttrace` confirma que as duas linhas de texto adjacentes (que ficam FORA do bbox declarado) não são desenhos e nunca entram no grupo; nenhuma borda de tabela, sublinhado, seta, ícone, ou desenho da árvore de consulta de D40 (página diferente, documento diferente na prática desta verificação) está em jogo aqui. O mecanismo não tenta descobrir automaticamente "que desenhos formam uma fórmula" em lugar nenhum do corpus - ele apenas confirma que desenhos reais existem dentro de um bbox já declarado por um humano/fase anterior, nunca infere o agrupamento por conta própria.

## H. Detecção

Não foi implementado um classificador geral de "isto é uma fórmula inline". A elegibilidade é inteiramente declarativa: um override `declare_inline_formula_region` (hash+página+bbox) mais uma reconfirmação estrutural obrigatória (`verify_drawings_present > 0`, PROMPT Seção 13: "a detecção do candidato seja estrutural") são as duas únicas condições que autorizam a construção de uma região. Nenhum sinal geométrico (tamanho, altura relativa, posição entre âncoras, ausência de borda de coluna, etc.) é usado para *decidir* automaticamente que um bbox é uma fórmula - esses sinais foram usados apenas por mim, manualmente, ao escrever o override, exatamente como a Fase 3Q usou evidência de baixo nível para escrever seus próprios overrides sem construir um classificador geral.

## I. Shadow mode

Como nenhuma regra geral de detecção foi construída, não há necessidade de rodar em "shadow mode" um classificador procurando novos candidatos em todo o corpus - não existe tal classificador. A validação de segurança real e obrigatória foi, em vez disso, a regeneração completa + `diff -rq` de todo o corpus protegido:

- 2008-b (77 questões): apenas `enade-2008-computing-q45.md` (+ seu novo `figure-02.png`) difere; as outras 76 questões, incluindo D40, são byte-idênticas.
- 2011 (55 questões): zero diferenças.
- 2021 CC-bacharelado/CC-licenciatura/Sistemas de Informação (120 questões): zero diferenças.

Como o mecanismo só pode construir uma região quando um override hash+página+bbox exato casa E `page.get_drawings()` confirma conteúdo vetorial real ali, e como apenas uma única entrada foi escrita (travada à página 19 de 2008-b), é estruturalmente impossível que ele afete qualquer outra linha de qualquer outro documento - confirmado empiricamente, não apenas presumido pelo desenho do mecanismo.

## J. Contraexemplos

A lista obrigatória da Seção 11 (grade de tabela, borda, sublinhado, separador, seta, ícone, logotipo, bullet, eixo de gráfico, curva plotada, diagrama, árvore de álgebra relacional, asset já publicado) é satisfeita trivialmente pelo mesmo motivo da Seção I: o mecanismo não pode alcançar nenhum desses casos sem um override individualmente escrito para eles, e nenhum foi escrito. Confirmado explicitamente, sem necessitar de fixtures sintéticas adicionais para cada categoria:

- **Árvore de álgebra relacional de D40 (o contraexemplo mais próximo estruturalmente - também vetor, também matemático):** nenhum override `declare_inline_formula_region` existe para a página 17 de D40; `git diff` confirma D40 byte-idêntica.
- **Os outros dois gaps de fórmula vetorial na PRÓPRIA Q45** ("(f $ 0)" na introdução; "como resultado da integral ."): nenhum override foi escrito para eles - permanecem exatamente como antes, confirmando que o mecanismo não generaliza nem mesmo dentro da mesma questão sem uma declaração explícita adicional.
- **`figure-01.png` de Q45 (o asset já publicado que também mostra esta mesma fórmula, por acidente de uma região de merge sobredimensionada e não relacionada):** não foi realocado, reescalado ou removido - permanece byte-idêntico (mesmo sha256) antes/depois.
- **Testes unitários novos** (`test_extraction_figures.py`, `test_extraction_assembler.py`, `test_layout_overrides.py`, `test_extraction_assets.py`) cobrem positivamente (bbox com desenho real → região construída; região `is_declared_inline_formula` → tipo `equation`; inserção entre duas linhas da mesma linha visual) e negativamente (bbox sem desenho real → nenhuma região; sem override → nenhuma região; hash/página divergente → nenhuma região; região comum não afetada pelo novo campo; ausência de linha à esquerda na mesma linha visual → cai para a regra geral Y-only sem quebrar).

## K. Content block

Nenhum novo tipo de `ContentBlock` (`formula`) foi criado. O schema existente (`ParagraphBlock`/`CodeBlock`/`TableBlock`/`AssetBlock`) já representa corretamente o caso "prosa - fórmula - prosa", exatamente como o precedente já estabelecido pela Fase 2C (D3-2011's fórmula de Fibonacci, `type: image`, inserida via `AssetBlock`/referência inline `![...]()` na string plana do enunciado). Q45 continua com `content_blocks: null` (como antes) - não precisou adotar a representação estruturada, já que o mecanismo de inserção atua diretamente sobre `assembler._build_statement_segments`/`render_statement_markdown`, a mesma via que já produz a string plana `statement` para toda questão sem `content_blocks`. O tipo de asset escolhido foi `AssetType.EQUATION` (existente no schema desde a Fase 1C, nunca antes exercitado em nenhuma questão publicada - agora tem seu primeiro caso real e positivo), selecionado apenas quando `VisualRegion.is_declared_inline_formula=True` (novo campo aditivo, default `False`, sem efeito em nenhuma outra região do corpus).

## L. Asset

`figure-02.png`, renderizado diretamente da página 19 do PDF-fonte via `page.get_pixmap()` no mesmo zoom (3x) e mecanismo (`assets._render_bbox`) já usados para todo asset deste corpus - sem OCR, sem redesenho, sem interpolação além da já padrão do renderizador PDF→pixmap. Diferente de todo outro asset, seu `owner_x_bounds` é um recorte apertado e fixo (bbox ± `INLINE_FORMULA_RENDER_PADDING`=6pt) em vez de ser alargado até a coluna/página inteira - a única mudança de comportamento de renderização introduzida nesta fase, e apenas para regiões marcadas `is_declared_inline_formula`. Dimensões resultantes: recorte de ~48pt de largura (406.68-6 a 442.92+6) por ~15.5pt de altura (481.92-4 a 493.44+4, usando o `RENDER_PADDING` vertical já existente), a 3x de zoom. sha256: `6c992854aee8fd5e615f9471f34d0cf831de7ad8ac4470c8724796c587222b7a` - confirmado idêntico em duas execuções independentes adicionais (Seção X).

## M. Placement

Âncora anterior: "eixo x, o grafico de" (bbox termina em x1=404.97, y0=483.28). Âncora posterior: "e as retas x = 0 e x = 2." (bbox começa em x0=443.97, mesmo y0=483.28) - ambas na mesma linha visual, ambas já restauradas como texto pela Fase 3Q. Um novo mecanismo de inserção ciente de X (`assembler._find_inline_formula_insertion_index`), aplicado apenas a regiões `is_declared_inline_formula`, localiza a linha da mesma faixa Y mais à esquerda do bbox da fórmula e insere logo após ela - nunca antes da linha inteira, como a regra geral (`_find_region_insertion_index`, Y-only) faria (confirmado por teste: a regra geral erra este caso específico, colocando a figura antes de "eixo x, o grafico de" em vez de entre as duas linhas). O resultado publicado tem exatamente esta ordem: "...delimitada pelo eixo x, o gráfico de" → `![...]➝figure-02.png` → "e as retas x = 0 e x = 2." - nem ao final da questão, nem antes do marcador III, nem entre alternativas, nem duplicado. O Markdown não suporta imagem verdadeiramente inline (dentro da mesma linha de texto) no corpo do enunciado desta base de código (investigado explicitamente: o único precedente de imagem verdadeiramente inline existe apenas dentro do texto de uma alternativa, Fase 2F - nunca no enunciado principal) - a representação em bloco (a imagem como seu próprio parágrafo, cercado por linhas em branco) foi usada em vez disso, exatamente como todo outro asset deste corpus, incluindo o próprio `figure-01.png` desta mesma questão. Esta é a limitação de layout documentada: a fórmula não fica literalmente na mesma linha de texto que a frase que a circunda, mas fica na posição documental correta, entre as duas frases certas, sem nenhuma ambiguidade de leitura.

## N. Representação textual

`structured_content`/`canonical_representation` permanecem `null` em toda parte relevante (não existe um campo `structured_content` neste schema - o equivalente é `canonical_representation` no source-token-ledger, e nenhum texto correspondente em `Question.statement`/`content_blocks`). Nenhuma string "f(x) = √x" ou "f(x) = sqrt(x)" foi inserida como conteúdo canônico em nenhum arquivo publicado - confirmado por busca literal: a string "sqrt" não aparece em `q45.statement` (verificado por teste automatizado), nem "√", nem "f(x)" na faixa entre as duas âncoras. Nenhum LaTeX foi gerado. Nenhum OCR foi usado como fonte de conteúdo canônico.

## O. Acessibilidade

A limitação é registrada explicitamente em `data/manifests/source-token-ledger-2008.yaml` (token `q45-item-iii-function-formula`, campo `evidence`): a fórmula é preservada apenas visualmente, não possui representação textual extraída, não possui LaTeX validado, e não é pesquisável como fórmula por busca de texto. **Nota de transparência**: o campo `alt_text` do modelo `Asset` (já existente no schema) foi deliberadamente deixado `null`, IGUAL a todo outro asset já publicado neste corpus inteiro (confirmado: nenhum dos 288+ assets publicados em 2008-b/2011/2021 usa `alt_text` até hoje) - popular apenas este asset romperia essa convenção uniforme e pré-existente sem uma decisão de produto mais ampla sobre acessibilidade de imagem no projeto como um todo. A limitação foi, portanto, registrada onde o projeto já registra esse tipo de nuance (o source-token-ledger), não silenciada, mas também não inventada como uma nova convenção de `alt_text` isolada para um único asset.

## P. Ownership

O dono é computado estruturalmente (`ownership.find_owner`, o mesmo mecanismo já usado por `figures.py` para toda outra região), nunca fixado por um literal "enade-2008-computing-q45" na lógica central - o override apenas declara o bbox; o código pergunta "qual QuestionRegion contém o centro deste bbox" e obtém `objective-45` como resposta, exatamente como faria para qualquer outra região daquela página. Confirmado por teste dedicado (`test_build_declared_inline_formula_regions_computes_owner_from_question_regions`). Nenhum dono concorrente existe (o bbox está inteiramente dentro do território de página conhecido de Q45, longe de qualquer questão vizinha).

## Q. Content assignment

O módulo genérico `content_assignment.py` (Fase 3J) é uma ferramenta de diagnóstico offline, deliberadamente escopada a Q13/D60 e nunca conectada ao pipeline principal (confirmado: não é chamada de `cli.py` nem `pipeline.py`) - não foi estendida nesta fase, pela mesma razão que a Fase 3R não a usou: o `source-token-ledger` já cumpre a função de registro de proveniência/papel/decisão para este tipo de token, com uma entrada dedicada por token, exatamente o padrão já estabelecido pela Fase 3Q. Os "gates" pedidos pela Seção 19 do prompt (fórmula sem owner, owner concorrente, fórmula duplicada, fórmula sem placement, ausente do Markdown mas presente no asset, etc.) foram verificados manualmente e via teste automatizado nesta fase (Seções J/M/S), não via uma nova infraestrutura de gate genérica - construir uma agora, para um único caso real, seria exatamente a generalidade especulativa que o próprio projeto (docs/generalization-contract.md) adverte contra.

## R. Source-token ledger

Entrada `q45-item-iii-function-formula` atualizada (schema idêntico ao já estabelecido pelas Fases 3Q/3R): `extraction_status` mudou de `drawing_verified` para `visual_only_verified` (o termo exato mandatado pela Seção 5 deste prompt), `canonical_representation` permanece `null`, `visual_fallback` agora aponta para o novo `figure-02.png` (com uma nota explícita sobre por que isso substitui a antiga referência ao `figure-01.png`, que era visualmente verdadeira mas mal posicionada). `bbox` foi refinado para os valores exatos re-confirmados nesta fase (406.679,481.919-442.919,493.439, vs. a aproximação 406.68,481.92-442.92,493.44 da Fase 3Q - a mesma região, precisão de casas decimais apenas). As 3 entradas pré-existentes (`q24-item-marker-I`, `q24-item-marker-II`, `d40-tree-selection-operator-sigma`) permanecem byte-idênticas - confirmado por comparação campo a campo.

## S. Safety oracle

```text
textual_content_before = textual_content_after
```
Confirmado: nenhuma string textual pré-existente foi alterada - o `diff` do Markdown mostra exclusivamente a inserção de duas linhas em branco + uma referência de imagem entre "o gráfico de" e "e as retas", nunca uma edição de palavra existente.

```text
missing_vector_information_before + verified_visual_fallback = documentary_information_after
```
Confirmado: a lacuna que antes existia (nenhuma representação de "f(x) = √x") agora tem exatamente um fallback visual verificado (`figure-02.png`) no ponto correto.

Verificações adicionais, todas confirmadas:
- Nenhuma string fabricada (Seção N).
- Nenhuma linha textual alterada (apenas inserção de blocos vazios/imagem entre linhas já existentes).
- Nenhuma palavra reordenada (a ordem de "eixo x, o gráfico de" → "e as retas..." é idêntica à publicada desde a Fase 3Q).
- Nenhum item duplicado (itens I/II/III aparecem exatamente uma vez cada).
- Nenhuma alternativa alterada (A-E idênticas, confirmado por `git diff` restrito a essa seção = vazio).
- Nenhum desenho estranho absorvido (apenas os 9 elementos re-confirmados dentro do bbox declarado).
- Nenhum asset existente modificado (`figure-01.png` de Q45 e ambos os assets de D40 confirmados com sha256 idêntico).
- Nenhuma questão não-alvo modificada (`diff -rq` completo de 2008-b: só Q45 difere).
- Exatamente um novo asset (`figure-02.png`).
- Exactly one placement (a fórmula aparece uma única vez, no ponto correto).
- Dono único (`objective-45`, sem concorrência).
- Hash determinístico (confirmado idêntico em 3 execuções independentes - Seção X).

## T. D40

`git diff` em `enade-2008-computing-d40.md`: vazio. sha256 de `figure-01.png`/`figure-02.png` de D40: idênticos antes/depois (`1c54ec1c...`/`0b4d1d61...`). O override `force_region_membership` da Fase 3R permanece byte-idêntico em `layout-overrides.yaml` (nenhuma edição, apenas uma nova entrada foi adicionada em outro ponto do arquivo). O operador σ de D40 continua corretamente suprimido do texto (não reapareceu); o vazamento irmão "B"/π permanece exatamente como a Fase 3R o deixou (fora de escopo, intocado). O blocker `d40-cosmetic-selection-operator-leak` continua `resolved`; o gold de D40 continua `verified`.

## U. Auditoria visual

`data/manifests/visual-audit-2008-computing.json`: `enade-2008-computing-q45` promovida de `status: failed` para `status: passed`. Diff do arquivo: exatamente 2 linhas alteradas (edição cirúrgica, preservando byte a byte as outras 76 entradas - a mesma disciplina de edição mínima estabelecida na Fase 3R após o incidente de reserialização completa daquela fase). Resultado agregado do gate real: **`published=77, passed=77, failed=0, not_performed=0`, `fully_covered=True`**.

## V. Blocker ledger

Dois blockers de Q45 resolvidos nesta fase, preservando o histórico completo em ambos:

- `q45-region-merge-content-loss`: `status` mudou de `open` para `resolved` (seu próprio mecanismo - perda de texto recuperável por merge de região - já não tinha nenhum resíduo genuíno; o único item que o mantinha "aberto" era uma referência cruzada ao blocker de fórmula, agora também resolvido). `visual_validation`: `failed` → `passed`.
- `q45-item-iii-formula-image-gap`: `status` mudou de `open` para `resolved`, `resolution` preenchido com `RESOLVED_BY_VISUAL_FALLBACK` (o termo exato pedido pela Seção 28 - não `resolved_by_structured_extraction`, já que nenhuma extração estruturada de texto ocorreu). Histórico preservado: a caracterização original incorreta ("um caractere ausente"), a descoberta das três linhas ausentes, a restauração dessas três linhas (Fase 3Q), o descarte da falsa inversão de ordem (Fase 3Q), a prova de que a fórmula é vetorial (Fase 3Q), e agora a solução por fallback visual (Fase 3S) com asset/bbox/hash/placement/limitação de acessibilidade/testes/validação visual documentados.

Total de blockers: 60 → 60 (nenhum blocker novo criado ou removido, apenas 2 promovidos de `open` para `resolved`). `resolved`: 50 → 52. `open`: 9 → 7.

## W. Gold e readiness

`enade build-gold --year 2008 --course all-computing`: **74/77 verified** (subiu de 73/77), `needs_review_count: 3` (D09, D10, D59 - Q45 removida de `unresolved_question_ids`). `enade verify-gold`: OK, hashes batem. `enade assess-readiness --year 2008 --course all-computing --ready-label READY_FOR_2008_ENGINEERING_TEST`: **`NOT_READY_FOR_2008_ENGINEERING_TEST`** (reportado literalmente pelo gate, sem dedução manual) — **visual audit: 77 passed, 0 failed, 0 not_performed** — exatamente o resultado esperado da Seção 27/36 deste prompt. 13 blockers estruturais remanescentes, TODOS pré-existentes e não-visuais: D09/D10 (padrão de resposta ausente da fonte, 2 cada), D59 (padrão de resposta apenas em imagens), Q8/Q38/Q55 (alternativas com imagens não estruturadas, excluídas), Q23 (vazamento cosmético textual, não relacionado). Nenhum desses foi corrigido, escondido, ou reinterpretado nesta fase - preservados e reconciliados exatamente como já estavam.

## X. Proteção, testes e reprodutibilidade

**Proteção**: confirmado por regeneração completa + `diff -rq` (não apenas pela suíte de testes): 2011 (55 questões) e os três cursos de 2021 (120 questões no total) são byte-for-byte idênticos ao corpus canônico antes e depois de todas as mudanças de código/dados desta fase. `pytest tests/test_protected_corpus.py`: 4/4 passando.

**Reprodutibilidade**: três gerações independentes de 2008-b comparadas entre si e contra o corpus canônico publicado - todas byte-idênticas, incluindo o hash SHA-256 do novo `figure-02.png` (`6c992854aee8fd5e615f9471f34d0cf831de7ad8ac4470c8724796c587222b7a`, idêntico nas três).

**Quality gates finais**:

```text
pytest tests/ -q          : 771 passed (antes: 750; +21 testes novos)
ruff check .               : All checks passed!
ruff format --check .      : 411 files already formatted
mypy src                   : Success: no issues found in 60 source files
enade validate-schema      : 13/13 fixture(s) valid
enade validate-manifest    : OK (0 warning(s))
enade audit-extraction (2008-b)         : 77/77 OK
enade audit-extraction (2011)           : 55/55 OK
enade audit-extraction (2021, 3 cursos) : 40/40 OK cada
enade verify-gold + assess-readiness (2008-b via all-computing, 2011, 2021 CC-B):
  consistentes com as Seções U/W acima
```

21 testes novos: `test_extraction_figures.py` (5 - `verify_drawings_present` positivo/negativo-vazio/negativo-sem-desenhos/múltiplos desenhos, + o campo aditivo `is_declared_inline_formula` default), `test_extraction_assembler.py` (7 - inserção ciente de mesma-linha/fallback Y-only, construção de região sem overrides/sem declaração casando/sem evidência real/com evidência real, cálculo de dono via `find_owner`), `test_layout_overrides.py` (5 - bbox correspondente, página diferente, hash diferente, múltiplos bboxes, ignora regras não relacionadas), `test_extraction_assets.py` (4 - `render_region` seleciona `equation` apenas quando marcado, `diagram`/`image` inalterados, recorte permanece apertado). Mais a reescrita de `tests/test_extraction_pipeline_2008.py::test_q45_item_iii_own_three_lines_are_now_complete` (agora confirma simultaneamente: as 3 linhas restauradas pela Fase 3Q + a ordem textual comprovada + a fórmula visual presente no ponto correto + zero transcrição textual fabricada - a combinação exata pedida pela Seção 24) e atualização de `test_q45_items_i_and_ii_are_now_complete` (contagem de assets: 1 → 2) - estas duas últimas não somam ao total de +21, pois substituem/ajustam testes já existentes em vez de adicionar novos.

## Y. Git final e recomendação

`git status --short` ao final desta fase lista exatamente os arquivos de dados/código/testes/documentação modificados por este trabalho (nenhum arquivo scratch remanescente - `diag_q45_*.py` e todos os diretórios temporários `/d/tmp_phase3s_*` foram apagados). Nenhum commit, push, PR, merge ou tag foi criado. `master`/`origin/master` inalterados.

**Recomendação**: com Q45 (e D40, resolvida na Fase 3R) integralmente resolvidas, 2008-b atinge `RESIDUAL_LAYOUT_STABILIZED` (77/77 visual) - mas o corpus como um todo permanece `NOT_READY_FOR_2008_ENGINEERING_TEST` por 13 blockers estruturais genuinamente não-visuais (padrões de resposta ausentes/incompletos, alternativas com imagens não estruturadas, um vazamento cosmético textual não relacionado). Recomenda-se uma **Fase 3T de reconciliação final** que:

1. Revise apenas os motivos reais retornados pelo gate atual (D09/D10/D59/Q8/Q38/Q55/Q23), decidindo caso a caso se cada um é: (a) genuinamente irresolúvel (documentar como limitação permanente), (b) resolúvel com uma extensão estrutural análoga à desta fase (ex.: Q8/Q38/Q55 poderiam se beneficiar de uma investigação de `page.get_drawings()`/`get_images()` similar, já que "alternativas com imagens não estruturadas" pode esconder o mesmo tipo de conteúdo vetorial ainda não corretamente recortado), ou (c) fora do escopo deste pipeline.
2. Não modifique o corpus apenas para elevar contagens de gold/readiness - qualquer promoção deve vir de fidelidade documental real, exatamente como nesta fase e nas anteriores.
3. Só depois de esgotar os blockers estruturais tratáveis, recomende teste em uma prova genuinamente inédita (nunca vista por nenhuma fase anterior) antes de declarar qualquer validação de generalização.
4. Não inicie automaticamente outro bundle/ano (2005 ou além) nesta futura fase.
5. Não faça commit do trabalho acumulado das Fases 3G-3S sem revisão humana explícita do conjunto.

## Arquivos alterados nesta fase

```text
src/enade/extraction/figures.py             (+ VisualRegion.is_declared_inline_formula,
                                               + verify_drawings_present,
                                               + INLINE_FORMULA_RENDER_PADDING)
src/enade/extraction/assembler.py           (+ _build_declared_inline_formula_regions,
                                               + _find_inline_formula_insertion_index,
                                               wired into the per-page region loop and
                                               _build_statement_segments's own insertion)
src/enade/extraction/assets.py              (render_region: is_declared_inline_formula
                                               selects AssetType.EQUATION)
src/enade/extraction/layout_overrides.py    (+ declared_inline_formula_regions)
data/manifests/layout-overrides.yaml        (+1 entrada: 63 -> 64)
data/manifests/source-token-ledger-2008.yaml (Q45 entry updated: drawing_verified ->
                                               visual_only_verified, visual_fallback
                                               repointed to figure-02.png)
data/manifests/blocker-ledger-2008.yaml     (2 blockers: open -> resolved; 60 -> 60
                                               total, 50 -> 52 resolved)
data/manifests/visual-audit-2008-computing.json (Q45: failed -> passed)
data/manifests/extraction-audit-2008-computing.{csv,json} (Q45: needs_review -> verified)
data/manifests/gold-2008-computing.json     (73/77 -> 74/77 verified)
data/manifests/extraction-capabilities.json (+1 capacidade, G1)
data/questions/2008/all-computing/enade-2008-computing-q45.md (+figure-02 inline
                                               entre "o grafico de" e "e as retas")
data/questions/2008/all-computing/enade-2008-computing-q45/figure-02.png (novo asset)
tests/test_extraction_figures.py            (+5 testes)
tests/test_extraction_assembler.py          (+7 testes)
tests/test_extraction_assets.py             (+4 testes, incluindo os já contados na
                                               Fase 3R para outra área do arquivo)
tests/test_layout_overrides.py              (+5 testes)
tests/test_extraction_pipeline_2008.py      (1 teste reescrito, 1 atualizado)
docs/phase-3s-report.md                     (novo)
```
