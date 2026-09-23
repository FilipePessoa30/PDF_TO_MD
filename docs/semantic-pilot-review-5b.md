# Pacote de revisão humana - reconciliação do piloto (Fase 5B)

30 questão(ões) - reconciliação adversarial das 30 anotações do piloto da Fase 5A, com foco nos 12 casos não-`proposed` (10 `unclassifiable` + 2 `needs_review`) e auditoria das 18 `proposed`.

Toda decisão marcada abaixo como 'proposta técnica' é apenas isso - uma proposta. Nenhuma anotação aqui foi humanamente revisada; nenhuma tem `review_status='reviewed'`. A decisão humana real (approve/correct/reject/defer) só pode ser registrada em `data/semantic/human-adjudication-template-5b.json`, nunca neste documento. O gabarito e o padrão de resposta nunca aparecem aqui.

---
## enade-2008-computing-d09

- **Ano/curso:** 2008 - Computação (livreto unificado)
- **Tipo:** discursiva
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): direitos-humanos-e-cidadania (Direitos Humanos e Cidadania)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): interpret, justify
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "selecione uma das concepções destacadas e esclareça por que ela representa um avanço para o exercício pleno da cidadania"

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - direitos humanos/cidadania, area formacao-geral.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2008-computing-q04

- **Ano/curso:** 2008 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): legislacao-e-direitos-sociais (Legislação e Direitos Sociais)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): interpret
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "São dois os temas mais específicos para essa legislação:"

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - legislacao/direitos das mulheres, area formacao-geral.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2008-computing-q14

- **Ano/curso:** 2008 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): arvores-e-estruturas-hierarquicas (Árvores e Estruturas Hierárquicas)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): arvores-e-estruturas-hierarquicas (Árvores e Estruturas Hierárquicas)
- tópico(s) secundário(s): recursao-e-iteracao (Recursão e Iteração)
- conceitos:
  - percurso-em-arvore (Percurso em Árvore (Pré-ordem/Em-ordem/Pós-ordem)) (papel: required, confiança: high)
- contexto (não avaliado centralmente): complexidade-de-algoritmos
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "O algoritmo utiliza push() e pop() como funções auxiliares de empilhamento e desempilhamento"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2008-computing-q30

- **Ano/curso:** 2008 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): meios-de-transmissao-e-redes-locais (Meios de Transmissão e Redes Locais/Sem Fio)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): meios-de-transmissao-e-redes-locais (Meios de Transmissão e Redes Locais/Sem Fio)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - tecnicas-de-multiplo-acesso (Técnicas de Múltiplo Acesso (CDMA/FDMA/TDMA)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): recall
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "Na comunicação sem fio, o espectro de radiofreqüência adotado é um recurso finito"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2008-computing-q55

- **Ano/curso:** 2008 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): probabilidade-e-estatistica-aplicada (Probabilidade e Estatística Aplicada)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): probabilidade-e-estatistica-aplicada (Probabilidade e Estatística Aplicada)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - confiabilidade-de-sistemas (Confiabilidade de Sistemas (Componentes em Paralelo/Série)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): calculate, apply
- confiança: `medium`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (asset/asset:figure-01) asset: enade-2008-computing-q55/figure-01.png
- (statement/statement) "Como os componentes estão montados em paralelo, o sistema falha no instante"

