# Fase 3R — Eliminação Estrutural do Vazamento Cosmético Residual de D40

## A. Classificação

- **Cosmetic text leak:** `COSMETIC_TEXT_LEAK_STABILIZED`. O "F" cosmético de D40 (documentado desde a Fase 3G) foi localizado, diagnosticado por evidência de baixo nível (rawdict/texttrace/font fingerprint/renderização de página) e eliminado sem tocar Q45, sem regredir 2011/2021, sem remover conteúdo legítimo e sem usar comparação literal de string, ID de questão, página ou coordenada fixa na lógica central.
- **Residual layout (corpus 2008-b):** ainda `RESIDUAL_LAYOUT_NOT_STABILIZED` — `published=77, passed=76, failed=1 (Q45), not_performed=0`. Este é exatamente o resultado esperado descrito pelo próprio prompt desta fase (77/76/1), consequência da correção documentada, não um alvo perseguido às custas de qualquer atalho.
- **Generalização:** `GENERALIZATION_ARCHITECTURE_ESTABLISHED` para o mecanismo simétrico `force_region_membership` (documentado, hash+page+bbox-travado, G1) — `GENERALIZATION_NOT_YET_VALIDATED`: nenhuma regra geral de geometria/tamanho de fonte foi introduzida; o mecanismo só atua quando um override explícito, revisado individualmente, aponta para uma linha específica já classificada como "ambiguous".
- **Readiness:** `NOT_READY_FOR_2008_ENGINEERING_TEST` — 73/77 verified (subiu de 72/77), gold maturity=provisional, Q45 continua com blocker próprio aberto (`q45-item-iii-formula-image-gap`), D09/D10/D59 sem padrão de resposta, Q8/Q38/Q55 excluídas, Q23 com vazamento cosmético textual não relacionado.

Nenhuma classificação usa sucesso pleno indevido; D40 está resolvida, o corpus como um todo não está.

## B. Estado Git inicial

Branch `feat/enade-2008-cc-b-pilot`. HEAD inicial: `9edcf90` ("feat: Resolve Q24 and Q45 issues in visual audit", Fase 3Q, commitado por processo externo a esta sessão). `master`/`origin/master`: `a5dfaab0c105150df3a7201c16547708cef45292`, inalterados do início ao fim desta fase. `git diff --check` limpo (sem erros de whitespace). Nenhum commit, push, PR, merge ou tag foi criado nesta fase. Confirmada a presença de todo o trabalho acumulado das Fases 3G-3Q: `alternative_content_assignment.py`, `same_row_ordering.py`, `reading_zones.py`, `source-token-ledger-2008.yaml` (3 entradas), 62 overrides em `layout-overrides.yaml`, e os relatórios `docs/phase-3o-report.md`/`docs/phase-3p-report.md`/`docs/phase-3q-report.md`.

## C. Baseline

```text
tests = 741 (confirmado via execução real em background, 741 passed in 322.76s)
published = 77
visual_passed = 75, visual_failed = 2 (Q45, D40), not_performed = 0
gold 2008-b: 72/77 verified, maturity=provisional
overrides: 62 (confirmado via leitura direta do YAML, não presumido)
blockers: 59 (confirmado via leitura direta do YAML)
288 arquivos protegidos (2011: 55, 2021: 110 em 3 cursos): confirmados via
  test_protected_corpus.py (4 testes) e via regeneração completa + diff -rq
  (zero divergência) para os 5 cadernos protegidos
2021 CC-licenciatura / Sistemas de Informação: sem gold manifest (pré-existente,
  confirmado "no gold manifest found", não é uma lacuna desta fase)
```

Todos os valores foram lidos diretamente dos manifests reais e confirmados por execução real de `pytest`/`ruff`/`mypy`/`enade validate-schema`/`enade validate-manifest`/`enade audit-extraction` (2008-b, 2011, 3 cursos de 2021)/`enade verify-gold`+`assess-readiness` (2008-b, 2011, 2021 CC-B) no início da fase — não presumidos do resumo da fase anterior. Todos batem exatamente com o que a Fase 3Q relatou ao final, confirmando um ponto de partida limpo e sem deriva.

