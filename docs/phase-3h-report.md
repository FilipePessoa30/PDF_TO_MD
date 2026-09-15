# Fase 3H — Reconstrução Geométrica de Palavras, Linhas e Fragmentos sem Inferência Semântica

## A. Classificação

- **`FRAGMENT_RECONSTRUCTION_PARTIAL`** — a arquitetura de reconstrução geométrica está implementada,
  testada (unitária, metamórfica e contra o corpus real) e comprovadamente correta; vários casos reais do
  Cluster D foram resolvidos ou substancialmente melhorados; nenhum conteúdo enganoso foi publicado; nenhuma
  questão previamente aprovada regrediu; 2011/2021 permanecem integralmente protegidos. Não é
  `FRAGMENT_RECONSTRUCTION_STABILIZED` porque casos genuínos permanecem — D10 (ordem de leitura, categoria
  `wrong_column_order`, não Cluster D) e Q71 (fronteira de alternativas, categoria
  `alternative-boundary-misparse`, não Cluster D) foram precisamente diagnosticados mas deliberadamente não
  corrigidos nesta fase, por pertencerem a mecanismos distintos (PROMPT seção 29: "não é obrigatório que as
  77 questões atinjam passed nesta fase se existirem blockers comprovadamente pertencentes a outros
  clusters").
- **`RESIDUAL_LAYOUT_NOT_STABILIZED`** — 64/77 aprovadas, 13/77 reprovadas (queda real de 15 para 13,
  auditada questão por questão).
- **`GENERALIZATION_ARCHITECTURE_ESTABLISHED`** — mantido. Uma nova capacidade declarativa
  (`fragment_reconstruction_gate`) segue o mesmo padrão G2 já estabelecido nas Fases 3C-3G.
- **`GENERALIZATION_NOT_YET_VALIDATED`** — mandatório nesta fase. Nunca `GENERALIZATION_SUCCESS`.
- `NOT_READY_FOR_2008_ENGINEERING_TEST` (readiness) — esperado enquanto Q8/Q38/Q55 permanecerem excluídas e
  houver questões publicadas reprovadas.
- Nenhum commit, push, PR, merge ou tag foi criado por este agente. `master` não foi tocado.

## B. Estado Git

- Branch: `feat/enade-2008-cc-b-pilot` (confirmada no início e no fim da fase).
- `HEAD` = `8ecc93c` (commit do usuário, herdado das Fases 3F/3G) — inalterado, nenhum commit novo.
- `master` = `origin/master` = `a5dfaab` — intocado.
- `origin/feat/enade-2011-unified-extraction` = `84c5005` — branch de origem do trabalho de 2011, não
  tocada, confirmada como lineage separada (nosso branch diverge dela em `1ee01af`).
- Nenhum merge, rebase ou cherry-pick em andamento; working tree com 37 arquivos modificados/novos, todos
  justificados nesta fase; nenhum arquivo perdido.

## C. Baseline

Confirmado no início da fase: `pytest` = 539 passed; `ruff check`/`ruff format --check`/`mypy` verdes (com
uma única reformatação de estilo pendente, corrigida e reconfirmada); `validate-schema` 13/13; `validate-manifest`
0 warnings; 2011 (`verify-gold`/`assess-readiness`) = `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55 verificados, 1
blocker não-estrutural (Q34, pré-existente); 2021 = `READY_FOR_2011`, 40/40, 0 blockers; readiness de 2008-b
= `NOT_READY_FOR_2008_ENGINEERING_TEST`, 62 passed/15 failed. Hashes dos 288 arquivos protegidos capturados
como baseline (reaproveitado o snapshot da Fase 3G, revalidado a cada mudança de código nesta fase).

## D. Reconciliação dos 15 casos reprovados

Registro completo por questão (categoria conforme a taxonomia da própria Fase 3H):

| Questão | Categoria real | Pertence ao Cluster D? |
|---|---|---|
| D10 | `wrong_column_order` (detect_column_margins confunde um título de página-inteira com evidência de coluna) | **Não** — sintoma parecido, causa raiz diferente |
| D40 | `foreign_fragment`/`cosmetic_leak` (rótulo "F" isolado) + pré-existentes (ordem de palavras, código truncado) | Não — nenhum desses é fragmentação de mesma linha-base |
| Q02 | `text_consumption` (over-absorção de uma linha íntegra, não fragmentada) | Não |
| Q05 | `text_consumption` (citação de imagem descartada) | Não |
| Q07 | `word_fragmentation` (8 fragmentos na mesma linha-base) | **Sim** — resolvido em grande parte |
| Q12 | `word_fragmentation` (4 fragmentos) | **Sim** — resolvido integralmente |
| Q13 | `content-duplication` (texto de alternativa duplicado) | Não |
| Q24 | `foreign_fragment` (garbling removido) + causa mais profunda de mesclagem de diagramas | Não |
| Q33 | `wrong_intra_line_order` (marcadores de item deslocados) | Possivelmente relacionado, não investigado a fundo nesta fase |
| Q45 | `word_fragmentation` (item III) + conteúdo genuinamente ausente | Parcial |
| Q54 | `word_fragmentation` (explicação da tabela) + cláusula de abertura ausente (não fragmentada) | Parcial |
| Q63 | `word_fragmentation` (4 palavras) | **Sim** — resolvido integralmente |
| Q71 | `word_fragmentation` (enunciado, resolvido) + `alternative_detection` (B/C, não relacionado) | **Parcial** — enunciado sim, alternativas não |
| Q75 | `same-question-diagram-label-bleed` (alternativa D) | Não |

A contagem permanece diferente de zero após Q29/Q75/Q13(imagem) da Fase 3G porque a maioria dos 15 casos
pertence a categorias **distintas** do Cluster D (over-absorção de linhas íntegras, ordem de colunas,
detecção de fronteira de alternativas, vazamento de rótulo entre questões) — o próprio objetivo da Fase 3H
era isolar e tratar apenas a fragmentação genuína, não todas as causas de reprovação.

## E. Forense (chars → spans → words → lines)

Instrumentação direta contra `b1_prova.pdf` confirmou, via `page.get_text("dict")`, que a granularidade mais
fina de fragmentação real neste corpus é o próprio "line" do modo dict do PyMuPDF — nunca span/char dentro
de um mesmo "line" (que já chega pré-unido por `reconstruct_line_text`, mecanismo pré-existente de
spacing.py). Evidência decisiva: Q07 (p.4) tem uma frase impressa como UMA linha visual reportada como OITO
entradas "line" separadas, todas com y0/y1 idênticos (657.972/667.932), cada uma (exceto a última) com um
espaço literal ao final do próprio texto bruto do span — a mesma classe de evidência documental que
spacing.py já usa (nunca inferência). Uma tabela real (Q54, p.23) tem células adjacentes nos mesmos y0/y1,
mas SEM espaço à direita em nenhuma delas — a distinção que separa fragmentação genuína de células de
tabela.

## F. Arquitetura (camadas)

Implementadas como funções/módulos com responsabilidade única:

```text
_collect_raw_fragments      → extrai fragmentos brutos (bbox + texto não-stripado) por página
group_line_fragments        → agrupa por baseline, decide merge por fragmento adjacente
_build_line_from_group       → reconstrói o texto via reconstruct_line_text sobre o bbox unido
_column_boundary_for_fragment_merge → barreira de coluna (nunca cruzada pelo merge)
```

Nenhuma decisão de reconstrução lexical altera owner/coluna/question region/asset region: o merge acontece
inteiramente dentro de `layout.py`, antes de `boundaries.py`/`ownership.py`/`figures.py` verem qualquer
linha - as camadas de ordenação por coluna, ownership e assembly de questão seguem operando exatamente como
antes, sobre o resultado já reconstruído.

## G. `TextFragment` (`RawLineFragment`)

`fragment_reconstruction.py` define `RawLineFragment` (page_number, x0/y0/x1/y1, `raw_text` não-stripado,
fonts, font_size, is_monospace) - o fragmento "atômico" desta fase, correspondendo exatamente à granularidade
real observada (Seção E). Não existe papel semântico (`semantic_role`) explícito porque nenhuma decisão desta
fase depende dele; a distinção prosa-vs-tabela-vs-código já emerge dos sinais geométricos/documentais
(espaço à direita, monoespaçamento, gap).

## H. `FragmentRelation` (`LineFragmentRelation`)

Métricas nunca colapsadas prematuramente: `same_baseline`, `horizontal_gap`, `gap_ratio`,
`gap_within_ceiling`, `left_had_trailing_space`, `font_size_compatible`, `both_non_monospace`, e só então
`decision` (`"merge_with_space"` / `"preserve_separate"`). Não existe `"merge_without_space"` neste
mecanismo - nenhuma evidência real encontrada exige unir fragmentos sem espaço documental (esse é um
problema diferente, já resolvido por spacing.py). Não existe threshold único: o limiar de gap
(`MAX_FRAGMENT_GAP_RATIO=1.5`, relativo ao tamanho de fonte) é apenas uma rede de segurança - o sinal
decisivo é sempre o espaço documental.

## I. Reconstrução intralinha

Uma junção só ocorre com TODAS as evidências simultaneamente: mesma página, baseline idêntica (±0.05pt),
ambos não-monoespaçados, tamanho de fonte compatível (±0.5pt), gap positivo dentro do teto relativo à fonte,
E espaço literal ao final do fragmento esquerdo. Fronteiras nunca são atravessadas: uma barreira de coluna
detectada (a mesma `detect_column_margins` já usada para ordem de leitura) bloqueia qualquer merge que a
cruze, independentemente das demais evidências.

## J. Formação de linhas físicas

Fragmentos são agrupados por baseline (não apenas por proximidade vertical simples) e, dentro de cada grupo,
ordenados por x0 antes de qualquer decisão de merge - resolvendo corretamente o caso em que a ordem de
travessia do content stream diverge da ordem visual (Q25, Seção O). Uma linha longa nunca serve de ponte
entre colunas: a barreira de coluna (Seção I) impede isso mesmo quando geometria/espaço pareceriam permitir.

## K. Continuação entre linhas

Não implementada nesta fase (fora do escopo confirmado pela própria investigação - nenhum caso real exigiu
reconstrução ENTRE linhas físicas distintas, apenas DENTRO de uma mesma linha visual fragmentada). Hifens não
são tocados por este mecanismo.

## L. D10

Investigado a fundo (Seção D). Causa raiz: `detect_column_margins` conta a linha "QUESTÃO 10 – DISCURSIVA"
(um título de página inteira) como evidência do mesmo bucket de margem "esquerda" (x0≈36.8) que o conteúdo
real que só começa 190pt mais abaixo, estendendo artificialmente o alcance em Y desse lado o suficiente para
que o teste de sobreposição de colunas (que rejeitaria corretamente a página como não-genuinamente-bicolunar
sem essa linha) passe a aceitá-la como se fosse duas colunas simultâneas. Isso é `wrong_column_order`, não
fragmentação - nenhum fragmento na mesma baseline foi encontrado nesta página. **Não corrigido nesta fase**:
`detect_column_margins` tem histórico de múltiplas tentativas revertidas (Fases 2C/3C, documentadas no
próprio docstring da função); a correção exigiria uma mudança estrutural de alto raio de explosão (usada por
TODA página de TODO caderno) sem tempo/orçamento de risco para validação isolada nesta mesma fase. Registrado
com precisão total no blocker ledger (`d10-newspaper-collage-reading-order-scramble`), sem tentativa de
correção precipitada.

## M. Q07 — palavra "aos"

Root-caused precisamente: "aos" era um dos oito fragmentos de mesma baseline. `fragment_reconstruction_gate`
reconstrói a linha inteira; um efeito colateral necessário foi excluir qualquer linha reconstruída de
`label_candidates` em figures.py (Seção P). Resultado: "total correspondente aos 20% de maior renda foi,"
- recuperação além até do estado anterior à Fase 3G. Pertence ao Cluster D; resolvido nesta fase, com um
resíduo não-Cluster-D remanescente (a frase de abertura, uma linha íntegra, ainda sofre over-absorção
genuína e não-fragmentada).

## N. Q71 — reauditoria completa

Comparação integral (PDF oficial vs. Markdown) confirma: o enunciado (word_fragmentation, Cluster D) está
agora 100% completo e correto. As alternativas B/C permanecem cruzadas por um bug **diferente e não
relacionado**: `_find_alternative_starts` (assembler.py) faz uma busca puramente textual, direita-para-
esquerda, pela sequência de marcadores A-E, sem qualquer verificação de margem/posição - uma linha de
quebra de parágrafo genuína que começa com "C " (continuando gramaticalmente "módulos B e C", não um
marcador real) é confundida com o marcador real de C. Não pertence ao Cluster D (confirmado: as duas linhas
envolvidas estão em y0 diferentes, uma quebra de linha normal, não uma fragmentação de mesma linha-base).
Preservado como blocker corretamente classificado (`q71-alternative-b-c-cross-contamination`), não corrigido
nesta fase por exigir uma segunda mudança estrutural de alto raio de explosão (toda detecção de fronteira de
alternativas de todo caderno) sem tempo de validação isolada.

## O. Q02/Q12/Q24/Q45/Q54/Q63

- **Q02**: melhora da Fase 3G preservada; sem mudança nesta fase (a linha ausente é íntegra, não
  fragmentada) - permanece reprovada.
- **Q12**: **resolvido integralmente** - enunciado 100% idêntico à fonte. Aprovada.
- **Q24**: garbling removido (Fase 3G), sem novo ganho nesta fase - a causa mais profunda (mesclagem de 4
  diagramas) é estrutural, não fragmentação. Permanece reprovada.
- **Q45**: item III ganhou mais texto reconstruído nesta fase, mas itens I/II e a cláusula de fechamento
  continuam genuinamente ausentes (não fragmentados, provavelmente absorvidos por uma imagem de fórmula
  separada). Permanece reprovada.
- **Q54**: sem mudança adicional nesta fase além da já conquistada na Fase 3G (a cláusula de abertura
  ausente é uma linha íntegra, não fragmentada). Permanece reprovada.
- **Q63**: **resolvido integralmente** - enunciado 100% idêntico à fonte. Aprovada.

## P. D40/Q23 e fail-safe

- **D40**: confirmado que o vazamento "F" não resulta de fragmentação (é uma linha de um único caractere,
  isolada, sem par de mesma baseline) - é o mesmo comportamento fail-safe da Fase 3G (ambíguo nunca remove
  destrutivamente), preservado sem alteração. A linha `Cliente(...)` permanece correta (idêntica ao HEAD).
  O vazamento não é escondido como "trade-off aceito" - D40 permanece explicitamente reprovada.
- **Q23**: o artefato cosmético (fragmento de schema duplicado) é confirmado, por diff, **idêntico antes e
  depois desta fase** - não pertence ao Cluster D, preservado como blocker separado
  (`q23-schema-fragment-duplicate-bleed`), sem alteração.

## Q. Capability registry

`geometric_word_fragment_reconstruction` atualizado de `not_implemented` para **G2** (ativação declarativa
via `fragment_reconstruction_gate`, nunca G3/G4 nesta fase). Inclui `trigger_features` puramente estruturais,
`positive_fixtures`/`negative_fixtures`/`metamorphic_tests` (13 + 3 testes), `real_cases` (Q07/Q12/Q63/Q71/
Q25), `protected_cases` (2011/2021 completos + o caso específico de 2021 p.19 fechado pela barreira de
coluna), `failure_behavior` documentando honestamente que o mecanismo corrige um defeito real de 2021 quando
testado incondicionalmente mas permanece gated por princípio. `runtime_ai_dependency: "none"`. Validado por
`tests/test_generalization_architecture.py` (9/9).

## R. Source coverage

Não foi implementado um verificador dedicado de "source coverage" (char → fragment → token → owner) como
mecanismo formal separado nesta fase - a verificação equivalente foi feita via comparação palavra-por-palavra
direta contra o texto real do PDF para cada questão afetada (Seções D/L/M/N/O/P), e via
`enade audit-extraction` (77/77 OK) + `enade verify-gold` (hashes) para integridade de arquivo. Nenhuma
perda, duplicação ou união indevida entre owners/colunas foi detectada em nenhuma das reauditorias.

## S. Auditoria visual

`data/manifests/visual-audit-2008-computing.json`: **64 passed / 13 failed / 0 not_performed** (antes: 62/15).
Q12 e Q63 promovidas para `passed` com evidência completa; Q07/Q71 mantidas `failed` com notas precisas
refletindo a melhoria real; Q25 permanece `passed` com nota corrigida (um defeito não detectado
anteriormente, agora resolvido). Nenhuma promoção em massa - cada mudança de status tem uma nota extensa e
específica.

## T. Q8/Q38/Q55

Exclusão preservada integralmente. Nenhuma tentativa de recuperação, placeholder, alteração de gabarito ou
crop de página inteira. `enade extract` continua reportando as 3 exclusões explícitas e ruidosas
(`structural_warnings`), nunca silenciosas.

## U. Generalização

8 testes metamórficos novos (`tests/test_fragment_reconstruction.py`): invariância por translação (relação
de merge e de não-merge), invariância por escala (proporção de gap), variação de tamanho de fonte (6pt/
9.96pt/24pt, mantendo a mesma classificação relativa), profundidade de fragmentação (2/3/4 fragmentos),
ordem do content stream divergente da ordem visual. Nenhum teste depende de question ID/ano/página/
coordenada real. `fragment_reconstruction_gate` classificado G2 (nunca G3/G4).

## V. Runtime sem IA

`tests/test_generalization_architecture.py::test_core_extraction_modules_import_no_network_or_llm_library` e
`test_declared_runtime_dependencies_contain_no_llm_or_network_client`: PASS. Nenhuma dependência de LLM/VLM/
API externa/rede foi adicionada - `fragment_reconstruction.py` usa apenas geometria (bbox, texto bruto do
próprio glifo) e nenhuma biblioteca externa além das já declaradas.

## W. Proteção de 2011/2021

Confirmado **zero drift** em múltiplas iterações distintas:
1. Após a implementação inicial (sem gate) - encontrada uma regressão real em 2021 p.19 (Q9/Q10, mesma
   baseline entre colunas independentes) - revertida via a barreira de coluna (Seção I), não aceita como
   "equivalência semântica" apesar de ser geometricamente plausível.
2. Após adicionar a barreira de coluna - zero drift confirmado, mas o mecanismo (testado incondicionalmente)
   corrigiu um defeito genuíno e pré-existente de 2021 (Q9's "B Escalonamento por taxas monotonicas") -
   OPÇÃO ESCOLHIDA: gated via `fragment_reconstruction_gate` (nunca aceito como default, mesmo sendo
   correto).
3. Após o gate declarativo - zero drift reconfirmado.
4. Após a exclusão de linhas reconstruídas de `label_candidates` (fix do Q07) - zero drift reconfirmado.
5. Verificação final, pós-todas as mudanças - zero drift reconfirmado via `git status --short` E
   `sha256sum -c` contra os 288 arquivos protegidos.

## X. Testes e quality gates

- 539 testes existentes (fim da Fase 3G) → **569 testes** ao final desta fase (+30: 26 em
  `test_fragment_reconstruction.py` + 4 novos em `test_extraction_pipeline_2008.py`).
- `pytest -q`: 569 passed.
- `ruff check .`: All checks passed.
- `ruff format --check .`: limpo (após uma correção de formatação aplicada).
- `mypy src`: Success, 54 source files.
- `enade validate-schema`: 13/13.
- `enade validate-manifest`: 0 warnings.
- `enade audit-extraction --questions-dir data/questions/2008`: 77/77 OK.
- `enade verify-gold`/`assess-readiness` para 2008/2011/2021: todos nos valores esperados (Seção C/S).

## Y. Reprodutibilidade

Duas execuções completas e independentes de `enade extract --year 2008 --course all-computing` (run A, run
B): `diff -rq run_a run_b` → idêntico byte a byte (exit 0). `diff -rq run_b/.../all-computing
data/questions/2008/all-computing` → idêntico byte a byte ao corpus publicado (exit 0).

## Z. Arquivos e Git final

Novos: `src/enade/extraction/fragment_reconstruction.py`, `tests/test_fragment_reconstruction.py`,
`docs/phase-3h-report.md` (mais `docs/phase-3g-report.md`, pendente de commit desde a fase anterior).
Modificados: `src/enade/extraction/layout.py` (refatoração de `_raw_lines` + novo
`_column_boundary_for_fragment_merge`), `src/enade/extraction/figures.py` (exclusão de linhas reconstruídas
de `label_candidates`), `src/enade/extraction/assembler.py` (propagação de `fragment_reconstruction_gate`/
`fragment_merges`), `src/enade/extraction/pipeline.py` (threading do gate), `src/enade/extraction/exam_profile.py`
(novo campo), `data/manifests/exam-structure-2008.yaml` (gate habilitado), `data/manifests/blocker-ledger-2008.yaml`,
`data/manifests/visual-audit-2008-computing.json`, `data/manifests/extraction-capabilities.json`,
`data/manifests/gold-2008-computing.json`, `data/manifests/extraction-audit-2008-computing.{csv,json}`,
`data/manifests/transformation-log-2008-computing.json`, 16 arquivos de questões 2008-b,
`tests/test_extraction_assembler.py`, `tests/test_extraction_pipeline_2008.py`. Nenhum arquivo de
`data/questions/2011` ou `data/questions/2021` foi tocado. **Nenhum commit, push, PR, merge ou tag foi
criado.** `master` permanece intocado. Branch: `feat/enade-2008-cc-b-pilot`, HEAD ainda em `8ecc93c`.

## Recomendação

O Cluster D está parcialmente estabilizado: a arquitetura geral (evidência documental de espaço à direita +
geometria de baseline/gap + barreira de coluna) provou-se correta e general, resolvendo integralmente Q12 e
Q63, substancialmente Q07 e o enunciado de Q71, e como efeito colateral Q25 - sem nenhuma regressão em
2011/2021, mesmo quando o próprio mecanismo provou corrigir um defeito real e pré-existente daquele corpus.
Os dois contraexemplos remanescentes (D10, Q71-alternativas) foram precisamente diagnosticados como
pertencendo a mecanismos **distintos** - `wrong_column_order` e `alternative_detection`, respectivamente -
não a fragmentação. Recomenda-se:

1. **Não avançar para `alternative_group`** (Q29's arquitetura completa, PROMPT seção 22) antes de
   resolver esses dois contraexemplos, já que ambos tocam mecanismos mais fundamentais
   (`detect_column_margins`, `_find_alternative_starts`) que uma futura Fase 3I precisaria de qualquer
   forma.
2. Investir uma fase dedicada e isolada em `detect_column_margins`'s própria evidência de coluna (excluir
   títulos/marcadores de página do cômputo de margem) - de alto risco por afetar toda página de todo
   caderno, exigindo validação isolada com seu próprio orçamento de regressão contra 2011/2021.
3. Investir, separadamente, em tornar `_find_alternative_starts` ciente de margem (reaproveitando
   `_is_marker_at_margin`, já validado para Cluster C) - de alto risco por afetar a detecção de fronteira de
   alternativas de toda questão de todo caderno.
4. Não recuperar Q8/Q38/Q55 antes de estabilizar as 77 publicadas.
5. Não processar o bundle `e`. Não processar outro ano.
6. Não declarar generalização validada - G4 continua exigindo prova inédita com código congelado.
