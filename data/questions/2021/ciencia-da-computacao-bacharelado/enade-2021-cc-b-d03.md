---
id: enade-2021-cc-b-d03
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-b
  pdf_sha256: 0254b274cc4adddbb503cf18553ee70c26014cbb0848fe3c5b787c80137b11e8
  source_path: 2021/b1_prova.pdf
  pages:
  - 14
  - 15
  question_number: 3
  section: componente-especifico-discursiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: componente-especifico-discursiva
question_number: 3
question_type: discursive
content_blocks:
- type: paragraph
  text: 'Um corpo de conhecimento representado na lógica proposicional utiliza os
    conectivos lógicos de implicação ( → ) que representa o condicional, conjunção
    ( ∧ ) que representa o operador lógico AND, a disjunção ( ∨ ) que representa o
    operador lógico OR e a negação ( ¬ ) que representa o operador lógico NOT. Seja
    P o seguinte conjunto de fórmulas da lógica proposicional: 1.a → ¬ b 2.b ∧ a 3.¬
    b ∨ b seja Q o seguinte conjunto de fórmulas da lógica proposicional: 4.a ∨ b
    5.b → a e seja R a fórmula 6.¬ b → a Veja a tabela-verdade para estas fórmulas.'
- type: table
  headers:
  - ''
  - ''
  - '1'
  - '2'
  - '3'
  - '4'
  - '5'
  - '6'
  rows:
  - - a
    - b
    - a → ¬ b
    - b ∧ a
    - ¬ b ∨ b
    - a ∨ b
    - b → a
    - ¬ b → a
  - - F
    - F
    - V
    - F
    - V
    - F
    - V
    - F
  - - F
    - V
    - V
    - F
    - V
    - V
    - F
    - V
  - - V
    - F
    - V
    - F
    - V
    - V
    - V
    - V
  - - V
    - V
    - F
    - V
    - V
    - V
    - V
    - V
  validation_status: verified
- type: asset
  asset_id: table-01
- type: paragraph
  text: 'Sabe-se que cada linha da tabela-verdade corresponde a uma atribuição de
    valores-verdade para os símbolos proposicionais (a e b) e cada coluna corresponde
    à avaliação da fórmula para esta atribuição. Algumas definições: (i) Uma fórmula
    é uma tautologia se e somente se, para toda atribuição de valores-verdade, sua
    avaliação é verdadeira. (ii) Uma atribuição de valores-verdade satisfaz a um conjunto
    de fórmulas se e somente se, para toda fórmula no conjunto, a avaliação é verdadeira.
    (iii) Um conjunto de fórmulas é satisfazível se e somente se existe uma atribuição
    de valores-verdade que satisfaz o conjunto. Em caso contrário, ele é insatisfazível.
    (iv) Uma fórmula é uma consequência lógica de um conjunto de fórmulas se e somente
    se, para toda atribuição de valores-verdade, se a atribuição satisfaz o conjunto
    então satisfaz a fórmula.'
- type: paragraph
  text: 'Com base nas informações apresentadas, responda os itens a seguir. a) Há
    alguma tautologia nas fórmulas 1 a 6? Justifique sua resposta. (valor: 2,5 pontos)
    b) Há algum conjunto (P ou Q) satisfazível? Justifique sua resposta. (valor: 2,5
    pontos) c) Há algum conjunto (P ou Q) insatisfazível? Justifique sua resposta.
    (valor: 2,5 pontos) d) A fórmula 6 é consequência lógica de Q? Justifique sua
    resposta. (valor: 2,5 pontos)'
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2021/b3_padrao.pdf
  pdf_sha256: c0348ce0006201f25e9f97502f59ad1b802c6c3e83c232b9c3c8330f6a6e7ded
  pages:
  - 4
  text: a) O respondente deve dizer que a fórmula 3 contém uma tautologia, pois apresenta
    avaliação verdadeira para toda atribuição (coluna de Vs). b) O respondente deve
    indicar que o conjunto Q é satisfazível, pois todas as fórmulas de Q (4 e 5) são
    verdadeiras para as atribuições 3 e 4 (bastaria uma). c) O respondente deve indicar
    que o conjunto P não é satisfazível, pois não há nenhuma atribuição para a qual
    as fórmulas de P (1, 2 e 3) sejam todas verdadeiras. d) O respondente deve indicar
    que a fórmula 6 é consequência lógica de Q, pois todas as atribuições que satisfazem
    Q (3 e 4) também satisfazem 6.
  assets: []
assets:
- id: table-01
  type: table
  path: enade-2021-cc-b-d03/table-01.png
  source_page: 14
  extraction_method: raster_crop
  sha256: 351e31a199403eec4c2db2bc12794492cd128b9fb7d878f0a80ed495405bb52a
  alt_text: null
  caption: null
subjects: []
topics: []
concepts: []
keywords: []
competencies: []
prerequisites: []
difficulty: null
alternative_diagnostics: {}
extraction_method: text_layer
ocr_confidence: null
extraction_status: verified
automatic_validation: passed
visual_validation: passed
taxonomy_review_status: pending
---

# Questão 3

Um corpo de conhecimento representado na lógica proposicional utiliza os conectivos lógicos de implicação ( → ) que representa o condicional, conjunção ( ∧ ) que representa o operador lógico AND, a disjunção ( ∨ ) que representa o operador lógico OR e a negação ( ¬ ) que representa o operador lógico NOT. Seja P o seguinte conjunto de fórmulas da lógica proposicional: 1.a → ¬ b 2.b ∧ a 3.¬ b ∨ b seja Q o seguinte conjunto de fórmulas da lógica proposicional: 4.a ∨ b 5.b → a e seja R a fórmula 6.¬ b → a Veja a tabela-verdade para estas fórmulas.

|  |  | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | b | a → ¬ b | b ∧ a | ¬ b ∨ b | a ∨ b | b → a | ¬ b → a |
| F | F | V | F | V | F | V | F |
| F | V | V | F | V | V | F | V |
| V | F | V | F | V | V | V | V |
| V | V | F | V | V | V | V | V |

![Tabela (fallback visual fiel)](enade-2021-cc-b-d03/table-01.png)

Sabe-se que cada linha da tabela-verdade corresponde a uma atribuição de valores-verdade para os símbolos proposicionais (a e b) e cada coluna corresponde à avaliação da fórmula para esta atribuição. Algumas definições: (i) Uma fórmula é uma tautologia se e somente se, para toda atribuição de valores-verdade, sua avaliação é verdadeira. (ii) Uma atribuição de valores-verdade satisfaz a um conjunto de fórmulas se e somente se, para toda fórmula no conjunto, a avaliação é verdadeira. (iii) Um conjunto de fórmulas é satisfazível se e somente se existe uma atribuição de valores-verdade que satisfaz o conjunto. Em caso contrário, ele é insatisfazível. (iv) Uma fórmula é uma consequência lógica de um conjunto de fórmulas se e somente se, para toda atribuição de valores-verdade, se a atribuição satisfaz o conjunto então satisfaz a fórmula.

Com base nas informações apresentadas, responda os itens a seguir. a) Há alguma tautologia nas fórmulas 1 a 6? Justifique sua resposta. (valor: 2,5 pontos) b) Há algum conjunto (P ou Q) satisfazível? Justifique sua resposta. (valor: 2,5 pontos) c) Há algum conjunto (P ou Q) insatisfazível? Justifique sua resposta. (valor: 2,5 pontos) d) A fórmula 6 é consequência lógica de Q? Justifique sua resposta. (valor: 2,5 pontos)
