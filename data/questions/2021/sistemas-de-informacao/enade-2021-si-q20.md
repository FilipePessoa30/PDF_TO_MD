---
id: enade-2021-si-q20
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-s
  pdf_sha256: 13d81a46488d93fb66836e7c704f9de1ba722c3b130ccb4f0aa9d3522c855ba7
  source_path: 2021/s1_prova.pdf
  pages:
  - 23
  question_number: 20
  section: componente-especifico-objetiva
applicable_courses:
- sistemas-de-informacao
section: componente-especifico-objetiva
question_number: 20
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: 'O paradigma de programação em lógica constitui-se como um processo de definição
    de relações em que se constroem fatos e regras sobre os elementos e suas relações.
    A ativação dos programas acontece por meio de consultas (ou perguntas) sobre o
    relacionamento definido. Ao construir-se um banco de dados referente a uma família,
    inicia-se pelas relações de parentesco, tais como: pai(joão,maria) convencionado
    que joão é pai de maria mãe(maria,luiz) convencionado que maria é mãe de luiz
    As cláusulas, sem condições, definem os fatos sobre o domínio do problema. De
    outra maneira, é possível definir as regras que são cláusulas com condições:'
- type: code
  text: avô_materno(joão,luiz):-pai(joão,maria), mãe(maria,luiz)
  language: null
- type: paragraph
  text: Nesse contexto, avalie as afirmações a seguir. I. A consulta mãe(maria, X)
    retorna verdadeiro conforme identificado na cláusula. II. A conclusão joão é avô
    materno de luiz é identificada como cabeça da cláusula. III. A regra irmão(X,Y):-pai(Z,
    X), pai(Z, Y) é uma regra genérica que define irmãos por parte de pai. IV. A regra
    avo_materno(X,Y):-pai(Z,X), mae(Y,Z) é uma regra genérica para o programa. É correto
    apenas o que se afirma em
correct_answer: B
official_answer_source: 2021/s2_gabarito.pdf
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

# Questão 20

O paradigma de programação em lógica constitui-se como um processo de definição de relações em que se constroem fatos e regras sobre os elementos e suas relações. A ativação dos programas acontece por meio de consultas (ou perguntas) sobre o relacionamento definido. Ao construir-se um banco de dados referente a uma família, inicia-se pelas relações de parentesco, tais como: pai(joão,maria) convencionado que joão é pai de maria mãe(maria,luiz) convencionado que maria é mãe de luiz As cláusulas, sem condições, definem os fatos sobre o domínio do problema. De outra maneira, é possível definir as regras que são cláusulas com condições:

```
avô_materno(joão,luiz):-pai(joão,maria), mãe(maria,luiz)
```

Nesse contexto, avalie as afirmações a seguir. I. A consulta mãe(maria, X) retorna verdadeiro conforme identificado na cláusula. II. A conclusão joão é avô materno de luiz é identificada como cabeça da cláusula. III. A regra irmão(X,Y):-pai(Z, X), pai(Z, Y) é uma regra genérica que define irmãos por parte de pai. IV. A regra avo_materno(X,Y):-pai(Z,X), mae(Y,Z) é uma regra genérica para o programa. É correto apenas o que se afirma em

## Alternativas

A. I e II.
B. II e III.
C. III e IV.
D. I, II e IV.
E. I, III e IV.
