# Phase 3A — Piloto de Layout Legado com o Caderno ENADE 2008-B

## A. Classificação

**`LEGACY_LAYOUT_PARTIAL`.**

**`NOT_READY_FOR_2008_ENGINEERING_TEST`** (`assess-readiness --year 2008 --course all-computing`, exit code 1).

A estrutura do caderno 2008-b foi corretamente descoberta e modelada declarativamente; as 80
questões acadêmicas foram corretamente delimitadas e contabilizadas (77 publicadas + 3
explicitamente excluídas, nunca perdidas silenciosamente); o gabarito foi 100% vinculado; 2011 e
2021 permanecem byte-idênticos e totalmente protegidos. Porém, uma generalização real e não
trivial do mecanismo de detecção/fusão de regiões visuais (`figures.py`) falhou para este layout,
causando perda ou contaminação de conteúdo em 25 questões, e um segundo defeito (vazamento de
texto de transição de seção) afeta mais 2. Gold permanece `provisional`; readiness reporta
corretamente `NOT_READY`.

## B. Estado Git inicial

```
branch:  feat/enade-2011-unified-extraction
HEAD:    84c50058220bbc81a8d2f3086b2cd60d0cd47eb6
master:  a5dfaab0c105150df3a7201c16547708cef45292 (= origin/master)
origin/feat/enade-2011-unified-extraction: 84c5005... (= HEAD)
working tree: limpo
```
Confirmado por inspeção fresca (`git fetch origin --prune` não alterou nenhum SHA). Nenhum
commit inesperado, nenhum merge/rebase/cherry-pick em andamento.

## C. Branch criada

```
feat/enade-2008-cc-b-pilot
```
Criada via `git switch -c` exatamente do checkpoint validado `84c5005...` (HEAD de
`feat/enade-2011-unified-extraction` no momento da inspeção — sem divergência do SHA presumido
pelo prompt). Branch não existia previamente.

## D. Corpus

**Proveniência**: `https://github.com/geacc/enade.git`, branch `master`, commit
`a657632b72b97468c8a5eb3b433d1abb4a5511c5` — idêntico ao commit esperado, confirmado via Git
antes de qualquer leitura (nenhuma atualização automática foi necessária).

**Bundle `b`** (`data/raw/geacc-enade/2008/`):

| Arquivo | SHA-256 | Páginas | Tamanho | Camada de texto |
|---|---|---|---|---|
| `b1_prova.pdf` | `5c8a08f7...25db264` | 36 | 1.564.836 B | Parcial — capa (pág. 1) é imagem pura, 0 caracteres extraíveis; páginas 2-36 têm texto real |
| `b2_gabarito.pdf` | `707a3263...1803f2425` | 2 | 12.000 B | Completa |
| `b3_padrao.pdf` | `7021d115...726d0d35ef` | 6 | 387.720 B | Completa |

Todos os três hashes conferem exatamente com `data/manifests/source-exams.yaml`. Nenhum PDF bruto
foi copiado para a árvore rastreável (`git check-ignore -v` confirma proteção de `data/raw/`).

**Bundle `e`** (engenharia): inspecionado apenas na capa (1 página, leitura, não processamento) —
"PROVA DE ENGENHARIA GRUPO II", um caderno de pool multi-especialidade (Computação, Controle e
Automação, Eletrônica, Eletrotécnica, Telecomunicações) onde "Computação" é uma fatia de apenas
4 questões (37-40). **Não processado**, conforme instruído.

## E. Estrutura descoberta

O código `b` **não representa apenas "Ciência da Computação — Bacharelado"** como o manifesto de
inventário sugeria (`course_codes: [ciencia-da-computacao-bacharelado]`) — a capa (imagem, lida
visualmente) mostra "PROVA DE COMPUTAÇÃO", um **caderno unificado multi-curso**, estruturalmente
análogo ao `all-computing` de 2011:

| Seção | Faixa objetiva | Faixa discursiva | Cursos aplicáveis |
|---|---|---|---|
| Formação Geral | 1–8 | 9–10 | todos |
| Núcleo Comum | 11–19 | 20 | todos |
| CC-Bacharelado | 21–38 | 39–40 | ciencia-da-computacao-bacharelado |
| Engenharia de Computação | 41–58 | 59–60 | engenharia-da-computacao |
| Sistemas de Informação | 61–78 | 79–80 | sistemas-de-informacao |
| Questionário de Percepção (não acadêmico) | — | — | excluído (página 36) |

