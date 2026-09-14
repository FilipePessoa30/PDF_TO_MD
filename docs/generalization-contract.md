# Contrato de Generalização

Este documento formaliza, a partir da Fase 3F, o que este projeto aceita chamar de "regra
geral" versus "correção específica", e o que é exigido de qualquer nova capacidade de extração
antes que ela conte como evidência de generalização. Ele não descreve uma aspiração — descreve
regras que `tests/test_generalization_architecture.py` verifica automaticamente contra o código
real a cada execução da suíte, e que `data/manifests/extraction-capabilities.json` registra por
capacidade.

## 1. Três categorias de regra

### 1.1 Generalização do núcleo

Uma regra pertence ao núcleo (`src/enade/extraction/*.py`, exceto `exam_profile.py` e
`layout_overrides.py` — ver seção 3) somente quando:

- é ativada por uma **característica observável** do documento (tamanho de fonte, proporção de
  aspecto, posição relativa à margem, ownership geométrico, densidade de fragmentos
  decorativos) — nunca por ano, ID de questão, número de página ou hash de arquivo;
- não consulta `year`, `question_id`, `question_number` ou `page_number`/`source_page` como
  condição (`tests/test_generalization_architecture.py::test_core_extraction_modules_never_branch_on_hardcoded_identity`
  verifica isso via AST em todo `src/enade/extraction/`, exceto os dois arquivos declarativos);
- possui pelo menos um exemplo positivo e um negativo, comprovados por teste unitário com
  fixture sintética (nunca apenas contra o corpus real, que não versiona os casos negativos
  explicitamente);
- funciona (ou é comprovadamente segura, i.e., não piora) em mais de uma família de layout —
  na prática hoje, isso significa nunca regredir 2011/2021 quando aplicada;
- falha de maneira segura diante de ambiguidade: nunca adivinha, nunca usa gabarito para
  reconstruir conteúdo, nunca atribui ownership por aproximação silenciosa.

Exemplos já no núcleo, sem qualquer condicional por ano/ID: `is_chrome_line`, `_is_rule_line`,
`_expand_with_labels`, `_line_in_region`, `find_owner`, `apply_forward_reference_transfers`.

### 1.2 Capacidade declarativa

Uma capacidade pode ser **habilitada pelo profile** (`ExamStructureProfile`, um arquivo YAML
por ano/caderno) quando:

- representa uma característica real da família de layout daquele caderno — não uma correção de
  conteúdo de uma questão específica;
- usa parâmetros estruturais (um limiar, uma tolerância, um booleano de "este layout tem X"),
  nunca uma lista de IDs ou um texto literal a procurar;
- pode, em princípio, ser selecionada automaticamente no futuro (nível G3 — ver seção 2) a
  partir de uma característica mensurável do próprio documento, mesmo que hoje seja ligada à
  mão após instrumentação direta;
- nunca é o único jeito de o núcleo funcionar corretamente — desligada (valor padrão), o
  comportamento é exatamente o que já existia antes dela.

Exemplos: `region_merge_x_tolerance`, `caption_font_size_gate`, `owner_exclusion_gate`,
`combined_numbering`, `source_letter`.

### 1.3 Override documental

Um override (`data/manifests/layout-overrides.yaml`, agrupado por hash de PDF) é permitido
somente quando:

- a irregularidade pertence genuinamente àquele arquivo específico — uma coincidência
  geométrica real, não reproduzível como regra;
- não representa uma regra geral disfarçada (se dois ou mais overrides compartilham a mesma
  forma, isso é evidência de que deveriam virar uma capacidade declarativa, não permanecer como
  overrides separados);
- possui hash do PDF, página, bounding box, justificativa e teste de regressão próprios;
- permanece visível nos relatórios de fase e no blocker ledger — nunca é usado para silenciar um
  defeito sem registro;
- **nunca conta como evidência de generalização** — um override resolve exatamente um arquivo,
  nada além dele.

## 2. Níveis de generalização (G0–G4)

| Nível | Nome | Critério |
|---|---|---|
| G0 | Correção específica | Codificada para um caso (`if question_id == "..."`, coordenadas exatas de uma prova, texto integral de uma questão como gatilho). **Proibida no núcleo** — se existir, é um bug de arquitetura, não uma capacidade. |
| G1 | Override documental | Exceção rastreável (seção 1.3) — resolve um arquivo, documentado, testado, nunca escondido. Não generalizado. |
| G2 | Capacidade declarativa | Regra reutilizável (seção 1.2), ainda precisa ser ligada manualmente por profile após instrumentação direta confirmar que o caderno precisa dela. |
| G3 | Detecção estrutural automática | A mesma regra de G2, mas selecionada automaticamente a partir de uma característica mensurável do PDF (densidade de fragmentos decorativos, presença de legendas com fonte menor, etc.) — sem exigir edição manual do profile. Nenhuma capacidade deste projeto está neste nível ainda. |
| G4 | Validado em prova inédita | G3 comprovado processando um caderno nunca antes visto pelo pipeline, com código e profiles **congelados** (nenhuma mudança feita durante ou por causa dessa prova). Nenhuma capacidade deste projeto está neste nível — não é possível estar, já que só processamos os cadernos já conhecidos (2008-b, 2011, 2021). |

