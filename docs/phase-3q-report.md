# Fase 3Q — Recuperação Documental de Tokens Ausentes em Q24 e Q45

## A. Classificação

- **Source token recovery:** `SOURCE_TOKEN_RECOVERY_PARTIAL`. Q24 foi integralmente resolvida (marcadores "I" e "II" recuperados, documentalmente comprovados, sem blocker próprio remanescente). Q45 permanece com um resíduo genuíno e não fabricável (a fórmula "f(x) = √x", desenhada como vetor, nunca texto) — não é `SOURCE_TOKEN_RECOVERY_STABILIZED` porque nem todas as questões-alvo ficaram integralmente corretas, mas também não é `_FAILED`, já que nenhuma identidade foi inventada, nenhuma regressão ocorreu e os corpora protegidos permanecem intactos.
- **Residual layout (corpus 2008-b):** `RESIDUAL_LAYOUT_NOT_STABILIZED` — `published=77, passed=75, failed=2 (Q45, D40), not_performed=0`. Não é 77/77.
- **Generalização:** `GENERALIZATION_ARCHITECTURE_ESTABLISHED` para a metodologia de evidência de baixo nível (rawdict/texttrace/font fingerprint/get_drawings) formalizada nesta fase — `GENERALIZATION_NOT_YET_VALIDATED` para qualquer mecanismo automático de recuperação de tokens (nenhum foi construído; toda correção usa o override já existente `protect_from_region_membership`).
- **Readiness:** `NOT_READY_FOR_2008_ENGINEERING_TEST` — 72/77 verified, gold maturity=provisional, blockers estruturais remanescentes (Q8/Q38/Q55 excluídas, Q45 e D40 com blockers próprios, D09/D10/D59 com padrões de resposta ausentes, Q23 com vazamento cosmético).

Nenhuma classificação usa `READY`/sucesso pleno; o resultado é honesto e parcial.

## B. Estado Git inicial

Branch `feat/enade-2008-cc-b-pilot`. HEAD inicial: `490d1e1` (Fase 3P, commitada por processo externo a esta sessão entre as fases, confirmado via `git log`). `master`/`origin/master`: `a5dfaab`, inalterados do início ao fim desta fase. Nenhum commit, push, PR, merge ou tag foi criado. Working tree ao final: 9 arquivos modificados + 1 novo (ver Seção Y), nenhum scratch script remanescente. Confirmada a presença de todas as mudanças acumuladas das Fases 3G-3P: `alternative_content_assignment.py`, `same_row_ordering.py`, `reading_zones.py`, os 26 overrides `protect_from_region_membership` da Fase 3O, os testes permanentes dos contraexemplos, e `docs/phase-3p-report.md`.

## C. Baseline

```text
tests = 740 (após adicionar 1 teste antes de qualquer mudança de dado; 739 confirmados
  imediatamente ao iniciar a fase, correspondendo exatamente ao relatado pela Fase 3P)
published = 77
visual_passed = 74
visual_failed = 3 (Q07 já resolvida na Fase 3P; os 3 reprovados eram Q24, Q45, D40)
not_performed = 0
gold 2008-b: 71/77 verified, maturity=provisional
overrides: 57 (26 com evidência apontando para a Fase 3O)
288 arquivos protegidos: confirmados via test_protected_corpus.py (4 testes, passam)
```

Todos os valores foram lidos diretamente dos manifests reais e confirmados por execução real de `pytest`/`enade verify-gold`/`enade assess-readiness` no início da fase — não presumidos do resumo da fase anterior. Nota: os comandos literais `enade verify-gold --year 2008 --course ciencia-da-computacao-bacharelado` do prompt não se aplicam a este projeto (2008 é um caderno unificado, `--course all-computing`, nunca dividido por curso como 2021) - o comando real equivalente foi usado em todo lugar. Nota adicional: os três cursos de 2021 têm, cada um, 40 questões publicadas (não 35 como relatado por engano na Fase 3P para CC-licenciatura/Sistemas de Informação) - confirmado via `enade audit-extraction` real; total de 2021 = 120 questões, não 110.

## D. Escopo

Trabalho exclusivo em Q24 (marcadores "I"/"II" ausentes) e Q45 (caractere ausente + nuance de mesma linha). D40 permanece inteiramente fora do escopo — seu vazamento cosmético "F" (documentado desde a Fase 3G) pertence a um mecanismo diferente (rótulo de diagrama, não token/marcador ausente) e não foi tocado, alterado, reauditado ou promovido nesta fase. Confirmado: `git diff` em `enade-2008-computing-d40.md` está vazio; seus três blockers permanecem exatamente nos mesmos status; seu visual audit permanece `failed`.