**Notas técnicas:** Confiança media: as 5 alternativas são formulas em imagem (raster/vetor, Fase 3Y/4B) sem texto - o enunciado visivel confirma o topico com seguranca, mas o raciocinio matematico exato depende de conteudo visual nao transcrito aqui (nunca inventado).

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-d03

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** discursiva
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): recursao-e-iteracao (Recursão e Iteração)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): recursao-e-iteracao (Recursão e Iteração)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - recursao (Recursão) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): design, compare
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "Apresente as vantagens e desvantagens de cada algoritmo"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q01

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): compreensao-e-interpretacao-textual (Compreensão e Interpretação Textual)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): interpret
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "No poema, a autora sugere que"

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - interpretacao textual/poema, area formacao-geral.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q14

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `needs_review`
- tópico(s) primário(s): conjuntos-relacoes-e-funcoes (Conjuntos, Relações e Funções)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): logica-proposicional (Lógica Proposicional)
- tópico(s) secundário(s): conjuntos-relacoes-e-funcoes (Conjuntos, Relações e Funções)
- conceitos:
  - expressao-booleana-de-regiao-de-conjuntos (Expressão Booleana de uma Região de Diagrama de Venn) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): interpret, analyze
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B auditoria adversarial (secao 11): needs_review resolvido - inspecao visual integral dos 7 assets revelou que a Fase 5A classificou incorretamente (leitura incompleta do enunciado fragmentado). Reclassificado de conjuntos-relacoes-e-funcoes para logica-proposicional (com conjuntos-relacoes-e-funcoes mantido como secundario, pois o diagrama de Venn ainda e o veiculo de representacao).

**Evidências:**
- (statement/statement) "Observe o diagrama de Venn a seguir."
- (statement/statement) "A função representada em azul no diagrama também"
- (asset/asset:figure-03) asset: enade-2011-computing-q14/figure-03.png

**Notas técnicas:** Fase 5B: reclassificado apos inspecao visual integral dos 7 assets (PROMPT secao 7/11) - a Fase 5A classificou como needs_review/baixa confianca sob conjuntos-relacoes-e-funcoes com base em leitura incompleta do enunciado fragmentado (nunca abriu as imagens). A inspecao real mostra que a questao pede para expressar uma regiao sombreada do diagrama de Venn como uma expressao booleana f(x,y,z) (AND/OR/NOT), nao uma propriedade abstrata de funcao (injetora/sobrejetora/bijetora). Erro de anotacao da Fase 5A, nao lacuna de taxonomia - o topico logica-proposicional ja existia.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q23

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `needs_review`
- tópico(s) primário(s): teoria-da-computacao (Teoria da Computação)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): teoria-da-computacao (Teoria da Computação)
- tópico(s) secundário(s): compiladores-e-linguagens-formais (Compiladores e Linguagens Formais)
- conceitos:
  - automato-finito (Autômato Finito) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, compare
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B auditoria adversarial (secao 11): needs_review resolvido - inspecao visual integral confirmou (nao contradisse) a classificacao original da Fase 5A.

**Evidências:**
- (statement/statement) "A figura abaixo apresenta um autômato que"
- (asset/asset:figure-01) asset: enade-2011-computing-q23/figure-01.png
- (asset/asset:figure-02) asset: enade-2011-computing-q23/figure-02.png

**Notas técnicas:** Fase 5B: needs_review resolvido - inspecao visual integral confirmou o conteudo (figure-01: producoes da gramatica livre de contexto S/A/B; figure-02: diagrama de transicao de estados de um automato finito de 6 estados sobre {a,b,c}) coerente com a classificacao ja proposta pela Fase 5A (teoria-da-computacao / automato-finito / compiladores-e-linguagens-formais). Confianca elevada de medium para high; status de needs_review para proposed.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q27

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): processos-e-concorrencia (Processos e Concorrência)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): processos-e-concorrencia (Processos e Concorrência)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - paralelizacao-de-algoritmos (Paralelização de Algoritmos) (papel: required, confiança: high)
- contexto (não avaliado centralmente): estruturas-de-dados-e-algoritmos
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "O objetivo é paralelizar esse código para que o tempo de execução seja reduzido em uma máquina com múltiplos processadores"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q31

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): curriculo-e-sociologia-da-educacao (Currículo e Sociologia da Educação)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de pedagogia de Licenciatura, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "Considerando o currículo na perspectiva crítica da Educação, avalie as afirmações a seguir."

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - pedagogia especifica de Licenciatura (nao formacao geral, nao Computacao).

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q33

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): demografia-aplicada-ao-planejamento-educacional (Demografia Aplicada ao Planejamento Educacional)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): interpret, analyze
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de pedagogia de Licenciatura, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "Constata-se a necessidade de construção, em larga escala, em nível nacional, de escolas especializadas na Educação de Jovens e Adultos"

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - pedagogia especifica de Licenciatura (nao formacao geral, nao Computacao).

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q39

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): paradigmas-de-programacao (Paradigmas de Programação)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): paradigmas-de-programacao (Paradigmas de Programação)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - tipo-de-dados-abstrato (Tipo de Dados Abstrato (TDA)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "O encapsulamento em linguagens de programação orientadas a objetos é um efeito positivo do uso de TDA"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q43

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): organizacao-de-processadores (Organização e Pipeline de Processadores)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): organizacao-de-processadores (Organização e Pipeline de Processadores)
- tópico(s) secundário(s): logica-digital-e-circuitos-combinacionais (Lógica Digital e Circuitos Combinacionais)
- conceitos:
  - clock-e-temporizacao-de-circuitos-sincronos (Clock e Temporização de Circuitos Síncronos) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `medium`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "O registrador do sistema mantém o valor chaveado e é comandado por um clock de sistema better-than-worst-case"
