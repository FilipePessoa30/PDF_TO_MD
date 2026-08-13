---
id: enade-2011-computing-q40
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 25
  question_number: 40
  section: componente-especifico-objetiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: componente-especifico-objetiva
question_number: 40
question_type: multiple_choice
content_blocks: null
correct_answer: B
official_answer_source: 2011/2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: image
  path: enade-2011-computing-q40/figure-01.png
  source_page: 25
  extraction_method: raster_crop
  sha256: dd186047586118fdd7cd495343f3cd3566da3ac7362e14a8eb57ae9d2b4c4c1a
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

# Questão 40

Considere que a figura abaixo corresponde ao cenário de um jogo de computador. Esse cenário é dividido em 24 quadrados e a movimentação de um personagem entre cada quadrado tem custo 1, sendo permitida apenas na horizontal ou na vertical. Os quadrados marcados em preto correspondem a regiões para as quais os personagens não podem se mover.

![Figura da questão](enade-2011-computing-q40/figure-01.png)

Nesse cenário, o algoritmoA* vai ser usado para determinar o caminho de custo mínimo pelo qual um personagem deve se mover desde o quadrado verde até o quadrado vermelho. Considere que, no A*, o custo f(x) = g(x) + h(x) de determinado nó x é computado somando-se o custo real g(x) ao custo da função heurística h(x) e que a função heurística utilizada é a distância de Manhattan (soma das distâncias horizontal e vertical de x até o objetivo). Desse modo, o custo f(x) do quadrado verde é igual a

## Alternativas

A. 2.
B. 3.
C. 5.
D. 7.
E. 9.
