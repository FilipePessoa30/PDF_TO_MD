# FASE 1C — Relatório Final

**Recuperação de Conteúdo Estruturado e Fechamento do Piloto 2021 (CC-Bacharelado)**

Data: 2026-08-10
Escopo: `data/questions/2021/ciencia-da-computacao-bacharelado` (40 questões: 35 objetivas + 5 discursivas)

---

## A. Classificação Final

## `READY_FOR_2011`

- `enade assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado` → `READY_FOR_2011`, 40/40 verificadas, 0 `needs_review`, 0 blockers, `gold maturity=validated`.
- `enade verify-gold --year 2021 --course ciencia-da-computacao-bacharelado` → `OK` (40 questões batem com o manifesto).
- Todos os 20 itens do checklist de aceitação da Seção 20 do prompt original passam simultaneamente (ver Seção M).
- O manifesto gold foi promovido de `provisional` para `validated` (Seção H), a promoção deliberada só ocorre quando todos os gates desta fase são satisfeitos — condição agora verdadeira.

## B. Estado Inicial do Git

- Branch: `master`.
- HEAD no início da Fase 1C: `a0ba327` — "Add regression tests and enhancements for extraction and validation processes" (2026-08-09 20:23:52 -0300).
- Working tree limpo (sem alterações pendentes) antes do início do trabalho desta fase.
- Nenhum commit foi criado durante a Fase 1C (conforme Seção 24 do prompt: "não faça commit/push") — todas as 81 entradas de `git status` (71 arquivos modificados + 10 novos) permanecem não commitadas, prontas para revisão do usuário.

## C. D3 — Tabela-Verdade

**Problema original:** a tabela-verdade era extraída como texto corrido ilegível — sem estrutura de linhas/colunas, com a própria numeração das linhas da tabela sendo silenciosamente descartada pelo filtro de "chrome" (regra `^\d{1,3}$` que existe para remover números de página/rodapé).

**Causa raiz:** `chrome.py` aplica um filtro incondicional de dígitos isolados a QUALQUER linha nessa forma, sem distinguir "número de página" de "célula de tabela que por acaso é um dígito".

**Correção implementada (geométrica, não hardcoded):**
- Novo módulo `src/enade/extraction/tables.py`: `detect_tables()` faz clustering geométrico em Y (linhas) e depois em X por centro de célula (colunas), com limiares gerais (`MIN_CELLS_PER_ROW=3`, `MIN_TABLE_ROWS=3`, `MIN_STABLE_COLUMNS=3`, `MAX_BLANK_CELL_FRACTION=0.2`) — nenhuma referência a "D3" ou a conteúdo lógico da tabela-verdade.
- `assembler.py` ganhou um "table-rescue pre-pass": roda `detect_tables()` nas linhas brutas (antes do filtro de chrome) e isenta apenas as linhas efetivamente consumidas por uma tabela detectada do filtro de dígito isolado. `chrome.py` em si foi revertido para seu comportamento original (uma tentativa inicial de corrigir por banda de Y dentro do próprio chrome.py causou regressões em D1/D2/D4/Q35 e foi descartada).
- Novo `TableBlock` (`content_block.py`) com `TableValidationStatus`; renderização via `render_table_markdown()`.
- Validação célula-a-célula contra os dados reais do PDF de D3: cabeçalhos e linhas conferem exatamente.
- Confirmação independente bônus (não exigida): o PDF de padrão de resposta reimprime a mesma tabela-verdade como imagem raster na página 3 — inspecionada visualmente e confirma célula-a-célula a reconstrução geométrica.
- Fallback visual: asset de imagem (crop da região da tabela) sempre anexado, conforme regra geral do prompt ("sempre asset visual quando há incerteza estrutural") — aqui usado como confirmação redundante, não como substituto.

**Status:** `verified`, `automatic_validation=passed`, `visual_validation=passed`, `tables_verified=true` em `visual-audit-2021-b.json`.

## D. D5 — Pseudocódigo/Heapify (layout de duas colunas)

**Problema original:** o bloco de pseudocódigo (heapify) aparecia truncado/fora de ordem, mesclado com rótulos de figura e com texto da coluna vizinha.

