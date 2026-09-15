# Fase 3I — Grupos de Alternativas, Boundaries B/C e Distinção entre Marcadores e Labels de Diagrama

## A. Classificação

- **`ALTERNATIVE_GROUP_PARTIAL`** — a nova arquitetura estrutural de detecção de alternativas
  (`AlternativeMarkerCandidate`/`AlternativeGroup`, `alternative_groups.find_alternative_group`) está
  implementada, testada (unitária, metamórfica e contra o corpus real) e comprovadamente correta; o caso
  obrigatório da fase (Q71, fronteira B/C) foi integralmente corrigido; dois regressões reais introduzidas
  pelo próprio mecanismo durante o desenvolvimento (Q28/Q52 em 2008-b, Q39 em 2011) foram encontradas e
  corrigidas via refinamentos do mesmo algoritmo geral, nunca por exceção de questão. Não é
  `ALTERNATIVE_GROUP_STABILIZED` porque 12/77 questões continuam falhando por defeitos pertencentes a
  **outros** mecanismos (`region-merge-content-loss`, `table-reading-order-scramble`,
  `same-question-diagram-label-bleed`, `content-duplication`, ausência de padrão de resposta), e Q8/Q38/Q55
  seguem excluídas por um mecanismo ainda não construído (associação de asset a alternativas com região
  visual grande/mesclada) — diagnosticadas nesta fase (Seção P) mas deliberadamente não publicadas.
- **`RESIDUAL_LAYOUT_NOT_STABILIZED`** — 65/77 aprovadas na auditoria visual, 12/77 reprovadas (queda real
  de 13 para 12, auditada questão por questão).
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido. Três novas capacidades declarativas
  (`alternative_group`, `diagram_internal_label_detection`, `alternative_boundary_assignment`) registradas,
  classificadas G2, seguindo o mesmo padrão das Fases 3C-3H.
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase. Nunca `GENERALIZATION_SUCCESS`.
- `NOT_READY_FOR_2008_ENGINEERING_TEST` (readiness) — confirmado (63/77 verified, 14 needs_review, 12
  reprovações estruturais remanescentes).
- Nenhum commit, push, PR, merge ou tag foi criado por este agente. `master` não foi tocado.

## B. Estado Git

- Branch: `feat/enade-2008-cc-b-pilot` (confirmada no início e no fim da fase).
- `HEAD` = `93190fc` (commit do usuário, herdado do fim da Fase 3H) — inalterado, nenhum commit novo criado
  por este agente.
- `master` = `origin/master` = `a5dfaab` — intocado.
- Nenhum merge, rebase ou cherry-pick em andamento; working tree com 10 arquivos modificados + 3 novos, todos
  justificados nesta fase; nenhum arquivo perdido; nenhum arquivo de scratch/diagnóstico remanescente
  (confirmado via `git status --short | grep "^??"` ao final — apenas os 3 arquivos novos legítimos
  aparecem).

## C. Baseline