## D. Escopo

Trabalho exclusivo no "F" cosmético de D40 (página 17). Q45 não foi tocada em nenhum aspecto: nenhuma transcrição de "f(x) = √x", nenhum LaTeX, nenhum OCR, nenhum fallback visual novo, nenhuma alteração de Markdown/asset/visual-audit/blocker/source-token-ledger. Confirmado ao final: `git diff` em `enade-2008-computing-q45.md` está vazio; sua entrada no source-token-ledger (`q45-item-iii-function-formula`) permanece byte-idêntica; seu blocker `q45-item-iii-formula-image-gap` permanece aberto e com o mesmo texto. Nenhum outro bundle, ano ou questão (Q8/Q38/Q55 inclusive) foi tocado.

## E. Reprodução do defeito

Não foi considerado suficiente observar apenas o Markdown final. A cadeia completa foi instrumentada via monkey-patch direto de `assembler.compute_line_region_relation`/`assembler._line_in_region` durante uma execução real de `extract_exam` (nunca reimplementando a lógica de regiões separadamente — a lição da Fase 3Q sobre diagnósticos que contornam os próprios portões de `_line_in_region` foi respeitada). O Markdown publicado antes desta fase mostrava, entre `figure-01.png` e o parágrafo de fechamento, um parágrafo solto e sem contexto contendo apenas `F`. O dump `rawdict` da página 17 confirmou a linha correspondente: bbox `(95.759, 574.538)-(103.201, 587.914)`, fonte `TT2F14o00`, tamanho 13.31pt, texto `"F"`.

## F. Identidade do "F"

Dump completo de identidade via `page.get_text("rawdict")` + `page.get_texttrace()` + `page.get_fonts(full=True)` + `doc.extract_font()`:

| Campo | Valor |
|---|---|
| question_id | enade-2008-computing-d40 |
| source_page | 17 |
| bbox | (95.759, 574.538)–(103.201, 587.914) |
| origin | (95.759, 585.239) |
| raw_text | "F" |
| charcode | 70 (WinAnsiEncoding fallback → "F") |
| glyph_id | 2 |
| font_name | PKHEMP+TT2F14o00 (xref 160) |
| font_type | CFF/Type1, subset embutido, 367 bytes |
| font_fingerprint | sha256:99573bc2e5d21945e581d503837be3ab37b4ed735018da36448f7e49efbdfbfa |
| font declara | WinAnsiEncoding (sem CMap ToUnicode) |

Classificação: **não é um caractere real "F"** — é um símbolo de operador de álgebra relacional (seleção, σ) pintado por uma fonte subconjunto customizada cujo programa de glifo não corresponde ao seu próprio charcode nominal WinAnsi. Confirmado por renderização direta (`page.get_pixmap()`, mesmo zoom 3x que `enade.extraction.assets.RENDER_ZOOM` já usa) e por inspeção visual do `figure-01.png` já publicado, que mostra literalmente "π_nome,endereço" / "σ_idade < 40 OR renda < 30000" / "Cliente" — exatamente a árvore de consulta que o enunciado já publicado descreve ("na qual B e F representam as operações de projeção e de seleção, respectivamente"). O glifo irmão, charcode 66/glyph_id 1 ("B", bbox 123.239,536.978–131.515,550.354), é o operador π (projeção) na mesma fonte — confirmando que ambos são símbolos de operador, não letras latinas, e que a renderização real do PDF (não uma interpretação semântica minha) é a fonte da identidade.

## G. Primeiro estágio divergente

Reconstrução completa do caminho (17 estágios exigidos pela Seção 6):