## E. Metodologia documental

Para cada token investigado, evidência de baixo nível foi coletada via `page.get_text("rawdict")` (spans/chars individuais, bbox, fonte, tamanho, flags), `page.get_texttrace()` (charcode, glyph_id, origin exato por caractere), `page.get_fonts(full=True)` (nome interno, encoding, xref) e, quando necessário, `doc.extract_font(xref)` (fingerprint SHA-256 do arquivo de fonte real). `page.get_drawings()` e `page.get_images(full=True)` foram usados para confirmar ou descartar conteúdo vetorial/imagem quando a camada textual não continha o token esperado. Nenhum backend externo (Poppler, OCR) foi necessário — toda identidade foi resolvida com PyMuPDF sozinho, já que nenhum caso encontrado envolveu fonte sem `ToUnicode`/encoding customizado.

## F. Token ledger

Criado `data/manifests/source-token-ledger-2008.yaml` (schema_version 1), com 3 entradas: `q24-item-marker-I`, `q24-item-marker-II` (ambos `extraction_status: raw_text_verified`) e `q45-item-iii-function-formula` (`extraction_status: drawing_verified`, `visual_fallback` apontando para o `figure-01.png` já publicado, que já cobre visualmente a mesma área). Nenhuma estrutura pré-existente representava esse nível de evidência (o blocker ledger documenta causas narrativas; `layout-overrides.yaml` documenta onde/por que um override existe, não a identidade de baixo nível do glifo em si) - a criação de uma nova estrutura foi, portanto, justificada pela Seção 8 regra 7 do próprio prompt.

## G. Q24 — diagnóstico

Reconstrução completa do caminho (Seção 6):

1. **PDF source / raw chars/spans:** "I" (charcode 73, glyph_id 35), "II" (dois chars, ambos charcode 73/glyph 35) e "III" (três chars, mesmo charcode/glyph) - todos na fonte `PKFJJH+TT2EC3o00` (WinAnsiEncoding, sem CMap customizado), confirmados via rawdict e texttrace.
2. **Extracted lines:** todos os três sobrevivem a `extract_page_lines` (com `fragment_reconstruction_gate=True`, igual ao pipeline real) como `Line` objects corretos, sem `fragment_merges`.
3. **Normalization:** `is_chrome_line("i")`/`is_chrome_line("ii")` retornam `False` (nenhum padrão de `_CHROME_REGEXES`/`_EXACT_CHROME_LINES` casa).
4. **Fragment reconstruction / same-row ordering:** ambos entram e saem de `_apply_same_row_ordering` inalterados (sem notas).
5. **Question slicing / _canonical_content_lines:** ambos sobrevivem inalterados.
6. **Region membership - primeira divergência real:** `_line_in_region("I", ...)` e `_line_in_region("II", ...)` retornam `True` (excluído) contra a região mesclada de Q24 (`owner=objective-24`, `bbox=(45.2,105.0)-(290.0,522.5)`); `_line_in_region("III", ...)` retorna `False`. Instrumentação direta confirma: `compute_line_region_relation` reporta `state=contained` (intersection_over_line_area ≥ 0.98) para "I"/"II", mas `state=boundary_crossing` para "III" - porque o próprio traço do marcador "III" (3 glifos) começa 1.3-2.8pt mais à esquerda (x0=43.9) que os traços mais estreitos de "I"/"II" (x0=45.2/46.7), o suficiente para cair fora do bbox crescido da região (x0=45.2) em vez de totalmente contido.

**Achado importante:** a própria Fase 3O havia concluído "region-exclusion" como causa DESCARTADA para este defeito - uma conclusão incorreta, obtida por um diagnóstico que chamava `compute_line_region_relation`/`_text_consumption_decision` diretamente, sem passar pelos próprios portões anteriores de `_line_in_region` (o ramo condicional a `contextual_relation_gate` e o teste `_is_marker_at_margin`). A instrumentação direta de `_line_in_region` nesta fase revelou a divergência real.

