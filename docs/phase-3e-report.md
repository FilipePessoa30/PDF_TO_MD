# Fase 3E — Ownership por Referência Futura e Estabilização das 77 Questões Publicadas

## A. Classificação

**`LEGACY_LAYOUT_PARTIAL` / `RESIDUAL_LAYOUT_NOT_STABILIZED`.**

Não todas as 77 questões publicadas passam sem defeito residual (62 `passed`, 15 `failed`, 0
`not_performed`), portanto o critério para `RESIDUAL_LAYOUT_STABILIZED` (77/77) não é atingido. Ao
mesmo tempo, nenhuma das condições de `LEGACY_LAYOUT_FAILED` ocorreu: nenhuma reatribuição foi
enganosa, nenhum span foi transferido incorretamente, nenhum asset foi perdido ou duplicado por
esta fase (a única duplicação de asset encontrada — Q13/Q12 — é um defeito **pré-existente**,
achado nesta fase, não introduzido por ela), nenhuma cobertura de fonte piorou, e 2011/2021
permanecem byte-a-byte idênticos (confirmado repetidamente, ver Seções P/Q). `PARTIAL` é o
resultado correto e honesto.

## B. Estado Git

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   4cd54688f3ecda2a4118f62c6c8034df4f1b7008 (inalterado - nenhum commit criado nesta fase)
```

Nenhum commit, push, PR, merge ou tag foi executado. `master` não foi tocado. O bundle `e` de 2008
e qualquer outro ano não foram processados.

Arquivos alterados/novos no working tree ao final desta fase (ver Seção Y para a lista completa):
código-fonte (`assembler.py`, `figures.py`, `pipeline.py`, novo `reference_captions.py`), testes
(novo `test_reference_captions.py`, `test_extraction_pipeline_2008.py` estendido), manifestos 2008
(`blocker-ledger-2008.yaml`, `visual-audit-2008-computing.json`, `gold-2008-computing.json`,
`extraction-audit-2008-computing.{csv,json}`), e 34 arquivos `.md` em `data/questions/2008` (3
com mudança real de conteúdo — D60/Q61/Q62 — os demais 31 apenas com frontmatter
`extraction_status`/`visual_validation` atualizado para refletir a auditoria desta fase).

## C. Baseline da Fase 3D

Estado herdado ao início desta fase: 496 testes, todos os *gates* de qualidade verdes,
`region_merge_x_tolerance` (Fase 3C) e `caption_font_size_gate` (Fase 3D) preservados e ativos
apenas para 2008-b, gold provisório, Q8/Q38/Q55 excluídos, `LEGACY_LAYOUT_PARTIAL` /
`RESIDUAL_LAYOUT_NOT_STABILIZED`. Q61/Q62/D60 diagnosticados com precisão (mecanismo de "legenda
de referência futura" identificado, não implementado). D10/D40 com defeito residual documentado.
Q24/Q29/Q33/Q63 ainda abertos. 30 questões nunca auditadas individualmente (`not_performed`).

## D. Correções preservadas

Ambas confirmadas intactas e re-testadas nesta fase (496/496 testes originais continuam passando
antes de qualquer mudança nova):

1. **`region_merge_x_tolerance`** (`ExamStructureProfile`, Fase 3C) — cap opcional de distância X
   para o merge de regiões por proximidade Y. Reutilizado nesta fase por
   `reference_captions._find_anchored_region`.
2. **`caption_font_size_gate`** (`ExamStructureProfile`, Fase 3D) — exige fonte estritamente menor
   que o corpo do texto para um candidato a legenda ser absorvido. Uma tentativa de generalização
   desta fase foi revertida (Seção X).

## E. Reconciliação

Reconciliação feita a partir do estado real dos arquivos (não das contagens presumidas do prompt):
`data/manifests/visual-audit-2008-computing.json` tinha, ao início desta fase, 32 `passed` + 15
`failed` + 30 `not_performed` = 77. `data/manifests/blocker-ledger-2008.yaml` tinha 44 blockers
(antes desta fase). Q61 já estava `passed` (seu próprio enunciado nunca foi truncado), mas sem
nenhuma figura — um vão que a auditoria anterior nunca havia sinalizado como defeito por si só.

## F. Referências futuras (mecanismo)

Novo módulo `src/enade/extraction/reference_captions.py`. Uma legenda que documenta
explicitamente sua própria questão dona ("Figura para a questão N" / "Tabela para a questão N" /
"Diagrama referente à questão N" / "Quadro para a questão N") é tratada como evidência documental
que sobrepõe o fatiamento por posição de marcador — mesmo quando o asset é impresso **antes** do
próprio marcador "QUESTÃO N" (2008-b página 27: D60 termina onde o diagrama ITIL de Q61 é
impresso, por falta de espaço após o próprio marcador de Q61 na mesma página).

Modelo de dados (`ReferenceCaption`/`CaptionReferenceTransfer`): `page_number`, `text`, `bbox`,
`reference_type`, `referenced_number`, `origin_question_key`, `direction`
(`current`/`forward`/`backward`), e o registro de transferência com `target_question_key`,
`candidate_asset_bbox`, `transferred_line_count`, `accepted`, `rejection_reason`.

**Precedência implementada**: referência textual explícita > nada mais é tentado (não há
fallback geométrico "nearest marker" neste módulo — um caption sem âncora válida é rejeitado e
logado, nunca adivinhado).

**Regex de detecção** (`_REFERENCE_CAPTION_RE`): ancorado do início ao fim da linha
(`^tipo\s+(?:para\s+a|referente\s+[àa])\s+questão\s+0*\d+\s*$`) — nunca casa uma menção solta
dentro de prosa real ("Considerando a figura da questão 61 apresentada anteriormente..." não
casa), nunca casa quando há texto após o número. Confirmado por teste unitário
(`test_does_not_match_ordinary_prose_mentioning_a_question_number`,
`test_does_not_match_when_trailing_text_follows_the_number`).

**Resolução do alvo** (`_resolve_target`): busca por número em *qualquer* tipo de questão (a
legenda não diz objetiva/discursiva); rejeita explicitamente se o número não existir
(`referenced_question_not_found`) ou se casar mais de uma questão simultaneamente
(`ambiguous_question_kind` — 2008-b usa numeração combinada objetiva+discursiva). Nunca um
fallback difuso.

**Direção**: determinada pela posição do span-alvo na lista de spans em ordem de documento
(nunca por comparação numérica de números de questão, que não é confiável com numeração
combinada). `current` (a legenda já está no próprio span-alvo) é um no-op. `backward` é
explicitamente rejeitado e logado (`backward_reference_not_supported`) — nenhum caso real
confirmado no corpus, nunca aplicado às cegas.

**Âncora do asset** (`_find_anchored_region`): usa `collect_page_candidates` (nova função
extraída de `figures.detect_visual_regions`, ver Seção Y) + `_merge_by_vertical_proximity` — **não**
`detect_visual_regions` completo, porque sem `question_regions` conhecido este último mescla por
sobreposição de "owner=None" com "owner=None", unindo indevidamente o diagrama de Q61, o
diagrama de Q63 e um logo institucional não relacionado em um único bbox (confirmado por
instrumentação direta contra a página 27 antes da correção). O cluster mais próximo abaixo da
legenda, dentro de `MAX_CAPTION_TO_ASSET_GAP` (40pt), é aceito; nenhum candidato dentro do limite
resulta em rejeição explícita (`no_anchored_asset_found`), nunca em "melhor esforço".

**Reserva antes de operação destrutiva**: `apply_forward_reference_transfers` roda logo após
`detect_question_boundaries` e antes de `compute_question_regions`/qualquer merge ou consumo de
texto (`pipeline.py`, comentário "a reserva deve ocorrer antes dessas operações destrutivas").

**Transferência local, nunca de intervalo inteiro**: apenas a legenda + linhas geometricamente
contidas no bbox ancorado (com padding de 3pt) são movidas — nunca um parágrafo inteiro, nunca
uma alternativa (`_ALTERNATIVE_LINE_RE` excluído explicitamente, testado em
`test_alternative_marker_is_never_swept_into_a_transfer`).

## G. Reserva de ownership (verificação)

Confirmado por teste dedicado (`test_transfer_is_deterministic_across_repeated_runs`) que duas
execuções do mecanismo sobre o mesmo estado produzem resultado idêntico. Confirmado por
regeneração completa (rodadas A/B, Seção V) que o pipeline real é determinístico ponta a ponta.

## H. Q61/Q62/D60

**Root cause exato**: o diagrama ITIL de Q61 (uma imagem raster única, atravessando as duas
colunas detectadas da página 27) é impresso com uma legenda explícita "Figura para a questão 61"
**antes** do próprio marcador "QUESTÃO 61", porque D60 (discursiva, terminando nesta página
compartilhada) ocupa o espaço acima dele. O fatiamento por posição de marcador atribuiu a legenda
e os rótulos da coluna esquerda a D60, e — por causa da reordenação por coluna — atribuiu os
rótulos da coluna direita e a própria região visual a Q62.

**Correção**: mecanismo da Seção F, aplicado uma vez, de forma genérica (nenhum `if question_id
==`), gated apenas pela detecção real do padrão textual.

**Dois bugs adicionais encontrados e corrigidos durante a verificação** (nenhum deles
específico de Q61 — ambos generalizam):

1. `assemble_question` (assembler.py) nunca usava `VisualRegion.owner_key` (já calculado por
   `figures.py` a partir da mesma geometria de `QuestionRegion`) para filtrar candidatos — usava
   apenas uma janela y/x fixa (15pt/5pt) herdada de antes do modelo de ownership (Fase 2C). Depois
   da transferência, o bbox de Q61 ficou largo o bastante para sobrepor por coincidência a região
   de Q63 (ER-diagram, `owner=objective-63`), que a janela antiga aceitava porque nunca checava
   dono. **Corrigido, mas com gate estrito**: a checagem por `owner_key` só é aplicada a spans que
   foram efetivamente alvo de uma transferência aceita nesta execução
   (`reference_transfer_target_keys`, populado a partir de `caption_reference_transfers`) — todo
   outro span, incluindo **todo** span de 2011/2021 (nunca alvo de transferência) e os outros 74
   spans de 2008-b, mantém exatamente o código original, sem qualquer risco. Uma primeira versão
   sem esse gate (testando "owner_key coincide" incondicionalmente) causou regressão real em
   2011 (Q4/Q25/Q39 ganharam figuras espúrias — ver Seção X); revertida e substituída pela versão
   gated.
2. `_strip_leading_marker` (assembler.py) só removia o marcador "QUESTAO N" da **primeira** linha
   do span. Depois da transferência, a legenda passa a ser a primeira linha (o marcador real fica
   no meio), então "QUESTÃO 61" vazava como texto solto no meio do enunciado. Generalizado para
   procurar o marcador em qualquer posição da lista (o regex é suficientemente específico para
   nunca casar por coincidência com uma legenda ou rótulo transferido).
3. `figures.py`: uma região cujo `.clip()` ao território do dono produz um retângulo degenerado
   (`y1<=y0` ou `x1<=x0`, quando o candidato bruto não sobrepõe o território do dono de jeito
   nenhum — encontrado num logo/cabeçalho de página não capturado por
   `compute_decorative_baseline`, que só rastreia *drawings*, nunca imagens) agora é descartada
   na fonte (`_is_valid_rect`), em vez de sobreviver como uma região quebrada que derrubava o
   renderizador de PNG (`enade-2008-computing-q21`, achado ao rodar a suíte completa após a
   correção 1 acima — corrigido antes de publicar qualquer coisa).

**Resultado verificado** (Q61): figura própria (ITIL) presente, na posição correta (antes do
texto "A figura acima..."), sem rótulos soltos, sem marcador duplicado.
**Resultado verificado** (Q62): `assets: []`, enunciado idêntico à página 27, alternativa E agora
exatamente "competência" (antes: "competência Suporte a serviços...").
**Resultado verificado** (D60): enunciado termina em "(valor: 4,0 pontos)", sem nenhum texto da
página 27.

Três novos testes de integração
(`test_q61_gains_its_own_itil_diagram`/`test_q62_no_longer_contaminated_by_q61_diagram`/
`test_d60_no_longer_contaminated_by_q61_diagram`) + 15 testes unitários do mecanismo
(`tests/test_reference_captions.py`).

## I. D10/D40

**D40**: reconfirmado aberto. O rótulo "B\tnome,endereco" (provável símbolo π de projeção
mal-renderizado) ainda vaza como texto solto — confirmado que precede `figure-01` (o esquema
relacional), não `figure-02` como o registro da Fase 3D dizia (corrigido no *ledger*).
**Experimento tentado e revertido** (ver Seção X): permitir que `caption_font_size_gate` aceite um
candidato com fonte igual/maior que o corpo quando seu próprio texto é curto (< 20 caracteres, a
teoria sendo que um cabeçalho real é sempre uma frase longa) corrigiu este rótulo, mas quebrou uma
palavra curta legítima da prosa real de D40 ("Cliente," — o próprio nome da relação, terminando
uma linha antes de uma quebra de parágrafo), que foi engolida pelo mesmo relaxamento, partindo
uma frase real em duas. Comprimento curto sozinho não distingue um rótulo de diagrama genuíno de
uma linha curta comum de prosa — revertido.

**D10**: **achado corrigido, mais grave que o documentado**. A Fase 3D afirmava que os três
recortes de jornal (manchete+corpo+citação) estavam completos, com apenas a ordem de leitura
errada. Re-auditoria desta fase (comparação palavra por palavra contra a página 7) encontrou isso
**incorreto**: o corpo inteiro da manchete 1 ("Apesar das várias avaliações que mostram que o
ensino médio está muito aquém do desejado... entre aqueles que foram bem, ela fica em 7,1.") está
ausente, e a cláusula de abertura do corpo da manchete 2 também está ausente — apenas um
fragmento desconectado sobrevive. O teste de regressão adicionado na Fase 3D
(`test_d10_no_longer_loses_its_own_newspaper_fragments`) só verifica títulos de manchete e
citações, nunca os corpos — por isso a perda não foi percebida antes. Recategorizado no *ledger*
de `table-reading-order-scramble` de volta para `region-merge-content-loss` (é perda de conteúdo
real, não apenas ordem). Docstring do teste corrigida para não repetir a alegação incorreta; a
asserção em si não foi alterada (documenta conteúdo confirmado presente, não afirma que o resto
esteja ausente).

Nenhuma correção geral de baixo risco foi encontrada para nenhum dos dois nesta fase (orçamento
gasto no mecanismo de referência futura); ambos permanecem abertos, com causa e evidência
precisas.

## J. Demais publicadas (Q24/Q29/Q33/Q63 e reavaliação completa)

**Não presumido** — a lista de questões ainda `failed` foi re-derivada da auditoria real desta
fase (ver Seção N), não copiada do prompt. Q24, Q29, Q33 e Q63 foram todas reconfirmadas ainda
abertas, cada uma com uma causa distinta:

- **Q24**: enunciado substituído por fragmentos de tabela-verdade/decodificador ("A\t0 B\tS0 /
  A\tII B\t1 / A\t0 B\tS0"). Página real tem um diagrama principal, uma tabela-verdade real, e
  três itens julgados (I/II/III) cada um com seu próprio sub-diagrama — precisa de um mecanismo
  dedicado de montagem multi-diagrama/item-julgado, não uma correção de absorção de rótulo. Não
  tentado (escopo/risco incompatível com o orçamento restante).
- **Q29**: fragmento de produção gramatical ("A ÷ a B ÷ b") ainda inserido no meio da frase. Mesma
  classe geral de vazamento de rótulo de diagrama que Q62/D60 (agora resolvida para esses dois),
  mas é um deslocamento **dentro do próprio span** (não entre questões), então o mecanismo da
  Seção F não se aplica.
- **Q33**: marcadores romanos I-IV e a palavra "bottom-up" ainda deslocados de suas posições
  corretas dentro do enunciado — defeito de ordem local, não contaminação cruzada.
- **Q63**: enunciado substituído por fragmentos de ER-diagram ("A\tatrA / C\tatrB B\tatrC").
  Confirmado que a própria região ER de Q63 (owner=objective-63, 18 elementos mesclados) está
  intacta e corretamente possuída (verificado nesta fase ao corrigir Q61 — nunca mais vaza para
  Q61), mas o vazamento residual dentro do próprio Q63 não foi isolado.

**Auditoria completa das 30 questões `not_performed`** (delegada a um subagente com instruções
precisas de comparação palavra-por-palavra contra o PDF fonte, nunca aprovação em massa): 29
confirmadas `passed` (conteúdo idêntico à fonte), 1 nova falha encontrada (Q05, Seção N).

**Dois novos defeitos encontrados** durante a reaudição completa, não presumidos pelo prompt:
- **Q13**: além do já conhecido `q13-duplicated-alternative-text`, `figure-01.png` de Q13 é
  byte-idêntico (SHA-256 confirmado) ao `figure-01.png` de Q12 — uma contaminação de **imagem**
  cruzada entre questões, não apenas de texto. Q13 é uma questão de partição de conjuntos sem
  nenhum diagrama na própria página fonte. Causa raiz não isolada nesta fase; novo blocker aberto
  (`q13-cross-question-image-contamination`).
- **Q05**: a citação da imagem ("STRICKLAND, Carol; BOSWELL, John...") está totalmente ausente do
  Markdown renderizado. Mesma família de absorção-de-rótulo-além-do-necessário que D09/D10/D40.
  Novo blocker aberto (`q05-image-citation-dropped`).

**Detalhes adicionais encontrados em blockers já conhecidos** (Q07, Q75): alternativas com
contaminação de rótulo de diagrama previamente não documentada — anotado no *ledger*, não corrigido.

## K. Q8/Q38/Q55

Confirmado, sem tentativa de recuperação: continuam ausentes do corpus publicado. `enade extract`
reporta, sem alteração em relação às fases anteriores:
```
objective 8: could not build a valid Question - 1 validation error for Alternative
objective 38: could not build a valid Question - 1 validation error for Alternative
objective 55: could not build a valid Question - 1 validation error for Alternative
```
Nenhuma inferência por gabarito, nenhum placeholder, nenhuma promoção a gold. Não regredido:
`test_all_80_academic_questions_are_accounted_for` continua verde.

## L. Source coverage

`enade audit-extraction --questions-dir data/questions/2008/all-computing`: **77/77 OK** (schema +
proveniência de fonte/asset). Nenhuma perda de cobertura de fonte introduzida por esta fase.

## M. Auditoria visual

Antes: 32 `passed` / 15 `failed` / 30 `not_performed` (+ 3 excluídas = 80 questões acadêmicas).
Depois: **62 `passed` / 15 `failed` / 0 `not_performed`** (+ 3 excluídas = 80).

Toda entrada tocada nesta fase carrega uma nota com evidência concreta (trecho do PDF fonte
comparado ao Markdown renderizado), nunca uma aprovação em massa. `data/manifests/visual-audit-2008-computing.json`
atualizado para as 46 entradas reavaliadas (30 antigas `not_performed` + 15 antigas `failed` + Q61
rechecada). O alvo do prompt (77 passed / 0 failed / 0 not_performed) **não foi atingido** — 15
questões têm defeitos reais e confirmados, não escondidos.

## N. Blocker ledger

`data/manifests/blocker-ledger-2008.yaml`: 46 blockers (antes: 44), `validate_ledger` → 0
problemas.

- **Resolvidos nesta fase**: `q62-cross-question-diagram-label-bleed`,
  `d60-cross-question-diagram-label-bleed` (23 `resolved` no total, incluindo os de fases
  anteriores).
- **Recategorizado**: `d10-label-absorption-newspaper-fragments` (de
  `table-reading-order-scramble` para `region-merge-content-loss`, achado corrigido — Seção I).
- **Novos, abertos**: `d60-valor-annotation-misattachment` (defeito diferente, exposto ao remover
  a contaminação ITIL de D60), `q05-image-citation-dropped`,
  `q13-cross-question-image-contamination`.
- **Enriquecidos com novo detalhe, status inalterado**: `q07-region-merge-content-loss`,
  `q75-region-merge-content-loss`, `d40-table-reading-order-scramble` (correção figure-01 vs
  figure-02 + registro do experimento revertido).
- **Total**: 23 `resolved`, 22 `open`, 1 `superseded`.

## O. Gold 2008-B

Reconstruído via `enade build-gold --year 2008 --course all-computing --maturity provisional`
(mesma maturidade de antes — nenhuma promoção a `validated` nesta fase, dado que 15 questões
seguem `failed`). `structural_blockers`: mesmas 7 categorias de antes (nenhuma categoria nova
introduzida — os 3 novos blockers reusam categorias já existentes). `verify-gold --year 2008
--course all-computing`: **OK (77 questions match)**, `verified=59 needs_review=18`.

## P. Readiness

```
assess-readiness --year 2008 --course all-computing \
  --ready-label READY_FOR_2008_ENGINEERING_TEST \
  --not-ready-label NOT_READY_FOR_2008_ENGINEERING_TEST
