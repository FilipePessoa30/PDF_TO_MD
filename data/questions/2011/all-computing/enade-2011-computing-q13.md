---
id: enade-2011-computing-q13
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 10
  question_number: 13
  section: componente-especifico-comum-objetiva
applicable_courses:
- all-computing
section: componente-especifico-comum-objetiva
question_number: 13
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: O problema do escalonamento de intervalos tem como entrada um conjunto de
    intervalos numéricos (usualmente interpretados como início e fim de atividades),
    e o objetivo é escolher, desse conjunto, o maior número possível de intervalos
    disjuntos dois a dois. Há vários problemas práticos que podem ser modelados dessa
    forma, como, por exemplo, a seleção de tarefas com horário marcado. O problema
    do escalonamento de intervalos pode ser resolvido com o algoritmo descrito a seguir.
    O conjunto de intervalos dados inicialmente é R e o conjunto de intervalos escolhidos,
    A, começa vazio.
- type: code
  text: "enquanto R não estiver vazio,\n    seja x o intervalo de R com menor tempo\n\
    de término, e que não tenha interseção com\nalgum intervalo em A\n    retire x\
    \ de R e adicione ao conjunto A\nretorne A"
  language: null
- type: paragraph
  text: A respeito desse algoritmo, analise as seguintes asserções. Para checar se
    o algoritmo está correto, basta verificar que o primeiro intervalo adicionado
    ao conjunto A necessariamente faz parte de uma solução ótima. PORQUE Pode-se mostrar,
    por indução no número máximo de intervalos calculados (ou seja, no número de vezes
    que o laço “enquanto” é executado), que, embora possa haver soluções tão boas
    quanto A, nenhuma delas é estritamente melhor que A. O conjunto com um único intervalo
    é a base de indução. Acerca dessas asserções, assinale a opção correta.
correct_answer: null
official_answer_source: 2011/2_gabarito.pdf
answer_validation_status: annulled
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

# Questão 13

O problema do escalonamento de intervalos tem como entrada um conjunto de intervalos numéricos (usualmente interpretados como início e fim de atividades), e o objetivo é escolher, desse conjunto, o maior número possível de intervalos disjuntos dois a dois. Há vários problemas práticos que podem ser modelados dessa forma, como, por exemplo, a seleção de tarefas com horário marcado. O problema do escalonamento de intervalos pode ser resolvido com o algoritmo descrito a seguir. O conjunto de intervalos dados inicialmente é R e o conjunto de intervalos escolhidos, A, começa vazio.

```
enquanto R não estiver vazio,
    seja x o intervalo de R com menor tempo
de término, e que não tenha interseção com
algum intervalo em A
    retire x de R e adicione ao conjunto A
retorne A
```

A respeito desse algoritmo, analise as seguintes asserções. Para checar se o algoritmo está correto, basta verificar que o primeiro intervalo adicionado ao conjunto A necessariamente faz parte de uma solução ótima. PORQUE Pode-se mostrar, por indução no número máximo de intervalos calculados (ou seja, no número de vezes que o laço “enquanto” é executado), que, embora possa haver soluções tão boas quanto A, nenhuma delas é estritamente melhor que A. O conjunto com um único intervalo é a base de indução. Acerca dessas asserções, assinale a opção correta.

## Alternativas

A. As duas asserções são proposições verdadeiras, e a segunda é uma justificativa correta da primeira.
B. As duas asserções são proposições verdadeiras, mas a segunda não é uma justificativa correta da primeira.
C. A primeira asserção é uma proposição verdadeira, e a segunda, uma proposição falsa.
D. A segunda asserção é uma proposição falsa e a segunda, uma proposição verdadeira.
E. Tanto a primeira quanto a segunda asserções são proposições falsas.