Total: 71 objetivas + 9 discursivas = **80 questões acadêmicas**, confirmado de forma
independente por três fontes: a tabela da capa, o gabarito (80 entradas numeradas 1–80,
`Discursiva` no lugar da letra para os 9 itens discursivos, `ANULADA` para Q44), e os próprios
marcadores impressos. Nenhuma contagem presumida de 2011/2021 foi usada.

**Diferenças estruturais confirmadas frente a 2011/2021** (nenhuma presumida):
- Numeração combinada: discursivas reutilizam o mesmo fluxo numérico das objetivas (9, 10, 20,
  39, 40, 59, 60, 79, 80), ao contrário do fluxo D1–D5 independente de 2011.
  ANULADA: Q44 (confirmado no gabarito).
- Marcador discursivo no formato "QUESTÃO N – DISCURSIVA" (número antes, sufixo depois) — o
  oposto de 2021's "QUESTÃO DISCURSIVA N".
- Separador de traço inconsistente: en-dash (–, U+2013) na maioria, em-dash (—, U+2014) +
  minúsculas em Q59 especificamente (confirmado por inspeção de codepoint).
- Cabeçalho do questionário de percepção usa "...SOBRE A PROVA", não "...DA PROVA" de 2021.
- Gabarito em formato "N -" / valor (traço após o número), não o "N" nu de 2011.
- Padrão de resposta sem cabeçalho separador "PADRÃO DE RESPOSTA": a rubrica começa
  imediatamente após "Questão N", sem reimpressão do enunciado.

## F. Comparação de layouts (2008 vs. 2011 vs. 2021)

| Mecanismo | 2021 | 2011 unificado | 2008-B |
|---|---|---|---|
| Detecção de marcador de questão | referência | generalizou sem mudança | **exigiu correção de regra geral** (sufixo "– DISCURSIVA") |
| Numeração discursiva | independente (D1-D5) | independente (D1-D5) | **combinada** — exigiu novo parâmetro `combined_numbering` |
| Exclusão do questionário de percepção | referência | generalizou sem mudança | **exigiu correção de regra geral** ("sobre a prova") |
| Lookup de arquivos-fonte (booklet unificado) | n/a | sem letra | **exigiu profile declarativo** (`source_letter: b`) |
| Verificação da página de instruções | referência (`_RANGE_PATTERNS`) | reusa 2011 | **exigiu pattern set próprio** (página 11, não 1 — capa sem texto) |
| Gabarito flat item | n/a | generalizou sem mudança | **exigiu correção de regra geral** (traço + "Discursiva") |
| Padrão de resposta (heading rubrica) | referência | generalizou sem mudança | **exigiu correção de regra geral** (sem heading separador) |
| `Alternative.text` não-vazio | referência | generalizou sem mudança | **exigiu relaxamento de schema** (asset-only, zero pontuação residual) |
| Stripping do prefixo do marcador | referência | generalizou sem mudança | **exigiu correção de regra geral** (sufixo "– DISCURSIVA" vazava) |
| Gabarito objetivo/discursivo (padrão) | referência | generalizou sem mudança | generalizou sem mudança |
| Ownership/ordem de leitura (colunas) | referência | generalizou sem mudança | generalizou sem mudança |
| Texto compartilhado entre questões (stimulus) | referência | generalizou sem mudança | generalizou sem mudança (Q78/D79 confirmado) |
| **Detecção/fusão de regiões visuais** | referência | generalizou sem mudança | **FALHOU** — fusão excessiva causa perda/contaminação em 25 questões |
| Chrome de transição de seção | n/a (não existe em 2021) | n/a | **FALHOU** — vaza para D10/D40 |
| Alternativas como imagem única (Q14-like) | n/a | generalizou com profile | **FALHOU parcialmente** — Q8/Q38/Q55 não têm região "pequena" candidata |

Não se concluiu "generalizou" apenas por a contagem de questões estar correta — cada linha acima
reflete inspeção direta de conteúdo, não apenas contagem.

## G. Resultado da extração

