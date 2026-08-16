---
id: enade-2008-computing-q51
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 22
  question_number: 51
  section: engenharia-computacao-objetiva
applicable_courses:
- engenharia-da-computacao
section: engenharia-computacao-objetiva
question_number: 51
question_type: multiple_choice
content_blocks: null
correct_answer: A
official_answer_source: 2008/b2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: diagram
  path: enade-2008-computing-q51/figure-01.png
  source_page: 22
  extraction_method: raster_crop
  sha256: 47cafcad88f13696a0c4e67ac5d4bcd91ad7d225430e981d76674174ac887e6d
  alt_text: null
  caption: null
- id: figure-02
  type: diagram
  path: enade-2008-computing-q51/figure-02.png
  source_page: 22
  extraction_method: raster_crop
  sha256: 5be18846057a966b63eb7d121a8642f72c9f9adf73b84b7efb30d096c7a23511
  alt_text: null
  caption: null
- id: figure-03
  type: diagram
  path: enade-2008-computing-q51/figure-03.png
  source_page: 22
  extraction_method: raster_crop
  sha256: 9d5c7ff6d19d8429dfbdc4280477f1ef35ccbb3483278d0587c31f75bdff377b
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

# Questão 51

Considere um jogo do tipo 8-puzzle, cujo objetivo é conduzir o tabuleiro esquematizado na figura abaixo para o seguinte estado final.

![Figura da questão](enade-2008-computing-q51/figure-02.png)

Considere, ainda, que, em determinado instante do jogo, se tenha o estado E0 a seguir.

![Figura da questão](enade-2008-computing-q51/figure-03.png)

Pelas regras desse jogo, sabe-se que os próximos estados possíveis são os estados E1, E2 e E3 mostrados abaixo.

![Figura da questão](enade-2008-computing-q51/figure-01.png)

Considere uma função heurística h embasada na soma das distâncias das peças em relação ao estado final desejado, em que a distância d a que uma peça p está da posição final é dada pela soma do número de linhas com o número de colunas que a separam da posição final desejada. Por exemplo, em E1, d(1) = 2 + 1 = 3. A partir dessas informações analise as asserções a seguir. Utilizando-se um algoritmo de busca gulosa pela melhor escolha que utiliza a função h, o próximo estado no desenvolvimento do jogo a partir do estado E0 tem de ser E3 porque, dos três estados E1, E2 e E3 possíveis, o estado com menor soma das distâncias entre a posição atual das peças e a posição final é o estado E3. Assinale a opção correta a respeito dessas asserções.

## Alternativas

A. As duas asserções são proposições verdadeiras, e a segunda é uma justificativa correta da primeira.
B. As duas asserções são proposições verdadeiras, e a segunda não é uma justificativa correta da primeira.
C. A primeira asserção é uma proposição verdadeira, e a segunda é uma proposição falsa.
D. A primeira asserção é uma proposição falsa, e a segunda é uma proposição verdadeira.
E. As duas asserções são proposições falsas.
