---
id: enade-2011-computing-q38
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 25
  question_number: 38
  section: componente-especifico-objetiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: componente-especifico-objetiva
question_number: 38
question_type: multiple_choice
content_blocks: null
correct_answer: E
official_answer_source: 2011/2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: image
  path: enade-2011-computing-q38/figure-01.png
  source_page: 25
  extraction_method: raster_crop
  sha256: ae4b37fd1a67dd389cb50b156c2aac9fe6e77ab696a78c5d5481864e7be9a106
  alt_text: null
  caption: null
- id: figure-02
  type: image
  path: enade-2011-computing-q38/figure-02.png
  source_page: 25
  extraction_method: raster_crop
  sha256: ace7993540025c156bca32f2402926d41cafebc4e213f7d9fba020394afff824
  alt_text: null
  caption: null
- id: figure-03
  type: image
  path: enade-2011-computing-q38/figure-03.png
  source_page: 25
  extraction_method: raster_crop
  sha256: 3515d6f4f52e78e160b972713ed6af885518127961f65adc379b09d592ad0b47
  alt_text: null
  caption: null
- id: figure-04
  type: image
  path: enade-2011-computing-q38/figure-04.png
  source_page: 25
  extraction_method: raster_crop
  sha256: 4f20b5db44bbab6bb08bec10dbf7e0ef1e063c8e027bda53ac654019c56b4238
  alt_text: null
  caption: null
- id: figure-05
  type: image
  path: enade-2011-computing-q38/figure-05.png
  source_page: 25
  extraction_method: raster_crop
  sha256: 225d251de725980e7c437a839114d55a35353fe48cbcdd96360be8197289644f
  alt_text: null
  caption: null
- id: figure-06
  type: image
  path: enade-2011-computing-q38/figure-06.png
  source_page: 25
  extraction_method: raster_crop
  sha256: 93c771c65746bc44b488d2594193740fef9cebddc334ac78915bf34bb66fb562
  alt_text: null
  caption: null
- id: figure-07
  type: image
  path: enade-2011-computing-q38/figure-07.png
  source_page: 25
  extraction_method: raster_crop
  sha256: 661751e3e48c1cd7ea02399dfb540fb2f9a2d97327ee6ea88eeb6cc01ae5ecbf
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

# Questão 38

É comum que linguagens de programação permitam a descrição textual de constantes em hexadecimal, além de descrições na base dez. O compilador para uma linguagem que suporte constantes inteiras em hexadecimal precisa diferenciar inteiros em base dez dos

![Figura da questão](enade-2011-computing-q38/figure-01.png)

hexadecimal. Uma maneira de resolver esse problema é exigindo que as constantes em hexadecimal terminem com o caracter “ ”. Assim, não há ambiguidade,g por g

![Figura da questão](enade-2011-computing-q38/figure-03.png)

A gramática a seguir descreve números inteiros, possivelmente com o símbolo “ ” após os dígitos. Os não

![Figura da questão](enade-2011-computing-q38/figure-02.png)

M → E M → N E → N N

![Figura da questão](enade-2011-computing-q38/figure-05.png)

N → d Durante a construção de um autômato LR para essa gramática, os seguintes estados são definidos: e0: M´ → ·M M → ·E M → ·N E → ·N N

![Figura da questão](enade-2011-computing-q38/figure-06.png)

N → ·d e1(e0, N): M → N · M → N ·

![Figura da questão](enade-2011-computing-q38/figure-07.png)

A respeito dessa gramática, analise as seguintes asserções e a relação proposta entre elas. A gramática descrita é do tipo LR(0). PORQUE É possível construir um autômato LR(0), determinístico, cujos estados incluem e acima descritos.

![Figura da questão](enade-2011-computing-q38/figure-04.png)

Acerca dessas asserções, assinale a opção correta.

## Alternativas

A. As duas asserções são proposições verdadeiras, e a segunda é uma justificativa correta da primeira.
B. As duas asserções são proposições verdadeiras, mas a segunda não é uma justificativa correta da primeira.
C. A primeira asserção é uma proposição verdadeira, e a segunda, uma proposição falsa.
D. A primeira asserção é uma proposição falsa, e a segunda, uma proposição verdadeira.
E. Tanto a primeira quanto a segunda asserções são proposições falsas.