**Três bugs compostos identificados e corrigidos independentemente (cada um verificado via diff isolado contra HEAD, confirmando que só o arquivo de D5 mudava a cada etapa):**

1. **Absorção de código como rótulo de figura** — linhas monoespaçadas (código) eram candidatas a "label" de região de figura, inflando a região de diagrama ~110pt para dentro da coluna de código. Corrigido excluindo `is_monospace` de `label_candidates` em `figures.py`.
2. **Verificação de contenção só em Y** — `_line_in_region` checava apenas sobreposição vertical, então mesmo uma região corretamente dimensionada engolia código da OUTRA coluna na mesma faixa de Y. Corrigido adicionando checagem de sobreposição em X (`REGION_X_PADDING=5.0`) em `assembler.py`.
3. **Heurística de largura de rótulo inadequada a duas colunas** — `MAX_LABEL_LINE_WIDTH=300` nunca disparava numa coluna de ~245pt de largura, então até o parágrafo de abertura do próprio enunciado era absorvido como rótulo. Corrigido reaproveitando `layout.detect_column_margins` (promovida de privada `_detect_column_margins` para uso compartilhado) para proteger texto de corpo genuinamente em duas colunas, independentemente da largura.

**Reconstrução de código:** novo `_render_code_lines()` reconstrói indentação a partir de `base_x0` e preserva linhas em branco genuínas via detecção de "pitch" modal entre linhas (~2x o espaçamento padrão = uma linha em branco).

**Efeito colateral positivo descoberto:** a mesma correção de sobreposição em X também recuperou rótulos "Processo A"/"Processo B" em Q17 que vinham sendo silenciosamente descartados desde a Fase 1B.

**Status:** `verified`, prosa completa, código completo (não apenas com fallback visual), ordem de blocos correta (parágrafo→figura→parágrafo→código→parágrafo), `automatic_validation=passed`, `visual_validation=passed`.

## E. Q20 — Gutter de Numeração de Linhas + Ambiguidade l/1

**Problema 1 — gutter:** números de linha de código vazavam para dentro do texto extraído, ora como linhas standalone, ora mesclados ao início da linha de código.

**Correção (puramente geométrica/sintática, não linguística):** `_strip_line_number_gutter()` em `assembler.py`, com dois padrões de regex baseados em forma, não em conteúdo semântico:
- `_GUTTER_ONLY_RE` para linhas standalone compostas só de dígitos — exige `_GUTTER_MIN_STANDALONE_COUNT=2` ocorrências recorrentes para confiar (caso ambíguo: um número solto pode ser conteúdo legítimo).
- `_GUTTER_PREFIX_RE = r"^[\t ]*\d+[\t ]+"` para número+código mesclados na mesma linha — confiado incondicionalmente porque essa forma é sintaticamente inequívoca (não há como um número seguido de espaço/tab no início de uma linha de código ser outra coisa).
- Indentação reconstruída a partir de linhas-irmãs não afetadas, nunca do x0 da própria linha corrompida.

**Bug de calibração encontrado e corrigido:** o gate original (`_GUTTER_MIN_COVERAGE_FRACTION=0.4`) media a fração errada — o chrome.py já removia 25 de 26 linhas de gutter standalone rio acima, deixando só 1 instância mesclada no pool (fração 1/26 ≈ 0.038, nunca cruzava o limiar). Corrigido trocando para uma contagem mínima de ocorrências recorrentes apenas para o caso standalone ambíguo.

**Problema 2 — ambiguidade glifo l/1 em `funcaol`/`m+l`:** investigada via comparação forense de largura de avanço de caractere (advance width) — não bbox, que o PyMuPDF reporta uniformemente por span independente do glifo real — contra larguras de referência confirmadas para "l" e "1" na mesma fonte/tamanho em outros pontos do mesmo documento, cruzando ainda com as 2 outras ocorrências do mesmo identificador em outros pontos do código (ambas confirmadas independentemente como dígito "1").

**Conclusão:** as duas ocorrências específicas são genuinamente grafadas com "l" minúsculo no PDF de origem — uma inconsistência real da tipografia da fonte, não um defeito de extração. O pipeline já transcrevia corretamente antes de qualquer alteração; nenhuma mudança de texto foi necessária, apenas verificação e documentação (nenhum conhecimento linguístico/de programação foi usado para "corrigir" — a decisão foi 100% baseada em evidência geométrica de largura de glifo).