Confirmado no início da fase: `pytest` = 569 passed (fim da Fase 3H); 2011 (`verify-gold`/`assess-readiness`)
= `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55 verificados, 1 blocker não-estrutural (Q34, pré-existente); 2021 =
`READY_FOR_2011`, 40/40, 0 blockers; readiness de 2008-b = `NOT_READY_FOR_2008_ENGINEERING_TEST`, 64
passed/13 failed na auditoria visual. Hashes dos 288 arquivos protegidos (270 em `data/questions/2011|2021` +
18 manifestos relacionados) capturados como baseline SHA-256 no início desta fase, reaproveitados em toda
verificação de drift subsequente.

## D. Detector anterior (`_find_alternative_starts`)

O detector removido tratava cada letra A-E como um token textual isolado, buscando da direita para a
esquerda (do fim do span para o início) a última linha cujo texto começa com aquela letra maiúscula seguida
de tab/espaço — sem qualquer noção de margem, sem avaliar a sequência A-E como uma estrutura única, e sem
distinguir um marcador real de uma linha de prosa/diagrama que apenas compartilha a mesma forma textual. Isso
produzia o defeito diagnosticado já na Fase 3H para Q71: uma linha de prosa dentro do próprio texto
já-mesclado de uma alternativa ("C\tEm relação à alternativa 1...") era confundida com o início real da
alternativa C, fazendo a fronteira B/C ser computada no lugar errado e o conteúdo de B vazar para dentro de
C. A função foi **totalmente removida** (não mantida como fallback) e substituída por
`alternative_groups.find_alternative_group` em ambos os pontos de chamada de `assembler.py`.

## E. `AlternativeMarkerCandidate`

`src/enade/extraction/alternative_groups.py` define um `@dataclass(frozen=True)` com `letter`, `line_index`,
`x0`, `y0`, `page_number` — um candidato geométrico puro, sem qualquer referência a question_id, ano ou
página específica como condição de lógica (apenas como dado observável). Coletado via
`_ALTERNATIVE_LINE_RE = re.compile(r"^([A-E])(?:[\t ](.*))?$")`, uma cópia autocontida da mesma regex de
`assembler.py` (duplicada deliberadamente para evitar import circular, já que `assembler.py` importa deste
módulo).

## F. `AlternativeGroup`

Avalia a sequência A-E inteira como uma estrutura, não cinco decisões independentes. Campos: `label_scheme`
(esquema declarativo de rótulos — apenas `LATIN_UPPER_SCHEME = ("A","B","C","D","E")` implementado nesta
fase, já que é o único usado neste corpus), `status` (`"resolved" | "ambiguous" | "incomplete"`), `accepted`
(`{letter: line_index}`), `reference_margin`, `competing` (candidatos rejeitados por letra, para
transparência/diagnóstico), e a propriedade `is_usable` (`status == "resolved"`). Resolução por letra, na
ordem `reversed(LATIN_UPPER_SCHEME)` (E→A), com `upper_bound` decrescente (cada letra deve ocorrer antes da
próxima já aceita) — preservando a ordem de leitura **local à questão**, nunca a ordem global da página (uma
página pode conter os marcadores de duas questões diferentes).

## G. Labels internos vs. marcadores reais

A distinção não usa um catálogo positivo de "formas de label de diagrama" (o que seria uma lista fechada,
frágil a qualquer novo diagrama). Em vez disso, um candidato falso é rejeitado puramente por estrutura: (1)
se cai fora do subconjunto "on-margin" quando esse subconjunto é uma partição estrita e não-vazia dos
candidatos daquela letra, ou (2) se perde o desempate final de ordem de leitura para um marcador genuíno mais
tardio na mesma margem. Ver `diagram_internal_label_detection` no registro de capacidades (Seção Q) para a
formalização completa. Esta é a metade "qual candidato vence" — a metade complementar, já existente desde a
Fase 3G (`diagram_internal_label_margin_check`), decide se uma linha em forma de marcador deve ser **ocultada
de uma região visual** por não estar na margem do corpo — os dois mecanismos são independentes e não foram
fundidos nesta fase.

## H. Margem como refinamento, nunca substituição da ordem de leitura

Prosa comum do corpus frequentemente começa com uma letra maiúscula isolada compartilhando a mesma margem
esquerda dos marcadores reais (ex.: "A chance de uma criança..."), portanto margem sozinha nunca discrimina.
`_reference_margin` calcula a moda (`Counter.most_common`) do `x0` arredondado de **todos** os candidatos de
**todas** as letras, mas só a considera confiável (`_MIN_MARGIN_VOTES = 2`) quando pelo menos dois votos
genuínos a sustentam — caso contrário retorna `None` e a resolução cai inteiramente na ordem de leitura
(`pool[-1]`, "o último candidato antes da próxima letra vence"), exatamente como o mecanismo anterior já
fazia, porém agora aplicado ao subconjunto correto. Quando a margem é confiável e particiona estritamente os
candidatos de uma letra (alguns on-margin, alguns não), o subconjunto on-margin vira o pool de resolução —
mas a escolha dentro desse pool continua sendo por ordem de leitura, nunca "o único on-margin vence
automaticamente" nem "ambíguo se há mais de um on-margin".

## I. Ordem de leitura local à questão

`upper_bound` é recalculado por questão a cada chamada de `find_alternative_group(lines)`, onde `lines` já é
o span de uma única questão (`coarse_lines`/`text_only_lines` de `assemble_question`) — nunca a página
inteira. Isso é o que permite duas questões diferentes compartilharem uma página (ex.: Q28/Q29 na página 13)
sem que os candidatos de uma vazem para a resolução da outra.

## J. Boundaries (B/C e demais)

`alternative_boundary_assignment` (Seção Q) descreve o mecanismo consumidor: uma vez que
`find_alternative_group` retorna um grupo `resolved`/`is_usable`, `assembler.py` fatia `text_only_lines` em
`alt_bounds` diretamente a partir de `AlternativeGroup.accepted`, substituindo a lista de índices que
`_find_alternative_starts` retornava antes — o restante da lógica de corte/tabela/estatement é inalterado.

## K. Q71 — caso obrigatório

Confirmado byte a byte contra o texto real do PDF (`data/raw/geacc-enade/2008/b1_prova.pdf`, página 30):

- Alternativa B: `"Em relação à alternativa 1, na alternativa 2, a coesão do módulo A é menor, a dos módulos
  B e C é maior e o acoplamento do projeto é maior."` — completa, sem a contaminação de C.