| Campo | `I` | `II` |
|---|---|---|
| página | 12 | 12 |
| bbox | (46.68,261.61)-(49.44,271.57) | (45.24,348.61)-(50.75,358.57) |
| fonte | PKFJJH+TT2EC3o00 | PKFJJH+TT2EC3o00 |
| charcode | 73 | 73, 73 |
| glyph ID | 35 | 35, 35 |
| Unicode bruto | "I" | "II" |
| backend | pymupdf rawdict+texttrace | pymupdf rawdict+texttrace |
| primeiro estágio divergente | region_membership | region_membership |
| representação visual | figure-01.png (já mostra o circuito I) | figure-01.png (já mostra o circuito II) |
| solução | override `protect_from_region_membership` | override `protect_from_region_membership` |
| validação | reviewed | reviewed |

## H. Q24 — correção

Nível 4 da hierarquia (override documental hash+bbox-locked) — nenhuma correção geral, regra de perfil ou glyph mapping foi necessária, já que a identidade textual nunca foi ambígua (nível 3 do prompt não se aplica). Dois novos overrides `protect_from_region_membership` em `data/manifests/layout-overrides.yaml`, hash-locked ao PDF real, bbox exato de cada marcador. Nenhuma mudança em detecção de região, merge, crescimento ou crop. Resultado visual confirmado diretamente contra `figure-01.png`: os três circuitos I/II/III (cada um com sua própria função lógica f(A,B)) já estavam corretamente representados na imagem; o texto agora nomeia os três itens na ordem correta, imediatamente antes de "Assinale a opção correta." `figure-01.png` permanece byte-idêntico.

## I. Item markers

Nenhuma estrutura `item_group` nova foi necessária — os marcadores "I"/"II"/"III" já eram corretamente identificados como tal pela extração (survivendo a `extract_page_lines`, nunca confundidos com alternativas A-E, já que `_ALTERNATIVE_LINE_RE`/`_ORPHAN_MARKER_RE` só casam letras A-E). O problema nunca foi de identificação de marcador - foi de exclusão por região, uma camada completamente posterior e não relacionada. Contraexemplos formais (`_ALTERNATIVE_LINE_RE.match` para variável de código, célula de tabela) confirmados via teste unitário reaproveitado da Fase 3P (`test_alternative_content_assignment.py`), sem necessidade de novos testes específicos de item markers - a distinção "I"/"II"/"III" vs. "A"-"E" já é estrutural e testada.

## J. Checkpoint pós-Q24

Executado antes de iniciar Q45 (Seção 13): `pytest` (740 testes, todos passando), `ruff check .` (limpo), `ruff format --check .` (limpo), `mypy src` (limpo), `enade validate-schema` (13/13), `enade validate-manifest` (OK), `enade audit-extraction` (77/77). Regeneração completa de 2008-b (77 questões) comparada byte a byte contra o publicado: apenas `enade-2008-computing-q24.md` difere (a mudança documental esperada); todas as demais 76 questões e todos os 49 assets PNG do caderno permanecem byte-idênticos. Nenhuma investigação adicional foi necessária.

## K. Q45 — diagnóstico

Q45's próprio item III, após a correção de items I/II na Fase 3O, permanecia truncado em "...pela rotação em" (faltando 3 linhas inteiras, não apenas "um caractere" como a Fase 3O havia caracterizado). Reconstrução do caminho: as 3 linhas ("torno do eixo x da região do plano delimitada pelo", "eixo x, o gráfico de", "e as retas x = 0 e x = 2.") sobrevivem a todos os estágios (extração, normalização, same-row ordering, canonical content lines) e divergem exatamente no mesmo estágio que Q24: `_line_in_region` as exclui contra a região mesclada de Q45 (`owner=objective-45`, `bbox=(318.6,168.5)-(559.2,493.3)`), `state=contained` para as três, mesmo mecanismo (crescimento da região por absorção de rótulos não relacionados, alcançando y1=493.3 muito além do seu próprio raw_bbox y1=449.9). Identidade textual das três linhas confirmada 100% sem ambiguidade via rawdict/texttrace - nenhuma fonte customizada envolvida.

O verdadeiro "caractere ausente" da Fase 3O é, na realidade, um **desenho vetorial**, não um caractere: `page.get_drawings()` reporta 9 elementos de caminho (curvas de Bézier cúbicas e segmentos de linha) preenchendo exatamente o intervalo x=406.7-442.9, y=481.9-493.4 - entre "o gráfico de" (termina x1=405.0) e "e as retas x = 0 e x = 2." (começa x0=444.0), ambas na mesma linha (y0=483.3). `page.get_text("rawdict")`/`get_texttrace()` não reportam nenhum span/char nesse intervalo. Inspeção visual direta de `figure-01.png` (que já cobre essa região da página) confirma que o desenho é a fórmula "f(x) = √x".