- (asset/asset:figure-01) asset: enade-2011-computing-q43/figure-01.png

**Notas técnicas:** Confianca media: conteudo tecnico denso (arquitetura razor) menos recorrente no corpus levantado - topico bem evidenciado, mas e um caso mais isolado que os demais.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q46

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): sql-e-esquemas-relacionais (SQL e Definição de Esquemas Relacionais)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): sql-e-esquemas-relacionais (SQL e Definição de Esquemas Relacionais)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - sql-agregacao-group-by-having (Agregação SQL (GROUP BY/HAVING)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): apply
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "DEPARTAMENTO (#CodDepartamento, NomeDepartamento)"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2011-computing-q49

- **Ano/curso:** 2011 - Computação (livreto unificado)
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): fundamentos-de-sistemas-de-informacao (Fundamentos de Sistemas de Informação)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): fundamentos-de-sistemas-de-informacao (Fundamentos de Sistemas de Informação)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - teoria-geral-de-sistemas (Teoria Geral de Sistemas) (papel: required, confiança: high)
- contexto (não avaliado centralmente): engenharia-de-software
- habilidade(s) cognitiva(s): apply, interpret
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "solicitações de mudanças originadas de um stakeholder externo"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-b-d01

- **Ano/curso:** 2021 - Ciência da Computação - Bacharelado
- **Tipo:** discursiva
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): arte-cultura-e-liberdade-de-expressao (Arte, Cultura e Liberdade de Expressão)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): interpret, justify
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "discorra a respeito da relação entre arte, cultura e censura"

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - arte/cultura/censura, area formacao-geral. Par compartilhado com enade-2021-si-d01.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-b-d03

- **Ano/curso:** 2021 - Ciência da Computação - Bacharelado
- **Tipo:** discursiva
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): logica-proposicional (Lógica Proposicional)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): logica-proposicional (Lógica Proposicional)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - tabela-verdade (Tabela-Verdade, Tautologia e Satisfazibilidade) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, justify
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "Uma fórmula é uma tautologia se e somente se, para toda atribuição de valores-verdade, sua avaliação é verdadeira."

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-b-q01

- **Ano/curso:** 2021 - Ciência da Computação - Bacharelado
- **Tipo:** múltipla escolha
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): mobilidade-social-e-desigualdade (Mobilidade Social e Desigualdade)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): interpret
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "A partir das informações apresentadas, é correto afirmar que"

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - mobilidade social, area formacao-geral.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-b-q18

- **Ano/curso:** 2021 - Ciência da Computação - Bacharelado
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): aprendizado-de-maquina (Aprendizado de Máquina)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): aprendizado-de-maquina (Aprendizado de Máquina)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - aprendizado-supervisionado-e-nao-supervisionado (Aprendizado Supervisionado e Não Supervisionado) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "As técnicas de aprendizado de máquinas empregam um princípio de inferência denominado indução"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-b-q22

- **Ano/curso:** 2021 - Ciência da Computação - Bacharelado
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): modelagem-de-dados-er (Modelagem de Dados (Entidade-Relacionamento))

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): modelagem-de-dados-er (Modelagem de Dados (Entidade-Relacionamento))
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - mapeamento-der-para-relacional (Mapeamento do Modelo Conceitual (DER) para o Modelo Lógico Relacional) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): apply
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "registra os pets (animais de estimação) amparados por ela, de acordo com o seguinte Diagrama Entidade Relacionamento (DER)"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-b-q25