- Alternativa C: `"Em relação à alternativa 1, na alternativa 2, a coesão do módulo A é maior, a dos módulos
  B e C é menor e o acoplamento do projeto é maior."` — presente integralmente, antes ausente (fundida
  dentro de B).

Testes dedicados: `tests/test_extraction_pipeline_2008.py::test_q71_alternative_b_c_boundary_is_now_correct`
(igualdade de string exata) e `test_q71_statement_is_now_complete` (renomeado — já não é "still open").
`data/manifests/blocker-ledger-2008.yaml`: `q71-alternative-b-c-cross-contamination` → `status: resolved`,
`visual_validation: passed`. `data/manifests/visual-audit-2008-computing.json`: Q71 → `passed`.
`enade extract` (re-executado) propagou automaticamente `visual_validation: passed` e
`extraction_status: verified` para o Markdown publicado (o pipeline lê o arquivo de auditoria visual em
tempo de extração — `pipeline.py` linha ~484 — não é um campo editado manualmente).

## L. Cluster C (Fase 3G) — preservado

`diagram_internal_label_margin_check` (mecanismo de exclusão de região, não de fronteira de alternativa) não
foi tocado nesta fase. Q24/Q29/Q63 permanecem exatamente como a Fase 3G os deixou (confirmado via
`blocker_ledger`: `q29-inline-sidebar-fragment` e `q63-region-merge-content-loss` seguem `resolved`, sem
alteração de conteúdo nesta fase).

## M. Fragment reconstruction (Fase 3H) — preservado

`fragment_reconstruction_gate` e `fragment_reconstruction.py` não foram alterados. Os casos que a Fase 3H
resolveu (Q12, Q63, parcialmente Q07/Q45/Q54) permanecem com o mesmo conteúdo — confirmado via
`blocker_ledger` (categorias `word_fragmentation`/`region-merge-content-loss` inalteradas exceto Q71, que
tinha as duas categorias e teve apenas a de fronteira de alternativa resolvida nesta fase).

## N. D10 — fora de escopo, confirmado intocado

`detect_column_margins`/`wrong_column_order` não foram tocados. `blocker_ledger`:
`d10-newspaper-collage-reading-order-scramble` permanece `open`, mesma descrição da Fase 3H. Nenhum código de
`layout.py`/coluna foi modificado nesta fase.

## O. Não-regressão (Seção 26 do PROMPT) — verificação individual

