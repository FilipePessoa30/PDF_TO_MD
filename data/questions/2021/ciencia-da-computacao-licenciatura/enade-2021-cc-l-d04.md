---
id: enade-2021-cc-l-d04
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-l
  pdf_sha256: 9537deb2d2d7f7e00eacd526a06b887e932fedf4b5e7abf9be6501138d561b72
  source_path: 2021/l1_prova.pdf
  pages:
  - 16
  question_number: 4
  section: componente-especifico-discursiva
applicable_courses:
- ciencia-da-computacao-licenciatura
section: componente-especifico-discursiva
question_number: 4
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2021/l3_padrao.pdf
  pdf_sha256: e8083c85e549eefeb4a31ff9220fb52eb8c657f903c65d2fed221db985d6e53e
  pages:
  - 5
  - 6
  text: 'O respondente deve descrever a tabela verdade e desenhar o diagrama, conforme
    abaixo.


    A tabela verdade pode ser feita de maneiras diferentes, trocando “1”s e “0” por
    “V” e “F”, ou por “T” ou “F”. Além disso, as linhas podem aparecer em qualquer
    ordem arbitrária. O circuito lógico pode ser resolvido de várias maneiras, existindo
    variações de notação, e mais de um circuito que realiza a mesma operação. O circuito
    proposto, inclusive, reúne as duas saídas em um só circuito. Notações possíveis
    são apresentadas na seguinte imagem, do padrão IEC 60617-12, e também do ANSI
    IEEE.


    Outros circuitos possíveis, sem ser uma lista completa, são: Exemplos de resposta
    possíveis para ‘S’:


    Exemplos de resposta possíveis para ‘Cout’:'
  assets:
  - id: padrao-01
    type: diagram
    path: enade-2021-cc-l-d04/answer-standard/padrao-01.png
    source_page: 5
    extraction_method: raster_crop
    sha256: 38b8eec545a826e0d18f07790d40e7be92d631e055ec534e579e071312414383
    alt_text: null
    caption: null
  - id: padrao-02
    type: diagram
    path: enade-2021-cc-l-d04/answer-standard/padrao-02.png
    source_page: 5
    extraction_method: raster_crop
    sha256: f5e2a42493bee59c0a1c04d6a3aeba5dad2aaedc072c2b9ce82e247024baf152
    alt_text: null
    caption: null
  - id: padrao-03
    type: diagram
    path: enade-2021-cc-l-d04/answer-standard/padrao-03.png
    source_page: 6
    extraction_method: raster_crop
    sha256: 4e3416284330269cfce726362e539837ea414dd52e7f15368dfba6c3e1eb2ca1
    alt_text: null
    caption: null
  - id: padrao-04
    type: diagram
    path: enade-2021-cc-l-d04/answer-standard/padrao-04.png
    source_page: 6
    extraction_method: raster_crop
    sha256: 2744dac26f9039e943264a50d78de39025a3bb80a775df5b5063cc72f864c193
    alt_text: null
    caption: null
assets:
- id: figure-01
  type: diagram
  path: enade-2021-cc-l-d04/figure-01.png
  source_page: 16
  extraction_method: raster_crop
  sha256: 9c4c1b2b4c072920e25aa057052e721ee41e568aa45052c8e2b4478ea33fa918
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
extraction_status: extracted
automatic_validation: passed
visual_validation: not_performed
taxonomy_review_status: pending
---

# Questão 4

A soma de dois números binários é feita bit a bit, começando da direita (menos significativo) para a esquerda (mais significativo), passando o transporte, vai um (do inglês, carry out, representado na figura como Cout), para o bit seguinte como vem um (do inglês, carry in, representado na figura como Cin). Uma forma simples de implementar um somador de N bits é implementar N somadores elementares de 1 bit. Cada somador de um bit tem as entradas A, B e carry in (Cin) e as saídas Soma (S) e carry out (Cout). DELGADO, J.; RIBEIRO, C. Arquitetura de Computadores. Rio de Janeiro: LTC, 2009 (adaptado).

![Figura da questão](enade-2021-cc-l-d04/figure-01.png)

A	S B	Somador Completo

Com base no somador completo de 1-bit apresentado na figura, descreva sua tabela verdade e o diagrama do seu circuito lógico. (valor: 10,0 pontos)
