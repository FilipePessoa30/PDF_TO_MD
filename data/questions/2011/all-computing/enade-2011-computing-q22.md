---
id: enade-2011-computing-q22
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 14
  question_number: 22
  section: componente-especifico-comum-objetiva
applicable_courses:
- all-computing
section: componente-especifico-comum-objetiva
question_number: 22
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: "Considere a seguinte tabela verdade, na qual estão definidas quatro entradas\
    \ – A, B, C e D – e uma saída S. A\tS C\t0 B\t1 D\t0"
- type: asset
  asset_id: figure-01
- type: table
  headers:
  - '0'
  - '0'
  - '0'
  - '1'
  - '0'
  rows:
  - - '0'
    - '0'
    - '1'
    - '0'
    - '1'
  - - '0'
    - '0'
    - '1'
    - '1'
    - '0'
  - - '0'
    - '1'
    - '0'
    - '0'
    - '1'
  - - '0'
    - '1'
    - '0'
    - '1'
    - '0'
  - - '0'
    - '1'
    - '1'
    - '0'
    - '1'
  - - '0'
    - '1'
    - '1'
    - '1'
    - '0'
  - - '1'
    - '0'
    - '0'
    - '0'
    - '1'
  - - '1'
    - '0'
    - '0'
    - '1'
    - '1'
  - - '1'
    - '0'
    - '1'
    - '0'
    - '0'
  - - '1'
    - '0'
    - '1'
    - '1'
    - '1'
  - - '1'
    - '1'
    - '0'
    - '0'
    - '0'
  - - '1'
    - '1'
    - '0'
    - '1'
    - '0'
  - - '1'
    - '1'
    - '1'
    - '0'
    - '1'
  - - '1'
    - '1'
    - '1'
    - '1'
    - '1'
  validation_status: needs_review
- type: asset
  asset_id: table-01
- type: asset
  asset_id: figure-02
- type: paragraph
  text: A menor expressão de chaveamento representada por uma soma de produtos correspondente
    à saída S é
correct_answer: C
official_answer_source: 2011/2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: image
  path: enade-2011-computing-q22/figure-01.png
  source_page: 14
  extraction_method: raster_crop
  sha256: d6ebd0fbc06cdc49386d80a549739c4f1ea4442ed303891cf0cfe3cca10df501
  alt_text: null
  caption: null
- id: figure-02
  type: image
  path: enade-2011-computing-q22/figure-02.png
  source_page: 14
  extraction_method: raster_crop
  sha256: fc47de09576cda535f57036fb34c893b66a13d66f10d70786751001539f4f6e2
  alt_text: null
  caption: null
- id: table-01
  type: table
  path: enade-2011-computing-q22/table-01.png
  source_page: 14
  extraction_method: raster_crop
  sha256: 1158fc7497ce693875d0b626865ef0764227e14ec911acde3371f11ea52d9398
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
extraction_status: needs_review
automatic_validation: passed
visual_validation: failed
taxonomy_review_status: pending
---

# Questão 22

Considere a seguinte tabela verdade, na qual estão definidas quatro entradas – A, B, C e D – e uma saída S. A	S C	0 B	1 D	0

![Figura da questão](enade-2011-computing-q22/figure-01.png)

| 0 | 0 | 0 | 1 | 0 |
| --- | --- | --- | --- | --- |
| 0 | 0 | 1 | 0 | 1 |
| 0 | 0 | 1 | 1 | 0 |
| 0 | 1 | 0 | 0 | 1 |
| 0 | 1 | 0 | 1 | 0 |
| 0 | 1 | 1 | 0 | 1 |
| 0 | 1 | 1 | 1 | 0 |
| 1 | 0 | 0 | 0 | 1 |
| 1 | 0 | 0 | 1 | 1 |
| 1 | 0 | 1 | 0 | 0 |
| 1 | 0 | 1 | 1 | 1 |
| 1 | 1 | 0 | 0 | 0 |
| 1 | 1 | 0 | 1 | 0 |
| 1 | 1 | 1 | 0 | 1 |
| 1 | 1 | 1 | 1 | 1 |

![Tabela (fallback visual fiel)](enade-2011-computing-q22/table-01.png)

![Figura da questão](enade-2011-computing-q22/figure-02.png)

A menor expressão de chaveamento representada por uma soma de produtos correspondente à saída S é

## Alternativas

A. AB’(D+C’)+A’D’+ABC.
B. AD + A’BD’+A’BC+A’B’C’.
C. A’D’ + AB’D+AB’C’+ABC.
D. (A’+D)(A+B+C’)(A+B’+C+D’).
E. (A+D’)(A’+B’+C)(A’+B+C’+D).
