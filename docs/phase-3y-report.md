# Fase 3Y — Modelagem, Extração e Publicação Segura do Grupo Horizontal de Fotografias da Q8

## A. Classificação

**`HORIZONTAL_VISUAL_GROUP_ESTABLISHED`**.

Justificativa: as 5 alternativas da Q8 (2008-b) são agora publicadas como 5 fotografias reais e
distintas, uma por alternativa, na ordem A–E correta, cada uma com sua própria legenda real
(texto genuíno da camada de texto do PDF, nunca OCR nem atribuição inventada); nenhum crop
monolítico redundante; nenhum vazamento de marcador/legenda vizinha; `automatic_validation=passed`;
`visual_validation=passed` (auditoria visual efetivamente realizada, 5 crops individualmente
renderizados e inspecionados); a exclusão original (`q08-unstructured-image-alternatives`) foi
removida com evidência, nunca por bypass de gate; os contraexemplos obrigatórios (Q38, Q55, Q57,
Q45, Q23, D40, D59, D10) permanecem intactos — inclusive dois regressões reais encontradas e
corrigidas durante o desenvolvimento (Seção R); 2011 e todos os 3 cursos de 2021 permanecem
byte-idênticos; reprodutibilidade confirmada (duas execuções independentes, hashes SHA-256
idênticos); 26 testes novos, todos permanentes.

Separadamente, como o prompt exige:

- **`EXCLUSION_CONTRACT_RECONCILED`**: a única exclusão restante do contrato de 2008-b
  (`q08-unstructured-image-alternatives`) foi fechada; 80/80 questões acadêmicas estão agora
  publicadas (0 excluídas). Não existe mais nenhuma questão em `structural_warnings` do tipo
  "could not build a valid Question".
- Readiness real (`enade assess-readiness --year 2008 --course all-computing`):
  **`NOT_READY_FOR_2011`**, com **4 blockers** (queda de 5→4, exatamente como previsto pelo prompt) —
  os 4 blockers restantes pertencem inteiramente a D09/D10 (`question_not_verified` +
  `missing_answer_standard` para cada um), que permanecem deliberadamente fora do escopo desta
  fase. Nenhum blocker de D09/D10 foi tocado, editado ou reclassificado.

Não declaro `GENERALIZATION_SUCCESS` apenas por resolver a Q8: o novo mecanismo
(`declare_raster_alternative_region`) tem exatamente **um** caso real comprovado no corpus rastreado
(Seção O) — a maturidade registrada no capability registry é `G1` (evidência de caso único,
individualmente verificado), nunca superior.

## B. Estado Git inicial

