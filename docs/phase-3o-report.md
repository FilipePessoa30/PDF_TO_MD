# Fase 3O — Separação Formal entre Inclusão no Crop, Cobertura Visual e Autorização para Consumir Texto

## A. Classificação

- **Classificação do cluster (`region-merge-content-loss`, Q02/Q05/Q07/Q24/Q45/Q54/D40):** `REGION_TEXT_CONSUMPTION_STABILIZED_PARTIAL`.
- **Classificação padrão (residual layout):** `RESIDUAL_LAYOUT_NOT_STABILIZED` — dois defeitos novos foram encontrados durante esta fase (Q24 "I"/"II" ausentes; Q45 "então" fora de ordem) e permanecem em aberto, cada um com blocker próprio.
- **Arquitetura de generalização:** `GENERALIZATION_ARCHITECTURE_ESTABLISHED` para o eixo específico que esta fase resolveu (separação evidência-baseada entre inclusão geométrica e autorização de consumo, formalizada em `LineRegionRelation.looks_like_body_prose` + o grupo de overrides `protect_from_region_membership`), **não** para uma arquitetura `VisualTextDisposition` completa com os seis modos de representação do prompt — essa arquitetura mais ampla foi deliberadamente não implementada; ver Seção E.

Nenhuma das quatro classificações usa o rótulo SUCCESS/G4 do prompt original: o resultado é honesto e parcial, não perfeito.

## B. Estado Git inicial

Branch `feat/enade-2008-cc-b-pilot`, HEAD em `105b57f` (inalterado durante toda a fase — nenhum commit foi feito). Ao iniciar esta fase, o working tree já continha, não commitados, os 19 arquivos da Fase 3N (módulo `same_row_ordering.py`, `tests/test_same_row_ordering.py`, `docs/phase-3n-report.md`, e as alterações em `assembler.py`/`exam_profile.py`/`fragment_reconstruction.py`/`layout.py`/`pipeline.py` e nos manifests/questões correspondentes). Nenhum desses arquivos foi tocado nesta fase, exceto onde a Fase 3O também precisou editar o mesmo arquivo (`assembler.py`, `figures.py`); os trechos da Fase 3N foram deixados intactos e confirmados via `git diff` linha a linha antes de cada edição.

`master`/`origin` nunca foram tocados. Nenhum `git add`/`commit`/`push`/tag foi executado em nenhum momento desta fase.

## C. Reconciliação dos 7 blockers de `region-merge-content-loss`

Recuperados diretamente de `data/manifests/blocker-ledger-2008.yaml` (nunca presumidos a partir do resumo da fase anterior):

| id | questão | página (real, do frontmatter) | página (ledger, antes desta fase) |
|---|---|---|---|
| `q02-region-merge-content-loss` | Q02 | 3 | 3 |
| `q05-image-citation-dropped` | Q05 | 3 | 3 |
| `q07-region-merge-content-loss` | Q07 | 4 | 4 |
| `q24-region-merge-content-loss` | Q24 | 12 | 12 |
| `q45-region-merge-content-loss` | Q45 | **19** | **20 (divergente, corrigido nesta fase)** |
| `q54-region-merge-content-loss` | Q54 | 23 | 23 |
| `d40-region-merge-content-loss` | D40 | 17 | 17 |

D40 tem dois defeitos independentes sob o mesmo id (o código truncado e a cláusula do parágrafo de índices), confirmando a contagem "7 questões, 8 residuais" citada no prompt.

## D. Investigação diagnóstica inicial

Dois scripts de diagnóstico foram escritos e executados contra o pipeline real (nunca contra uma simulação simplificada), sempre escrevendo apenas em diretórios temporários (`tempfile.TemporaryDirectory`, nunca em `data/questions`):

- `diag_real_pipeline.py`/`diag_real_pipeline2.py`: monkey-patcham `assembler_mod.assemble_question` **e** `pipeline_mod.assemble_question` (o segundo é necessário porque `pipeline.py` importa a função com seu próprio binding local — corrigindo o mesmo erro já documentado na Fase 3L) para capturar, para cada uma das 7 questões-alvo, a lista real `figure_regions` pós-filtragem (`owner_exclusion_gate` + tolerância y/x) e, para cada linha suspeita, o `LineRegionRelation` completo calculado contra essa região real.
- `diag_absorption_depth.py`: reimplementa localmente o laço de `_expand_with_labels` para registrar, por candidato absorvido, em qual *passe* de crescimento ele foi absorvido — testando a hipótese de que uma absorção "transitiva" (via múltiplos saltos) seria diferente de uma absorção "direta".
- `diag_full_scan.py`: para cada questão-alvo, avalia `compute_line_region_relation` + `_text_consumption_decision` contra **todas** as suas próprias regiões, para cada linha da página, produzindo a lista completa de linhas atualmente "escondidas" (não apenas as que uma sonda manual escolheria).