## L. Q45 — nuance de mesma linha

Investigação da relação `SameRowRelation` (Fase 3N) para o par "então"/"para ci...": ambos os spans compartilham `origin.y = 440.04` (idêntico até a última casa decimal reportada), confirmando que estão fisicamente na mesma linha impressa, na mesma ordem em que já aparecem no texto extraído (`então` primeiro, `para ci...` depois). A comparação `bbox.y0` vs. `origin.y` (exigida pela Seção 15) mostra: `bbox.y0=432.37` para ambos os spans, mas o `origin.y` (a baseline real) é o dado que importa, e ele é idêntico. **Conclusão: não há defeito de ordenação aqui.** A caracterização da Fase 3O ("entao" lendo fora de ordem) estava ela mesma equivocada - confirmado por evidência de baixo nível, não presumido. Nenhuma alteração em `same_row_ordering.py` foi feita ou necessária; os dois sintomas de Q45 documentados na Fase 3O eram, na realidade, um mecanismo real (as 3 linhas ausentes) e um nãodefeito (a suposta nuance de ordem).

## M. Q45 — correção

Três novos overrides `protect_from_region_membership` (mesmo nível 4 da hierarquia, mesma justificativa que Q24) restauram as 3 linhas ausentes do item III. O gap da fórmula "f(x) = √x" **não foi preenchido** - nenhum caractere foi inventado, seguindo estritamente a Seção 5/17 do prompt: a identidade exata da fórmula (embora visualmente muito provável de ser "f(x) = √x", dado o contexto) nunca foi comprovada por evidência textual (é desenho, não texto), e um fallback visual completo já existe (a mesma imagem `figure-01.png` já publicada cobre essa área). Novo blocker `q45-item-iii-formula-image-gap` documenta esse resíduo explicitamente, com o token correspondente no ledger (`extraction_status: drawing_verified`). Q45 permanece `failed`.

## N. Font fingerprints

Único fingerprint relevante nesta fase: `PKFJJH+TT2EC3o00`, CFF/Type1, 12043 bytes, SHA-256 `343d7586022dff8987613f327f457dbfc4c8cad430d340b0fe4d6fda949d0980`, WinAnsiEncoding padrão (sem CMap customizado) - usado pelos marcadores I/II/III de Q24. Nenhum glyph mapping restrito por fingerprint foi necessário (nível 3 da hierarquia nunca foi acionado): a fonte usa encoding padrão, então o charcode 73 já mapeia para "I" sem qualquer tabela adicional. Q45's próprio gap não envolve fonte alguma (é desenho vetorial puro), então nenhum fingerprint de fonte se aplica a ele.

## O. Fallbacks visuais

Um fallback visual foi **identificado como já existente e suficiente**, não criado do zero: o gap de Q45 (`f(x) = √x`) já está coberto pela imagem `figure-01.png` já publicada, cujo crop já inclui essa área da página (a fórmula é visualmente legível na imagem, como confirmado por inspeção direta). Nenhum novo asset foi necessário. Nenhum fallback foi dispensado (nenhum caso exigiu um e não recebeu).

## P. Shadow mode

Cada uma das duas correções (Q24, Q45) foi validada por regeneração completa e comparação byte a byte contra o corpus publicado ANTES de qualquer publicação - a metodologia usada nas Fases 3O/3P, aplicada aqui igualmente. Resultado: **true positive** único em cada rodada (apenas a questão-alvo muda); **zero false positives** (nenhuma outra questão, em 2008-b, 2011 ou nos três cursos de 2021, muda); nenhum caso ambíguo encontrado (as duas correções, ao contrário da Fase 3P, não precisaram de uma condição de segurança adicional tipo "move-se para trás" - a evidência geométrica, `state=contained` vs. `boundary_crossing`, já discrimina corretamente sem risco demonstrado). Nenhuma regra foi ativada corpus-wide - ambos os overrides são hash+bbox-locked, aplicáveis somente às linhas exatas documentadas.

## Q. Contraexemplos