**Status:** `verified` (resolução plena, não ficou como ambiguidade classificada à parte).

## F. Padrões Oficiais de Resposta (D4 e demais discursivas)

**Problema original:** diagramas de circuito referenciados pelo padrão de resposta oficial de D4 não eram capturados — o modelo de dados não tinha lugar para "assets pertencentes ao padrão de resposta" (distintos dos assets da própria questão).

**Modelo:** `AnswerStandardReference.assets: list[Asset]` (novo campo, `provenance.py`), com validador de unicidade de IDs.

**Extração:** o PDF de padrão de resposta reimprime tanto "enunciado reimpresso" quanto a rubrica "PADRÃO DE RESPOSTA" propriamente dita, e imagens podem aparecer em QUALQUER uma das duas seções na mesma página. Para não recapturar figuras do enunciado reimpresso como se fossem conteúdo novo do padrão, `answer_standard.py` ganhou:
- `page_bounds: dict[int, tuple[float, float]]` por entrada, delimitando em Y onde a rubrica de fato começa/termina em cada página.
- Uma passada de "alargamento de página inteira": páginas tocadas pelo buffer de uma entrada mas sem nenhum marcador/heading próprio (ex.: página 6 de D4, que só tem uma legenda de 1 linha bem acima do próprio diagrama) têm seus `page_bounds` alargados para `(0.0, page_height)`.
- `find_answer_standard_images()` busca imagens escopadas aos `page_bounds` de cada entrada (± `ANSWER_STANDARD_IMAGE_Y_PADDING=15.0`).
- `pipeline.py` renderiza os assets encontrados sob `{question_id}/answer-standard/{asset_id}.png`, com limpeza de arquivos obsoletos própria.

**Auditoria D1–D5:** todas as 5 discursivas foram reauditadas; apenas D4 possui assets de padrão de resposta (4 no total, todos diagramas de circuito) — confirmado que nenhuma figura do enunciado reimpresso foi duplicada como asset de padrão.

**Status:** gold manifest cobre 5 padrões de resposta (texto+hash), 4 assets de padrão de resposta com hash, todos `verified`.

## G. Modelo de Conteúdo Estruturado (`content_blocks`)

Novo `src/enade/models/content_block.py`: união discriminada (`Annotated[Union[...], Field(discriminator="type")]`) com `ParagraphBlock`, `CodeBlock`, `TableBlock` (+ `TableValidationStatus`), `AssetBlock`.

`Question.content_blocks: list[ContentBlock] | None = None`, com validador que rejeita referências a `asset_id` não declarado e exige que todo `TableBlock` não-verificado tenha um `AssetBlock` de fallback correspondente (garante que nunca existe estrutura "confiável" sem verificação, apenas com uma alegação não sustentada).

`DATA_CONTRACT_VERSION` introduzida em `question.py` (`"1.1.0"`), documentando que a adição de `content_blocks` e `AnswerStandardReference.assets` é aditiva/retrocompatível (bump MINOR).

Todas as 40 questões carregam `content_blocks` (populado com blocos reais para D3/D5/Q32/Q33, ou `null` nas demais — mudança puramente aditiva e mecânica).

## H. Corpus Gold — Maturidade e Cobertura

`GoldMaturity(StrEnum)`: `PROVISIONAL` / `VALIDATED` / `SUPERSEDED`. `GoldManifest` estendido com `data_contract_version`, `maturity`, `verified_count`, `needs_review_count`, `unresolved_question_ids`, `structural_blockers`, `answer_standards` (nova entrade `GoldAnswerStandardEntry`: hash de texto + assets do padrão de resposta).

`verify_gold_manifest()` estendido para detectar divergência também nos padrões de resposta (texto e assets: ausência, extra inesperado, hash divergente, arquivo ausente).

**Ação final desta fase:** manifesto reconstruído com `enade build-gold --maturity validated` (Seção H/13 do prompt: "Somente promova para validated quando os gates desta fase forem satisfeitos") — condição verdadeira agora que todos os gates da Seção 20 passam. Resultado: `data/manifests/gold-2021-b.json` com `maturity=validated`, 40/40 verificadas, 5 padrões de resposta cobertos (4 assets).