→ NOT_READY_FOR_2008_ENGINEERING_TEST (exit code 1)
  59/77 verified, 18 needs_review, gold maturity=provisional
  visual audit: 62 passed, 15 failed, 0 not_performed (fully_covered=True)
  50 blocker(s)
```
`fully_covered=True` é novo nesta fase (antes: `False`, por conta dos 30 `not_performed`) — a
cobertura da auditoria visual está agora completa; o que resta são defeitos reais, não lacunas de
auditoria. O rótulo `READY_FOR_2008_ENGINEERING_TEST`, quando alcançado, significa prontidão para
testar o bundle `e` de 2008 — não iniciado.

## Q. Proteção de 2011

Confirmado, múltiplas vezes ao longo da fase (a cada mudança de código):
`git status --short` sobre os 270 arquivos de `data/questions/2011` + os 4 manifestos próprios
(`blocker-ledger-2011.yaml`, `exam-structure-2011.yaml`, `extraction-audit-2011-computing.{csv,json}`,
`gold-2011-computing.json`, `transformation-log-2011-computing.json`, `visual-audit-2011-computing.json`)
— **zero saída, sempre** (nenhuma mudança detectada pelo próprio git, o que evita a armadilha de
comparar `git show` (LF) contra o working tree (CRLF) encontrada em fases anteriores). Regeneração
completa (`enade extract --year 2011 --course all-computing`) para um diretório separado,
comparada byte a byte (`diff -rq`) contra o corpus real: **zero diferenças**, em três rodadas
distintas ao longo da fase (após o mecanismo de referência futura; após a primeira versão,
regredida, do filtro por `owner_key`; após a versão final, gated). `assess-readiness --year 2011`
inalterado: `READY_FOR_LEGACY_LAYOUT_TEST`, 54/55 verified, Q34 como único blocker (idêntico a
antes desta fase).

## R. Proteção de 2021

Mesmo protocolo: os 14 manifestos próprios de 2021 (`extraction-audit-2021-{b,l,s}.{csv,json}`,
`gold-2021-b.json`, `transformation-log-2021-{b,l,s}.json`, `visual-audit-2021-b.json`) + 0
arquivos de `data/questions/2021` alterados, confirmados via `git status --short` (saída vazia)
repetidamente. Regeneração completa das 3 disciplinas (`ciencia-da-computacao-bacharelado`,
`ciencia-da-computacao-licenciatura`, `sistemas-de-informacao`) comparada byte a byte: **zero
diferenças**, três rodadas. `assess-readiness --year 2021 --course ciencia-da-computacao-bacharelado`:
`READY_FOR_2011`, 40/40 verified, sem blockers — inalterado.

**Total combinado**: 270 + 18 = 288 arquivos protegidos, confirmados byte-idênticos ao HEAD em
todas as verificações desta fase.

## S. Testes

**514 testes, todos verdes** (antes: 496; +18 novos):
- 15 novos testes unitários/integração em `tests/test_reference_captions.py` (padrão da legenda,
  narrowness contra prosa comum, `_resolve_target` explícito para ambíguo/inexistente,
  transferência forward completa, no-op para `current`, rejeição explícita de `backward`, rejeição
  de referência inexistente, rejeição de "sem âncora" sem fallback, alternativa nunca varrida,
  determinismo).
- 3 novos testes de integração em `tests/test_extraction_pipeline_2008.py`
  (`test_q61_gains_its_own_itil_diagram`, `test_q62_no_longer_contaminated_by_q61_diagram`,
  `test_d60_no_longer_contaminated_by_q61_diagram`), contra o corpus real.
- 1 docstring de teste existente corrigida (`test_d10_no_longer_loses_its_own_newspaper_fragments`)
  para não repetir a alegação incorreta da Fase 3D — a asserção em si inalterada.

Nenhum teste antigo alterado além dessa correção de docstring. Nenhum teste removido.

## T. Quality gates

```
pytest -q                    → 514 passed
ruff check .                 → All checks passed!
ruff format --check .        → 377 files already formatted (após auto-format dos 2 arquivos novos)
mypy src                     → Success: no issues found in 53 source files
enade validate-schema        → 13/13 fixture(s) valid
enade validate-manifest      → OK (0 warnings)
enade audit-extraction (2008)→ 77/77 OK
```

## U. Reprodutibilidade

Duas execuções independentes de `enade extract --year 2008 --course all-computing` para
diretórios de scratch separados: **byte-idênticas entre si** e **byte-idênticas ao corpus real
committed**. Confirmado duas vezes nesta fase (uma vez logo após o mecanismo de referência
futura + fix de ownership, uma segunda vez após todas as mudanças, incluindo a correção do
*visual-audit*/gold).

## V. Desempenho

`enade extract --year 2008 --course all-computing`: ~61s (36 páginas processadas, incluindo a
página de percepção excluída). Não medido como baseline explícito em fases anteriores para
comparação direta; o novo passo de pré-processamento (`apply_forward_reference_transfers`) escaneia
cada span uma vez por padrão de legenda — custo desprezível frente ao tempo de renderização de
assets, que domina o tempo total. Não é um caminho quente (pipeline em lote, executado sob
demanda), sem impacto prático.

## W. Experimentos revertidos

1. **Filtro de região por `owner_key` incondicional** (assembler.py) — primeira tentativa de
   corrigir Q61/Q63: confiar em `owner_key` sempre que definido, ignorando a janela y/x antiga.
   Corrigiu Q61/Q63, mas causou regressão real em 2011 (Q4, Q7, Q10, Q15, Q20, Q25, Q30, Q34, Q39,
   Q43, Q45, Q50, D01, D04 ganharam figuras espúrias — fragmentos de cabeçalho de página não
   capturados por `compute_decorative_baseline`, atribuídos a essas questões pelo fallback de
   "vizinho mais próximo na mesma coluna" de `find_owner`, sem limite de distância). Substituída
   por uma versão com checagem de sobreposição geométrica real (`_overlaps_own_region`) — reduziu
   a regressão de 14 para 3 questões (Q25, Q34, Q39), mas não eliminou. **Versão final adotada**:
   gated por `reference_transfer_target_keys` — a relaxação só se aplica a spans que foram
   efetivamente alvo de uma transferência aceita nesta execução; todo outro span (o que inclui
   **todo** span de 2011/2021, que nunca recebe uma transferência) mantém o código original,
   inalterado. Zero *drift* confirmado por regeneração completa.
2. **Exceção de texto curto em `caption_font_size_gate`** (figures.py, para corrigir D40) —
   permitir um candidato com fonte igual/maior que o corpo quando seu texto é curto (< 20
   caracteres). Corrigiu o rótulo "B nome,endereco" de D40, mas engoliu a palavra legítima
   "Cliente," da prosa real da mesma questão, partindo uma frase em duas. Revertida integralmente;
   D40 permanece com o defeito original documentado (Seção I).

Ambos os experimentos foram testados via regeneração completa + *diff* byte a byte antes de
qualquer decisão de manter ou reverter — nenhum foi aceito "no escuro", e nenhum foi escondido:
ambos estão documentados aqui e no *blocker ledger*.

## X. Bugs encontrados

1. **Região degenerada em `figures.py`** (afeta potencialmente qualquer booklet, achado em 2008-b
   Q21): `QuestionRegion.clip()` pode produzir um retângulo invertido (`y1<y0`) quando o candidato
   bruto não sobrepõe de jeito nenhum o território do próprio dono — corrigido com `_is_valid_rect`
   descartando a região na fonte, em vez de deixá-la sobreviver como uma região quebrada (que
   derrubava o renderizador de PNG com "Invalid bandwriter header dimensions"). Achado ao rodar a
   suíte completa após o primeiro fix de ownership, corrigido antes de publicar qualquer coisa —
   nunca chegou ao corpus real.
2. **Q13/Q12 contaminação de imagem** (achado nesta fase, pré-existente, não introduzido por
   nenhuma mudança de código desta fase — confirmado presente na versão committed antes de
   qualquer alteração): `figure-01.png` de Q13 é byte-idêntico ao de Q12. Documentado como novo
   blocker aberto (Seção N); não corrigido (fora do escopo desta fase, causa raiz não isolada).
3. **D60 valor-annotation-misattachment** (achado nesta fase, pré-existente — confirmado presente
   na versão committed antes de qualquer alteração desta fase, apenas obscurecido pela
   contaminação ITIL que ficava depois): documentado como novo blocker aberto; não corrigido.

## Y. Arquivos

**Código-fonte**:
- `src/enade/extraction/reference_captions.py` (novo, ~250 linhas) — mecanismo de legenda de
  referência futura completo.
- `src/enade/extraction/assembler.py` — `_strip_leading_marker` generalizado; novo parâmetro
  `reference_transfer_target_keys` em `assemble_question`; filtro de região por página reescrito
  (janela y/x original preservada como *default* para todo span não-alvo de transferência; checagem
  por `owner_key` + sobreposição geométrica real, gated, para spans que foram alvo).
- `src/enade/extraction/figures.py` — `collect_page_candidates` extraída como função reutilizável;
  `_is_valid_rect` novo, aplicado nos dois pontos de construção de `VisualRegion` após `.clip()`;
  comentário do experimento revertido documentado inline em `FONT_SIZE_CAPTION_MARGIN`.
- `src/enade/extraction/pipeline.py` — chamada a `apply_forward_reference_transfers` logo após
  `detect_question_boundaries`/antes de qualquer consumo; `reference_transfer_target_keys`
  computado e propagado a cada `assemble_question`; novo campo
  `ExtractionResult.caption_reference_transfers`.

**Testes**:
- `tests/test_reference_captions.py` (novo, 15 testes).
- `tests/test_extraction_pipeline_2008.py` (+3 testes, 1 docstring corrigida).

**Manifestos 2008** (únicos manifestos tocados — nenhum manifesto 2011/2021 alterado):
- `data/manifests/blocker-ledger-2008.yaml` (44→46 blockers; 2 resolvidos, 1 recategorizado, 3
  novos, 2 enriquecidos).
- `data/manifests/visual-audit-2008-computing.json` (46 entradas atualizadas com evidência).
- `data/manifests/gold-2008-computing.json` (reconstruído, mesma maturidade `provisional`).
- `data/manifests/extraction-audit-2008-computing.{csv,json}` (reflete o estado atual).

**Corpus 2008** (`data/questions/2008/all-computing/`): 3 arquivos com mudança real de conteúdo
(`enade-2008-computing-{d60,q61,q62}.md`), 1 asset removido (`q62/figure-01.png`, contaminado), 1
asset novo (`q61/figure-01.png`, correto), 31 arquivos com apenas frontmatter
`extraction_status`/`visual_validation` atualizado (reflete a auditoria desta fase, sem mudança
de conteúdo).

**Limpeza**: todos os scripts de diagnóstico temporários (`diag_*.py`) criados durante a
investigação foram removidos antes da conclusão da fase. `git status --short | grep "^??"`
confirma apenas os 3 arquivos novos intencionais (2 de código/teste + 1 diretório de asset).

## Z. Git final

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   4cd54688f3ecda2a4118f62c6c8034df4f1b7008 (inalterado - nenhum commit criado nesta fase)
46 caminhos com alterações no working tree (staged: 0), 3 não rastreados
```
**Confirmado explicitamente**: nenhum commit, push, PR, merge ou tag foi executado nesta fase.
`master` não foi tocado. Nenhum outro ano ou o bundle `e` foi processado.

