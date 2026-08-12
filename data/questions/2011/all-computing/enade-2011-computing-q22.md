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
  text: Considere a seguinte tabela verdade, na qual estão definidas quatro entradas
    – A, B, C e D – e uma saída S.
- type: table
  headers:
  - A
  - B
  - C
  - D
  - S
  rows:
  - - '0'
    - '0'
    - '0'
    - '0'
    - '1'
  - - '0'
    - '0'
    - '0'
    - '1'
    - '0'
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
  validation_status: verified
- type: asset
  asset_id: table-01
- type: paragraph
  text: A menor expressão de chaveamento representada por uma soma de produtos correspondente
    à saída S é
correct_answer: C
official_answer_source: 2011/2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: table-01
  type: table
  path: enade-2011-computing-q22/table-01.png
  source_page: 14
  extraction_method: raster_crop
  sha256: 8947a731978088902220fa2e933a310a99d47ed4deee51a18ef1cb897ba580d1
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

# Questão 22

Considere a seguinte tabela verdade, na qual estão definidas quatro entradas – A, B, C e D – e uma saída S.

| A | B | C | D | S |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 1 |
| 0 | 0 | 0 | 1 | 0 |
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

A menor expressão de chaveamento representada por uma soma de produtos correspondente à saída S é

## Alternativas

A. AB’(D+C’)+A’D’+ABC.
B. AD + A’BD’+A’BC+A’B’C’.
C. A’D’ + AB’D+AB’C’+ABC.
D. (A’+D)(A+B+C’)(A+B’+C+D’).
E. (A+D’)(A’+B’+C)(A’+B+C’+D).
