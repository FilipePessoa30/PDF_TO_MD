# Diretrizes de anotação semântica (Fase 5A)

Este documento orienta quem for revisar ou estender as anotações produzidas pela
Fase 5A (`data/semantic/question-annotations-5a.json`) ou expandir a taxonomia
(`data/taxonomy/computing-v1.yaml`). Ele não substitui a leitura de
`docs/phase-5a-report.md`, que registra o estado real desta fase; é um guia de
convenções para quem for anotar as próximas questões.

## 1. Separação de camadas

A extração responde **"o que o documento contém"**. A taxonomia e a anotação
respondem **"qual conhecimento está sendo avaliado"**. Uma camada nunca corrige,
completa ou reinterpreta silenciosamente a outra:

- Nunca edite `data/questions/**/*.md` para adicionar tags semânticas.
- Nunca use uma anotação semântica para "consertar" um problema de extração — se
  um defeito de extração for encontrado durante a leitura, registre-o
  separadamente (ex.: um novo achado no relatório da fase) e não o esconda atrás
  de uma anotação semântica.

## 2. Área / Tópico / Conceito / Termo de busca / Contexto / Habilidade

Estes seis níveis nunca devem ser misturados em uma lista plana de tags:

| Nível | O que é | Exemplo |
|---|---|---|
| Área (`subject`) | Domínio amplo | Redes de Computadores |
| Tópico (`topic`) | Subárea avaliável | Computação em Nuvem |
| Conceito (`concept`) | Unidade específica necessária para interpretar/resolver a questão | Modelos SaaS/PaaS/IaaS |
| Termo de busca (`search_terms`) | Expressão de busca, com variantes/aliases | "cloud computing", "computação em nuvem" |
| Contexto (`context_tags`) | Domínio mencionado mas não o conhecimento central avaliado | Uma questão de lógica que menciona "sistemas digitais" apenas como pano de fundo |
| Habilidade cognitiva (`cognitive_skills`) | Ação cognitiva exigida | `analyze`, `calculate`, `justify` |

## 3. Critérios de inclusão de um conceito na taxonomia (seção 9 do prompt)

Um conceito só deve ser incluído se satisfizer **pelo menos um** destes critérios:

1. Recorrência real no corpus (aparece em mais de uma questão).
2. Presença documentada em uma fonte curricular oficial.
3. Necessidade de separar semanticamente duas questões que, sem o conceito,
   ficariam indistinguíveis.
4. Utilidade demonstrável para busca/recomendação futura.

Conceitos raros (satisfazendo apenas o critério 3 ou 4) podem existir, mas a
justificativa deve ficar registrada em `source_references`.

## 4. Tópico primário vs. secundário (seções 12-13)

- **Primário**: representa o conhecimento efetivamente avaliado pela questão —
  nunca apenas uma palavra frequente no enunciado.
- Mais de um tópico primário só é aceitável quando o conhecimento é
  verdadeiramente indissociável (nunca para evitar uma decisão).
- **Secundário**: conhecimento relevante mas não central. Nunca classifique como
  secundário: cenário narrativo, tecnologia citada apenas como exemplo,
  organização mencionada, formato visual, palavra presente apenas em uma
  alternativa claramente distratora, ou conteúdo de outra questão (asset
  contaminado).
- Toda associação de tópico secundário precisa de evidência própria.

## 5. Conceitos (seção 14)

Cada `ConceptAssociation` tem um papel:

- `required`: indispensável para resolver a questão.
- `supporting`: ajuda a resolver, mas a questão é solúvel sem ele.
- `contextual`: aparece no enunciado mas não é exigido para a resposta.

Nunca infira um conceito a partir do gabarito. Nunca use conhecimento externo
para completar silenciosamente uma informação ausente no documento. Se o
conceito depende de uma fórmula/imagem, use o asset como evidência (nunca
transcreva a fórmula "de memória"); se a imagem for ilegível ou ausente,
registre a limitação em vez de inventar.

## 6. Evidência (seção 15)

Toda anotação deve apontar para um trecho ou asset **real e re-verificável**:

- `text_excerpt` deve ser uma citação curta e literal do enunciado/alternativa
  publicado — nunca uma paráfrase.
- Evidência visual deve apontar para `asset_path` + `asset_sha256` (reaproveite
  o hash já publicado do asset, nunca recalcule).
- Nunca use apenas um índice de lista como identidade da evidência.
- `validate_evidence_integrity` sempre re-lê o arquivo real do disco — uma
  evidência que não bate mais com o arquivo publicado é uma anotação com hash
  "stale" e precisa ser corrigida, nunca ignorada.

## 7. Anti-vazamento de gabarito (seção 16)

A anotação primária **nunca** pode usar a alternativa correta, o gabarito ou o
padrão de resposta para justificar o tópico. `AnnotatableContent`
(`src/enade/semantic/annotatable_content.py`) não tem nenhum campo capaz de
carregar essas informações — isso é uma garantia estrutural, não apenas uma
convenção. Qualquer anotação derivada do padrão de resposta no futuro deve
viver em um modelo explicitamente separado.

## 8. Confiança e status (seção 19)

- Confiança (`high`/`medium`/`low`) deve refletir critérios objetivos: quanto o
  enunciado textual, isoladamente, sustenta a classificação. Uma questão
  fortemente dependente de uma figura não descrita em texto deve ter confiança
  `medium` ou `low`, nunca `high` só porque "parece óbvio".
- `annotation_status` distingue `proposed` / `needs_review` / `reviewed` /
  `rejected` / `unclassifiable`. **Nenhuma anotação produzida automaticamente ou
  por este pipeline pode receber `reviewed`** sem revisão humana real — o
  próprio modelo (`QuestionAnnotation`) recusa `review_status="reviewed"` sem
  uma nota citando `reviewer: <nome>`.
- Uma questão fora do escopo da taxonomia (ex.: formação geral, pedagogia
  específica de Licenciatura) deve ser marcada `unclassifiable` — isso é um
  resultado honesto, não uma falha do processo.

## 9. Questões compartilhadas entre cursos (seção 10)

Quando o mesmo enunciado é publicado sob IDs diferentes em cursos diferentes
(ex.: `enade-2021-cc-b-q25` e `enade-2021-cc-l-q25`), ambas as anotações devem
ser **idênticas em conteúdo semântico**. Registre o grupo em
`shared_question_groups` no arquivo de anotações — não presuma que o sinalizador
estrutural `is_shared_across_courses` detecta esse caso: ele só é verdadeiro
quando o curso usa o alias `ALL_COMPUTING` (2008/2011), nunca quando dois
livretos de 2021 já divididos por curso publicam o mesmo texto sob IDs
distintos. Essa duplicação só é detectável lendo o conteúdo integral.

## 10. Habilidades cognitivas (seção 18)

Vocabulário fechado: `recall`, `interpret`, `apply`, `calculate`, `analyze`,
`compare`, `evaluate`, `design`, `justify`. Nunca confunda habilidade cognitiva
com dificuldade. Nunca atribua `design` só porque um sistema é mencionado — a
questão precisa pedir para o estudante efetivamente projetar algo.

## 11. Termos de busca (seção 17)

`search_terms` deve derivar da taxonomia/anotação (nunca ser uma lista
independente inventada livremente). Preserve grafia original (maiúsculas,
acentos, hífens); nunca aplique stemming agressivo que funda conceitos
diferentes.