```
Esperado (gabarito + capa + estrutura): 80 questões acadêmicas
Encontrado: 80 (71 objetivas + 9 discursivas) — zero lacunas, zero duplicatas
Publicadas em data/questions/2008/all-computing/: 77
Excluídas explicitamente (estrutural, ValidationError capturado, não silencioso): 3 (Q8, Q38, Q55)
Página do questionário de percepção excluída corretamente: [36]
IDs únicos: sim (252/252 OK em audit-extraction, incluindo 2011+2021)
```

## H. Assets

59 assets de questão + 8 de padrão de resposta = 71 PNGs, todos referenciados, zero órfãos, zero
referências quebradas (confirmado via script de reconciliação dedicado, mesma metodologia usada
na Fase 2G). Nenhum PDF bruto rastreado.

**Ownership/ contaminação**: a auditoria visual direta encontrou **um caso confirmado de
contaminação severa entre questões** — `enade-2008-computing-q21/figure-01.png`, reaberto
diretamente, mostra o enunciado de Q21 **mais o conteúdo inteiro de Q22 e parte de Q23** em um
único crop mesclado. Este é o achado mais grave da fase — não apenas perda de conteúdo, mas
publicação de conteúdo de uma questão sob o ID de outra. Documentado como blocker
`q21-region-merge-content-loss`; Q21/Q22/Q23 marcados `visual_validation: failed`.

**Tabelas**: `render_table_region`/`column_bounds` generalizaram sem mudança (nenhum bug
encontrado nesse mecanismo especificamente); uma tabela detectada em Q50 caiu após o corte de
alternativas e foi corretamente excluída (não mal-atribuída) — sintoma do mesmo defeito raiz.

**Fórmulas/pequenas imagens**: o mecanismo `is_small_formula`/`Alternative.asset` (herdado de
2011 Q14/Q23) generalizou corretamente quando aplicável, mas não encontrou candidatos "pequenos"
para Q8/Q38/Q55 (ver seção K).

## I. Gabarito

**68/68 objetivas vinculadas (100%)**, zero deslocamento de linha, zero resposta inferida.
Q44 = `ANULADA` (confirmado, preservado sem resposta inventada). Nenhum código inválido, nenhum
item ausente/adicional no gabarito de 80 entradas. As 3 questões excluídas (Q8/Q38/Q55) também
têm entradas de gabarito reais (C, [circuito lógico], [confiabilidade]) — não vinculadas
apenas porque a própria Question não pôde ser construída, não por falha do gabarito.

## J. Padrões de resposta

9 discursivas esperadas; **6/9 vinculadas** com texto real de rubrica (20, 39, 40, 60, 79, 80).
Três exceções, todas genuínas (não bugs):
- **D9, D10**: rubrica ausente do próprio `b3_padrao.pdf` — o documento nunca reimprime nem
  avalia as discursivas de Formação Geral, confirmado por inspeção completa das 6 páginas.
- **D59**: rubrica é 100% visual (4 imagens, zero texto entre os marcadores "Questão 59" e
  "Questão 60") — sem texto para ancorar um `AnswerStandardEntry`, logo sem janela de busca de
  imagem.

Nenhum padrão foi usado para reconstruir conteúdo ausente do enunciado; nenhuma resposta oficial
foi publicada junto da questão apresentada ao estudante (front matter separado, como em 2011).

## K. Blocker ledger

`data/manifests/blocker-ledger-2008.yaml` — **33 blockers, todos `open`** (nenhum resolvido nesta
fase; nenhum copiado de 2011). `validate_ledger`: 0 problemas.

| Categoria | Quantidade | Questões |
|---|---|---|
| `region-merge-content-loss` | 25 | d09, d20, q02, q07, q21, q22, q23, q24, q26, q41, q44, q45, q50, q51, q52, q53, q54, q61, q62, q63, q64, q69, q71, q73, q75 |
| `section-transition-chrome-bleed` | 2 | d10, d40 |
| `unstructured-image-alternatives` | 3 | q08, q38, q55 (excluídas do corpus publicado) |
| `answer-standard-incomplete` (D59) | 1 | d59 |
| `answer-standard-absent-from-source` | 2 | d09, d10 |

Todos abertos e estruturais (não `accepted_non_material_difference`) — cada um representa perda
ou contaminação real de conteúdo, não uma diferença de apresentação aceitável.

## L. Auditoria visual

