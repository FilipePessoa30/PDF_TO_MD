---
id: enade-2021-cc-b-q32
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-b
  pdf_sha256: 0254b274cc4adddbb503cf18553ee70c26014cbb0848fe3c5b787c80137b11e8
  source_path: 2021/b1_prova.pdf
  pages:
  - 41
  question_number: 32
  section: componente-especifico-objetiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: componente-especifico-objetiva
question_number: 32
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: 'Existe um grande número de implementações para algoritmos de ordenação. Um
    dos fatores a serem considerados, por exemplo, é o número máximo e médio de comparações
    que são necessárias para ordenar um vetor com n elementos. Diz-se também que um
    algoritmo de ordenação é estável se ele preserva a ordem de elementos que são
    iguais. Isto é, se tais elementos aparecem na sequência ordenada na mesma ordem
    em que estão na sequência inicial. Analise o algoritmo abaixo, onde A é um vetor
    e “i, j, lo e hi” são índices do vetor:'
- type: code
  text: "algoritmo ordena(A, lo, hi)\n    se lo < hi então\n       p := particao(A,\
    \ lo, hi)\n       ordena(A, lo, p - 1)\n       ordena(A, p + 1, hi)"
  language: null
- type: code
  text: "algoritmo particao(A, lo, hi)\n    pivot := A[hi]\n    i := lo\n    repita\
    \ para j := lo até hi\n       se A[j] < pivot entao\n       troca A[i] com A[j]\n\
    \       i := i + 1\n    troca A[i] com A[hi]\n    return i"
  language: null
- type: paragraph
  text: Com relação ao algoritmo apresentado, avalie as afirmações a seguir. I. O
    algoritmo precisa de um espaço adicional O(n) para a pilha de recursão. II. O
    algoritmo apresentado é um algoritmo de ordenação recursivo e estável. III. O
    algoritmo precisa, em média, de O(n log n) comparações para ordenar n itens. IV.
    O uso do primeiro elemento do vetor como “pivot” é mais eficiente que usar o último.
    É correto apenas o que se afirma em
correct_answer: A
official_answer_source: 2021/b2_gabarito.pdf
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
extraction_status: verified
automatic_validation: passed
visual_validation: passed
taxonomy_review_status: pending
---

# Questão 32

Existe um grande número de implementações para algoritmos de ordenação. Um dos fatores a serem considerados, por exemplo, é o número máximo e médio de comparações que são necessárias para ordenar um vetor com n elementos. Diz-se também que um algoritmo de ordenação é estável se ele preserva a ordem de elementos que são iguais. Isto é, se tais elementos aparecem na sequência ordenada na mesma ordem em que estão na sequência inicial. Analise o algoritmo abaixo, onde A é um vetor e “i, j, lo e hi” são índices do vetor:

```
algoritmo ordena(A, lo, hi)
    se lo < hi então
       p := particao(A, lo, hi)
       ordena(A, lo, p - 1)
       ordena(A, p + 1, hi)
```

```
algoritmo particao(A, lo, hi)
    pivot := A[hi]
    i := lo
    repita para j := lo até hi
       se A[j] < pivot entao
       troca A[i] com A[j]
       i := i + 1
    troca A[i] com A[hi]
    return i
```

Com relação ao algoritmo apresentado, avalie as afirmações a seguir. I. O algoritmo precisa de um espaço adicional O(n) para a pilha de recursão. II. O algoritmo apresentado é um algoritmo de ordenação recursivo e estável. III. O algoritmo precisa, em média, de O(n log n) comparações para ordenar n itens. IV. O uso do primeiro elemento do vetor como “pivot” é mais eficiente que usar o último. É correto apenas o que se afirma em

## Alternativas

A. I e III.
B. II e IV.
C. III e IV.
D. I, II e III.
E. I, II e IV.