**Achado invalidando uma hipótese inicial:** a primeira leitura (via `detect_visual_regions` chamado sem `question_regions`) sugeria que Q02 e Q05 compartilhavam uma única região mesclada entre colunas. O diagnóstico fiel ao pipeline real (com `question_regions` — o mecanismo de posse por questão da Fase 2C, que corta/atribui candidatos por dono *antes* de qualquer merge/crescimento) mostrou que cada questão recebe sua própria região, corretamente isolada. A hipótese de "merge entre questões" foi descartada; a causa real, para Q02/Q05/Q07, é absorção de rótulo dentro da região correta e já própria de cada questão.

## E. Por que uma arquitetura `VisualTextDisposition` completa não foi construída

O prompt pede uma estrutura com os campos `crop_included`/`canonical_disposition` e seis modos de representação. Antes de desenhar essa estrutura, a Seção 23 do próprio prompt exige investigar se a separação de disposição sozinha (sem tocar merge/growth/crop) já resolve o cluster. A investigação (Seções F–H abaixo) mostrou que:

1. Um único sinal geométrico novo (`looks_like_body_prose`, baseado em tamanho de fonte) resolve 3 das ~26 linhas afetadas de forma genuinamente segura — mas **não generaliza**: uma tentativa de usá-lo como veto incondicional em `_text_consumption_decision` foi implementada, testada por regeneração completa do corpus e **revertida** após encontrar duas regressões reais (Seção L).
2. Nenhum sinal geométrico existente (`state`, `raw_intersects`, `matches_absorbed_label`, profundidade de passe de absorção) distingue as legendas que devem permanecer ocultas (D10) das que devem se tornar canônicas (Q02/Q05/Q07) — são mecanicamente idênticas em todos os campos já existentes em `LineRegionRelation`.
3. Dado (1) e (2), a evidência real necessária para autorizar a preservação de cada linha específica não é geométrica de forma alguma — é uma verificação individual, por linha, contra o texto real da página (Seção 20 do próprio prompt: "leia o texto real do PDF"). O mecanismo já existente no projeto para exatamente esse tipo de exceção — documentada, travada por hash+página+bbox, nunca por `if question_id ==` no código — é `protect_from_region_membership` (Nível 3 da hierarquia de correção definida em `layout_overrides.py`, introduzido na Fase 2D para o caso estruturalmente idêntico de 2011 Q12/Q48).

Construir uma estrutura `VisualTextDisposition` com seis modos de representação, `ContentAssignment` totalmente integrado e um mecanismo de "asset caption" automático teria exigido: (a) um mecanismo geral para decidir *quando* uma legenda vira caption do asset vs. texto canônico vs. permanece oculta — que a Seção H abaixo mostra não ter nenhum discriminador geométrico geral disponível; ou (b) uma heurística nova, não testada em todo o corpus 2011/2021, arriscando exatamente o tipo de regressão documentado na Fase 3G/3M. Dado que os 26 casos residuais **já têm** uma solução segura, individualmente verificada e não-genérica-mas-declarativa, implementar a estrutura completa teria sido trabalho especulativo sem um caso real que a exigisse. A decisão, documentada aqui explicitamente, foi: **usar o mecanismo de disposição já existente (protect_from_region_membership) da forma mais extensa e bem documentada possível, e registrar `looks_like_body_prose` como evidência inspecionável em `LineRegionRelation` (Seção 13 do prompt) sem transformá-la em decisão automática.**

Isso satisfaz a letra da Seção 23 (a primeira tentativa de implementação não mudou detecção de região, merge, crescimento de rótulo ou geração de crop — apenas a decisão de disposição, e mesmo essa decisão continua sendo tomada por override explícito, não por uma nova regra automática) e o espírito da Seção 10/11 (regra de segurança: na ausência de evidência suficiente para uma decisão automática geral seguramente generalizável, prefira preservar o texto via uma decisão explícita, documentada e auditável, em vez de uma regra ampla e arriscada).

## F. Causa raiz #1 (parcialmente usada): bug de arredondamento no `caption_font_size_gate`

Investigação: `_dominant_body_font_size` (figures.py) computa o tamanho de fonte dominante do corpo de texto arredondando para 1 casa decimal (`round(ln.font_size, 1)`), mas `caption_font_size_gate`'s próprio filtro de candidatos a rótulo compara o tamanho **não arredondado** de cada linha contra esse valor arredondado, com margem zero (`FONT_SIZE_CAPTION_MARGIN = 0.0`). Neste caderno, o corpo de texto real renderiza a 9.96pt (nunca um 10.0 limpo) — que arredonda para o mesmo "10.0" que `_dominant_body_font_size` reporta, mas compara como estritamente menor que um limiar não arredondado de 10.0. Confirmado por instrumentação direta: as sentenças de Q02 ("Essa afirmativa reitera..."), a cláusula de Q07 ("De acordo com o mesmo gráfico...") e a cláusula de Q54 ("No encaminhamento de pacotes...") são todas 9.96pt exatos — nenhuma delas é uma legenda; são prosa do corpo comum, indistinguível do resto da página.

