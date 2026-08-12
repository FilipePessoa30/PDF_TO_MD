# FASE 2A — Relatório Final

**Teste de Generalização: Caderno Unificado ENADE Computação 2011**

Data: 2026-08-11
Branch: `feat/enade-2011-unified-extraction`
Escopo: `data/questions/2011/all-computing` (55 questões canônicas: 50 objetivas + 5 discursivas, materializadas em 4 provas virtuais)

---

## A. Classificação

## `GENERALIZATION_PARTIAL`
## `NOT_READY_FOR_LEGACY_LAYOUT_TEST`

O pipeline construído para 2021 **generalizou substancialmente** para o layout de 2011 sem nenhum hardcode de ano espalhado pelo extrator — mas a auditoria visual encontrou **3 defeitos estruturais reais e não corrigidos** (detalhados nas Seções L/R), e apenas 8/55 questões foram individualmente verificadas visualmente. Isso é exatamente o critério documentado para `GENERALIZATION_PARTIAL` ("maioria extraída; existirem needs_review; gold 2011 permanece provisional; 2021 permanece preservado") e para `NOT_READY_FOR_LEGACY_LAYOUT_TEST` — não escolhido por segurança excessiva, mas porque a evidência de fato aponta para isso.

## B. Git

- Baseline confirmado: `master` = `origin/master` = `a5dfaab0c105150df3a7201c16547708cef45292`, working tree limpo.
- Branch criada a partir desse baseline: `feat/enade-2011-unified-extraction` (sem tocar `master`).
- HEAD atual: ainda em `a5dfaab` na branch nova — **nenhum commit foi criado** durante esta fase.
- `master`/`origin/master` permanecem intocados (reconfirmado ao final: mesmo SHA).
- Estado final: 8 arquivos modificados + 11 novos (ver Seção S), nada staged, nada commitado, nada enviado.

## C. Corpus

| Arquivo | SHA-256 | Páginas | Tamanho |
|---|---|---|---|
| `2011/1_prova.pdf` | `eb3b497f...4548` | 32 | 1.886.812 bytes |
| `2011/2_gabarito.pdf` | `e799cac6...0577b` | 1 | 24.369 bytes |
| `2011/3_padrao.pdf` | `386353635a...0cd412` | 5 | 115.597 bytes |

Todos os três hashes conferem **exatamente** com `data/manifests/source-exams.yaml` (manifesto da Fase 0, `commit_sha: a657632b72b97468c8a5eb3b433d1abb4a5511c5` do repositório upstream `geacc/enade`). Nenhum arquivo bruto foi modificado. Camada de texto confirmada utilizável nos três (já registrado na Fase 0).

## D. Estrutura Oficial (confirmada diretamente no PDF, não assumida)

Evidência primária, lida diretamente do PDF (não copiada de documentação anterior — a própria `docs/corpus.md` continha uma tabela ASCII ambígua que foi re-verificada e confirmada correta apenas após leitura do texto bruto):

- **Página 1** (tabela de instruções “Partes / Número das questões”): confirma `1 a 8` (FG objetivas), `Discursiva 1 e Discursiva 2` (FG discursivas), `9 a 30` (Comum objetivas), `Discursiva 3 a Discursiva 5` (Comum discursivas), `31 a 35` / `36 a 40` / `41 a 45` / `46 a 50` (blocos por curso), `1 a 9` (questionário de percepção).
- **Cabeçalhos de página**: `COMPUTAÇÃO` (genérico, Q1-30+D1-5), `LICENCIATURA` (p.21-23), `CIÊNCIA DA COMPUTAÇÃO` (p.24-25), `ENGENHARIA DA COMPUTAÇÃO` (p.26-29), `SISTEMAS DE INFORMAÇÃO` (p.30-31).
- **Página 21/22** (bloco “ATENÇÃO!”): reafirma a mesma tabela curso→intervalo, textualmente, para o estudante.
- **Página 32**: cabeçalho `QUESTIONÁRIO DE PERCEPÇÃO DA PROVA` explícito + reuso de marcadores `QUESTÃO 1`..`QUESTÃO 9` — corretamente excluída da extração acadêmica (`excluded_perception_pages: [32]` em toda execução).
- Essa estrutura foi codificada em `data/manifests/exam-structure-2011.yaml` (perfil declarativo) e **cross-verificada em tempo de execução** contra o texto real da página 1 (`exam_profile.verify_declared_profile`) — 0 divergências em toda execução.

## E. Resultado Canônico

