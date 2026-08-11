---
id: fixture-2021-b-d99-content-blocks
exam_year: 2021
source_occurrences:
  - exam_id: enade-2021-b
    pdf_sha256: deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
    source_path: 2021/b1_prova.pdf
    pages: [14]
    question_number: 99
    section: componente-especifico
applicable_courses:
  - ciencia-da-computacao-bacharelado
section: componente-especifico
question_number: 99
question_type: discursive
correct_answer: null
official_answer_source: null
answer_validation_status: pending
content_blocks:
  - type: paragraph
    text: "Considere a tabela-verdade a seguir para as proposições p e q."
  - type: table
    headers: ["p", "q", "p -> q"]
    rows:
      - ["V", "V", "V"]
      - ["V", "F", "F"]
      - ["F", "V", "V"]
      - ["F", "F", "V"]
    validation_status: verified
  - type: paragraph
    text: "A seguir, o trecho de pseudocódigo que implementa a verificação:"
  - type: code
    text: |-
      funcao implica(p, q)
          retorne (nao p) ou q
      fim funcao
    language: pseudocode
  - type: asset
    asset_id: table-crop-01
assets:
  - id: table-crop-01
    type: table
    path: fixture-2021-b-d99-content-blocks/table-crop-01.png
    source_page: 14
    extraction_method: raster_crop
    sha256: null
    alt_text: "Crop fiel da tabela-verdade original, usado como fallback visual"
    caption: "Tabela-verdade (fallback visual)"
subjects: []
topics: []
concepts: []
keywords: []
competencies: []
prerequisites: []
difficulty: null
alternative_diagnostics: {}
extraction_method: pending
ocr_confidence: null
extraction_status: needs_review
taxonomy_review_status: pending
---

# Questão 99

Considere a tabela-verdade a seguir para as proposições p e q.

| p | q | p -> q |
| --- | --- | --- |
| V | V | V |
| V | F | F |
| F | V | V |
| F | F | V |

A seguir, o trecho de pseudocódigo que implementa a verificação:

```pseudocode
funcao implica(p, q)
    retorne (nao p) ou q
fim funcao
```

![Tabela-verdade (fallback visual)](fixture-2021-b-d99-content-blocks/table-crop-01.png)
