---
id: enade-2008-computing-d20
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 10
  question_number: 20
  section: nucleo-comum-discursiva
applicable_courses:
- all-computing
section: nucleo-comum-discursiva
question_number: 20
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
  text: 'A. Colisões ocorrerão entre elementos cujas chaves forem mapeadas pela função
    de dispersão h(x) = x mod 23 no mesmo endereço-base. Portanto, o conjunto de chaves
    envolvidas em colisões é dado por {44, 49, 95, 90}. B. O estudante deverá mostrar
    a seguinte configuração da tabela de dispersão.


    Entradas da tabela foram omitidas por questão de espaço (entradas de 6 a 20) e
    correspondem a entradas com ponteiros nulos, semelhantes à entrada de índice 22.'
  assets:
  - id: padrao-01
    type: diagram
    path: enade-2008-computing-d20/answer-standard/padrao-01.png
    source_page: 1
    extraction_method: raster_crop
    sha256: da3895e08c98dc818371326f73e44198af203adce1b50dec62921a5123cab6a0
    alt_text: null
    caption: null
assets:
- id: figure-01
  type: diagram
  path: enade-2008-computing-d20/figure-01.png
  source_page: 10
  extraction_method: raster_crop
  sha256: 387cf7485170eab59f1f3ffa7e5a23a856de1e1723d32f8b3954834554cdaa9b
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

# Questão 20

Tabelas de dispersão (tabelas

![Figura da questão](enade-2008-computing-d20/figure-01.png)

hash) armazenam elementos com base no valor absoluto de suas chaves e em técnicas de tratamento de colisões. As funções de dispersão transformam chaves em endereços- base da tabela, ao passo que o tratamento de colisões resolve conflitos em casos em que mais de uma chave é mapeada para um mesmo endereço-base da tabela. Suponha que uma aplicação utilize uma tabela de dispersão com 23 endereços-base (índices de 0 a 22) e empregue h(x) = x mod 23 como função de dispersão, em que x representa a chave do elemento cujo endereço-base deseja-se computar. Inicialmente, essa tabela de dispersão encontra-se vazia. Em seguida, a aplicação solicita uma seqüência de inserções de elementos cujas chaves aparecem na seguinte ordem: 44, 46, 49, 70, 27, 71, 90, 97, 95. Com relação à aplicação descrita, faça o que se pede a seguir. A Escreva, no espaço reservado, o conjunto das chaves envolvidas em

B Assuma que a tabela de dispersão trate colisões por meio de