- **50 objetivas + 5 discursivas = 55 questões canônicas únicas.** Confirmado por `detect_question_boundaries`: 55 spans, 0 warnings, 0 lacunas, 0 duplicatas em toda a extração final.
- Nenhuma questão comum (Q1-30, D1-5) foi duplicada por curso — cada uma existe **uma única vez** no banco, com `applicable_courses: [all-computing]`.
- IDs: `enade-2011-computing-{q|d}NN` (shorthand `computing`, não ligado a nenhum curso específico) — estáveis, únicos, confirmados sem colisão.

## F. Aplicabilidade

| Questões | `applicable_courses` | Evidência |
|---|---|---|
| Q1-30, D1-5 | `all-computing` | Tabela p.1 + cabeçalho genérico "COMPUTAÇÃO" |
| Q31-35 | `ciencia-da-computacao-licenciatura` | Cabeçalho "LICENCIATURA" p.21-23 |
| Q36-40 | `ciencia-da-computacao-bacharelado` | Cabeçalho "CIÊNCIA DA COMPUTAÇÃO" p.24-25 |
| Q41-45 | `engenharia-da-computacao` | Cabeçalho "ENGENHARIA DA COMPUTAÇÃO" p.26-29 |
| Q46-50 | `sistemas-de-informacao` | Cabeçalho "SISTEMAS DE INFORMAÇÃO" p.30-31 |

Regra `all-computing` não combinado com curso explícito: validada por `ExamStructureProfile`'s próprio model_validator (mesma regra do ADR 3 da Fase 0), testada em `tests/test_exam_profile.py`.

## G. Virtual Exam Sets

Materializados via `virtual_exam.materialize_virtual_exam_set` (view read-only sobre o banco canônico, sem duplicar dado):

| Curso | Objetivas | Discursivas | Total | Issues |
|---|---|---|---|---|
| Licenciatura | 35 (1-30 + 31-35) | 5 | 40 | 0 |
| Ciência da Computação | 35 (1-30 + 36-40) | 5 | 40 | 0 |
| Engenharia de Computação | 35 (1-30 + 41-45) | 5 | 40 | 0 |
| Sistemas de Informação | 35 (1-30 + 46-50) | 5 | 40 | 0 |

`validate_virtual_exam_set` confirma para os 4 cursos: contagem correta, ordem ascendente preservada, zero duplicatas, zero contaminação cruzada entre cursos.

## H. Extração — Generalização vs. Adaptação vs. Hardcode

**Reutilizado sem nenhuma mudança** (validado rodando contra o PDF real de 2011):
- `detect_question_boundaries` (regex de marcador `QUESTAO [DISCURSIVA] N` + exclusão de página de percepção) — funcionou nos 55/55 marcadores reais sem nenhum ajuste.
- `answer_standard.py` (marcadores `QUESTAO DISCURSIVA N` / `Padrão de resposta`) — idêntico em 2011.
- `tables.py`, `content_block.py`, assets/figuras (mecanismo geral), `gold.py`, `readiness.py`, `visual_audit.py` — reutilizados como estão.

**Mudanças gerais implementadas** (bugs reais, gerais, aplicáveis a qualquer ano/layout, não hardcode de 2011):
1. `detect_column_margins`: troca de "top-2 buckets por frequência" para "maior gap entre buckets qualificados" — corrige más classificações de coluna quando uma coluna tem múltiplos níveis de indentação.
2. `_merge_orphan_markers`: agora exige que o candidato a parceiro esteja na **mesma coluna** (não só perto em Y) — corrige merges cross-coluna espúrios.
3. `MIN_LINES_PER_COLUMN`: 4→3 — uma coluna genuína pode ter poucas linhas "substanciais".
4. `detect_column_margins` exclui linhas de chrome (cabeçalho/rodapé) do pool de evidência — cabeçalhos repetidos por página não devem fabricar uma coluna falsa.
5. `chrome.py`: adicionados os literais exatos do cabeçalho/transição específicos de 2011 (ano "2011", variante sem espaços do cabeçalho, bloco "ATENÇÃO!" completo, títulos de bloco por curso) — mesmo padrão já usado para os literais de 2021, apenas evidência nova.
6. `answer_key.py`: novo `parse_flat_item_gabarito` para o formato de gabarito "ITEM→GABARITO" (tabela plana, sem prefixo "QUESTAO") — formato de documento genuinamente diferente, não um branch por ano.
7. `to_question.build_question`/`pipeline.extract_exam`: generalizados para aceitar `applicable_courses`/`section`/`id_shorthand` resolvidos externamente (por um profile declarativo OU pelo caminho de curso único de 2021), em vez de assumir um único curso fixo.