| caso | resultado |
|---|---|
| Q07 (Fase 3P) | `test_q07_alternative_e_is_no_longer_contaminated_by_the_chart_citation` - passa, inalterado |
| Q64 (Fase 3P) | regenerado, byte-idêntico ao publicado |
| Q01 (Fase 3O) | `test_q01_multi_caption_page_is_not_regressed_by_font_size_gate` - passa |
| Q73 (Fase 3O) | `test_q73_neighboring_question_paragraph_is_not_regressed` - passa |
| Q33 (Fase 3N) | regenerado, byte-idêntico ao publicado |
| D40 | regenerado, byte-idêntico ao publicado; blockers/visual audit inalterados (Seção D) |
| 2011 Q23 | regenerado, byte-idêntico ao publicado (confirmado nas duas checagens de shadow-mode) |
| 2021 SI Q33 | regenerado, byte-idêntico ao publicado |
| Todos os casos das Fases 3L-3P | cobertos pela suíte completa `test_extraction_pipeline_2008.py` (43 testes), todos passando sem modificação além dos 3 testes novos/atualizados desta fase |

## R. Overrides

Os 26 overrides da Fase 3O permanecem **byte-idênticos** (confirmado: nenhuma entrada existente foi editada; apenas 5 novas entradas foram anexadas - 2 para Q24, 3 para Q45). Total de overrides: 57 → 62. Todas as novas entradas seguem o padrão hash+bbox-locked já estabelecido, com `question_id`, `reason`, `evidence` (apontando para este relatório e para o token ledger) e `status: reviewed`. Nenhum override existente teve suas coordenadas, efeitos ou status alterados.

## S. D40

Confirmado explicitamente: `git diff --stat data/questions/2008/all-computing/enade-2008-computing-d40.md` retorna vazio (nenhuma mudança). Seus três blockers (`d40-section-transition-chrome-bleed`, `d40-table-reading-order-scramble`, `d40-region-merge-content-loss`) permanecem exatamente com os mesmos status de antes desta fase. Seu `visual_validation` permanece `failed`. D40 serviu como controle de não regressão passivo (nunca lido nem escrito por nenhum script desta fase).

## T. Auditoria visual

```text
published = 77
visual_passed = 75 (era 74; +Q24)
visual_failed = 2 (Q45, D40)
visual_not_performed = 0
```

Reinspecionadas: Q24 (promovida, `passed`), Q45 (permanece `failed`, notas atualizadas com o achado do desenho vetorial e a correção do "então"). D40 preservada sem reauditoria (output byte-idêntico). Nenhuma promoção em massa - cada mudança de status foi individualmente justificada por comparação visual direta contra o PDF/PNG real.

## U. Blocker ledger

| id | status antes | status depois |
|---|---|---|
| `q24-region-merge-content-loss` | open | resolved |
| `q24-item-i-ii-markers-missing` | open | resolved |
| `q45-region-merge-content-loss` | open | open (residual reclassificado, não fechado) |
| `q45-item-iii-formula-image-gap` (novo) | — | open |