- **Ano/curso:** 2021 - Ciência da Computação - Bacharelado
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): computacao-em-nuvem (Computação em Nuvem)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): computacao-em-nuvem (Computação em Nuvem)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - modelos-de-servico-saas-paas-iaas (Modelos de Serviço em Nuvem (SaaS/PaaS/IaaS)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "A computação em nuvem (cloud computing) pode ser definida como a infraestrutura de comunicação"

**Notas técnicas:** Questao com o MESMO enunciado publicado em enade-2021-cc-b-q25 e enade-2021-cc-l-q25 (questao compartilhada entre cursos, PROMPT Fase 5A secao 10) - mesma anotacao atribuida a ambas deliberadamente, ver docs/phase-5a-report.md secao I.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-b-q29

- **Ano/curso:** 2021 - Ciência da Computação - Bacharelado
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): processamento-e-segmentacao-de-imagens (Processamento e Segmentação de Imagens)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): processamento-e-segmentacao-de-imagens (Processamento e Segmentação de Imagens)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - operacoes-morfologicas-erosao-dilatacao (Operações Morfológicas (Erosão e Dilatação)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "As operações morfológicas aplicam um elemento estruturador B a uma imagem A de entrada"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-cc-l-q25

- **Ano/curso:** 2021 - Ciência da Computação - Licenciatura
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): computacao-em-nuvem (Computação em Nuvem)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): computacao-em-nuvem (Computação em Nuvem)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - modelos-de-servico-saas-paas-iaas (Modelos de Serviço em Nuvem (SaaS/PaaS/IaaS)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "A computação em nuvem (cloud computing) pode ser definida como a infraestrutura de comunicação"

**Notas técnicas:** Questao com o MESMO enunciado publicado em enade-2021-cc-b-q25 e enade-2021-cc-l-q25 (questao compartilhada entre cursos, PROMPT Fase 5A secao 10) - mesma anotacao atribuida a ambas deliberadamente, ver docs/phase-5a-report.md secao I.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-si-d01

- **Ano/curso:** 2021 - Sistemas de Informação
- **Tipo:** discursiva
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): arte-cultura-e-liberdade-de-expressao (Arte, Cultura e Liberdade de Expressão)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): interpret, justify
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "discorra a respeito da relação entre arte, cultura e censura"

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - arte/cultura/censura, area formacao-geral. Par compartilhado com enade-2021-cc-b-d01.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-si-d02

- **Ano/curso:** 2021 - Sistemas de Informação
- **Tipo:** discursiva
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): sustentabilidade-e-desenvolvimento-urbano (Sustentabilidade e Desenvolvimento Urbano)
- tópico(s) secundário(s): _(nenhum)_
- contexto (não avaliado centralmente): internet-das-coisas-e-cidades-inteligentes (computing-v1.1, mencionado apenas como contexto/premissa, nunca avaliado tecnicamente aqui)
- habilidade(s) cognitiva(s): interpret, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "Explique de que modo as cidades inteligentes podem contribuir para a melhoria das questões relacionadas ao desenvolvimento sustentável."

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - cidades inteligentes tratadas pela otica de sustentabilidade/politica urbana, area formacao-geral. Tecnologia (TIC/IoT) e mencionada apenas como premissa/contexto, nunca o conhecimento central avaliado - ver context_tags. Contraste deliberado com enade-2021-si-q34 (mesmo tema, tratado tecnicamente, permanece em computing-v1.1).

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-si-d03

- **Ano/curso:** 2021 - Sistemas de Informação
- **Tipo:** discursiva
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): fundamentos-de-sistemas-de-informacao (Fundamentos de Sistemas de Informação)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): fundamentos-de-sistemas-de-informacao (Fundamentos de Sistemas de Informação)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - hierarquia-dado-informacao-conhecimento (Hierarquia Dado-Informação-Conhecimento (DIKW)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): apply, interpret
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "Informações podem ser analisadas para gerar conhecimento tácito ou explícito"

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-si-q05