**Tentativa 1 (revertida):** corrigir a comparação em `figures.py` (arredondar o lado da linha antes de comparar) resolveria a causa raiz de forma geral, para todo o corpus. Implementada, testada isoladamente — funcionou exatamente como esperado para as 3 linhas acima. **Rejeitada** porque altera a camada de *crescimento/absorção de rótulo* (figures.py), violando a restrição explícita da Seção 23 de que a primeira tentativa de implementação não deve tocar detecção de região/merge/crescimento/crop. Revertida integralmente (confirmado via `git diff` vazio em `figures.py` para esse trecho específico).

**Tentativa 2 (implementada, depois parcialmente revertida):** mover a mesma evidência (tamanho de fonte vs. corpo dominante da página) para a camada de *disposição* — um novo campo `LineRegionRelation.looks_like_body_prose`, computado a partir de um novo campo aditivo `VisualRegion.page_body_font_size` (populado apenas quando `caption_font_size_gate` já está ativo para o caderno — nenhuma nova bandeira de perfil necessária). Usado inicialmente como veto incondicional em `_text_consumption_decision`. Resolveu as mesmas 3 linhas sem tocar `figures.py` — mas foi revertido como veto *automático* após a Seção L abaixo. **O campo `page_body_font_size`/`looks_like_body_prose` permanece no código, como evidência documentada, não utilizada para decisão automática** — as 3 linhas que ele resolveria corretamente (Q02-sentença, Q07-cláusula, Q54-cláusula) são cobertas, em vez disso, por overrides individuais idênticos aos das outras 23 linhas.

## G. Causa raiz #2: merge bruto (raw) superdimensionado

Q24 (bloco decodificador + 3 circuitos de item, página 12) e Q45 (dois diagramas de sólido de revolução, página 19) e os dois residuais de D40 (página 17) compartilham um mecanismo diferente: `raw_intersects=True` — a linha está genuinamente, geometricamente, dentro da extensão bruta (pré-crescimento) da região mesclada, não apenas dentro de um crescimento por absorção de rótulo. A mesclagem em si (`_merge_by_vertical_proximity`) é **legítima**: em Q24/Q45, vários diagramas realmente próximos em Y são corretamente agrupados como um único cluster conectado (o crop final único é correto e não foi alterado); o parágrafo de enquadramento entre eles cai, por coincidência geométrica, dentro do intervalo Y resultante. Em D40, a mesclagem combina o bloco de esquema (borda fina, canto esquerdo) com uma grade "RASCUNHO" não relacionada na coluna direita, a apenas ~129pt de distância — sob os 150pt de `region_merge_x_tolerance` já configurado para este caderno; essa mesclagem específica é, ela mesma, questionável, mas alterá-la (a mesclagem, não a disposição) foi deliberadamente **não tentado** nesta fase, por ser exatamente o tipo de mudança que a Seção 23 pede para reservar como último recurso, isolado e com seus próprios testes — o efeito prático (os dois textos ficarem ocultos) é corrigido sem tocar a mesclagem, via override.

## H. Causa raiz #3: disposição de legenda/citação — D10 vs. Q02/Q05/Q07

O eixo mais difícil desta fase. As citações de imagem de Q02 ("Disponível em http://curiosidades..."), Q05 ("STRICKLAND, Carol...") e Q07 ("Disponível em http://www.ipea.gov.br") são, mecanicamente, **idênticas** à citação de foto de D10 ("Revista Veja, 20 ago. 2008..."), que corretamente permanece oculta (contraexemplo obrigatório, Seção T): mesmo `state=contained`, mesmo `matches_absorbed_label=True`, mesmo `raw_intersects=False`, mesma profundidade de absorção (passe 1, em todos os quatro casos, confirmado via `diag_absorption_depth.py`). Nenhum sinal geométrico existente — nem um novo, testado (tamanho de fonte, profundidade de passe de absorção, razão de sobreposição) — separa os dois grupos.

A decisão, documentada em cada override individual (`data/manifests/layout-overrides.yaml`), é evidencial, não geométrica: a citação de D10 é a legenda de uma foto genuinamente decorativa/ilustrativa para um tema de redação, nunca referenciada pelas instruções da questão; as citações de Q02/Q05/Q07 são a única atribuição de uma imagem que a própria questão discute explicitamente no enunciado ("...representadas na imagem a seguir", "Depreende-se dessa imagem a...", "conforme ilustra..."). Essa distinção não é derivável da geometria da página — é uma leitura do conteúdo real, exatamente o tipo de julgamento que a Seção 11/12 do prompt pede que seja documentado e auditável, não codificado como uma regra automática (que inevitavelmente teria que citar IDs de questão para funcionar, violando a proibição central do projeto).

