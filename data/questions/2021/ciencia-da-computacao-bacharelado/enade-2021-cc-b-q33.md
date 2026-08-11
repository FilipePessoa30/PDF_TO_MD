---
id: enade-2021-cc-b-q33
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-b
  pdf_sha256: 0254b274cc4adddbb503cf18553ee70c26014cbb0848fe3c5b787c80137b11e8
  source_path: 2021/b1_prova.pdf
  pages:
  - 42
  question_number: 33
  section: componente-especifico-objetiva
applicable_courses:
- ciencia-da-computacao-bacharelado
section: componente-especifico-objetiva
question_number: 33
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: A linguagem PROLOG pertence ao paradigma da programação lógica, no qual a
    lógica proposicional e algorítmica pode ser expressa na forma de descritores de
    fatos e regras de produção de respostas. No contexto da árvore genealógica de
    uma família, analise a seguinte base de fatos descrita em linguagem Prolog.
- type: code
  text: 'paide(ana,francisco).

    paide(maria,francisco).

    paide(luiz,francisco).

    maede(jose,maria).

    maede(angelica,ana).

    paide(luiza,luiz).

    paide(joaquim,luiz).

    homem(francisco).

    homem(jose).

    homem(luiz).

    homem(joaquim).

    mulher(ana).

    mulher(maria).

    mulher(angelica).

    mulher(luiza)'
  language: null
- type: paragraph
  text: Qual regra lógica de produção está corretamente escrita para verificar uma
    das situações lógicas em que duas pessoas são irmãs?
correct_answer: null
official_answer_source: 2021/b2_gabarito.pdf
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

# Questão 33

A linguagem PROLOG pertence ao paradigma da programação lógica, no qual a lógica proposicional e algorítmica pode ser expressa na forma de descritores de fatos e regras de produção de respostas. No contexto da árvore genealógica de uma família, analise a seguinte base de fatos descrita em linguagem Prolog.

```
paide(ana,francisco).
paide(maria,francisco).
paide(luiz,francisco).
maede(jose,maria).
maede(angelica,ana).
paide(luiza,luiz).
paide(joaquim,luiz).
homem(francisco).
homem(jose).
homem(luiz).
homem(joaquim).
mulher(ana).
mulher(maria).
mulher(angelica).
mulher(luiza)
```

Qual regra lógica de produção está corretamente escrita para verificar uma das situações lógicas em que duas pessoas são irmãs?

## Alternativas

A. saoirmas(X,Y):-paide(X,P), paide(Y,P), X\=Y.
B. saoirmas(X,Y):-paide(X,P), paide(Y,P), X\=Y, mulher(X).
C. saoirmas(X,Y):-paide(X,P), paide(Y,P), X\=Y, mulher(X,Y).
D. saoirmas(X,Y):-paide(X,P), paide(Y,P), X\=Y, mulher(X), mulher(Y).
E. saoirmas(X,Y):-paide(X,P), maede(Y,M), X\=Y, mulher(X), mulher(Y).