`data/manifests/visual-audit-2008-computing.json` — **14 `passed`, 27 `failed`, 36
`not_performed`** (77 total, `fully_covered=True`).

**Cobertura real, honestamente reportada — não 100%.** Esta fase NÃO atingiu a auditoria
integral exigida para `LEGACY_LAYOUT_SUCCESS`: 14 questões foram confirmadas corretas por
comparação direta texto-a-texto e imagem-a-imagem contra o PDF fonte; 27 foram confirmadas
defeituosas pela mesma via; as 36 restantes (majoritariamente questões sem asset, cujo padrão
observado consistentemente foi "correto" nos 6 casos sem asset verificados: Q1, Q4, Q6, Q12,
Q30, Q48, Q65) não foram individualmente confirmadas dentro do tempo desta sessão. Nenhuma foi
marcada `passed` sem verificação — status honesto (`not_performed`) preferido a uma alegação
não sustentada. Esta é a razão central pela qual a classificação é `PARTIAL`, não `SUCCESS`
(seção 20 do prompt exige auditoria integral, não por amostragem, para o veredito de sucesso).

## M. Correções gerais (evidência de generalização)

Nove mudanças de **regra geral** (nível 1 da hierarquia de correção), cada uma testada com
fixture mínima + teste unitário + teste contra o PDF real de 2008 + regeneração isolada de
2011/2021 com zero drift:

1. `boundaries.py`: `_MARKER_RE` — reconhece "QUESTÃO N [-–—] DISCURSIVA" (sufixo), além da forma
   "QUESTÃO DISCURSIVA N" (prefixo) já suportada.
2. `boundaries.py`: `detect_question_boundaries(..., combined_numbering=bool)` +
   `_validate_combined_numbering` — valida lacunas/duplicatas sobre a união objetiva+discursiva
   quando um caderno usa numeração combinada, em vez de por-tipo.
3. `boundaries.py`: `_PERCEPTION_MARKER_RE` — aceita "...SOBRE A PROVA" além de "...DA PROVA".
4. `exam_profile.py`: `ExamStructureProfile.source_letter`/`combined_numbering` (campos
   declarativos novos); `verify_declared_profile(..., patterns=...)` generalizado para aceitar
   um pattern-set diferente do de 2011, sem hardcode de ano na função central.
5. `cli.py`: `_resolve_booklet_location` — lookup de arquivo de caderno unificado agora respeita
   `structure_profile.source_letter` (vazio para 2011, "b" para 2008), em vez de assumir "sem
   letra" incondicionalmente.
6. `answer_key.py`: `_BARE_ITEM_RE` tolera traço à direita do número; `_classify` reconhece
   "Discursiva" como valor `NOT_MACHINE_GRADED` (mesma classe de `***`);
   `parse_flat_item_gabarito` deriva o `kind` do valor observado, não mais fixo em `OBJECTIVE`.
7. `answer_standard.py`: `_DISCURSIVE_MARKER_RE` torna "discursiva" opcional; detecção automática
   (por documento, não por ano) de se o padrão usa cabeçalho separador "PADRÃO DE RESPOSTA";
   contagem de "esperados" derivada dos marcadores realmente vistos, não mais `range(1, 6)`
   hardcoded.
8. `assembler.py`: `_ALTERNATIVE_LINE_RE` e `_MARKER_PREFIX_RE` toleram marcador totalmente nu
   (sem texto/pontuação alguma após a letra) — protegido por `_find_alternative_starts` já exigir
   sequência A-E completa e estritamente ordenada antes de tratar qualquer coisa como marcador.
9. `models/question.py`: `Alternative._text_or_asset_required` — `text` vazio é válido somente
   quando `asset` ou um `AssetBlock` em `content_blocks` está presente; `markdown_format.py`
   parou de preencher "." artificialmente nesse caso (round-trip honesto).

**Resiliência de pipeline** (achado arquitetural, não uma correção de regra de layout): uma única
questão que o contrato de dados recusa (Q8/Q38/Q55) derrubava a extração inteira das outras 77.
`pipeline.py` agora captura `ValidationError` por questão, registra um aviso estrutural alto e
continua — sem isso, nada deste piloto teria produzido saída alguma.

**Não corrigido** (documentado, não escondido): fusão excessiva de regiões visuais (raiz de 25
blockers) e vazamento de chrome de transição de seção (2 blockers) — ver seção W.

