---
id: enade-2011-computing-q43
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 27
  question_number: 43
  section: componente-especifico-objetiva
applicable_courses:
- engenharia-da-computacao
section: componente-especifico-objetiva
question_number: 43
question_type: multiple_choice
content_blocks: null
correct_answer: D
official_answer_source: 2011/2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: image
  path: enade-2011-computing-q43/figure-01.png
  source_page: 27
  extraction_method: raster_crop
  sha256: 2a7e4a2cf75bd6d34840fd3f5254305353b187b431564caeb9957fc680b3cda0
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

# Questão 43

![Figura da questão](enade-2011-computing-q43/figure-01.png)

O registrador do sistema mantém o valor chaveado e é comandado por um clock de sistema better-than-worst-case. Um registrador adicional é comandado separadamente por um clock ligeiramente atrasado com relação ao do sistema. Se os resultados armazenados nos dois registradores são diferentes, então um erro ocorreu, provavelmente devido à temporização. A porta XOR detecta o erro e faz com que este valor seja substituído por aquele no registrador do sistema. Wolf, W. High-performance embedded computing: architectures, applications, and methodologies. Morgan Kaufmann, 2007 Considerando essas informações, analise as afirmações a seguir. I. Sistemas digitais são tradicionalmente concebidos como sistemas assíncronos regidos por um clock. II. Better-than-worst-case é um estilo de projeto alternativo em que a lógica detecta e se recupera de erros, permitindo que o circuito possa operar com uma frequência maior. III. Nos sistemas digitais, o período de clock é determinado por uma análise cuidadosa para que os valores sejam armazenados corretamente nos registradores, com o período de clock alargado para abranger o atraso de pior caso. É correto o que se afirma em

## Alternativas

A. I, apenas.
B. III, apenas.
C. I e II, apenas.
D. II e III, apenas.
E. I, II e III.