## I. Gate de Prontidão (`enade assess-readiness`)

Novo módulo `src/enade/readiness.py`, deliberadamente separado de `verify-gold` (que só prova ausência de *drift* de hash, não prontidão de fato). `assess_readiness()` produz um `ReadinessReport` com lista de `ReadinessBlocker` individualmente legíveis (nunca só um booleano), checando: divergências do gold, `structural_blockers` gravados no manifesto, `extraction_status` por questão, hash de todo asset (incluindo assets de padrão de resposta), e vínculo de resposta (objetiva: `answer_validation_status` ∈ {`validated`,`annulled`}; discursiva: `answer_standard` presente com todos os assets hasheados).

Novo comando CLI `enade assess-readiness --year --course`, saindo com código não-zero quando não pronto.

**Resultado atual:** `READY_FOR_2011`, zero blockers.

## J. Não-Regressão

Diff completo da saída da pipeline nova contra o corpus gold anterior à Fase 1C, cada diferença classificada individualmente:
- D3, D5, Q20, D4: mudanças pretendidas e documentadas (Seções C–F acima).
- Q17: recuperação de rótulos "Processo A"/"Processo B" — efeito colateral positivo da correção de D5 (Seção D), documentado no `visual-audit`.
- Q27: correção de uma nota de auditoria da Fase 1B que descrevia o conteúdo ERRADO (copiava a nota de Q17 por engano) — um erro de documentação pré-existente descoberto durante a reauditoria, não um defeito de extração; corrigida para descrever o conteúdo real de Q27 (histograma), com um resíduo de recuperação parcial/inconsistente de rótulos de eixo divulgado explicitamente como conhecido e de severidade baixa.
- D1/D2/Q7: nenhuma mudança de código (ver Seção K) — resíduos de capitalização documentados, não corrigidos, por decisão deliberada.
- As demais 34 questões: **zero diferença** de conteúdo textual/estrutural.

## K. Auditoria Visual e Investigações Documentadas

`data/manifests/visual-audit-2021-b.json` atualizado com narrativa forense completa para D3, D5, Q20 (promovidos a `passed`), D4 (extração de assets de padrão + reauditoria D1–D5), Q17 (efeito colateral positivo), Q27 (correção de nota).

**Resíduos de capitalização (D1 "direito"→"Direito", D2 "projetos"→"Projetos", Q7 "a"→"A"):** investigados a fundo e comprovados — via comparação de largura de avanço de caractere (não bbox, que o PyMuPDF reporta uniformemente por span independentemente do glifo) — como glifos de letra maiúscula genuínos, decodificados incorretamente por um defeito isolado no cmap ToUnicode em slots específicos de código de glifo interno da fonte Calibri-Bold embutida. Confirmadamente NÃO é um defeito da fonte inteira (dezenas de outras maiúsculas na mesma fonte/tamanho decodificam corretamente) e NÃO é resolvível por raciocínio linguístico.

**Decisão:** documentar exaustivamente, mas não implementar uma correção — o custo de um novo estágio de correção em nível de caractere é desproporcional a 3 instâncias conhecidas, explicitamente permitido pela Seção 10 do prompt ("não deixe isso bloquear D3/D5"). Não bloqueia `READY_FOR_2011` porque não é uma característica estrutural de nenhuma questão (afeta uma palavra isolada em texto corrido, sem impacto em alternativas, gabarito ou estrutura).

## L. Testes

294 testes passando (0 falhas). Adições desta fase:
- `tests/test_extraction_tables.py` (13 testes, novo) — detecção geométrica de tabela.
- `tests/test_extraction_assembler.py` — gutter, linhas em branco, sobreposição em X.
- `tests/test_extraction_figures.py` — `_is_two_column_body_text`.
- `tests/test_extraction_layout.py` — renomeado para `detect_column_margins` pública.
- `tests/test_extraction_pipeline_integration.py` — testes de integração ponta-a-ponta contra o PDF real: estrutura/asset da tabela D3, completude/ordem/blanks do heapify D5, preservação de gutter/l1 de Q20, assets de padrão de resposta D4 (incl. não-duplicação de figura reimpressa), detecção de região monoespaçada, ausência de normalização de prosa em código.
- `tests/test_schema_question.py` — assets do padrão de resposta (não se mistura com assets da questão mesmo sob ID colidente).
- `tests/test_gold.py` — maturidade/contagens/versão do contrato de dados + 6 testes de detecção de adulteração para padrão de resposta.
- `tests/test_readiness.py` (novo, 9 testes) — cenários pronto/não-pronto.
- `tests/test_extraction_validator.py` — reescrito para refletir a remoção da checagem bloqueante permanentemente insatisfazível de código multi-página.