Total de blockers: 58 → 59. Blockers abertos: 10 → 9 (Q24's 2 resolvidos, Q45 ganha 1 novo mas mantém o antigo aberto com escopo reduzido - efeito líquido -1). Cada blocker resolvido possui causa, solução, evidência, testes e arquivos afetados documentados; nenhum histórico foi apagado (as descrições anteriores, incluindo os enganos da Fase 3O já identificados, foram preservadas e corrigidas in-line, nunca removidas silenciosamente).

## V. Gold e readiness

```text
gold-2008-computing.json: 72/77 verified (era 71/77), maturity=provisional
readiness: NOT_READY_FOR_2008_ENGINEERING_TEST (inalterado - correto, pois
  ainda há blockers estruturais: Q8/Q38/Q55 excluídas, D09/D10 sem padrão
  de resposta, D59 com padrão apenas em imagem, Q23 com vazamento
  cosmético, Q45/D40 com blockers próprios)
```

D09/D59 continuam com a distinção já documentada (fidelidade visual vs. ausência de padrão de resposta no PDF) - nenhuma mudança. Q8/Q38/Q55 permanecem fora desta fase, exatamente como determinado.

## W. Proteção de 2011/2021

`test_protected_corpus.py` (4 testes, 288 arquivos) - passa, hashes inalterados. Regeneração completa e independente de 2011 (55 questões) e dos três cursos de 2021 (120 questões: 40+40+40, não 110/35+35 como a Fase 3P relatou por engano) - `0 mismatches, 0 missing` em ambas as checagens de shadow-mode (pós-Q24 e pós-Q45). `enade verify-gold`/`enade assess-readiness` para 2011 e 2021 CC-bacharelado: idênticos ao estado anterior à fase (`READY_FOR_LEGACY_LAYOUT_TEST`, `READY_FOR_2011` respectivamente - rótulos de convenção pré-existente do projeto). CC-licenciatura e Sistemas de Informação continuam sem gold manifest travado (estado pré-existente, não uma lacuna desta fase).

## X. Testes e quality gates

- Testes: 739 (baseline real, confirmado por execução) → 740 (após Q24) → 741 (após Q45). Todos passando em cada checkpoint, duração ~5 minutos por execução completa.
- `ruff check .`/`ruff format --check .`: limpos (409 arquivos formatados) após remoção dos scripts de diagnóstico temporários.
- `mypy src`: limpo (60 arquivos).
- `enade validate-schema`: 13/13. `enade validate-manifest`: OK, 0 avisos.
- `enade audit-extraction`: 77/77 (2008), 55/55 (2011), 40/40 × 3 (2021).
- Nenhuma falha, nenhum warning inesperado, nenhum skip além dos já esperados (corpus real não clonado em CI, não aplicável aqui).

## Y. Reprodutibilidade e Git final

Duas extrações limpas e independentes de 2008-b (run A, run B), cada uma em diretório temporário próprio, comparadas entre si e contra o corpus publicado: **77 arquivos idênticos em run A, 77 em run B, 0 diferenças A≠B, 0 diferenças A≠publicado**. Reprodutibilidade confirmada.

**Arquivos novos:** `data/manifests/source-token-ledger-2008.yaml`, `docs/phase-3q-report.md`.
**Arquivos modificados:** `data/manifests/{blocker-ledger-2008.yaml, extraction-audit-2008-computing.{csv,json}, extraction-capabilities.json, gold-2008-computing.json, layout-overrides.yaml, visual-audit-2008-computing.json}`, `data/questions/2008/all-computing/{enade-2008-computing-q24.md, enade-2008-computing-q45.md}`, `tests/test_extraction_pipeline_2008.py`.
**Arquivos removidos:** nenhum de produção. Scripts de diagnóstico temporários (`diag_q24_forensic.py`, `diag_q24_pipeline_trace.py`, `diag_q45_pipeline_trace.py`, `diag_full_shadow_scan.py`, `diag_reproducibility_check.py`), todos apagados antes do fim da fase.
**Nenhum código-fonte (`src/`) foi alterado nesta fase** - toda correção usa o mecanismo de override já existente, sem ampliar o raio de mudança do extrator, exatamente como o título da fase pede.

Git: nenhum commit, push, PR, merge ou tag. `master`/`origin/master` inalterados (`a5dfaab`). Branch de trabalho: `feat/enade-2008-cc-b-pilot`, HEAD ainda em `490d1e1` (o commit da Fase 3P) ao final desta sessão.

## Recomendação

Q24 está integralmente resolvida. Q45 permanece parcialmente resolvida, com um resíduo genuíno (fórmula vetorial não recuperável como texto) que exigiria, para ser fechado com fidelidade completa, um mecanismo de renderização de asset dedicado para desenhos vetoriais inline pequenos - fora do escopo desta fase ("sem ampliar o raio de mudança do extrator"). Recomenda-se:

- uma **Fase 3R** dedicada ao artefato cosmético "F" de D40 (não iniciada nesta fase);
- uma fase futura, escopada especificamente para renderização de fórmulas vetoriais inline (generalizando o mecanismo já existente de `is_small_formula`/`_is_small_formula_candidate` para desenhos vetoriais como o de Q45, não apenas imagens raster), antes de tentar fechar `q45-item-iii-formula-image-gap` com fidelidade textual completa;
- não iniciar Q8/Q38/Q55 nem processar o bundle `e` ou qualquer prova inédita;
- antes de validação cega em prova inédita, considerar uma fase para reduzir/generalizar os agora 31 overrides específicos de 2008-b introduzidos entre as Fases 3O-3Q, já que cada um documenta uma instância do mesmo mecanismo geral (região crescida por absorção de rótulo capturando conteúdo genuíno não relacionado).

Menor próximo trabalho, caso se queira insistir em Q45: implementar uma extensão do mecanismo de "small formula" (figures.py) para reconhecer clusters de desenho vetorial pequenos e legíveis como candidatos a asset dedicado, com seu próprio crop - permitindo que "f(x) = √x" seja, no mínimo, exibido como uma imagem inline própria (não apenas parte do crop maior de figure-01.png), sem nunca convertê-lo em texto adivinhado.
