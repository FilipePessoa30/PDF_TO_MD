---
id: enade-2008-computing-q18
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 9
  question_number: 18
  section: nucleo-comum-objetiva
applicable_courses:
- all-computing
section: nucleo-comum-objetiva
question_number: 18
question_type: multiple_choice
content_blocks: null
correct_answer: C
official_answer_source: 2008/b2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets: []
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

# Questão 18

Os números de Fibonacci constituem uma seqüência de números na qual os dois primeiros elementos são 0 e 1 e os demais, a soma dos dois elementos imediatamente anteriores na seqüência. Como exemplo, a seqüência formada pelos 10 primeiros números de Fibonacci é: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34. Mais precisamente, é possível definir os números de Fibonacci pela seguinte relação de recorrência: fib (n) = 0, se n = 0 fib (n) = 1, se n = 1 fib (n) = fib (n ! 1) + fib (n ! 2), se n > 1 Abaixo, apresenta-se uma implementação em linguagem funcional para essa relação de recorrência: fib :: Integer -> Integer fib 0 = 0 fib 1 = 1 fib n = fib (n ! 1) + fib (n ! 2) Considerando que o programa acima não reutilize resultados previamente computados, quantas chamadas são feitas à função fib para computar fib 5?

## Alternativas

A. 11
B. 12
C. 15
D. 24
E. 25