## Recomendação

Dado o resultado `PARTIAL`/`RESIDUAL_LAYOUT_NOT_STABILIZED`, em ordem de impacto esperado:

1. **Mecanismo dedicado de "ilha de leitura local"** (`local_reading_region`, nunca implementado
   como mecanismo formal em nenhuma fase até aqui) — D10 (colagem de recortes), Q29/Q33 (item
   deslocado dentro do próprio span), e D60 (anotações de valor deslocadas) são todos instâncias
   do mesmo problema geral: um layout onde a ordem de leitura "esquerda-completa-depois-direita"
   não corresponde à ordem real impressa. Correções pontuais adicionais em `detect_column_margins`
   têm alto risco demonstrado (dois experimentos revertidos nesta fase e duas nas fases
   anteriores) — a resposta certa é um mecanismo geral, não mais ajustes de tolerância.
2. **Mecanismo de montagem multi-diagrama/item-julgado** para Q24 — layout com diagrama principal
   + tabela real + 3 sub-diagramas por item julgado, arquiteturalmente diferente de qualquer
   mecanismo existente.
3. **Investigar `q13-cross-question-image-contamination`** (achado novo, potencialmente sério: se
   a causa for a mesma classe do bug de `find_owner` sem limite de distância corrigido nesta fase
   para o *filtro de inclusão*, pode haver uma correção geral análoga para a atribuição de asset
   em si — mas isso precisa de investigação própria, não deve ser presumido).
4. **Completar Q02/Q05/Q07/Q12/Q45/Q54/Q75** — mesma família de absorção-de-legenda-além-do-corpo
   já identificada em fases anteriores; nenhuma correção geral de baixo risco foi encontrada até
   aqui (o gate de tamanho de fonte já resolveu os casos "cabeçalho vs legenda"; os que restam
   parecem ser "legenda genuína pequena, ainda assim descartada" — categoria distinta).
5. **Q8/Q38/Q55**: mecanismo de fatiamento de região grande por alternativa, análogo ao
   `is_small_formula` existente mas para candidatos grandes — recomendado como fase própria e
   dedicada desde a Fase 3A, ainda não iniciado.

**O bundle `e` de 2008 não deve ser o próximo teste** até que este primeiro caderno esteja
integralmente validado (`READY_FOR_2008_ENGINEERING_TEST`). Não iniciado nesta fase.