**Adaptações declarativas** (dados, não código):
- `data/manifests/exam-structure-2011.yaml` — perfil da estrutura do caderno unificado.
- CLI: `course=all-computing` seleciona o caminho de caderno unificado (busca de arquivo sem letra, uso do profile) — um único ponto de despacho, não espalhado pelo extrator.

**Hardcodes**: nenhum `if year == 2011` foi introduzido em nenhum módulo de extração compartilhado. A única menção literal a "2011" no código é o nome do arquivo de perfil default (`exam-structure-{year}.yaml`, funciona para qualquer ano) e os literais evidence-based em `chrome.py` (mesmo padrão que já existia para 2021).

**Complexidade real**: a generalização exigiu 4 correções geométricas genuínas no `layout.py` (não apenas "plugar o profile") — o layout mais denso e com mais colunas de 2011 expôs bugs latentes que o layout de 2021 nunca havia exercitado. Uma quinta tentativa de correção (largura mínima de marcador órfão) foi implementada, verificada, e **revertida** por regredir o corpus 2021 já certificado (ver Seção R).

## I. Assets

- 34 assets de questão renderizados (crops de figura/tabela) para as 55 questões — 28 questões têm ao menos 1 asset.
- 0 assets de padrão de resposta — achado real e verificado: `3_padrao.pdf` não contém nenhuma imagem incorporada em nenhuma de suas 5 páginas (`page.get_images()` = 0 em todas), diferente de 2021 (cujo D4 tinha 4 imagens). D3/D4/D5 do padrão contêm pseudocódigo e estruturas tabulares como texto simples, preservadas linearmente (sem reconstrução de tabela/código dedicada para o padrão — mesmo escopo que o modelo `AnswerStandardReference` já suportava antes desta fase).
- **Integridade**: 2 problemas reais confirmados por inspeção visual direta (Seção L/R: Q13 região espúria, Q22 tabela incompleta incluindo o próprio fallback visual). Os demais 26 assets com figura não foram individualmente confirmados pixel-a-pixel contra o PDF (fora do escopo de tempo desta fase) — Q35 (tirinha de 5 quadros) foi confirmado completo e correto por inspeção direta.

## J. Gabarito

`2011/2_gabarito.pdf`: tabela plana `ITEM`/`GABARITO`, 50 itens, confirmada **estruturalmente diferente** do formato "QUESTAO N" usado em todos os outros anos deste corpus — exigiu um parser novo (`parse_flat_item_gabarito`), não uma adaptação do existente.

- 50/50 itens parseados, 0 warnings.
- 2 anuladas confirmadas: item 13 (dentro do bloco comum Q9-30, afeta todos os 4 cursos) e item 44 (dentro do bloco Engenharia Q41-45, afeta só esse curso).
- Modeladas como `correct_answer=null, answer_validation_status=annulled` — nunca `"ANULADA"` como alternativa, conforme exigido.
- Nenhuma ambiguidade nos demais 48 valores (todos A-E reconhecidos).

## K. Discursivas (D1-D5)

| # | Tema | Conteúdo do padrão | Assets |
|---|---|---|---|
| D1 | Vantagens da EaD | Prosa | 0 |
| D2 | Analfabetismo/políticas públicas | Prosa | 0 |
| D3 | Fibonacci (iterativo+recursivo) | Pseudocódigo (2 algoritmos) | 0 |
| D4 | Árvore binária de busca | Pseudocódigo + função recursiva | 0 |
| D5 | Mapeamento de memória cache | Prosa + 3 mini-tabelas rótulo/valor | 0 |

Todos os 5 textos/páginas/hashes do padrão foram extraídos e vinculados (5/5 `answer_standards_linked`). Um glifo de atribuição mal-decodificado ("Å", provavelmente "←") foi observado no pseudocódigo de D3/D4 e **não corrigido** — resíduo documentado, mesma política da Fase 1C para resíduos de glifo isolados sem investigação forense completa nesta fase.

## L. Auditoria Visual

**Não é 55/55.** 9 questões foram individualmente inspecionadas visualmente (via leitura direta das páginas do PDF real e comparação com o Markdown/asset renderizado) — 6 `passed` + 3 `failed` = 9, +46 `not_performed` = 55 (CORRIGIDO NA FASE 2B: o resumo original desta seção somava erroneamente 8+46=54; o dado machine-readable em `visual-audit-2011-computing.json` sempre esteve correto — 9 entradas, nenhuma faltando, nenhuma duplicada — só a prosa deste relatório contava errado. A Fase 2B adicionou `assess_visual_audit_coverage()` como gate reutilizável e testado para que esse tipo de erro de contagem manual nunca mais precise ser confiado à leitura humana):