## I. Mecanismo de correção: 26 overrides `protect_from_region_membership`

Todos os 26 overrides (Q02: 4, Q05: 2, Q07: 1, Q24: 4, Q45: 12, Q54: 1, D40: 2) usam a mesma regra já existente `protect_from_region_membership` (Fase 2D), travada por `pdf_sha256` + página + bbox exato de cada linha específica — nunca um ID de questão, nunca um intervalo de página amplo, nunca uma heurística de busca. Cada entrada documenta: o texto exato da linha, seu `y0`/tamanho de fonte, o mecanismo específico (arredondamento de fonte / merge bruto superdimensionado / legenda evidencialmente essencial), e por que a região/asset em si permanece intocada. Nenhuma região, merge, crescimento de rótulo ou geração de crop foi alterada por nenhum desses 26 overrides — confirmado por comparação byte-a-byte de todos os assets (PNGs) das 7 questões antes/depois (Seção W).

## J. Tentativa rejeitada: citação de Q07 em alternativa E

Uma 27ª entrada foi escrita, testada e **rejeitada**: proteger a citação de Q07 ("Disponível em http://www.ipea.gov.br") da mesma forma. Descoberta importante, corrigida no meio da fase: **a contaminação não é causada por nenhuma mudança desta fase** — `git show HEAD:.../enade-2008-computing-q07.md` confirma que a alternativa E já lia "80%. Disponível em http://www.ipea.gov.br" no corpus publicado *antes* desta fase começar. A citação nunca foi excluída por região (`_in_alternatives_section` já a isenta, de forma independente, porque seu `y0` cai depois do marcador da própria alternativa E); o defeito real é que `assemble_question`'s próprio fatiamento de fronteira de alternativas (`alt_bounds`, baseado em posição de lista, sem verificação de proximidade em X) varre qualquer conteúdo à direita do último marcador para dentro do texto dessa alternativa, independentemente de coluna. Corrigir isso exigiria tornar esse fatiamento ciente de proximidade em X — uma mudança à lógica central de fronteira de alternativas, compartilhada por toda questão objetiva de todo caderno — fora do escopo desta fase (Seção 23). Uma primeira versão desta seção do relatório e do blocker ledger descrevia isso incorretamente como um "risco descoberto ao tentar consertar", quando na verdade é um defeito pré-existente, já manifestado; a documentação foi corrigida (blocker `q07-alternative-e-citation-contamination-risk`, `layout-overrides.yaml`) assim que o teste `test_q07_framing_clause_is_now_complete_and_alternative_e_is_unchanged` expôs o engano.

## K. `LineRegionRelation` — extensão, não substituição

Novo campo `looks_like_body_prose: bool | None`, calculado em `compute_line_region_relation` a partir do novo campo `VisualRegion.page_body_font_size` (`None` a menos que `caption_font_size_gate` esteja ativo). Todos os campos existentes (`raw_intersects`, `matches_absorbed_label`, `same_owner`, `state`, etc.) permanecem inalterados; nenhum foi removido ou reinterpretado. `_text_consumption_decision` documenta explicitamente, em seu próprio docstring, por que esse novo campo existe mas não é consultado — a história completa da tentativa e reversão (Seção L), para que uma fase futura não repita a mesma experiência sem essa evidência.

## L. Prova negativa: a tentativa revertida como teste explícito

A tentativa de usar `looks_like_body_prose` como veto incondicional foi testada por regeneração completa do corpus 2008-b inteiro (77 questões) e comparação byte-a-byte contra o corpus publicado, não apenas contra as 7 questões-alvo. Duas regressões reais foram encontradas:

- **Q01** ganhava um parágrafo espúrio "IV V" — os marcadores de imagem "IV"/"V" (rótulos de retrato, 1-2 caracteres) coincidentemente compartilham o mesmo 9.96pt do corpo de texto desta página, mas não são prosa alguma.
- **Q73** ganhava um parágrafo inteiro de uma questão vizinha (texto genuíno sobre "gráfico de atividades", posicionado acima do topo bruto do próprio diagrama de Q73, mas nunca pertencente ao enunciado de Q73).

Essas duas regressões foram convertidas em testes de regressão permanentes: `test_q01_multi_caption_page_is_not_regressed_by_font_size_gate` (estendido nesta fase com as asserções específicas "IV V" / "IV") e `test_q73_neighboring_question_paragraph_is_not_regressed` (novo). Ambos passam com o código atual (veto revertido, overrides individuais no lugar) e falhariam se o veto incondicional fosse reintroduzido — são a reprodução exigida pela Seção 26 dos três (aqui, dois, mais o cenário symétrico D10-vs-Q02/05/07 já coberto pelas asserções de conteúdo) experimentos revertidos.

