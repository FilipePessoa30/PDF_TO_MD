---
id: enade-2011-computing-q44
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 28
  question_number: 44
  section: componente-especifico-objetiva
applicable_courses:
- engenharia-da-computacao
section: componente-especifico-objetiva
question_number: 44
question_type: multiple_choice
content_blocks: null
correct_answer: null
official_answer_source: 2011/2_gabarito.pdf
answer_validation_status: annulled
answer_standard: null
assets:
- id: figure-01
  type: image
  path: enade-2011-computing-q44/figure-01.png
  source_page: 28
  extraction_method: raster_crop
  sha256: 540b405fd4deaec12f68a98552370c7c2f51c1075810dddc8c19bdf294ca845f
  alt_text: null
  caption: null
- id: figure-02
  type: image
  path: enade-2011-computing-q44/figure-02.png
  source_page: 28
  extraction_method: raster_crop
  sha256: 1e654c30e3204d11e10c28f344e8fba75388cf6b08c7af8330bdf9d048903a6d
  alt_text: null
  caption: null
- id: figure-03
  type: image
  path: enade-2011-computing-q44/figure-03.png
  source_page: 28
  extraction_method: raster_crop
  sha256: e5f00da72ab556fe7b8eb5d36d7e5746ba6548a4bf9df3ce584d49fe2c67c3f7
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

# Questão 44

A utilização dos somadores completos em cascata no projeto de Unidades Lógicas Aritméticas pode comprometer o seu desempenho, uma vez que o sinal de vai-um final deve propagar por todos os somadores, desde as entradas dos bits menos significativos. Esse caminho crítico insere um atraso no sistema que compromete o projeto de ULAs rápidas. Para reduzir esse atraso, mecanismos de predição de vai-um podem ser usados. Um esquema bem simples de predição de vai-um para um somador de 8 bits é apresentado na figura a seguir.

![Figura da questão](enade-2011-computing-q44/figure-01.png)

Os 4 bits mais significativos são somados de forma redundante, considerando o vem-um 0 no primeiro somador e vem-um igual a 1 no segundo somador. A saída dos somadores é selecionada a partir de um multiplexador, que é acionado pelo vai-um resultado da soma dos 4 bits menos significativos. Como os 3 somadores podem realizar as operações ao mesmo tempo, o multiplexador pode entregar o resultado mais rapidamente. Considere as seguintes equações dos somadores:

![Figura da questão](enade-2011-computing-q44/figure-02.png)

Considere, ainda, a equação dos multiplexadores a seguir:

![Figura da questão](enade-2011-computing-q44/figure-03.png)

Suponha que o somador de 8 bits tem predição de vai-um baseada na duplicação da soma dos 4 bits mais significativos e que 7 ns é o tempo de atraso de propagação por nível de porta AND, OR e XOR. Desconsiderando os inversores, o aumento do número de portas e a redução do tempo de propagação podem ser expressos, em porcentagem, como aumento de

## Alternativas

A. 26 portas, representando 65% de acréscimo no número de portas e redução de 112 ns para 70 ns, redução de 47% do tempo para a execução da soma.
B. 20 portas, representando 50% de acréscimo no número de portas e redução de 112 ns para 70 ns, redução de 47% do tempo para a execução da soma.
C. 26 portas, representando 65% de acréscimo no número de portas e redução de 112 ns para 56 ns, redução de 50% do tempo para a execução da soma.
D. 20 portas, representando 50% de acréscimo no número de portas e redução de 112 ns para 56 ns, redução de 50% do tempo para a execução da soma.
E. 26 portas, representando 65% de acréscimo no número de portas. Não há redução no tempo de atraso de propagação para a execução da soma.