- **Ano/curso:** 2021 - Sistemas de Informação
- **Tipo:** múltipla escolha
- **Componente:** formacao_geral

**Classificação Fase 5A (histórica):**
- status: `unclassifiable`
- tópico(s) primário(s): _(nenhum)_

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `general-education-v1@1.0.0-pilot`
- status: `proposed`
- tópico(s) primário(s): saude-publica-e-populacoes-vulneraveis (Saúde Pública e Populações Vulneráveis)
- tópico(s) secundário(s): _(nenhum)_
- habilidade(s) cognitiva(s): analyze, evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B secao 7/8: diagnostico individual confirmou conteudo genuino de formacao geral, nunca Computacao - reclassificado para a taxonomia separada general-education-v1 em vez de permanecer unclassifiable.

**Evidências:**
- (statement/statement) "Considerando as informações apresentadas e o alto índice de suicídio da população indígena, avalie as afirmações a seguir."

**Notas técnicas:** Fase 5B: reclassificado de unclassifiable (computing-v1) para general-education-v1 - saude publica/populacoes vulneraveis, area formacao-geral.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-si-q25

- **Ano/curso:** 2021 - Sistemas de Informação
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): principios-de-seguranca-da-informacao (Princípios de Segurança da Informação)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): principios-de-seguranca-da-informacao (Princípios de Segurança da Informação)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - principios-cid-confidencialidade-integridade-disponibilidade (Princípios CID (Confidencialidade, Integridade, Disponibilidade)) (papel: required, confiança: high)
  - legalidade-e-autenticidade-da-informacao (Legalidade e Autenticidade da Informação) (papel: supporting, confiança: medium)
- habilidade(s) cognitiva(s): evaluate
- confiança: `high`

**Motivo da mudança (5A → 5B):** Fase 5B auditoria adversarial (secao 12): a questao testa 5 afirmacoes (I-V), nao apenas a triade CID (I-III) - adicionado concept de suporte para legalidade/autenticidade (IV/V).

**Evidências:**
- (statement/statement) "Em conformidade com a ABNT NBR ISO/IEC 27002 (2013), segurança da informação"

**Notas técnicas:** Fase 5B: adicionado concept de suporte legalidade-e-autenticidade-da-informacao (itens IV/V, nao cobertos pelo concept CID original da Fase 5A).

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer

---

## enade-2021-si-q34

- **Ano/curso:** 2021 - Sistemas de Informação
- **Tipo:** múltipla escolha
- **Componente:** componente_especifico

**Classificação Fase 5A (histórica):**
- status: `proposed`
- tópico(s) primário(s): internet-das-coisas-e-cidades-inteligentes (Internet das Coisas e Cidades Inteligentes)

**Classificação Fase 5B (proposta técnica):**
- taxonomia: `computing-v1@1.1.0-pilot`
- status: `proposed`
- tópico(s) primário(s): internet-das-coisas-e-cidades-inteligentes (Internet das Coisas e Cidades Inteligentes)
- tópico(s) secundário(s): _(nenhum)_
- conceitos:
  - internet-das-coisas (Internet das Coisas (IoT)) (papel: required, confiança: high)
- habilidade(s) cognitiva(s): evaluate, analyze
- confiança: `high`

**Motivo da mudança (5A → 5B):** unchanged - adversarial audit (PROMPT Fase 5B secao 12) found no defect; carried forward under the new taxonomy version.

**Evidências:**
- (statement/statement) "Tornar as cidades mais inteligentes pode ajudar a melhorar os serviços urbanos"

**Notas técnicas:** Contraste deliberado com enade-2021-si-d02 (mesmo tema 'cidade inteligente', mas tratado ali na perspectiva de sustentabilidade/formacao geral, unclassifiable) - aqui a perspectiva e tecnica (TIC/IoT), componente especifico.

**Decisão humana pendente (preencher apenas em `data/semantic/human-adjudication-template-5b.json`, nunca aqui):** ☐ approve ☐ correct ☐ reject ☐ defer