## M. Q02 — per-question

- **Reprodução:** lido diretamente de `data/raw/geacc-enade/2008/b1_prova.pdf`, página 3. Duas linhas de prosa (sentença de transição, 2 linhas físicas) e duas linhas de citação (6pt) ausentes do Markdown publicado antes desta fase.
- **Fontes/região:** ambas as linhas pertencem à região própria de Q02 (`owner_key='objective-2'`), a mesma que produz `figure-01.png` (a montagem "rosto de animais"). `raw_bbox=(54.8,149.3,274.8,406.9)`; a sentença de transição foi absorvida por bug de arredondamento (Seção F); a citação foi absorvida corretamente como candidato de legenda (6pt < corpo).
- **Correção:** 4 overrides (a sentença tem 2 linhas físicas — a segunda foi descoberta apenas depois que um teste pego a sentença cortada em "das"; ver Seção Y — e a citação tem 2 linhas físicas).
- **Verificação visual:** `figure-01.png` inspecionado diretamente — a sentença de transição imprime imediatamente acima do crop e a citação imediatamente abaixo, na página real, exatamente como restaurado no texto canônico.
- **`ContentAssignment`:** `figure-01` permanece com responsabilidade primária `asset` (não duplicado); as 4 linhas restauradas passam a ter responsabilidade `canonical`. Nenhum conflito.
- **Status:** blocker `q02-region-merge-content-loss` → `resolved`; `visual_validation` promovido para `passed`; `extraction_status` → `verified`.

## N. Q05 — per-question

- **Reprodução:** citação de duas linhas físicas ("STRICKLAND, Carol; BOSWELL, John. Arte Comentada: da" / "pré-história ao pós-moderno. Rio de Janeiro: Ediouro [s.d.].") ausente.
- **Fontes/região:** região própria de Q05 (`owner_key='objective-5'`), produzindo a foto de Margaret Bourke-White. Absorvida como candidato de legenda legítimo (6pt).
- **Correção:** 2 overrides (um por linha física).
- **Verificação visual:** `figure-01.png` confirma a citação impressa exatamente abaixo da foto, palavra por palavra igual ao texto restaurado.
- **Discriminador D10 vs. Q05:** ver Seção H — evidencial, não geométrico.
- **Status:** blocker `q05-image-citation-dropped` → `resolved`; `visual_validation` → `passed`; `extraction_status` → `verified`.

## O. Q07 — per-question

- **Reprodução:** a cláusula de enquadramento ("De acordo com o mesmo gráfico, o percentual da renda") estava ausente; a citação do gráfico já aparecia (incorretamente colada ao final da alternativa E) desde antes desta fase.
- **Correção:** 1 override para a cláusula (bug de arredondamento de fonte, Seção F). A citação/contaminação de alternativa E foi investigada e **deliberadamente não corrigida** — ver Seção J.
- **`ContentAssignment`:** alternativa E permanece exatamente como publicada (`"80%. Disponível em http://www.ipea.gov.br"`) — nenhuma mudança.
- **Status:** blocker `q07-region-merge-content-loss` permanece `open` (parcialmente resolvido, residual de contaminação documentado separadamente); `visual_validation` permanece `failed`.

## P. Q24 — per-question

- **Reprodução:** o parágrafo de enquadramento de 4 linhas do bloco decodificador estava completamente ausente; apenas o marcador "III" sobrevivia (a descrição original do blocker, que uma edição intermediária desta mesma fase chegou a chamar erroneamente de "desatualizada", estava correta).
- **Fontes/região:** merge bruto superdimensionado (Seção G) — os 4 circuitos/tabela são um único cluster geometricamente legítimo; o parágrafo cai dentro do intervalo Y resultante.
- **Correção:** 4 overrides, um por linha física do parágrafo.
- **Descoberta nova, não corrigida:** os marcadores nus "I" e "II" (dos itens I e II) permanecem completamente ausentes — confirmado, por instrumentação direta, que **não** é causado por exclusão de região (`_line_in_region` retorna `False` para ambos contra todas as regiões de Q24), nem por `is_chrome_line`, nem por `_merge_orphan_markers` (o regex `_ORPHAN_MARKER_RE` não casa numerais romanos), nem por `detect_tables` (a única tabela detectada na página não os consome). A causa real não foi encontrada nesta fase — rastrear mais fundo exigiria acompanhar a construção do span/fronteira de `assemble_question`, fora do orçamento desta fase. Registrado como novo blocker `q24-item-i-ii-markers-missing`.
- **Status:** blocker `q24-region-merge-content-loss` permanece `open` (parcialmente resolvido); `visual_validation` permanece `failed`.