| Questão | Blocker(s) relevante(s) | Status | Regrediu? |
|---|---|---|---|
| Q07 | `region-merge-content-loss` | `open` (pré-existente, não relacionado a alternativas) | Não |
| Q12 | `region-merge-content-loss` (`q12-partial-content-loss`) | `resolved` | Não |
| Q13 | `content-duplication` (open) + `cross-question-image-contamination` (resolved) | inalterado | Não |
| Q25 | `word_fragmentation` (`q25-alternative-b-word-order-scramble`) | `resolved` | Não |
| Q29 | `table-reading-order-scramble` (`q29-inline-sidebar-fragment`) | `resolved` | Não |
| Q61 | `region-merge-content-loss` | `resolved` | Não |
| Q62 | `region-merge-content-loss` (`superseded`) + `cross-question-diagram-label-bleed` (`resolved`) | inalterado | Não |
| Q63 | `region-merge-content-loss` | `resolved` | Não |
| Q68 | `table-reading-order-scramble` (`q68-sql-code-block-reordering`) | `resolved` | Não |
| Q71 | `alternative-boundary-misparse` + `region-merge-content-loss` | **ambos `resolved` nesta fase** | Corrigido (não regressão) |
| Q75 | `region-merge-content-loss` (resolved) + `same-question-diagram-label-bleed` (open, pré-existente, não relacionado) | inalterado | Não |
| D10 | ver Seção N | `open` (categoria não relacionada) | Não |
| D40 | `table-reading-order-scramble` (open, pré-existente) | inalterado | Não |
| D60 | `table-reading-order-scramble` (open, pré-existente) + `cross-question-diagram-label-bleed` (resolved) | inalterado | Não |
| Q1, Q49 | nenhum blocker registrado (nunca problemáticas) | — | Não |
| Q50 | `region-merge-content-loss` | `resolved` | Não |
| 2011 Q34 | não-estrutural, pré-existente (`needs_review`) | inalterado | Não |

Confirmado adicionalmente via `enade audit-extraction` (77/77, 55/55, 40/40 OK), suíte de testes completa
(589 passed) e diff byte a byte de duas execuções independentes (Seção Y).

## P. Q8/Q38/Q55 — diagnóstico sem publicação

Investigação isolada por questão (não por página inteira — página 15 e 23 são exclusivas de Q38/Q55
respectivamente; página 5 é exclusiva de Q8, sem outra questão compartilhando essas páginas), via
monkeypatch de `assemble_question` filtrando por `span.number`, com uma execução real e completa de
`extract_exam` para 2008-b (script de diagnóstico descartado ao final, nenhuma alteração de código):

| Questão | Página | Layout dos marcadores | `find_alternative_group` | Regiões visuais na página | Causa real da exclusão |
|---|---|---|---|---|---|
| Q8 | 5 | Horizontal, 2 linhas (A/B/C em y=346; D/E em y=632), 1 candidato por letra | `resolved`, sem competição | 2 regiões: 492×343pt e 522×221pt, ambas `is_small_formula=False` | `ValidationError`: "alternative A: text is empty and no asset is set" |
| Q38 | 15 | Vertical, todas em x0=336.24, y crescente | `resolved`; `competing` mostra 1 candidato descartado por letra (linhas 1-7, não relacionadas), o marcador real (linhas 12-16) aceito corretamente via ordem de leitura | 1 região: 333×341pt, `is_small_formula=False` | Mesmo erro: alternativa A sem texto nem asset |
| Q55 | 23 | Vertical, todas em x0=332.16, y crescente, 1 candidato por letra | `resolved`, sem competição | 2 regiões: 268×245pt e 317×84pt, ambas `is_small_formula=False` | Mesmo erro: alternativa A sem texto nem asset |

**Classificação, por questão** (mesma para as três, evidência idêntica):