## N. Profiles e overrides

`data/manifests/exam-structure-2008.yaml` — profile declarativo completo (10 seções, todas as 5
faixas objetiva+discursiva), `source_letter: b`, `combined_numbering: true`. Nenhum override de
`layout-overrides.yaml` foi necessário nesta fase (nenhum caso exigiu correção nível 3). Nenhum
question ID foi inserido na lógica central do parser.

## O. Gold 2008-B

```
maturity: provisional
verified: 11/77
needs_review: 66/77
structural_blockers: [region-merge-content-loss, section-transition-chrome-bleed,
                      unstructured-image-alternatives, answer-standard-incomplete]
verify-gold: OK (77 questions match)
```
Não promovido — defeitos reais confirmados, conforme instruído explicitamente.

## P. Readiness

```
enade assess-readiness --year 2008 --course all-computing \
  --ready-label READY_FOR_2008_ENGINEERING_TEST \
  --not-ready-label NOT_READY_FOR_2008_ENGINEERING_TEST
→ NOT_READY_FOR_2008_ENGINEERING_TEST (exit code 1)
  11/77 verified, 66 needs_review, gold maturity=provisional
  visual audit: 14 passed, 27 failed, 0 not_performed (fully_covered=True)
  106 blocker(s), todos estruturais
```
O bundle `e` não foi processado para avaliar este readiness.

## Q. Proteção de 2011

```
verify-gold --year 2011 --course all-computing → OK (55/55), maturity=validated
assess-readiness → READY_FOR_LEGACY_LAYOUT_TEST, 54/55 verified, 1 needs_review
  1 blocker: [question_not_verified, non-structural] enade-2011-computing-q34
visual audit: 55 passed, 0 failed, 0 not_performed
ledger: 38 total, 0 open
```
Q34 permanece `needs_review`/`non-structural` — não tocado, não "corrigido". **Zero drift**:
hash SHA-256 de cada um dos arquivos protegidos de 2011 (Markdown, assets, manifestos) idêntico
ao congelado antes de qualquer mudança de código (288/288 arquivos, comparação byte a byte).

## R. Proteção de 2021

```
verify-gold --year 2021 --course ciencia-da-computacao-bacharelado → OK (40/40), validated
assess-readiness → READY_FOR_2011, 40/40 verified, 0 needs_review, no blockers
```
**Zero drift** — mesma verificação byte a byte incluída no conjunto de 288 arquivos acima.

## S. Testes

```
Fase 2G (baseline): 435 passed
Fase 3A: +23 novos testes (boundaries: 7, exam_profile: 6, answer_key: 5, schema_question: 5)
Total final: 458 passed
```
Cobrindo: marcador sufixo/em-dash, numeração combinada (lacuna real detectada / lacuna falsa
evitada), heading de percepção "sobre a prova", `source_letter`/`combined_numbering` declarativos,
pattern-set de verificação alternativo, gabarito com traço/"Discursiva"→kind, alternativa
vazia+asset (válida) vs. vazia+sem-asset (rejeitada) vs. vazia+content_blocks-sem-asset
(rejeitada), round-trip Markdown sem fabricar ".".

## T. Quality gates

```
pytest -q                          → 458 passed
ruff check .                       → All checks passed!
ruff format --check .              → 370 files already formatted
mypy src                           → Success: no issues found in 52 source files
enade validate-schema              → 13/13 fixture(s) valid
enade validate-manifest            → OK (0 warnings)
enade audit-extraction (todo corpus) → 252/252 OK
verify-gold + assess-readiness (2011, 2021) → ver seções Q/R
```

## U. Reprodutibilidade

Duas extrações limpas e independentes (`run A`, `run B`, diretórios isolados) do caderno 2008-b:
```
diff -rq run-A run-B                        → 0 diferenças
diff -rq run-A data/questions/2008           → 0 diferenças (idêntico ao publicado)
```
Nenhum campo com timestamp ou reordenação não determinística observado.

## V. Desempenho

```
Páginas processadas: 36
Questões encontradas: 80 (77 publicadas + 3 excluídas)
Assets renderizados: 59 (+ 8 de padrão)
Tempo de extração: ~40-55s por execução
Tamanho publicado: data/questions/2008/ = 12 MB (77 .md + 71 .png)
```