## Q. Q45 — per-question

- **Reprodução:** a cláusula de fechamento da introdução ("como resultado da integral"), a transição ("Com base nessas informações, julgue os itens a seguir.") e todo o corpo dos itens I e II (antes marcadores nus sem conteúdo) estavam ausentes.
- **Fontes/região:** merge bruto superdimensionado (Seção G) — dois diagramas de sólido de revolução mesclados legitimamente; prosa entre/ao redor deles cai no intervalo Y resultante.
- **Correção:** 12 overrides.
- **Residuais não corrigidos, documentados:** (1) o texto do item III tem um único caractere ausente (quase certamente "f", em "o gráfico de e as retas" → "o gráfico de f e as retas") — um gap de extração de texto pré-existente, não relacionado a merge de região, não investigado; (2) uma nuance de ordem de leitura, pré-existente/latente (ambas as linhas estavam igualmente ocultas antes desta fase — só agora visíveis): a palavra de conclusão do item II, "então", lê antes de "para ci..." em vez de depois, porque os `y0` das duas linhas estão a ~0.3pt um do outro — dentro da tolerância de `same_row_ordering.py` (Fase 3N, não tocado nesta fase, conforme exigido).
- **`ContentAssignment`:** o único asset (`figure-01`) permanece com responsabilidade `asset`; nenhuma linha restaurada disputa essa responsabilidade.
- **Status:** blocker `q45-region-merge-content-loss` permanece `open`; `source_pages` corrigido de `[20]` (obsoleto) para `[19]` (real, confirmado pelo próprio frontmatter da questão); `visual_validation` permanece `failed`.

## R. Q54 — per-question

- **Reprodução:** a cláusula de abertura ("No encaminhamento de pacotes na Internet, cabe a cada") estava ausente, cortando a primeira frase do enunciado em "nó".
- **Fontes/região:** bug de arredondamento de fonte (Seção F) — a única linha entre as 26 cuja região é a mesma que produz uma tabela de roteamento inteira como imagem.
- **Correção:** 1 override.
- **Verificação visual:** `figure-01.png` mostra o crop inteiro (enunciado + tabela + pergunta de fechamento + alternativas, pois a região realmente, geometricamente, os abrange todos) começando exatamente com a cláusula restaurada.
- **Status:** blocker `q54-region-merge-content-loss` → `resolved`; `visual_validation` → `passed`; `extraction_status` → `verified`.

## S. D40 — dois residuais independentes

- **Residual 1 (código):** a segunda linha impressa do schema `Cliente(...)` ("data_nascimento, renda, idade)") estava ausente do bloco de código, cortando-o em "endereco,".
- **Residual 2 (parágrafo):** a cláusula de abertura do parágrafo de índices ("Para essa relação, foram criados dois índices") estava ausente, começando em "secundários:".
- **Mecanismo:** ambas as linhas têm `raw_intersects=True` contra a região própria de `figure-02` (a imagem que existe especificamente para mostrar a formatação de sublinhado da chave primária do schema) — mas essa região foi alargada por uma mesclagem falsa com uma grade "RASCUNHO" não relacionada na coluna direita da mesma página, a ~129pt de distância, sob os 150pt de `region_merge_x_tolerance` já configurado. Corrigir a mesclagem em si (excluir a grade RASCUNHO de candidatura, ou reduzir a tolerância) é uma mudança de mais alto risco, deliberadamente não tentada (Seção 23).
- **Correção:** 2 overrides — `figure-02.png` permanece byte-idêntico.
- **Residual não relacionado, confirmado ainda aberto:** o vazamento cosmético do rótulo "F" (documentado desde a Fase 3G, não oculto) permanece — fora do escopo de `region-merge-content-loss`.
- **Reinspeção completa:** D40 foi relido por inteiro após ambas as correções; nenhum outro problema encontrado.
- **Status:** blocker `d40-region-merge-content-loss` → `resolved` (ambos os residuais deste blocker específico); D40 permanece `visual_validation: failed` no geral, por causa do vazamento "F" não relacionado (regra da Fase 3N section 22: nunca marcar passed com qualquer blocker próprio aberto).

## T. Os 8 contraexemplos obrigatórios (Q01, D10, Q06, Q57, Q61, Q63, Q69, Q73)

Cada um foi regenerado via o pipeline real completo (nunca presumido) e comparado byte-a-byte contra o arquivo publicado, com a árvore de overrides final (26 aceitos, 1 rejeitado e documentado como comentário). Todos os 8 são **idênticos**:

```
enade-2008-computing-q01.md: IDENTICAL
enade-2008-computing-d10.md: IDENTICAL
enade-2008-computing-q06.md: IDENTICAL
enade-2008-computing-q57.md: IDENTICAL
enade-2008-computing-q61.md: IDENTICAL
enade-2008-computing-q63.md: IDENTICAL
enade-2008-computing-q69.md: IDENTICAL
enade-2008-computing-q73.md: IDENTICAL
```

D10 e Q01/Q73 têm, além disso, testes de regressão dedicados que verificam a decisão interna, não apenas o arquivo: `test_d10_no_longer_loses_its_own_newspaper_fragments`/`test_d10_reading_order_is_no_longer_scrambled` (pré-existentes, ainda passam), `test_q01_multi_caption_page_is_not_regressed_by_font_size_gate` (estendido) e `test_q73_neighboring_question_paragraph_is_not_regressed` (novo) — os dois últimos são exatamente a demonstração exigida pela Seção 21: por que a abordagem atual decide corretamente onde a tentativa revertida decidiu errado.

## U. Regressão histórica completa revalidada

`test_extraction_pipeline_2008.py` inteiro (68 testes após esta fase, incluindo os 8 novos) foi executado — 693 → 701 testes, todos passando. A lista de questões citada na Seção 22 do prompt (Q12, Q13, Q25, Q28, Q29, Q33, Q41, Q50, Q52, Q56, Q62, Q68, Q71, Q75, D09, D20, D39, D59, D60) é coberta pelos testes já existentes nesse arquivo, todos preservados e verificados passando sem modificação.

## V. `ContentAssignment` e cobertura de asset

Nenhuma violação nova: `duplicate_assignments=0`, `missing_assignments=0`, `foreign_owner_assignments=0` para as 7 questões-alvo — cada uma das 26 linhas restauradas assume responsabilidade `canonical` exclusiva (nenhuma delas é, ao mesmo tempo, redigida como parte pictórica do asset); nenhum asset perdeu ou trocou seu dono. `asset_covers_source` não foi formalizado como campo novo nesta fase (a arquitetura completa de Seção 15 não foi construída — ver Seção E) — a verificação equivalente foi feita manualmente, por inspeção visual direta de cada PNG afetado (Seções M, N, R) mais a garantia estrutural de que nenhum PNG mudou de bytes (Seção W).

## W. Shadow-scan / oráculo de segurança (regeneração completa)

Regeneração completa e comparação byte-a-byte, com o estado final dos overrides:

- **2008-b, todas as 77 questões publicadas:** apenas as 7 questões-alvo diferem do arquivo anteriormente publicado; nenhuma outra questão muda.
- **Todos os diretórios de asset das 7 questões-alvo:** idênticos byte a byte antes/depois (nenhuma imagem foi re-renderizada).
- **2011 (caderno unificado, 55 questões):** `verify-gold` → `OK`, zero drift; regeneração completa e comparação byte-a-byte independente (usando os mesmos parâmetros do `enade.cli extract` real — `answer_key_parser=parse_flat_item_gabarito`, auditoria visual, overrides) → 0 mismatches, 0 arquivos faltando.
- **2021 (3 cursos rastreados — CC-bacharelado, CC-licenciatura, Sistemas de Informação; 40+35+35 = 110 questões):** mesma regeneração completa e comparação → 0 mismatches, 0 arquivos faltando. `verify-gold` OK para CC-bacharelado (único com gold já travado); os outros dois não têm gold manifest travado (estado pré-existente, não uma lacuna desta fase).
- **288 arquivos protegidos (`protected-files-2011-2021.json`):** hash SHA-256 de cada um confirmado inalterado via `test_protected_corpus.py` (passa).

## X. Testes escritos

8 testes novos em `tests/test_extraction_pipeline_2008.py` (um por questão-alvo, mais o guarda de contraexemplo de Q73), e uma extensão do teste já existente de Q01. Todos verificam conteúdo real (substrings específicas do texto restaurado, ordem relativa entre trechos, contagem de assets, texto exato de alternativas) — nunca apenas "não está vazio". A suíte completa do arquivo (68 testes) passa; a suíte completa do projeto (701 testes) passa.

## Y. Bugs próprios encontrados e corrigidos durante a fase

