---
id: enade-2008-computing-d39
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 16
  question_number: 39
  section: cc-bacharelado-discursiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: cc-bacharelado-discursiva
question_number: 39
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2008/b3_padrao.pdf
  pdf_sha256: 7021d115731ddcbad3c227da50f6d8c9c2c7f8a5a4b4d7dabce4b3726d0d35ef
  pages:
  - 1
  text: 'A. O estudante deverá mostrar a seguinte árvore de análise sintática, sendo
    facultativo desenhar as elipses


    B. Não. O fato de haver diversas derivações possíveis para uma expressão não implica
    a existência de árvores de análise sintática distintas. Uma árvore de análise
    sintática geralmente corresponde a diversas derivações e isso não significa que
    a gramática seja ambígua. A gramática seria ambígua se houvesse mais de uma árvore
    de análise sintática para uma mesma expressão.'
  assets:
  - id: padrao-01
    type: diagram
    path: enade-2008-computing-d39/answer-standard/padrao-01.png
    source_page: 1
    extraction_method: raster_crop
    sha256: 093af7d31238d2484a74986c08d5649e094465f168e645679a69d8d1c2f22fe5
    alt_text: null
    caption: null
assets:
- id: figure-01
  type: diagram
  path: enade-2008-computing-d39/figure-01.png
  source_page: 16
  extraction_method: raster_crop
  sha256: ac6a73426c436a2d90c8707e7a0a242cdc2036d72e2e11426e4d91f537ae50b7
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

# Questão 39

Qualquer expressão aritmética binária pode ser convertida em uma expressão totalmente parentizada, bastando reescrever cada subexpressão binária a q b como (a q b), em que q denota um operador binário. Expressões nesse formato podem ser definidas por regras de uma gramática livre de contexto, conforme apresentado a seguir. Nessa gramática, os símbolos não-terminais E, S, O e L representam expressões, subexpressões, operadores e literais, respectivamente, e os demais símbolos das regras são terminais. E 6 ( S O S ) S 6 L | E O 6 + | - | * | / L 6 a | b | c | d | e Tendo como referência as informações acima, faça o que se pede a seguir. A Mostre que a expressão (a * (b / c)) pode ser obtida por derivações das regras acima. Para isso, desenhe a árvore de análise sintática correspondente. (valor: 5,0 pontos)

B Existem diferentes derivações para a expressão (((a + b) * c) + (d * e)). É correto, então, afirmar que a

![Figura da questão](enade-2008-computing-d39/figure-01.png)