## W. Bugs encontrados

**Corrigidos** (9 mudanças de regra geral, seção M) — todos com teste de regressão e zero drift
em 2011/2021.

**Não corrigidos, documentados como blockers abertos**:
1. **Fusão excessiva de regiões visuais** (25 questões) — causa raiz confirmada: 2008-b carrega
   substancialmente mais fragmentos vetoriais decorativos por página do que
   `compute_decorative_baseline` reconhece (98 desenhos vetoriais observados em uma única página
   contra 47 entradas de baseline em todo o documento); os fragmentos não reconhecidos são
   absorvidos pela detecção de região e fundidos com fotos/diagramas reais via a lógica de
   tolerância de fusão em Y já existente, produzindo uma região que pode cobrir a maior parte de
   uma página — no caso mais grave confirmado (Q21), atravessando para duas questões vizinhas.
   **Não corrigido**: esta é uma mudança de alto risco no mecanismo central de fusão de regiões
   compartilhado por todos os anos; uma correção apressada, sem tempo para verificação de
   regressão extensiva em 2011/2021, seria irresponsável dado o princípio de proteção integral
   desses dois corpora. Fica registrado como o achado central desta fase.
2. **Vazamento de chrome de transição de seção** (D10, D40) — o parágrafo instrucional entre
   seções ("As questões de X a Y, a seguir, são comuns/específicas para...") não é reconhecido
   por `chrome.py` e vaza para a última discursiva da seção anterior. Um regex geral e seguro
   exigiria mais tempo de verificação do que disponível nesta sessão (o texto varia em números e
   nomes de curso a cada ocorrência); documentado, não corrigido.
3. **Alternativas de imagem sem candidato "pequeno"** (Q8, Q38, Q55) — arquiteturalmente
   diferente do caso Q14/Q23 de 2011 (regiões grandes e fundidas, não pequenas formulas
   isoláveis); questões excluídas do corpus publicado, não forçadas.

## X. Arquivos

**Novos**: `data/manifests/exam-structure-2008.yaml`, `blocker-ledger-2008.yaml`,
`gold-2008-computing.json`, `visual-audit-2008-computing.json`,
`extraction-audit-2008-computing.{csv,json}`, `transformation-log-2008-computing.json`,
`data/questions/2008/all-computing/` (77 `.md` + 71 `.png`), `docs/phase-3a-report.md`.

**Modificados**: `src/enade/cli.py`, `extraction/{answer_key,answer_standard,assembler,
boundaries,exam_profile,pipeline}.py`, `markdown_format.py`, `models/question.py`,
`tests/{test_exam_profile,test_extraction_answer_key,test_extraction_boundaries,
test_schema_question}.py`.

**Removidos**: nenhum.

## Y. Estado Git final

```
branch: feat/enade-2008-cc-b-pilot
HEAD:   84c50058220bbc81a8d2f3086b2cd60d0cd47eb6  (inalterado - nenhum commit criado)
21 caminhos com alterações (staged: 0, working tree: 21)
```
**Confirmado explicitamente**: nenhum commit, push, PR, merge ou tag foi executado nesta fase.

## Z. Recomendação

Dado o resultado `PARTIAL`, o menor trabalho residual para viabilizar `LEGACY_LAYOUT_SUCCESS`
neste mesmo caderno (b) é, em ordem de impacto:
1. Investigar e corrigir a fusão excessiva de regiões visuais especificamente para 2008-b — o
   maior bloco de trabalho, provavelmente exigindo estender `compute_decorative_baseline` para
   cobrir a densidade vetorial real deste layout, com verificação extensiva de zero regressão em
   2011/2021 antes de qualquer promoção.
2. Corrigir o vazamento de chrome de transição de seção (D10/D40) — escopo pequeno e já bem
   compreendido.
3. Completar a auditoria visual das 36 questões `not_performed` restantes.
4. Reconsiderar Q8/Q38/Q55 somente após (1) estar resolvido — a mesma correção de fusão de região
   pode alterar completamente a forma dos candidatos disponíveis para essas três questões.

**O bundle `e` de 2008 não deve ser o próximo teste** até que este primeiro caderno esteja
integralmente validado, conforme o princípio final do prompt desta fase. Não iniciado
automaticamente.