| Questão | Status | Achado |
|---|---|---|
| Q09 | passed | Completa, correta |
| Q11 | passed | Sem figura real; aviso automático é falso-positivo benigno |
| Q13 | **failed** | Região de figura espúria corrompe o bloco de pseudocódigo |
| Q22 | **failed** | Tabela-verdade perde cabeçalho + primeira linha (estrutura E fallback visual) |
| Q23 | **failed** | Notação matemática inline ausente (Σ, λ, expressão regular) |
| Q34 | passed | Sem figura real; aviso automático é falso-positivo benigno |
| Q35 | passed | Tirinha de 5 quadros, completa e correta |
| Q46 | passed | SQL preservado corretamente como prosa (fonte não é monoespaçada) |
| Q47 | passed | Completa, correta |

As 46 questões restantes permanecem `visual_validation: not_performed` — honestamente, não inspecionadas, conforme autorizado explicitamente pela Seção 21 do prompt.

## M. Gold 2011

- `maturity: provisional` (deliberado — não seria honesto declarar `validated` com 3 blockers estruturais abertos e 46 questões não auditadas visualmente).
- 55 questões, 4 verified, 51 needs_review.
- 5 padrões de resposta cobertos (texto+hash), 0 assets de padrão (achado real, não omissão).
- `verify-gold`: OK (55 questões batem com o manifesto — hashes íntegros).
- 3 `structural_blockers` registrados explicitamente (Q13, Q22, Q23 — ver Seção R).

## N. Regressão 2021

Confirmado **zero mudança** em qualquer artefato do corpus 2021, verificado repetidamente após cada mudança de código (não apenas uma vez no final):
- `diff -rq` byte-a-byte contra `data/questions/2021/ciencia-da-computacao-bacharelado` após cada uma das 6 mudanças em `layout.py`/`chrome.py`/`pipeline.py`/`to_question.py`: idêntico em todas.
- `enade verify-gold --year 2021`: OK, 40/40, `maturity=validated` (inalterado).
- `enade assess-readiness --year 2021`: `READY_FOR_2011`, 0 blockers (inalterado).
- `git status --short data/questions/2021`: 0 linhas.

Uma tentativa de correção (largura mínima do marcador órfão, ver Seção R) **foi revertida** especificamente porque, embora corrigisse a Q22 de 2011, alterava 3 arquivos já certificados de 2021 (Q23, Q34, D4) — a proteção do corpus 2021 teve prioridade sobre a correção do defeito de 2011, conforme exigido.

## O. Testes

- Suíte herdada: 294 testes (Fase 1C), todos ainda passam.
- Novos: 24 testes — `test_exam_profile.py` (10), `test_virtual_exam.py` (7), extensões em `test_extraction_layout.py` (+3) e `test_extraction_answer_key.py` (+4).
- **Total: 318 testes, 318 passando, 0 falhas.**

## P. Quality Gates

```
pytest                  318 passed
ruff check               All checks passed!
ruff format --check      198 files already formatted
mypy src                  Success: no issues found in 49 source files
validate-schema           13/13 fixture(s) valid
validate-manifest         OK (0 warning(s))
audit-extraction (2021)   40/40 OK
audit-extraction (2011)   55/55 OK
verify-gold (2021)        OK, maturity=validated, 40/40
verify-gold (2011)        OK, maturity=provisional, 4 verified/51 needs_review
assess-readiness (2021)   READY_FOR_2011, 0 blockers
assess-readiness (2011)   NOT_READY_FOR_LEGACY_LAYOUT_TEST, 54 blockers (3 estruturais + 51 needs_review)
```

## Q. Reprodutibilidade

Duas execuções independentes de `enade extract --year 2011 --course all-computing` em diretórios de scratch separados, a partir do zero: **byte-idênticas entre si** (`diff -rq` código 0, 89 arquivos cada — 55 md + 34 assets) e **byte-idênticas ao corpus real committed**. Tempo de execução: ~13-16s por corrida completa (32 páginas, 55 questões, 34 assets).

## R. Bugs Encontrados

Todos, incluindo os corrigidos, revertidos, e os deixados como limitação conhecida:

1. **[Geral, corrigido]** `detect_column_margins` escolhia os 2 buckets de x0 mais frequentes em vez dos mais separados — misclassificava colunas quando uma coluna tinha 2 níveis de indentação. Corrigido (maior gap). Zero regressão 2021.
2. **[Geral, corrigido]** `_merge_orphan_markers` ignorava X, só considerava Y — permitia merge cross-coluna espúrio. Corrigido (mesma coluna exigida). Zero regressão 2021.
3. **[Geral, corrigido]** `MIN_LINES_PER_COLUMN=4` rejeitava colunas genuínas com poucas linhas longas. Reduzido para 3. Zero regressão 2021.
4. **[Geral, corrigido]** Linhas de chrome (cabeçalho de página) contavam como evidência de coluna, fabricando uma coluna falsa a partir de um parágrafo indentado único. Corrigido (chrome excluído da evidência). Zero regressão 2021.
5. **[Específico de 2011, corrigido]** Cabeçalho de página "EXAME NACIONAL..." falhava a reconstrução geométrica de espaços em algumas páginas, vazando como palavra colada; ano "2011" e blocos "ATENÇÃO!"/títulos de curso vazavam para dentro do conteúdo. Corrigido via literais exatos em `chrome.py` (mesmo padrão de 2021).
6. **[Formato de documento novo, corrigido]** Gabarito 2011 usa tabela plana `ITEM/GABARITO`, não o marcador `QUESTAO N` de todo o resto do corpus. Novo parser dedicado, não um hack no parser existente.
7. **[Real, NÃO corrigido, documentado]** Q13: uma região de "figura" espúria e mal-delimitada captura conteúdo de Q11/Q12 não relacionado e corrompe o bloco de pseudocódigo de Q13. Causa raiz não isolada; nenhuma correção tentada (risco/tempo). `needs_review`.
8. **[Real, tentativa corrigida E revertida]** Q22: cabeçalho da tabela-verdade ("A B C D S") e primeira linha de dados são absorvidos pelo mesmo mecanismo de marcador órfão (bug #2, mas por largura de glifo, não coluna) — uma correção por largura mínima resolveu isso mas alterou 3 arquivos já certificados de 2021 (Q23, Q34, D4), então foi **revertida**. `needs_review`, documentado com a causa raiz completa para uma correção futura mais cirúrgica.
9. **[Real, NÃO corrigido, documentado]** Q23: notação matemática inline (Σ, λ, expressão regular) ausente do texto extraído — provavelmente uma subfonte de fórmula/imagem inline não reconhecida como figura nem como texto. Não investigado a fundo nesta fase (limitação de tempo, não de risco). `needs_review`.
10. **[Limitação conhecida, não corrigida]** Q10: alternativas em formato de fração (numerador/denominador empilhados) só capturam o denominador no texto — a fração completa nunca é reconstruída. Achado durante a auditoria visual; não corrigido.

## S. Arquivos

**Modificados (8):** `src/enade/cli.py`, `src/enade/extraction/{answer_key,chrome,layout,pipeline,to_question}.py`, `tests/test_extraction_{answer_key,layout}.py`.

**Novos (11):** `src/enade/extraction/exam_profile.py`, `src/enade/virtual_exam.py`, `tests/test_{exam_profile,virtual_exam}.py`, `data/manifests/exam-structure-2011.yaml`, `data/manifests/{extraction-audit,gold,transformation-log,visual-audit}-2011-computing.{csv,json}`, `data/questions/2011/` (55 arquivos `.md` + 34 assets `.png` = 89 arquivos).

Nenhum arquivo de 2021 foi tocado. Nenhum PDF bruto foi modificado. `docs/phase-2a-report.md` (este arquivo) também é novo.

## T. Recomendação

**Como a fase foi `GENERALIZATION_PARTIAL`, não `SUCCESS`:** o próximo trabalho mínimo, antes de considerar processar outro ano legado, é:
1. Investigar a causa raiz de Q13 (região espúria) — provavelmente um bug real no detector de regiões de figura, distinto dos 4 já corrigidos.
2. Encontrar uma correção mais cirúrgica para Q22 (ex.: recuperação de cabeçalho escopada a `detect_tables()`, não ao mecanismo geral de marcador órfão) que não toque 2021.
3. Investigar a notação matemática ausente de Q23 (provavelmente recorrente em outras questões com fórmulas).
4. Completar a auditoria visual das 46 questões restantes antes de promover `gold-2011-computing.json` para `validated`.

Não recomendo expandir para outro ano (2005/2008/2014/2017/2019) até que os itens acima sejam resolvidos — fazer isso agora replicaria os mesmos 3 defeitos conhecidos sem entendê-los.

**Revisão e commit:** as mudanças desta fase estão prontas para revisão na branch `feat/enade-2011-unified-extraction`. Nenhum commit foi feito automaticamente, conforme instruído.

Confirmações finais:
- Nenhum commit, nenhum push, nenhum PR.
- `master`/`origin/master` intocados (`a5dfaab`, confirmado antes e depois desta fase).
- Nenhum outro ano processado.