- `recoverable_by_general_rule`: **NÃO** — corrigir isso exigiria construir um mecanismo inteiramente novo
  (associar uma sub-região de uma imagem grande/mesclada a cada alternativa individual quando nenhuma região
  "pequena" existe), explicitamente fora do escopo desta fase (Seção 20 do PROMPT: "não altere o corpus
  publicado... não remova os blockers... não promova gold").
- `still_ambiguous`: **NÃO** — em nenhuma das 15 letras (3 questões × 5 letras) houve empate estrutural; o
  novo mecanismo resolve todas de forma determinística, incluindo o caso de Q38 com candidatos concorrentes.
- `missing_asset`: **SIM** — esta é a causa raiz real e única. `_attach_alternative_formula_regions`/
  `_is_alternative_formula_candidate` só reconhecem regiões classificadas como "small formula" (o mesmo
  padrão que resolveu 2011 Q14/Q23); as regiões próximas a Q8/Q38/Q55 são blobs grandes e mesclados,
  arquiteturalmente diferentes.
- `missing_label`: **NÃO** — todas as 5 letras A-E estão presentes e na ordem correta em cada questão.
- `wrong_boundary`: **NÃO** — a fronteira computada por `find_alternative_group`/`alternative_boundary_assignment`
  é exatamente correta nas três questões; o problema surge **depois** da fronteira, na tentativa de anexar
  conteúdo (texto ou asset) a cada alternativa já corretamente delimitada.

**Conclusão desta seção**: o objetivo #6 da fase ("manter compatibilidade futura com Q8/Q38/Q55") está
satisfeito — a nova arquitetura de `AlternativeGroup` não é o que bloqueia essas três questões, e uma futura
fase que implemente associação de asset para regiões grandes/mescladas não precisará revisitar
`alternative_groups.py`. Nenhuma alteração foi feita ao corpus publicado, ao `blocker_ledger` ou ao gold para
essas três questões — permanecem excluídas exatamente como antes, com a mesma mensagem de exclusão
(`structural_warnings`, nunca silenciosa).

## Q. Capability registry

Três novas entradas adicionadas a `data/manifests/extraction-capabilities.json` (14 capacidades totais,
antes 11), todas G2, `runtime_ai_dependency: "none"`, `introduced_phase: "3I"`, validadas por
`tests/test_generalization_architecture.py` (9/9, incluindo
`test_capability_registry_entries_have_every_required_field`,
`test_capability_registry_never_cites_a_question_id_as_a_trigger`):

1. **`alternative_group`** — o mecanismo `find_alternative_group` em si (coleta de candidatos, margem de
   referência com voto mínimo, resolução por ordem de leitura). `parameters: {}` — não é gated por
   `ExamStructureProfile`; é uma substituição incondicional do algoritmo anterior, validada como estritamente
   superior após dois ciclos completos de regressão real (Q28/Q52, depois 2011 Q39).
2. **`diagram_internal_label_detection`** — a metade de "qual candidato vence" da distinção entre marcador
   real e linha que apenas compartilha a forma textual, sem catálogo positivo de formas de diagrama.
3. **`alternative_boundary_assignment`** — o consumo de `AlternativeGroup.accepted` por `assembler.py` para
   fatiar `text_only_lines` em cada alternativa.

## R. Auditoria visual

`data/manifests/visual-audit-2008-computing.json`: **65 passed / 12 failed / 0 not_performed** (antes: 64/13).
Apenas Q71 promovida, com nota extensa e específica documentando a causa e a correção. Nenhuma promoção em
massa.

## S. Generalização

18 testes novos em `tests/test_alternative_groups.py` (unitários + metamórficos: invariância por translação,
invariância de escala do alinhamento de margem, variação de largura de coluna, variação de fonte/espaçamento,
candidato exatamente no limite de tolerância, ordem do content stream). Nenhum teste depende de question
ID/ano/página/coordenada real do PDF — todas as fixtures são sintéticas. `find_alternative_group` classificado
G2 (nunca G3/G4). O status `"ambiguous"` permanece arquiteturalmente suportado (`AlternativeGroupStatus`) mas
não é produzido por nenhuma regra implementada nesta fase — decisão deliberada, não uma lacuna: nenhum caso
real do corpus (2008-b, 2011, 2021) produziu um empate estrutural genuíno após os dois ciclos de correção, e
`docs/generalization-contract.md` (seção 1.1, "não introduza uma capacidade sem exemplo positivo e negativo
real") orienta explicitamente contra inventar um gatilho sintético só para exercitar o código.

## T. Runtime sem IA

`tests/test_generalization_architecture.py::test_core_extraction_modules_import_no_network_or_llm_library` e
`test_declared_runtime_dependencies_contain_no_llm_or_network_client`: PASS. `alternative_groups.py` usa
apenas geometria (`x0`/`y0`/`line_index`) e `collections.Counter` da stdlib — nenhuma dependência nova.

## U. Proteção de 2011/2021

Confirmado **zero drift** em múltiplas iterações distintas:

1. Após a implementação inicial do particionamento por margem — encontrada uma regressão real em 2008-b
   (Q28/Q52, mesmo corpus sendo trabalhado) — corrigida via resolução por ordem de leitura dentro do
   subconjunto on-margin, nunca bloqueio por ambiguidade de margem.
2. Após essa correção — encontrada uma regressão real em **2011** (Q39, corpus protegido) — corrigida via
   `_MIN_MARGIN_VOTES = 2`.
3. Após `_MIN_MARGIN_VOTES` — zero drift reconfirmado em 2011 (regeneração completa,
   `git status --short data/questions/2011` vazio) e 2021 (3 cursos, mesma verificação) e apenas Q71 alterada
   em 2008-b.
4. Verificação final, pós-todas as mudanças (incluindo a reextração para propagar `visual_validation`) —
   zero drift reconfirmado via `git status --short data/questions/2011 data/questions/2021` (vazio) **e**
   `sha256sum -c` contra os 288 arquivos protegidos (exit 0).

## V. Testes e quality gates

- 569 testes existentes (fim da Fase 3H) → **589 testes** ao final desta fase (+20: 18 em
  `tests/test_alternative_groups.py` + 1 em `tests/test_extraction_pipeline_2011.py` (novo arquivo) + 1 em
  `tests/test_extraction_pipeline_2008.py`).
- `pytest -q`: 589 passed.
- `ruff check .`: All checks passed.
- `ruff format --check .`: limpo (após uma correção de formatação aplicada em
  `alternative_groups.py`, puramente cosmética — quebra de linha de uma expressão).
- `mypy src/enade`: Success, 55 source files.
- `enade validate-schema`: 13/13.
- `enade validate-manifest`: 0 warnings.
- `enade audit-extraction` — 2008: 77/77 OK; 2011: 55/55 OK; 2021 (ciencia-da-computacao-bacharelado): 40/40
  OK.
- `enade verify-gold`/`assess-readiness`:
  - 2008 (`all-computing`): `verify-gold` OK (77/77); `assess-readiness` →
    `NOT_READY_FOR_2008_ENGINEERING_TEST`, 63/77 verified, 14 needs_review, 43 blocker(s) (estruturais
    recorrentes + não-estruturais, nenhum novo).
  - 2011 (`all-computing`): `verify-gold` OK (55/55); `assess-readiness` → `READY_FOR_LEGACY_LAYOUT_TEST`,
    54/55 verified, 1 blocker não-estrutural (Q34, pré-existente, inalterado).
  - 2021 (`ciencia-da-computacao-bacharelado`): `verify-gold` OK (40/40); `assess-readiness` →
    `READY_FOR_2011`, 40/40 verified, 0 blockers.

## W. Reprodutibilidade

Duas execuções completas e independentes de `enade extract --year 2008 --course all-computing` (run A, run
B), com diretórios de saída isolados: `diff -rq run_a run_b` → idêntico byte a byte (exit 0). `diff -rq
run_a/all-computing data/questions/2008/all-computing` → idêntico byte a byte ao corpus publicado (exit 0).
Diretórios temporários removidos ao final.

## X. Bugs encontrados e corrigidos durante a fase

1. **Q28/Q52 (2008-b)**: a primeira versão do particionamento por margem declarava `ambiguous=True` sempre
   que sobravam ≥2 candidatos on-margin após excluir os off-margin — mas o layout horizontal/grade de Q28/Q52
   tem a letra A com um candidato de prosa real e o marcador real compartilhando a mesma margem. Corrigido
   removendo o conceito de `ambiguous` por margem inteiramente: o subconjunto on-margin é apenas um *pool* de
   resolução, sempre resolvido por ordem de leitura (`pool[-1]`).
2. **2011 Q39 (corpus protegido)**: layout totalmente horizontal em que cada letra tem seu próprio `x0` único
   — nenhum compartilha margem de verdade. Um candidato falso de A (texto de item julgado) coincidiu, por
   pura ordem de iteração/inserção, em ser tratado como "moda" com um único voto não-repetido. Corrigido com
   `_MIN_MARGIN_VOTES = 2`, exigindo pelo menos dois votos genuínos antes de confiar em qualquer margem de
   referência.

Ambos encontrados por scripts de diagnóstico com monkeypatch da função real contra uma execução completa do
pipeline (não apenas os testes unitários sintéticos), ambos confirmados corrigidos por regeneração completa
do corpus afetado + comparação byte a byte, e ambos documentados nos testes correspondentes
(`test_two_on_margin_candidates_plus_one_off_margin_resolves_via_reading_order`,
`test_reference_margin_requires_at_least_two_votes`,
`test_horizontal_grid_layout_with_no_shared_margin_defers_to_reading_order`,
`tests/test_extraction_pipeline_2011.py`).

## Y. Arquivos e Git final

Novos: `src/enade/extraction/alternative_groups.py`, `tests/test_alternative_groups.py`,
`tests/test_extraction_pipeline_2011.py`, `docs/phase-3i-report.md`.
Modificados: `src/enade/extraction/assembler.py` (remoção de `_find_alternative_starts`, adoção de
`find_alternative_group` nos dois pontos de chamada), `tests/test_extraction_assembler.py`,
`tests/test_extraction_pipeline_2008.py`, `data/manifests/blocker-ledger-2008.yaml`,
`data/manifests/visual-audit-2008-computing.json`, `data/manifests/extraction-capabilities.json`,
`data/manifests/gold-2008-computing.json`, `data/manifests/extraction-audit-2008-computing.{csv,json}`,
`data/questions/2008/all-computing/enade-2008-computing-q71.md`. Nenhum arquivo de `data/questions/2011` ou
`data/questions/2021` foi tocado (confirmado por `git status --short` vazio e SHA-256 baseline). Nenhum
arquivo de scratch/diagnóstico remanescente. **Nenhum commit, push, PR, merge ou tag foi criado.** `master`
permanece intocado. Branch: `feat/enade-2008-cc-b-pilot`, HEAD ainda em `93190fc`.

## Recomendação

A arquitetura de `AlternativeGroup` está estabelecida e comprovadamente correta: resolveu integralmente o
caso obrigatório (Q71), sobreviveu a dois ciclos de regressão real encontrados pelo próprio processo de
validação exaustiva (nunca escondidos, sempre corrigidos na raiz do algoritmo geral) e não regrediu nenhuma
das 17 questões/clusters da lista de não-regressão. Os 12 casos remanescentes na auditoria visual pertencem,
sem exceção, a mecanismos **distintos** já diagnosticados em fases anteriores (fusão de região, ordem de
leitura de tabela, duplicação de conteúdo, padrão de resposta ausente da fonte) — nenhum deles é mais uma
fronteira de alternativa mal calculada. Recomenda-se:

1. **Não tentar recuperar Q8/Q38/Q55** nesta ou na próxima fase isoladamente — a causa raiz (associação de
   asset a alternativas quando a única região próxima é um blob grande/mesclado) é um mecanismo novo e de
   risco moderado (afeta `_attach_alternative_formula_regions`, potencialmente usado por outras questões já
   publicadas com sucesso via o caminho de "small formula"). Deve ser uma fase própria, com seu próprio
   orçamento de regressão contra 2011 (Q14/Q23, o precedente que já funciona) e 2008-b inteiro.
2. Priorizar, entre os 12 restantes, os que já têm causa raiz mais simples e isolada: `q13-duplicated-alternative-text`
   (cosmético, sem perda de conteúdo) e `d60-valor-annotation-misattachment` parecem candidatos de menor
   risco para uma próxima fase, por não tocarem geometria de coluna nem fronteira de alternativa.
3. Manter `detect_column_margins`/D10 fora de escopo até uma fase dedicada e isolada, dado o alto raio de
   impacto (afeta toda página de todo caderno) já registrado nas recomendações da Fase 3H.
4. Não processar o bundle `e`. Não processar outro ano.
5. Não declarar generalização validada — G4 continua exigindo prova inédita com código congelado.