- Branch: `feat/enade-2008-cc-b-pilot`.
- `HEAD` inicial: `2aa6b30dd7d1f853f8761f3cccbc78017f4bab70` ("feat: Resolve Q38 by fully
  publishing circuit diagram and alternatives" — commit externo da Fase 3X, antes desta fase).
- `git status --short` inicial: árvore de trabalho limpa (nenhuma alteração pendente).
- Nenhum commit, push, PR, tag ou merge foi feito durante esta fase; `master` nunca foi tocada.

## C. Baseline

- Suíte de testes no início: 818 testes (herdados da Fase 3X).
- Corpus 2008-b: 79/80 questões publicadas, `enade-2008-computing-q08` excluída
  (`structural_warnings`: "objective 8: could not build a valid Question").
- Corpus 2011 (`all-computing`, 55 questões) e 2021 (3 cursos, 120 questões totais): protegidos,
  sem alterações previstas.
- `blocker-ledger-2008.yaml`: 60 entradas, `q08-unstructured-image-alternatives` com
  `status: open`, `visual_validation: not_performed`.
- `data/manifests/layout-overrides.yaml`: 91 overrides (herdados da Fase 3X).

## D. Blockers iniciais

`enade assess-readiness --year 2008 --course all-computing` (estado inicial, antes de qualquer
mudança): **`NOT_READY_FOR_2011`**, 5 blockers:

1. `[question_not_verified, structural] enade-2008-computing-d09`
2. `[missing_answer_standard, structural] enade-2008-computing-d09`
3. `[question_not_verified, structural] enade-2008-computing-d10`
4. `[missing_answer_standard, structural] enade-2008-computing-d10`
5. `[blocker_ledger_open, structural] q08-unstructured-image-alternatives`

## E. Estado herdado da Fase 3X

A Fase 3X resolveu integralmente a Q38 (camadas 1–3 do seu próprio defeito), deixando a Q8
deliberadamente aberta e fora de escopo — real fotografias, layout horizontal em 2 linhas, sem
precedente no corpus até então. A Fase 3W já havia feito a reclassificação forense correta da Q8
(imagens raster reais, nunca fórmulas vetoriais) mas decidiu **não** tentar a extração, por falta de
precedente seguro. Esta fase (3Y) parte exatamente desse ponto: a classificação forense da Q8 já
estava correta; faltava apenas o mecanismo de extração/publicação em si.

## F. Anatomia documental da Q8

Papel documental classificado por evidência estrutural pura (nunca pela resposta correta): cada
uma das 5 alternativas (A–E) é uma fotografia (obra de arte) e nada mais — não há texto de
alternativa que preceda ou complemente a imagem além de sua própria legenda impressa. O enunciado
("Das obras a seguir, a que reflete esse enfoque artístico é") pede explicitamente que se escolha
**entre as obras**, não que se interprete uma figura comum a todas. Não há numeração romana
compartilhada (ao contrário da Q01, que referencia figuras I–V a partir do texto das alternativas —
ver Seção Q), não há região "da questão" separada das alternativas, e cada imagem está posicionada
imediatamente à direita do seu próprio marcador circular (A–E). Classificação: **`alternative_visual_group`**
— reaproveitando integralmente o contrato pré-existente `Alternative.asset` + `Alternative.text`
(nenhuma categoria nova foi necessária).

## G. Inventário de imagens

Fonte: `page.get_images(full=True)` + `page.get_image_info(xrefs=True)` na página 5 de
`2008/b1_prova.pdf` (sha256 `5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264`).

| xref | letra | bbox (pt)                              | w×h (px) | colorspace | bpc | smask | rotação |
|------|-------|-----------------------------------------|----------|------------|-----|-------|---------|
| 50   | A     | (50.999, 241.799, 193.442, 437.639)     | 198×272  | sRGB/DCT   | 8   | não   | não (escala+translação simples) |
| 51   | B     | (221.039, 242.519, 369.824, 435.839)    | 207×270  | sRGB/DCT   | 8   | não   | não |
| 52   | C     | (405.239, 238.799, 558.746, 435.239)    | 213×274  | sRGB/DCT   | 8   | não   | não |
| 53   | D     | (121.799, 520.799, 263.626, 722.399)    | 197×280  | sRGB/DCT   | 8   | não   | não |
| 54   | E     | (291.959, 518.639, 463.859, 719.639)    | 238×280  | sRGB/DCT   | 8   | não   | não |

Nenhuma outra imagem existe na página 5 — confirmado por `page.get_image_info()` sem filtro
(retorna exatamente esses 5 xrefs). Marcadores (rawdict/texttrace): A `(36.84,346.27)–(45.35,356.23)`;
B `(206.88,346.27)–(218.15,356.53)`; C `(376.91,346.27)–(400.55,356.23)`; D `(107.64,631.99)–
(116.15,641.95)`; E `(277.67,631.99)–(286.19,641.95)`. Legendas (linhas de texto reais, nunca OCR):
cada uma composta por 2–3 linhas (título da obra, artista/museu, opcionalmente "Disponível em:
<url>"), com `y0` iniciando poucos pontos abaixo do próprio `bbox[3]` da imagem correspondente.

Ordem visual/impressa: A, B, C (linha 1, esquerda→direita), D, E (linha 2, esquerda→direita) —
coincide exatamente com a ordem alfabética dos marcadores, sem conflito de ordenação.

## H. Forense de xrefs/máscaras/transformações

- `get_drawings()` na página 5: nenhum traço vetorial relevante sobreposto às 5 imagens (nenhuma
  moldura desenhada; qualquer aparência de borda nas capturas vem do próprio JPEG).
- Nenhuma das 5 imagens tem `smask` (sem transparência/máscara suave).
- Todas as 5 são JPEG (`DCTDecode`), 8 bits por canal, sRGB, sem rotação (matriz de transformação é
  escala+translação pura, verificado via `page.get_image_info(xrefs=True)["transform"]`).
- A imagem D (Caravaggio) contém uma barra preta com texto branco **dentro do próprio JPEG**
  (identificada como um watermark de origem, provavelmente ligado à URL de legenda
  "vr.theatre.ntu.edu.tw"). Confirmado byte-a-byte: `pymupdf.Pixmap(doc, 53)` (extração direta do
  xref, sem qualquer recorte/render) produz pixels idênticos aos do crop publicado — é conteúdo
  genuíno da fonte, nunca um artefato desta extração. Documentado nas notas de auditoria visual
  (Seção T) para que nunca seja confundido com um bug.

## I. Papel documental do grupo

Confirmado (nunca presumido pela resposta correta): as 5 fotografias formam um
`alternative_visual_group` horizontal em 2 linhas (3+2). Critérios estruturais simultâneos que
sustentam essa classificação: mesma região/página da questão; mesma sobreposição vertical
aproximada dentro de cada linha; gaps horizontais limitados (27.6–35.4pt entre A/B/C); nenhum
bloco de texto interveniente entre marcador e imagem; nenhum "owner" concorrente (nenhuma outra
questão reivindica essas imagens); ordem estável esquerda→direita, depois topo→baixo. Modelo de
agrupamento "complete-link" (nunca *single-linkage* transitivo): cada marcador é ligado à sua
própria imagem individualmente — não existe uma etapa de fusão transitiva via membro intermediário.

## J. Modelo de dados

Reaproveitado integralmente, nenhuma abstração nova de domínio foi criada:

- `VisualRegion` (já existente, `figures.py`) ganhou um único campo novo, aditivo, com default
  `False` (zero regressão): `is_exact_raster_bbox: bool` — sinaliza que o `bbox` já é a extensão
  exata de uma imagem raster real (nunca um envelope vetorial aproximado), usado apenas no
  passo de renderização (`assets.py`) para pular o *padding* padrão.
- `ExtractedAlternative` (já existente, `assembler.py`) — usado sem nenhuma mudança de schema
  (`letter`, `text`, `figure_region_index`).
- `Alternative.asset` + `Alternative.text` (já existente, `provenance.py`/modelos de questão) —
  usado sem nenhuma mudança de schema; a Q8 nunca dependeu do carve-out "texto vazio com asset"
  (Fase 3W), pois toda legenda de Q8 tem texto real e não-vazio.
- Nenhum `visual_group` genérico (sugerido como alternativa no prompt) foi introduzido: o contrato
  existente já cobre o caso integralmente, e criar uma abstração concorrente teria violado a
  instrução explícita de reaproveitar estruturas existentes sempre que suficiente.

## K. Algoritmo de agrupamento

Novo par de funções em `assembler.py`, nunca reaproveitando o código de fórmulas
(`_attach_alternative_formula_regions`) por serem tipos documentais diferentes:

- **`_build_declared_raster_alternative_regions(doc, page_number, overrides, pdf_sha256)`**: para
  cada `declare_raster_alternative_region` declarado (hash+página+bbox), exige evidência estrutural
  positiva via `figures.verify_image_present(page, bbox, min_containment=0.9)` — conta imagens
  embutidas reais cuja própria área esteja ≥90% contida no bbox declarado (disciplina mais forte
  que o "toque com padding=2.0" de `verify_drawings_present`, escolhida porque uma fotografia
  genuína deve **dominar** quase totalmente seu próprio bbox declarado, ao contrário de fragmentos
  de desenho vetorial esparsos). Sem evidência, nenhuma região é construída — o override fica sem
  efeito, nunca aplicado às cegas.
- **`_attach_declared_raster_alternative_regions(ordered_letters, text_only_lines, alt_bounds,
  declared_regions)`**: para cada letra, localiza sua própria linha-marcador e calcula o
  centro-Y do marcador; entre as regiões declaradas ainda não usadas que estejam estritamente à
  direita do marcador (`marker.x1 <= região.bbox[0]`), escolhe a de centro-Y mais próximo
  (correspondência bijetiva — uma região nunca é reutilizada). Tudo-ou-nada por desenho: retorna
  `None` a menos que as 5 letras sejam casadas com sucesso, delegando integralmente ao mecanismo
  geral pré-existente nesse caso (nunca um resultado parcial).

## L. Ordering

A ordem de publicação (A, B, C, D, E) vem inteiramente da correspondência marcador→região descrita
acima — nunca de uma ordenação puramente geométrica por posição de xref (que aliás já é
inconsistente: os xrefs 50–54 já seguem A–E na ordem de inserção do PDF, mas isso nunca foi
assumido nem confiado; a correspondência é sempre por marcador, não por ordem de xref). Nenhum
conflito de ordenação foi encontrado (a ordem impressa, a ordem dos marcadores e a ordem final
publicada coincidem integralmente) — se houvesse conflito, o desenho exige recusar a correspondência
inteira (retornar `None`) em vez de adivinhar uma ordem.

## M. Ownership

Cada uma das 5 regiões declaradas é resolvida diretamente pela função de anexação via
correspondência de marcador (nunca por "nearest marker" genérico nem por associação geométrica
ampla) — não há parâmetro `question_regions`/ownership na função construtora, porque a atribuição
de dono é feita explicitamente letra-a-letra, nunca por proximidade genérica que poderia (por
exemplo) confundir conteúdo de uma questão vizinha ou de chrome de página. Nenhuma das 5 imagens é
compartilhada com nenhuma outra questão (confirmado: nenhuma outra questão em 2008-b reivindica
conteúdo da página 5).

## N. Labels e legendas

Cada legenda é recuperada como texto real, extraível, da própria camada de texto do PDF — nunca
OCR, nunca atribuição de artista/obra inventada por conhecimento externo. Critério geométrico:
linha cuja `x0` esteja a ≤6.0pt do `bbox[0]` da região (mesma coluna visual da foto) e cujo `y0`
esteja entre o `bbox[3]` da região e até 10.0pt abaixo dele — nunca a linha-marcador em si (excluída
explicitamente). Múltiplas linhas nesse intervalo são ordenadas por `y0` e unidas com espaço. Uma
consequência honesta e não corrigida artificialmente: quando a legenda real tem 3 linhas mas a
terceira ultrapassa a janela de 10pt a partir do bbox (ex.: alternativa A, cuja 3ª linha
"Disponível em: http://www.allposters.com" fica a ~15.5pt do bbox), essa linha extra fica de fora
da legenda publicada — nunca fabricada nem forçada a entrar; é uma limitação documentada (Seção Y),
não um bug, e afeta apenas 1 das 5 legendas (A). Nenhuma duplicação entre asset e Markdown: a
legenda nunca é redesenhada dentro da própria imagem (cada crop é exatamente a extensão da imagem
embutida, nada além disso).

## O. Assets publicados

5 assets, um por alternativa, tipo `image`, `extraction_method: raster_crop`:

| id | letra | sha256 (arquivo final) |
|----|-------|------------------------|
| figure-01 | A | `313d3c25b05f3be4986376b0c4daa8d66efa69ea762cedd11cfe0a87e14e4dfd` |
| figure-02 | B | `d1b1db475aee8d30b7fac9bec82ac50cb41c15e8f2cf6948b856376cc263d203` |
| figure-03 | C | `2f1bf05347b01d3236b44047bbe92dc82dad5bf4dc248807e13b90433a13b5f0` |
| figure-04 | D | `9b8f97751fabe0a27974af3fd72aa3db0afd6d47d2489700c9fb5bcbbe731b50` |
| figure-05 | E | `69b08046ed0d97aebe573169929caf5c1f455480db7932ea3b5a07c877460b7a` |

`enade-2008-computing-q08.md` final: `6fe5007e3b7ff30647f26b94e89b30815189c19818e7967e8c3cffc1b802ddd8`.
Cada crop foi individualmente renderizado e inspecionado visualmente (Seção T): completo, sem
distorção, sem conteúdo vizinho, sem duplicação. Nenhum crop monolítico por linha permanece — os 2
blobs genéricos (linha 1 A+B+C; linha 2 D+E) que o mecanismo geral, dono-neutro, de
`detect_visual_regions` ainda produzia foram suprimidos via 2 overrides `suppress_visual_region`
(ver Seção Q/R), pois duplicavam, em bounds mais grosseiros, o que os 5 assets individuais já
mostram corretamente.

**Único asset pré-existente sobrescrito**: `figure-01.png` já existia no repositório (commit
`1ee01af`, anterior a esta fase) como um artefato remanescente de um diagnóstico anterior — a mesma
imagem monolítica da linha 1 (A+B+C) que este trabalho identificou e suprimiu — apesar de a Q8
estar oficialmente excluída (nenhum `.md` publicado). Confirmado como resíduo órfão, nunca
referenciado por nenhum arquivo publicado antes desta fase; corretamente substituído pelo novo
conteúdo (o crop individual da alternativa A).

## P. Inserção no conteúdo

Nenhuma reutilização de `_find_inline_formula_insertion_index` (mecanismo específico para fórmulas
inline dentro do enunciado, documentalmente incorreto para este caso). A inserção segue o padrão
já existente em `markdown_format.py` para `Alternative.asset` não-nulo — inalterado nesta fase:
`{letra}. ![Alternativa {letra}](caminho) {texto}` — imagem primeiro, depois a legenda, exatamente
a ordem da fonte impressa. Nenhuma alternativa foi dividida incorretamente, nenhuma inserção após
as alternativas, nenhuma duplicação de inserção (confirmado pelo `automatic_validation=passed` e
pela leitura completa do `.md` final — Seção O).

## Q. Shadow mode

Varredura obrigatória (Seção 17 do prompt) antes de ativar qualquer regra geral: como o novo
mecanismo só é ativado por um override declarativo explícito (nunca por heurística geométrica
automática), ele estruturalmente não pode disparar espontaneamente em nenhum outro lugar do
corpus. Ainda assim, foi feita uma varredura ativa por candidatos equivalentes:

1. **Busca geométrica** (`page.get_image_info()` por página, agrupando imagens ≥15×15pt por
   proximidade) em 2008-b, 2011 e nos 3 cadernos de 2021: encontrados 6 páginas com ≥3 imagens
   substanciais agrupadas, além da própria Q5 da Q8:
   - 2008-b página 2 (Q01): 5 imagens — mas Q01 é um `referenced_figure_sequence`
     (alternativas são texto puro: "I e III.", "I e V." etc.; as 5 imagens são numeradas I–V e
     mostradas **no enunciado**, referenciadas coletivamente pelas alternativas) — já corretamente
     publicada (`extraction_status: verified`, `visual_validation: passed`) como 2 crops
     agregados no enunciado. Estrutura documentalmente diferente da Q8; nenhuma ação tomada.
   - 2011 páginas 5, 11, 27 e 2021-b página 38: todas são fragmentos de um único
     gráfico/tabela/diagrama já corretamente fundidos em 1 asset por questão (Q06, Q14, Q43 em
     2011; Q29 em 2021-b) — nenhuma tem alternativas-imagem; falsos positivos da heurística de
     proximidade pura, não candidatos reais.
2. **Busca direta por alternativas-imagem** (`grep "!\[Alternativa"` em todo o corpus publicado):
   exatamente 5 arquivos no corpus inteiro têm alguma alternativa como imagem: Q08, Q38, Q55
   (2008-b) e Q14, Q23 (2011) — todos já contabilizados; nenhum outro caso, publicado ou excluído,
   existe.

Nenhum outro candidato foi encontrado e deixado sem publicar silenciosamente — o resultado da
varredura está integralmente documentado aqui.

## R. Contraexemplos

Todos os contraexemplos obrigatórios foram re-verificados após a implementação final:

- **Q38**: circuito completo, 5 labels sem vazamento, `figure-01.png` byte-idêntico, 9 overrides
  `force_region_membership` ativos, alternativas com `text=""` e `asset.type=EQUATION` — **uma
  regressão real foi encontrada e corrigida** (ver abaixo).
- **Q55**: 5 alternativas intactas, flags preservadas, alternativa com texto vazio + asset intacta.
- **Q57**: alternativas numéricas intactas, sem regressão em `_merge_orphan_markers`.
- **Q45**: posição/asset da fórmula inline inalterados.
- **Q23**: quebra de parágrafo preservada.
- **D40**: apenas sigma, sem falso "F".
- **D59**: padrão de resposta visual-only, exatamente um asset.
- **D10**: ordem zonal, 478/478 palavras preservadas.

Confirmado por regeneração completa (`diff -rq` byte-a-byte): **zero divergência** em qualquer um
dos itens acima, e zero divergência em qualquer outro arquivo de 2008-b, 2011 ou 2021 além da
própria Q8.

**Duas regressões reais foram encontradas durante o desenvolvimento e corrigidas antes da conclusão
(nenhuma chegou a ser aplicada ao corpus canônico):**

1. **Blobs genéricos redundantes (Seção O)**: o mecanismo geral, dono-neutro, de mesclagem de
   `detect_visual_regions` continuava agrupando as mesmas 5 fotografias em 2 blobs por linha,
   mesmo com as 5 regiões declaradas individualmente presentes — um deles virava um crop
   monolítico espúrio no enunciado, o outro era descartado silenciosamente com um aviso "fell
   after the alternatives cutoff". Corrigido com 2 overrides `suppress_visual_region`.
2. **Sequestro da Q38 pelo novo mecanismo**: a primeira versão passava a lista *inteira* de regiões
   (`regions`) para `_attach_declared_raster_alternative_regions`, em vez de filtrá-la. Como a Q38
   também tem 5 regiões declaradas (`declare_inline_formula_region`) posicionadas à direita de
   seus próprios marcadores, o novo mecanismo as recasava por conta própria — usando o bbox
   declarado diretamente (nunca fatiado por linha, ao contrário do mecanismo correto
   `_attach_alternative_formula_regions`), produzindo crops com alturas ligeiramente diferentes
   (ex.: 49→53px) das já publicadas. **Detectado por bissecção sistemática** (revertendo cada um
   dos 4 arquivos modificados isoladamente e regenerando o corpus completo até isolar
   `assembler.py` como a causa, depois isolando a linha exata da chamada). Corrigido filtrando a
   lista de candidatos para apenas regiões com `is_exact_raster_bbox=True` (um flag que só o novo
   construtor de regiões desta fase atribui) antes de chamar a função de anexação — confirmado por
   regeneração completa retornando Q38/Q55 a byte-idênticos. Um teste de regressão permanente foi
   adicionado especificamente para este caso
   (`test_assemble_question_declared_inline_formula_alternatives_are_never_hijacked_by_raster_mechanism`),
   verificado por reversão manual do fix (falha sem ele, passa com ele).

## S. Exclusões

Critério de 15 pontos para remoção de exclusão, todos atendidos:

1. Todas as 5 fotos presentes — sim.
2. Contagem/ordem batem com a fonte — sim (5, A–E).
3. Crops completos — sim (Seção O/T).
4. Labels/legendas corretos — sim (Seção N).
5. Posição correta do conteúdo — sim (dentro de cada alternativa, imagem antes do texto).
6. Alternativas intactas — sim (5, únicas, sem duplicação).
7. Nenhuma imagem de questão vizinha — sim (Seção M).
8. Nenhuma duplicação de asset — sim (5 assets únicos, sem repetição de sha256).
9. Nenhuma fabricação — sim (nenhuma legenda/atribuição inventada).
10. Auditoria visual passa — sim (Seção T).
11. Validadores mecânicos passam — sim (`automatic_validation=passed`, `audit-extraction` 80/80 OK).
12. Gold aceita — sim (`verify-gold` OK).
13. Readiness não depende mais desta exclusão — sim (blocker removido; apenas D09/D10 restam).
14. Testes permanentes — sim (Seção W).
15. A/B byte-idênticos — sim (Seção X).

Reconciliação entre as 4 camadas: extração (Q8 agora presente em `data/questions`), validação
automática (`automatic_validation=passed`), verificação gold (`verify-gold` 80/80 OK), e exclusão
de readiness (`blocker_ledger_open` removido do `assess-readiness`) — nenhuma camada ficou
desalinhada ou escondida silenciosamente.

## T. Auditoria visual

Checklist completo, realizado por renderização e inspeção direta de cada um dos 5 crops finais
(não apenas leitura de metadados):

- `all_members_present`: sim (5/5).
- `correct_member_count`: sim.
- `correct_order`: sim (A–E, confirmado por posição de marcador).
- `complete_crops`: sim — nenhum recorte parcial; a barra de watermark da alternativa D é conteúdo
  genuíno da imagem-fonte (Seção H), não um artefato de recorte.
- `correct_aspect_ratio`: sim (crop exato do bbox real da imagem embutida, sem distorção).
- `labels_complete`: sim, com a limitação documentada da 3ª linha da legenda de A (Seção N).
- `captions_complete`: idem.
- `correct_insertion_point`: sim (dentro de cada alternativa, nunca no enunciado).
- `no_duplicate_assets`: sim (5 sha256 distintos).
- `no_neighbor_content`: sim (confirmado após a correção do padding — Seção R/U).
- `no_chrome`: sim.
- `alternatives_intact`: sim.

Resultado registrado em `data/manifests/visual-audit-2008-computing.json` (`status: passed`, nota
completa incluindo a ressalva do watermark da alternativa D e a explicação da limitação da 3ª
linha da legenda de A).

## U. Capability registry e ledgers

- **`extraction-capabilities.json`**: nova entrada `declared_raster_alternative_group_preservation`,
  `generalization_level: "G1"` (caso único comprovado, nunca promovido além disso),
  `introduced_phase: "3Y"`. `trigger_features` descreve apenas sinais estruturais (presença de
  override individualmente revisado + correspondência bijetiva completa) — nenhum ID de questão,
  hash ou título de obra aparece em `trigger_features` (verificado programaticamente e pelo teste
  `test_capability_registry_never_cites_a_question_id_as_a_trigger`, que passa). IDs de questão
  aparecem apenas em `real_cases` (permitido, como em toda entrada pré-existente).
- **`blocker-ledger-2008.yaml`**: entrada `q08-unstructured-image-alternatives` atualizada
  (`status: resolved`, `resolution`, `cause` com histórico completo preservado — nunca apagando a
  investigação da Fase 3W —, `affected_assets` com os 5 nomes reais de arquivo, `regression_tests`
  com os 12 testes relevantes, `visual_validation: passed`). D09/D10 não foram tocados.
- **`source-token-ledger-2008.yaml`**: **nenhuma extensão feita**, pela mesma razão já estabelecida
  para Q23/Q38 — este ledger documenta identidade de *caractere/glifo* (evidência de
  charcode/glyph-id/fingerprint de fonte) quando há uma reivindicação de identidade textual
  ambígua. A Q8 nunca faz essa reivindicação: as legendas são recuperadas por correspondência
  geométrica direta de linhas de texto já íntegras (nunca ambíguas em nível de glifo), e as
  imagens são fotografias, não texto. A proveniência de imagem (xref, bbox, hash, verificação de
  containment) já está integralmente registrada em `layout-overrides.yaml` (razão/evidência por
  alternativa) e no próprio front-matter do `.md` (lista `assets` com sha256) — reaproveitando
  essas estruturas existentes em vez de criar um ledger concorrente, como o prompt exige.

## V. Gold e readiness

`enade build-gold --year 2008 --course all-computing --maturity provisional`: 80 questões
(78 verified, 2 needs_review — apenas D09/D10). `enade verify-gold --year 2008 --course
all-computing`: **OK**, 80/80. `enade assess-readiness --year 2008 --course all-computing`:
**`NOT_READY_FOR_2011`**, 4 blockers, todos D09/D10 (Seção A) — resultado literal reportado sem
suavização; D09/D10 permanecem honestamente `needs_review`/`source_unavailable`, nunca fabricados
para simular prontidão.

## W. Testes e quality gates

- Suíte completa: **844 passed** (818 herdados + 26 novos), 0 falhas, 0 skips inesperados.
- `ruff check .`: **All checks passed!**
- `ruff format --check .`: **420 files already formatted**.
- `mypy src`: **Success: no issues found in 60 source files**.
- `enade verify-gold --year 2008 --course all-computing`: OK (80/80).
- `enade verify-gold --year 2011 --course all-computing`: OK (55/55, inalterado).
- `enade verify-gold --year 2021 --course ciencia-da-computacao-bacharelado`: OK (40/40, inalterado).
- `enade audit-extraction --questions-dir data/questions/2008/all-computing`: **80/80 OK**.
- `enade validate-schema`: 13/13 fixtures válidas (inalterado).

26 novos testes, todos permanentes, cobrindo: casos-limite de agrupamento (nenhuma região à
direita, menos de 5 regiões, correspondência por centro mais próximo sem reuso), corretude de
asset (containment, sem padding, hash determinístico), corretude de inserção (imagem-primeiro,
sem duplicação), segurança de remoção de exclusão (o teste de pipeline completo da Q8), e o
contraexemplo específico da Q38 contra o sequestro pelo novo mecanismo.

## X. Reprodutibilidade e arquivos

Duas execuções independentes de `enade extract --year 2008 --course all-computing` (diretórios
temporários distintos, mesmo código/overrides) produziram `enade-2008-computing-q08.md` e os 5
`figure-NN.png` **byte-idênticos** entre si (`diff -rq` sem saída) e idênticos ao estado final
aplicado ao corpus canônico. Hashes finais registrados na Seção O.

Inventário completo de arquivos alterados/criados nesta fase:

- `src/enade/extraction/figures.py` — `verify_image_present` (nova); `VisualRegion.is_exact_raster_bbox` (novo campo).
- `src/enade/extraction/layout_overrides.py` — `declared_raster_alternative_regions` (novo método).
- `src/enade/extraction/assembler.py` — `_build_declared_raster_alternative_regions`,
  `_attach_declared_raster_alternative_regions` (novas); wiring em `assemble_question` (filtro
  `is_exact_raster_bbox` incluso).
- `src/enade/extraction/assets.py` — `_render_bbox`/`render_region` ganham `vertical_padding`
  (default preserva comportamento existente; `0.0` apenas quando `is_exact_raster_bbox`).
- `data/manifests/layout-overrides.yaml` — 5 `declare_raster_alternative_region` + 2
  `suppress_visual_region` para a Q8.
- `data/manifests/blocker-ledger-2008.yaml`, `visual-audit-2008-computing.json`,
  `extraction-capabilities.json`, `gold-2008-computing.json`,
  `extraction-audit-2008-computing.{csv,json}` — atualizados.
- `data/questions/2008/all-computing/enade-2008-computing-q08.md` + 5 `figure-NN.png` — novos/publicados.
- `tests/test_extraction_figures.py`, `tests/test_layout_overrides.py`,
  `tests/test_extraction_assembler.py`, `tests/test_extraction_assets.py`,
  `tests/test_extraction_pipeline_2008.py` — novos/atualizados (26 testes).
- `docs/phase-3y-report.md` — este arquivo, novo.

**Nenhum arquivo de scratch permanece.** Todos os diretórios temporários usados durante a
investigação (`/tmp/phase3y_*`) foram explicitamente removidos antes da conclusão da fase.
`git status --short` final não mostra nenhum arquivo além do inventário acima.

## Y. Estado Git final e recomendação

`git status --short` final:

```
 M data/manifests/blocker-ledger-2008.yaml
 M data/manifests/extraction-audit-2008-computing.csv
 M data/manifests/extraction-audit-2008-computing.json
 M data/manifests/extraction-capabilities.json
 M data/manifests/gold-2008-computing.json
 M data/manifests/layout-overrides.yaml
 M data/manifests/visual-audit-2008-computing.json
 M data/questions/2008/all-computing/enade-2008-computing-q08/figure-01.png
 M src/enade/extraction/assembler.py
 M src/enade/extraction/assets.py
 M src/enade/extraction/figures.py
 M src/enade/extraction/layout_overrides.py
 M tests/test_extraction_assembler.py
 M tests/test_extraction_assets.py
 M tests/test_extraction_figures.py
 M tests/test_extraction_pipeline_2008.py
 M tests/test_layout_overrides.py
?? data/questions/2008/all-computing/enade-2008-computing-q08.md
?? data/questions/2008/all-computing/enade-2008-computing-q08/figure-02.png
?? data/questions/2008/all-computing/enade-2008-computing-q08/figure-03.png
?? data/questions/2008/all-computing/enade-2008-computing-q08/figure-04.png
?? data/questions/2008/all-computing/enade-2008-computing-q08/figure-05.png
```

Nenhum commit, push, PR, tag ou merge foi realizado. `master` nunca foi tocada. Branch permanece
`feat/enade-2008-cc-b-pilot`.

**Limitações conhecidas, honestamente documentadas (nunca escondidas):**

- A 3ª linha da legenda da alternativa A ("Disponível em: http://www.allposters.com") fica fora do
  texto publicado por estar a ~15.5pt do próprio bbox da imagem, além da janela geométrica de
  10pt usada para recuperação de legenda (Seção N). Não é um erro de conteúdo essencial (título da
  obra e artista/museu estão completos), mas é uma pequena lacuna de completude que uma fase
  futura, estritamente escopada, poderia fechar com uma janela de captura de legenda mais generosa
  — desde que verificada contra os 5 casos já publicados (Q8) e os 2 casos de fórmula (Q38/Q55)
  para não introduzir regressão.
- O watermark da alternativa D é conteúdo genuíno da imagem-fonte, não uma falha — documentado
  explicitamente para que nenhuma fase futura o confunda com um bug de recorte.

**Recomendação**: como a Q8 foi integralmente resolvida e o contrato de exclusões de 2008-b está
agora reconciliado (0 exclusões restantes), recomendo — mas não inicio automaticamente — uma
eventual Fase 3Z dedicada a formalizar a política de readiness para D09/D10
(`source_unavailable`), que são os únicos blockers restantes. Essa fase não deve, em nenhuma
circunstância, fabricar um padrão de resposta ausente, nem confundir "fidelidade à fonte
disponível" com "completude do corpus" — as duas dimensões devem permanecer conceitualmente
separadas, exatamente como o prompt desta fase exige.