Nunca usar a palavra "generalizada" sozinha para G0 ou G1 — o nível deve sempre ser citado
explicitamente ao descrever uma correção (ver `data/manifests/extraction-capabilities.json`).

## 3. Onde ano/hash/página podem existir

Apenas em quatro lugares, nunca dentro da lógica central de decisão:

1. **Profiles** (`data/manifests/exam-structure-*.yaml`) — `year`, `source_letter`,
   `combined_numbering` e as capacidades G2 são campos de dados de um profile, lidos por
   `pipeline.py` e passados como parâmetros; a lógica que os *consome* (`assemble_question`,
   `detect_visual_regions`, etc.) nunca compara esses valores contra um literal de ano — apenas
   contra o próprio parâmetro recebido.
2. **Manifests** (blocker ledger, visual audit, gold, extraction-capabilities) — registros
   *sobre* o resultado da extração, nunca lidos de volta pelo pipeline para decidir como
   extrair.
3. **Overrides documentais** (`layout-overrides.yaml`) — um registro por arquivo, com hash e
   bbox como dados, consultado (nunca com um `if` hardcoded) por `layout_overrides.py`'s próprio
   método `protects_from_region_membership`/`suppresses_region`/etc., que faz correspondência de
   dados contra dados, não uma ramificação por identidade no código do parser.
4. **Testes** e **seleção explícita de corpus** (`--year`/`--course` na CLI, escolhendo *qual*
   arquivo abrir — nunca *como* interpretá-lo).

`tests/test_generalization_architecture.py` verifica isso automaticamente: nenhum módulo em
`src/enade/extraction/` (exceto `exam_profile.py`/`layout_overrides.py`, cujos próprios campos
são verificados separadamente) contém uma comparação `==`/`!=` entre um campo com sufixo
`year`/`question_id`/`question_number`/`page_number`/`source_page`/`number` e um literal.

## 4. Parâmetros relativos, não absolutos

Sempre que possível, um limiar geométrico deve ser derivado da própria geometria do documento
(fonte corporal dominante, largura de coluna detectada, altura de linha mediana), não um valor
absoluto fixo — um valor relativo se adapta a variações de escala/DPI/fonte entre cadernos sem
precisar de um novo profile a cada caderno. Já em uso no núcleo:

- `caption_font_size_gate`: `line.font_size < body_font_size - FONT_SIZE_CAPTION_MARGIN` (a
  fonte do corpo é medida no próprio documento, via `_dominant_body_font_size`).
- `_is_short_off_size_column`: altura relativa a `MIN_COLUMN_HEIGHT_RATIO` da outra coluna, mais
  fonte relativa ao corpo — nunca uma altura/fonte absoluta fixa.
- `_is_rule_line`: proporção de aspecto (espessura vs. comprimento), não uma dimensão fixa.

Valores absolutos permanecem em uso como **limites de segurança** (`MAX_ABSORPTION_GROWTH`,
`REGION_X_PADDING`) quando uma tentativa de torná-los relativos foi investigada e não teve
evidência suficiente para ser aceita com segurança nesta fase — ver
`docs/phase-3f-report.md`, seção "Experimentos revertidos", para o caso concreto investigado
(`_line_in_region`'s própria janela X) e por que permanece absoluto por ora.

## 5. Prova de vida: nenhuma IA generativa em runtime

`tests/test_generalization_architecture.py` também verifica, estaticamente:

- nenhum módulo em `src/enade/extraction/` importa uma biblioteca de cliente LLM/VLM ou uma
  biblioteca de rede genérica (`openai`, `anthropic`, `langchain`, `requests`, `httpx`, sockets
  brutos, etc.);
- `pyproject.toml` não declara nenhuma dessas bibliotecas como dependência de runtime.

As únicas dependências de runtime deste projeto são `pydantic`, `PyYAML`, `typer`, `pypdf` e
`pymupdf` — nenhuma delas é um cliente de rede ou de modelo generativo. Nenhum OCR está em uso
neste momento (todo o corpus processado até aqui — 2008-b, 2011, 2021 — é PDF-nativo, com
camada de texto real); se um OCR local vier a ser introduzido para um caderno futuro sem texto
extraível, ele deve ser opcional, declarado explicitamente no profile daquele caderno, mantido
fora do núcleo PDF-nativo, e nunca autorizado a substituir silenciosamente texto documental já
extraído da camada de texto real.