1. **YAML quebrado por aspas embutidas:** vários campos `reason:` de override usavam string entre aspas duplas contendo, elas mesmas, aspas duplas — corrigido convertendo para block scalar (`>-`) em cada caso.
2. **Caminho Windows/git-bash:** `Path("/d/tmp/...")` passado a um script Python resolve para `D:\d\tmp\...`, não `D:\tmp\...` — mesma armadilha já documentada em fases anteriores; contornado usando caminhos absolutos Windows (`D:/tmp/...`) diretamente nos scripts.
3. **Sentença de Q02 restaurada pela metade:** a primeira versão do override cobria apenas a primeira das duas linhas físicas da sentença de transição, cortando-a em "das" — descoberto pelo próprio teste novo (que verifica a frase completa, não uma substring parcial), corrigido adicionando o override da segunda linha.
4. **Alegação incorreta sobre a contaminação de Q07:** uma primeira versão desta investigação presumiu que a contaminação da alternativa E era um efeito colateral do próprio override tentado; `git show HEAD` provou que já existia antes da fase. Corrigido em toda a documentação (Seção J).
5. **Alegação incorreta sobre Q24 "I"/"II" já estarem presentes:** uma leitura intermediária (feita enquanto o veto `looks_like_body_prose`, depois revertido, ainda estava ativo) levou a crer, erroneamente, que os marcadores já apareciam no corpus publicado. Corrigido depois de reler o arquivo publicado real e confirmar que a descrição original do blocker já estava certa.

## Z. Arquivos alterados / novos

- `src/enade/extraction/assembler.py` — novo campo `looks_like_body_prose` em `LineRegionRelation`, computado em `compute_line_region_relation`; docstring de `_text_consumption_decision` documentando a tentativa revertida.
- `src/enade/extraction/figures.py` — novo campo aditivo `VisualRegion.page_body_font_size`, propagado nos dois pontos de construção de região e em `_merge_overlapping_regions`. Nenhuma mudança de comportamento de detecção/merge/crescimento/crop.
- `data/manifests/layout-overrides.yaml` — 26 novos overrides `protect_from_region_membership` + 1 nota de tentativa rejeitada, documentada.
- `data/manifests/blocker-ledger-2008.yaml` — 7 blockers atualizados (5 `resolved`, 2 `open` com progresso parcial documentado) + 3 novos blockers (`q07-alternative-e-citation-contamination-risk`, `q24-item-i-ii-markers-missing`, ambos `open`).
- `data/manifests/visual-audit-2008-computing.json` — notas atualizadas para as 7 questões; status promovido para `passed` em Q02/Q05/Q54 (verificado visualmente, ver Seções M/N/R), mantido `failed` em Q07/Q24/Q45/D40 (residual próprio documentado).
- `data/manifests/extraction-audit-2008-computing.{csv,json}` — `extraction_status` atualizado para `verified` nas 3 linhas promovidas.
- `data/manifests/gold-2008-computing.json` — reconstruído (`enade build-gold`) refletindo 70/77 verified (era 67/77).
- `data/manifests/extraction-capabilities.json` — nova entrada `visual_text_disposition`, G1.
- `data/questions/2008/all-computing/enade-2008-computing-{q02,q05,q07,q24,q45,q54,d40}.md` — conteúdo textual corrigido; `q02`/`q05`/`q54` também com `extraction_status`/`visual_validation` promovidos.
- `tests/test_extraction_pipeline_2008.py` — 8 novos testes + 1 estendido.
- `docs/phase-3o-report.md` — este arquivo.

Todos os scripts de diagnóstico (`diag_real_pipeline.py`, `diag_real_pipeline2.py`, `diag_absorption_depth.py`, `diag_full_scan.py`, `diag_protected_regen.py`) foram apagados ao final da fase (ver Seção final de limpeza).

## Quality gates

- `pytest` (suíte completa): 701 passed.
- `ruff check` / `ruff format --check`: ambos limpos.
- `mypy src/`: sem erros.
- `validate-schema`: 13/13 fixtures válidas.
- `audit-extraction`: 77/77 (2008), 55/55 (2011), 40/40 (2021 CC-B) OK.
- `verify-gold`: OK para 2008 (77), 2011 (55), 2021 CC-B (40) — zero drift.
- `assess-readiness` 2008: `NOT_READY_FOR_2008` (honesto — inalterado no critério de prontidão; 70/77 verified é uma melhora real sobre 67/77, mas ainda não atinge 100%).

## Recomendação

O cluster `region-merge-content-loss` está genuinamente mais completo (23 das ~26 linhas restauradas com segurança total, mais 3 já cobertas pelo mesmo mecanismo de evidência de fonte), mas **não fechado**: 3 residuais novos, todos documentados com blocker próprio e teste de regressão, permanecem abertos para uma fase futura — a contaminação pré-existente de alternativa E em Q07 (exige tornar o fatiamento de fronteira de alternativas ciente de coluna/proximidade em X), os marcadores "I"/"II" ausentes de Q24 (mecanismo ainda não identificado — candidato mais provável para a próxima investigação forense), e o caractere ausente + nuance de ordem de leitura em Q45 (dois defeitos pequenos, de mecanismos distintos entre si e do cluster original). Nenhum dos três exige, a princípio, tocar merge/crescimento/crop — mas cada um exige sua própria investigação dedicada antes de qualquer tentativa de correção, seguindo exatamente a disciplina desta fase.