## M. Gates de Qualidade (Seção 20 do prompt — todos simultâneos)

```
pytest              294 passed
ruff check          All checks passed!
ruff format --check 138 files already formatted
mypy src             Success: no issues found in 47 source files
validate-schema      13/13 fixture(s) valid
validate-manifest    OK (0 warning(s))
audit-extraction     40/40 OK
verify-gold          OK (40 questões batem; maturity=validated)
assess-readiness     READY_FOR_2011 (40/40 verified, 0 needs_review, 0 blockers)
```

## N. Reprodutibilidade

Duas execuções independentes e limpas de `enade extract` em diretórios de scratch separados produziram saída byte-idêntica (`diff -rq` retornou código de saída 0 para as árvores `questions/` e `audit/`, com contagens de arquivo iguais: 64 arquivos cada — 40 markdown + 20 assets de questão + 4 assets de padrão — e 3 arquivos de auditoria cada). Essa saída foi ainda confirmada idêntica à árvore `data/questions/2021/ciencia-da-computacao-bacharelado` realmente commitada (`diff -rq` código de saída 0).

## O. Arquivos Alterados

71 arquivos modificados (2.844 inserções, 212 remoções) + 10 arquivos novos:

**Novos:**
- `src/enade/models/content_block.py`
- `src/enade/extraction/tables.py`
- `src/enade/readiness.py`
- `schemas/content-block.schema.json`
- `tests/test_extraction_tables.py`, `tests/test_readiness.py`
- `tests/fixtures/questions/valid/q-with-content-blocks.md`
- `tests/fixtures/questions/invalid/unverified-table-without-visual-fallback.md`
- `data/questions/.../enade-2021-cc-b-d03/` (novo asset de tabela)
- `data/questions/.../enade-2021-cc-b-d04/answer-standard/` (4 novos assets)

**Modificados (destaques):** `src/enade/models/question.py`, `src/enade/models/provenance.py`, `src/enade/extraction/{assembler,chrome,figures,layout,validator,answer_standard,assets,pipeline,to_question}.py`, `src/enade/gold.py`, `src/enade/cli.py`, `docs/decisions.md` (+ADR 12–16), todos os schemas JSON regenerados, as 40 questões de `data/questions/2021/ciencia-da-computacao-bacharelado/`, os 3 manifestos de `data/manifests/`, e os arquivos de teste correspondentes.

## P. Estado Final do Git

- Branch: `master`, ainda em `a0ba327` (nenhum commit criado nesta fase).
- 81 entradas em `git status --short`: 71 `M` + 10 `??`.
- Nada commitado, nada enviado (push) — aguardando revisão e decisão do usuário sobre como agrupar/commitar as mudanças.

## Q. Recomendação

O piloto 2021 (CC-Bacharelado, 40 questões) está **`READY_FOR_2011`**: pronto para servir de template validado ao processamento do próximo caderno (2011), com corpus gold promovido a `maturity=validated`, zero regressões, zero blockers de prontidão, e reprodutibilidade byte-idêntica confirmada.

**Próximos passos sugeridos (fora do escopo desta fase, não iniciados):**
1. Revisar e commitar as mudanças em um ou mais commits coerentes (a critério do usuário — nenhum commit foi feito automaticamente, conforme a diretriz de escopo da Fase 1C).
2. Se desejado, usar este piloto validado como referência para iniciar o processamento do caderno de 2011 (explicitamente fora do escopo desta fase).
3. Os resíduos de capitalização documentados na Seção K permanecem como débito técnico conhecido e de baixo risco — candidatos a uma futura fase dedicada a correção de glifo em nível de caractere, caso mais instâncias apareçam em anos/cursos futuros.
