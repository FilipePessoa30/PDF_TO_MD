---
id: enade-2008-computing-q23
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 11
  question_number: 23
  section: cc-bacharelado-objetiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: cc-bacharelado-objetiva
question_number: 23
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: Considere o esquema de banco de dados relacional apresentado a seguir, formado
    por 4 relações, que representa o conjunto de estudantes de uma universidade que
    podem, ou não, morar em repúblicas (moradias compartilhadas por estudantes). A
    relação Estudante foi modelada como um subconjunto da relação Pessoa. Considere
    que os atributos grifados correspondam à chave primária da respectiva relação
    e os atributos que são seguidos da palavra referencia sejam chaves estrangeiras.
- type: asset
  asset_id: figure-01
- type: paragraph
  text: 'Suponha que existam as seguintes tuplas no banco de dados:'
- type: code
  text: 'Pessoa(1, ‘José Silva’, ‘Rua 1, 20’);

    Republica(20, ‘Várzea’, ‘Rua Chaves, 2001’)'
  language: null
- type: paragraph
  text: Qual opção apresenta apenas tuplas válidas para esse esquema de banco de dados
    relacional?
correct_answer: E
official_answer_source: 2008/b2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: diagram
  path: enade-2008-computing-q23/figure-01.png
  source_page: 11
  extraction_method: raster_crop
  sha256: 54d4c7766146ac13f8d5e5f37bd09928f8ecde74d1421190d5c2e8bcd2ac2fb5
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

# Questão 23

Considere o esquema de banco de dados relacional apresentado a seguir, formado por 4 relações, que representa o conjunto de estudantes de uma universidade que podem, ou não, morar em repúblicas (moradias compartilhadas por estudantes). A relação Estudante foi modelada como um subconjunto da relação Pessoa. Considere que os atributos grifados correspondam à chave primária da respectiva relação e os atributos que são seguidos da palavra referencia sejam chaves estrangeiras.

![Figura da questão](enade-2008-computing-q23/figure-01.png)

Suponha que existam as seguintes tuplas no banco de dados:

```
Pessoa(1, ‘José Silva’, ‘Rua 1, 20’);
Republica(20, ‘Várzea’, ‘Rua Chaves, 2001’)
```

Qual opção apresenta apenas tuplas válidas para esse esquema de banco de dados relacional?

## Alternativas

A. Estudante(10, ‘jsilva@ig.com.br’, null, 20); FonePessoa(10, ‘019’, ‘3761’, ‘1370’)
B. Estudante(10, ‘jsilva@ig.com.br’, 1, null); FonePessoa(10, ‘019’, ‘3761’, ‘1370’)
C. Estudante(10, ‘jsilva@ig.com.br’, 1, 20); FonePessoa(1, null, ‘3761’, ‘1370’)
D. Estudante(10, ‘jsilva@ig.com.br’, 1, 50); FonePessoa(1, ‘019’, ‘3761’, ‘1370’)
E. Estudante(10, ‘jsilva@ig.com.br’, 1, null); FonePessoa(1, ‘019’, ‘3761’, ‘1370’)