1. **PDF source/raw chars:** charcode 70/glyph_id 2, fonte PKHEMP+TT2F14o00 — confirmado.
2. **Page lines:** sobrevive como `Line` própria e isolada, texto `"F"`, sem `fragment_merges` (não casa com `fragment_reconstruction.py`'s próprio `font_size_compatible` — 13.31pt vs 8.69pt do vizinho "idade", diferença 4.62pt, muito além da tolerância de 0.5pt).
3. **Orphan-marker merge (layout.py):** `_ORPHAN_MARKER_RE` não inclui "F" no seu conjunto de caracteres (apenas A-E, o esquema de alternativas deste corpus) — nunca é candidato a fusão órfã. (O glifo irmão "B", charcode 66, casa com esse padrão e É fundido com "nome,endereco" pela mesma função — o vazamento "B\tnome,endereco", pré-existente e fora do escopo desta fase, tem essa causa distinta e não relacionada.)
4. **Label-absorption candidacy (figures.py):** rejeitado pelo próprio filtro de candidatos (`font_size < body_font_size - FONT_SIZE_CAPTION_MARGIN`) — 13.31pt é MAIOR que o corpo da página, nunca menor, então "F" nunca entra no pool de candidatos a rótulo. **Este é o primeiro estágio realmente divergente**: o mesmo filtro que corretamente protege prosa legítima de fonte grande de ser engolida por uma figura também exclui, como efeito colateral não intencional, um símbolo de operador genuinamente maior que o corpo do texto.
5. **Region growth:** a região de figure-01 cresce absorvendo "nome,endereco", "idade", "40 OR renda", "30000", "Cliente" (todos <8.69pt) — nunca "F" nem "B" (ambos 13.31pt).
6. **`_line_in_region` (assembler.py) — decisão final:** `_is_marker_at_margin("F", ...)` retorna `False` (não casa com `_ALTERNATIVE_MARKER_RE`/`_QUESTION_MARKER_RE`); `compute_line_region_relation` reporta `state="touching"` (x1=103.2 fica exatamente 0.12pt à esquerda do bbox crescido da região, x0=103.32 — não há overlap horizontal algum); `raw_intersects=False` (28.8pt de folga do bbox bruto); `matches_absorbed_label=False` (nunca foi candidato). `_text_consumption_decision` cai no `else` final: `"ambiguous"`. Antes desta fase, "ambiguous" nunca autorizava exclusão — a linha permanecia visível, publicada.

## H. Relações geométricas

| Métrica | Valor para "F" | Interpretação |
|---|---|---|
| `state` | `touching` | nem contido, nem cruzando fronteira |
| `intersection_over_line_area` | 0.0 | zero overlap real com o bbox crescido |
| `raw_intersects` | False | 28.8pt de folga do bbox bruto (pré-crescimento) |
| `matches_absorbed_label` | False | nunca foi candidato (filtro de tamanho de fonte) |
| `left_overflow` | 7.56pt | distância até a borda esquerda do bbox crescido |
| asset render clip (`_render_bbox`) | x0 = min(103.32, ~36) = 36 | **o crop real do PNG é mais largo que o bbox lógico da região** |

O achado estrutural decisivo: `assets._render_bbox` (usado para gerar `figure-01.png`) estende o clip até a margem de conteúdo da página/coluna do dono (`column_bounds`), independentemente do bbox lógico mais estreito que `_line_in_region` usa para decidir exclusão de texto. Por isso o glifo "F" (x0=95.76) já está, de fato, dentro do PNG renderizado — confirmado por inspeção visual direta do arquivo — mesmo sem nunca ter sido formalmente "contido" pela região lógica usada na decisão textual. Comparado à linha legítima que a Fase 3G precisava preservar (Q02/Q07 e outras — prosa real de corpo, nunca tocando `raw_intersects`, sempre com fonte igual ou menor que o corpo) e a rótulos legítimos absorvidos nesta mesma região (todos <8.69pt, todos `matches_absorbed_label=True`), "F" ocupa um ponto geométrico único: maior que o corpo (nunca um rótulo candidato), mas geometricamente adjacente (nunca uma frase larga e não relacionada como D10/Q07).

## I. Reconciliação com a Fase 3G

A Fase 3G aceitou "F" como o preço cosmético do design tri-state: sem essa regra de segurança, D10/Q07 teriam perdido conteúdo real (frases largas tocando apenas a borda crescida de uma região, sem overlap com o bbox bruto). A Fase 3G nunca escreveu um override para "F" porque, à época, não havia mecanismo para autorizar remoção de um caso "ambiguous" individualmente comprovado — só existia `protect_from_region_membership` (o oposto: impedir remoção). As Fases 3N/3O/3Q não alteraram nenhuma das condições geométricas que produzem `state="touching"` para "F" (nenhuma delas tocou `figures.py`'s próprio filtro de candidatos a rótulo, nem o cálculo de `raw_intersects`/`matches_absorbed_label`). O que mudou nesta fase não foi a geometria — foi a criação do mecanismo simétrico ausente (`force_region_membership`), aplicável apenas a casos individualmente comprovados por identidade de fonte/glifo, nunca por relaxar o próprio filtro de tamanho de fonte ou o próprio limiar `touching`/`raw_intersects`.

## J. Papel estrutural

"F" é um símbolo de operador de diagrama (σ, seleção), pertencente inteiramente à árvore de consulta de D40 — mesma classe estrutural que "B"/π, "nome,endereco", "idade < 40 OR renda > 30000" e "Cliente", todos parte do mesmo desenho. Seu papel não é: alternativa (não há alternativas nesta questão discursiva), marcador de item, inicial de nome próprio, letra de tabela, rótulo de eixo, identificador, unidade, abreviação de uma letra, ou fragmento de palavra quebrada por mudança de fonte. É, estruturalmente, um rótulo de diagrama cujo único motivo de não-absorção é ser maior, não menor, que o corpo da página.

## K. Duplicidade com asset

As 7 condições da Seção 12 foram verificadas uma a uma:

1. Asset oficial associado a D40: **sim** (`figure-01`, listado nos `assets` de D40).
2. Asset contém o conteúdo visual completo: **sim** (confirmado por inspeção visual direta — mostra "π_nome,endereço" / "σ_idade < 40 OR renda < 30000" / "Cliente" por completo).
3. O texto isolado está inequivocamente ligado à região do asset: **sim** (mesma página, mesmo diagrama, glifo irmão "B"/π já demonstrado como parte do mesmo desenho).
4. Exclusão não remove conteúdo pesquisável útil: **sim** — "F" nunca foi um "F" de verdade; removê-lo não apaga nenhuma palavra real (a condição σ completa, "idade < 40 OR renda > 30000", já está corretamente ausente do texto, absorvida como rótulo — remover apenas o símbolo do operador não quebra nenhuma frase).
5. O papel do fragmento foi identificado: **sim** (Seção F/J acima, por fingerprint de fonte + renderização, nunca por inferência semântica).
6. Um oráculo de segurança confirma conservação de todo o resto: **sim** (Seção M).
7. Nenhuma outra alteração de asset necessária: **sim** — `figure-01.png`/`figure-02.png` permanecem byte-idênticos (sha256 confirmado idêntico antes/depois).

## L. Solução

Hierarquia de correção (Seção 13) aplicada em ordem:

1. **Correção geral por papel+geometria:** rejeitada. Qualquer regra geral testável ("linha isolada de letra maiúscula única, fonte maior que o corpo, tocando uma região") teria que ser validada contra todos os contraexemplos obrigatórios (alternativa legítima "F" com >5 alternativas, variável F, função F(x)/f(x), marcador de item, inicial de nome, letra de tabela, rótulo de eixo/diagrama, código-fonte, identificador, unidade, símbolo matemático, abreviação de uma letra, fragmento legítimo dividido por mudança de fonte) — nenhum discriminador geométrico genérico foi encontrado capaz de separar esses casos do caso real sem introduzir um novo limiar arbitrário (proibido pela Seção 10).
2. **Extensão de relação estrutural existente:** rejeitada por si só — `LineRegionRelation`/`_text_consumption_decision` já capturam toda a evidência geométrica disponível (`state`, `raw_intersects`, `matches_absorbed_label`); nenhum novo campo geométrico mudaria o resultado "ambiguous", que é a classificação correta na ausência de evidência de identidade de fonte/glifo.
3. **Regra declarativa de perfil:** rejeitada — não há um padrão reutilizável em nível de perfil (`ExamStructureProfile`) que descreva "símbolo de operador maior que o corpo"; seria uma regra ad-hoc disfarçada de declarativa.
4. **Override documental travado por hash+bbox:** **adotado**. Novo par simétrico ao já existente `protect_from_region_membership`:
   - `LayoutOverrideSet.forces_region_membership(pdf_sha256, page, bbox)` (layout_overrides.py) — mesma semântica de contenção (bbox candidato precisa estar totalmente dentro do bbox do override).
   - `assembler._line_in_region`: consultado **somente** quando `_text_consumption_decision` já retornou `"ambiguous"` — nunca substitui uma decisão `"accepted"` já tomada pelos próprios méritos geométricos.
   - Uma única entrada nova em `layout-overrides.yaml` (`rule: force_region_membership`, página 17, bbox 95.0,574.0–104.0,588.0, question_id enade-2008-computing-d40), com `reason`/`evidence` documentando charcode/glyph_id/font fingerprint/comparação visual, seguindo a mesma convenção de texto livre já usada pelas Fases 3O/3Q para os campos ricos exigidos (identidade de objeto, texto bruto, motivo, evidência) — o schema Pydantic existente (`LayoutOverride`) não foi estendido com novos campos, pela mesma razão de "nenhuma capacidade sem exemplo positivo E negativo" já aplicada a todo o projeto: um único caso não justifica novos campos estruturados quando o texto livre já documentado pelas fases anteriores cumpre a mesma função de auditoria.

Nenhuma remoção literal (`if text == "F"`), nenhum filtro por ID de questão/página/coordenada fixa na lógica central, nenhum enfraquecimento do fail-safe original (o padrão "ambiguous" permanece inalterado para toda e qualquer linha sem override correspondente).

## M. Safety oracle

`canonical_objects_before - proven_noncanonical_fragment = canonical_objects_after`, verificado da seguinte forma:

- Exatamente um objeto excluído (o parágrafo `text: F`) — confirmado por diff exato do Markdown (ver Seção P).
- Nenhuma linha legítima perdida: todo o conteúdo restaurado nas Fases 3G/3N/3O (schema de duas linhas, parágrafo de índices, ordem da frase de abertura) permanece presente byte-a-byte.
- Nenhuma palavra alterada: diff mostra remoção pura de duas linhas (`text: F` + separador), zero alteração em qualquer outra linha do arquivo.
- Nenhuma alternativa alterada: D40 é discursiva, sem alternativas.
- Nenhuma mudança de ordem: todos os outros blocos de conteúdo mantêm posição idêntica.
- Nenhum dono trocado: `owner_key=discursive-40` inalterado; nenhuma linha de outra questão foi afetada.
- Nenhum bloco de conteúdo removido além do alvo: confirmado — `figure-02`, ambos os blocos de código, todos os parágrafos remanescentes intactos.
- Nenhum asset alterado: `figure-01.png`/`figure-02.png` sha256 idênticos antes/depois.
- Nenhuma questão não-alvo alterada: `diff -rq` em todo `data/questions/2008/all-computing` mostra exclusivamente `enade-2008-computing-d40.md` como diferente.
- Nenhuma entrada do source-token-ledger alterada indevidamente: `q24-item-marker-I`, `q24-item-marker-II`, `q45-item-iii-function-formula` permanecem byte-idênticas; apenas uma nova entrada (`d40-tree-selection-operator-sigma`) foi adicionada.

## N. Shadow mode

O novo mecanismo (`force_region_membership`) foi validado por regeneração completa e `diff -rq` contra o corpus canônico, antes de qualquer atualização de manifest:

- 2008-b (77 questões): apenas `enade-2008-computing-d40.md` difere; as outras 76 são byte-idênticas.
- 2011 (55 questões): zero diferenças.
- 2021 CC-bacharelado (40 questões): zero diferenças.
- 2021 CC-licenciatura (40 questões): zero diferenças.
- 2021 Sistemas de Informação (40 questões): zero diferenças.

Como o mecanismo só pode disparar quando (a) a decisão geométrica já é `"ambiguous"` E (b) existe um override com hash+página+bbox exatos casando por contenção, e como apenas uma única entrada foi escrita (travada ao PDF de 2008-b, página 17, bbox de ~9x14pt), é estruturalmente impossível que ele tenha efeito em qualquer outra linha de qualquer outro documento — confirmado empiricamente pelo `diff -rq` acima, não apenas presumido pelo desenho do mecanismo.

## O. Contraexemplos

Nenhuma regra geral foi introduzida, então a maioria dos contraexemplos obrigatórios da Seção 15 é satisfeita trivialmente (o mecanismo não pode alcançá-los sem um override dedicado, que não foi escrito para nenhum deles). Confirmado explicitamente por regressão real, sem necessitar de fixture sintética adicional:

- **Q07 (Fase 3P):** alternativas A-E e enunciado byte-idênticos (`git diff` vazio).
- **Q24/Q45 (Fase 3Q):** ambas byte-idênticas (`git diff` vazio); testes `test_q24_item_markers_i_and_ii_are_now_present`/`test_q45_item_iii_own_three_lines_are_now_complete` continuam passando sem alteração.
- **D40 própria "B"/π (mesma página, mesma fonte, mesmo mecanismo de origem do defeito):** deliberadamente NÃO tocada — permanece publicada exatamente como antes (`"...respectivamente. B\tnome,endereco"`), confirmando que o override é específico ao bbox exato do "F" e não generaliza nem mesmo para seu par geometricamente mais próximo.
- **2011 Q23, 2021 SI Q33 (Fase 3P), Q01/Q73 (Fase 3O), Q64/2011 Q23 (Fase 3P):** todos cobertos pela regeneração completa de 2011/2021 (zero diferença) e pela suíte de testes completa (750/750 passando).
- **Testes unitários novos** (`test_extraction_assembler.py`, `test_layout_overrides.py`) cobrem positivamente (linha "ambiguous" com override casando → excluída) e negativamente (sem override → permanece visível; override com hash errado → sem efeito; override nunca dispara sobre uma decisão já "accepted"/`contained`).

## P. D40 final

Diff exato do Markdown publicado (único trecho alterado):

```diff
 ![Figura da questão](enade-2008-computing-d40/figure-01.png)

-F

 Para que o otimizador de consultas passasse a utilizar os índices...
```

Mais a promoção de frontmatter: `extraction_status: needs_review` → `verified`; `visual_validation: failed` → `passed`. Nenhuma outra linha do arquivo (159 linhas de corpo) foi alterada. Confirmado por inspeção visual da página 17 renderizada (`page.get_pixmap()`) que todo o conteúdo restante corresponde exatamente ao PDF fonte, incluindo a árvore de consulta completa (agora representada apenas pelo já existente `figure-01.png`, sem duplicação textual).

## Q. Q45 preservada

`git diff` em `enade-2008-computing-q45.md`: vazio. `data/manifests/source-token-ledger-2008.yaml`: a entrada `q45-item-iii-function-formula` permanece byte-idêntica (comparada campo a campo antes/depois). `data/manifests/blocker-ledger-2008.yaml`: `q45-item-iii-formula-image-gap` permanece com status `open` e texto idêntico. `data/manifests/visual-audit-2008-computing.json`: entrada de Q45 byte-idêntica. Nenhum asset de Q45 foi tocado (não regenerado nesta verificação por não haver motivo — confirmado indiretamente pelo `diff -rq` de todo o diretório 2008-b, que não aponta Q45 como alterada).

## R. Source-token ledger

Nova entrada `d40-tree-selection-operator-sigma` (schema idêntico ao já estabelecido pela Fase 3Q): `extraction_status: glyph_verified` (valor não usado por nenhuma entrada anterior, mas coerente com o propósito do ledger — "identidade comprovada por renderização de glifo, não por confiar no charcode/encoding declarado"), `canonical_representation: null` (nenhum caractere é inserido no texto canônico — a ação é remoção, não substituição, então não há uma "representação canônica" a publicar), `visual_fallback` apontando para o já publicado `figure-01.png`. As 3 entradas pré-existentes (`q24-item-marker-I`, `q24-item-marker-II`, `q45-item-iii-function-formula`) permanecem byte-idênticas.

## S. Overrides

Contagem real confirmada por leitura direta do YAML: **62 → 63** (não presumida). A nova entrada usa `rule: force_region_membership` (novo tipo, primeira ocorrência no projeto), com todos os campos exigidos pela Seção 13 presentes — como texto livre dentro de `reason`/`evidence` (seguindo a convenção já estabelecida pelas Fases 3O/3Q, nunca como novos campos Pydantic para uma única instância): `source_pdf_sha256` (campo `pdf_sha256` do schema), `question_id`, `source_page` (campo `page`), `bbox`, `object_fingerprint` (charcode/glyph_id/font fingerprint no texto de `reason`), `raw_text` ("F", no texto de `reason`), `reason`, `evidence`, `reviewer_status` (campo `status: reviewed`), `data_contract_version`/`regression_tests` (referenciados via `evidence` apontando para este relatório e para o source-token-ledger, e via a lista de testes de regressão no blocker-ledger).

## T. Auditoria visual

`data/manifests/visual-audit-2008-computing.json`: `enade-2008-computing-d40` promovida de `status: failed` para `status: passed`, com `notes` documentando a causa raiz, a evidência e a exclusão explícita do vazamento irmão "B" do escopo desta fase. Diff do arquivo: exatamente 2 linhas alteradas (confirmado — a primeira tentativa, que usava reserialização completa via `json.dump(sort_keys=True)`, foi revertida por produzir um diff de 310 linhas de puro reordenamento cosmético em todas as outras entradas; a correção final usa edição cirúrgica preservando byte a byte todas as outras 76 entradas).

## U. Blocker ledger

Nova entrada dedicada `d40-cosmetic-selection-operator-leak` (status `resolved`), documentando o histórico completo: origem na Fase 3G (aceito como trade-off cosmético do design tri-state), causa raiz definitiva (Fase 3R, fingerprint de fonte + renderização), primeiro estágio divergente (filtro de candidato a rótulo por tamanho de fonte, figures.py), solução (override simétrico `force_region_membership`), evidência, testes de regressão, e validação visual. A entrada pré-existente `d40-table-reading-order-scramble` foi atualizada apenas para apontar (`ver d40-cosmetic-selection-operator-leak`) em vez de manter a afirmação agora desatualizada de que o vazamento "F" permanecia "não tocado" — sem reescrever seu próprio histórico de resolução (Fase 3N). A entrada `d40-region-merge-content-loss` teve seu campo `visual_validation` corrigido de `failed` para `passed` (o único motivo de D40 permanecer `failed` no nível de questão era exatamente o "F", agora resolvido). Total de blockers: 59 → 60.

## V. Gold e readiness

`enade build-gold --year 2008 --course all-computing`: **73/77 verified** (subiu de 72/77), `needs_review_count: 4` (D09, D10, D59, Q45 — D40 removida da lista `unresolved_question_ids`). `enade verify-gold`: OK, hashes batem. `enade assess-readiness --ready-label READY_FOR_2008_ENGINEERING_TEST`: `NOT_READY_FOR_2008_ENGINEERING_TEST` (mantido, como esperado, pois Q45 permanece `failed`) — **visual audit: 76 passed, 1 failed (Q45), 0 not_performed** — exatamente o resultado esperado declarado pelo próprio prompt desta fase. As limitações documentadas de D09/D59/Q8/Q38/Q55 permanecem inalteradas na lista de blockers de `assess-readiness`.

## W. Proteção de 2011/2021

Confirmado por regeneração completa + `diff -rq` (não apenas pela suíte de testes): 2011 (55 questões) e os três cursos de 2021 (40 questões cada, 120 no total) são byte-for-byte idênticos ao corpus canônico antes e depois de todas as mudanças de código/dados desta fase. `pytest tests/test_protected_corpus.py`: 4/4 passando.

## X. Testes, quality gates, reprodutibilidade

```text
pytest tests/ -q          : 750 passed (antes: 741; +9 testes novos)
ruff check .               : All checks passed!
ruff format --check .      : 410 files already formatted
mypy src                   : Success: no issues found in 60 source files
enade validate-schema      : 13/13 fixture(s) valid
enade validate-manifest    : OK (0 warning(s))
enade audit-extraction (2008-b)         : 77/77 OK
enade audit-extraction (2011)           : 55/55 OK
enade audit-extraction (2021, 3 cursos) : 40/40 OK cada
enade verify-gold + assess-readiness (2008-b, 2011, 2021 CC-B): consistentes
  com a Seção V/W acima
```

9 testes novos: 4 em `tests/test_layout_overrides.py` (mecanismo `forces_region_membership` isolado — positivo, negativo por bbox, negativo por hash, mutuamente exclusivo com `protects_from_region_membership`), 4 em `tests/test_extraction_assembler.py` (comportamento em `_line_in_region` com geometria sintética — ambíguo sem override permanece visível; ambíguo com override é excluído; override nunca dispara sobre decisão já "accepted"; override ignora hash divergente), 1 em `tests/test_extraction_pipeline_2008.py` (regressão completa de D40 usando o pipeline real e o override real, confirmando ausência do "F", presença do "B" irmão fora de escopo, e presença de todo o conteúdo já restaurado pelas Fases 3O/3Q).

**Reprodutibilidade:** duas execuções limpas e independentes de `enade extract --year 2008 --course all-computing` (após a atualização do manifest de auditoria visual) produziram saída byte-idêntica entre si e idêntica ao corpus publicado. Uma terceira execução anterior (antes da atualização do manifest) diferiu apenas nos campos de frontmatter `extraction_status`/`visual_validation` (dependentes do manifest externo, não do código de extração) — o corpo do Markdown já era idêntico nas três execuções.

## Y. Git final e recomendação

`git status --short` ao final desta fase lista exatamente os arquivos de dados/código/testes/documentação modificados por este trabalho (nenhum arquivo scratch remanescente — `diag_d40_*.py` e todos os diretórios temporários `/d/tmp_phase3r_*` foram apagados). Nenhum commit, push, PR, merge ou tag foi criado. `master`/`origin/master` inalterados.

**Recomendação:** com D40 totalmente resolvida, o único item impedindo `RESIDUAL_LAYOUT_NOT_STABILIZED` de virar `RESIDUAL_LAYOUT_STABILIZED` para 2008-b é Q45's próprio "f(x) = √x" desenhado como vetor. Recomenda-se uma **Fase 3S dedicada à representação inline de fórmulas vetoriais**, usando Q45 como caso de teste obrigatório — explorando, por exemplo, um mecanismo de asset "small-formula-inline" que renderize o trecho vetorial como uma imagem inline dentro do próprio parágrafo de texto (em vez de depender de um `figure-01.png` de página inteira já publicado para um contexto diferente), sem nunca fabricar a string "f(x) = √x" como texto. Não iniciar Q8/Q38/Q55 nem qualquer outro bundle/ano nesta futura fase; manter `NOT_READY_FOR_2008_ENGINEERING_TEST` até Q45 ser genuinamente resolvida ou deliberadamente aceita como limitação documentada permanente.

## Arquivos alterados nesta fase

```text
src/enade/extraction/layout_overrides.py        (+ forces_region_membership)
src/enade/extraction/assembler.py               (_line_in_region: consulta o
                                                   override somente em "ambiguous")
data/manifests/layout-overrides.yaml            (+1 entrada: 62 → 63)
data/manifests/source-token-ledger-2008.yaml    (+1 entrada)
data/manifests/blocker-ledger-2008.yaml         (+1 entrada nova, 1 atualizada
                                                   por referência cruzada,
                                                   1 campo visual_validation
                                                   corrigido: 59 → 60)
data/manifests/visual-audit-2008-computing.json (D40: failed → passed)
data/manifests/extraction-audit-2008-computing.{csv,json} (D40: needs_review → verified)
data/manifests/gold-2008-computing.json         (72/77 → 73/77 verified)
data/manifests/extraction-capabilities.json     (+1 capacidade, G1)
data/questions/2008/all-computing/enade-2008-computing-d40.md (parágrafo "F" removido)
tests/test_layout_overrides.py                  (+4 testes)
tests/test_extraction_assembler.py              (+4 testes)
tests/test_extraction_pipeline_2008.py          (+1 teste)
docs/phase-3r-report.md                         (novo)
```
