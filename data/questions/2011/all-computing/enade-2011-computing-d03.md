---
id: enade-2011-computing-d03
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 18
  question_number: 3
  section: componente-especifico-comum-discursiva
applicable_courses:
- all-computing
section: componente-especifico-comum-discursiva
question_number: 3
question_type: discursive
content_blocks: null
correct_answer: null
official_answer_source: null
answer_validation_status: not_applicable
answer_standard:
  source_path: 2011/3_padrao.pdf
  pdf_sha256: 386353635a8e2fa8081dce177f37918bcaf9426d8ee6881b88aa739bdf0cd412
  pages:
  - 2
  text: 'Algoritmo iterativo int fibonacci(n) { prevFib Å 0, currFib Å 1 if n == 1
    return 0 if n == 2 return 1 for i Å 1 to n − 2 /* repetir n‐2 vezes */ { temp
    Å prevFib + currFib prevFib Å currFib currFib Å temp }


    return currFib } Algoritmo recursivo int fibonacci(n) { if n == 1 return 0 if
    n == 2 return 1 else return fibonacci(n‐1) + fibonacci(n‐2) } Discussão: A solução
    recursiva clássica possui a vantagem de ser implementada diretamente a partir
    da definição do problema, mas tem a grande desvantagem de possuir uma ordem de
    complexidade exponencial. A versão iterativa tem complexidade linear o que a torna
    mais vantajosa em termos de eficiência, mas exige mais atenção na implementação.'
  assets: []
assets:
- id: figure-01
  type: image
  path: enade-2011-computing-d03/figure-01.png
  source_page: 18
  extraction_method: raster_crop
  sha256: acc9ec93cf7ecbc515bd5c51eaba75cfe83188a9a63326ab9044ad97f614b294
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

# Questão 3

Os números de Fibonacci correspondem à uma sequência infinita na qual os dois primeiros termos são 0 e 1. Cada termo da sequência, à exceção dos dois primeiros, é igual à soma dos dois anteriores, conforme a relação de recorrência abaixo.

![Figura da questão](enade-2011-computing-d03/figure-01.png)

Desenvolva dois algoritmos, um iterativo e outro recursivo, que, dado um número natural n > 0, retorna o n-ésimo termo da sequência de Fibonacci. Apresente as vantagens e desvantagens de cada algoritmo. (valor: 10,0 pontos)
