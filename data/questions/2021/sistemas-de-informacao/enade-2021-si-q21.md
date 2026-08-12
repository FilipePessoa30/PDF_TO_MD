---
id: enade-2021-si-q21
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-s
  pdf_sha256: 13d81a46488d93fb66836e7c704f9de1ba722c3b130ccb4f0aa9d3522c855ba7
  source_path: 2021/s1_prova.pdf
  pages:
  - 24
  question_number: 21
  section: componente-especifico-objetiva
applicable_courses:
- sistemas-de-informacao
section: componente-especifico-objetiva
question_number: 21
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: Dado o controle de estoques de uma empresa de produção e embarque de peças,
    observe a descrição do esquema relacional abaixo para as tabelas Peça, Fornecedor
    e Embarque.
- type: code
  text: 'Peça(CodPeça, NomePeça, CorPeça, PesoPeça)

    Fornecedor(CodFornecedor, NomeFornecedor, StatusFornecedor)'
  language: null
- type: paragraph
  text: Embarque(CodPeça, CodFornecedor, QuantidadeEmbarque), tal que CodPeça
- type: code
  text: 'referencia Peça e CodFornecedor

    referencia Fornecedor.'
  language: null
- type: paragraph
  text: Considere que os atributos sublinhados no esquema relacional representam as
    chaves primárias das tabelas. Considere, ainda, que é necessário executar um comando
    Structured Query Language (SQL) que recupere todas as tuplas na base de dados
    (CodPeça,NomePeça) que possuem a quantidade de peças embarcadas maior do que 100.
    Com base nessas informações, avalie os comandos a seguir. I. SELECT Embarque.CodPeça,
    Peça.NomePeça
- type: code
  text: "FROM Peça WHERE CodPeça IN\n      (SELECT Embarque.CodPeça\n       FROM Embarque\n\
    \       WHERE Embarque.QuantidadeEmbarque > 100);"
  language: null
- type: paragraph
  text: II. SELECT Peça.CodPeça, Peça.NomePeça
- type: code
  text: "FROM Peça Embarque\n\aWHERE\n             Peça.CodPeça\n                \
    \                   =\n                                           Embarque.CodPeça\n\
    \                                                                     AND\nEmbarque.QuantidadeEmbarque\
    \ > 100;"
  language: null
- type: paragraph
  text: III. SELECT P.CodPeça, P.NomePeça
- type: code
  text: "\aFROM Peça P JOIN Embarque E ON P.CodPeça = E.CodPeça AND\nE.QuantidadeEmbarque\
    \ > 100;"
  language: null
- type: paragraph
  text: IV. SELECT CodPeça, NomePeça
- type: code
  text: "\aFROM Peça JOIN Embarque ON Peça.CodPeça = Embarque.CodPeça AND\nEmbarque.QuantidadeEmbarque\
    \ > 100;"
  language: null
- type: paragraph
  text: São comandos SQL que promovem a recuperação da informação apenas os descritos
    em
correct_answer: C
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

# Questão 21

Dado o controle de estoques de uma empresa de produção e embarque de peças, observe a descrição do esquema relacional abaixo para as tabelas Peça, Fornecedor e Embarque.

```
Peça(CodPeça, NomePeça, CorPeça, PesoPeça)
Fornecedor(CodFornecedor, NomeFornecedor, StatusFornecedor)
```

Embarque(CodPeça, CodFornecedor, QuantidadeEmbarque), tal que CodPeça

```
referencia Peça e CodFornecedor
referencia Fornecedor.
```

Considere que os atributos sublinhados no esquema relacional representam as chaves primárias das tabelas. Considere, ainda, que é necessário executar um comando Structured Query Language (SQL) que recupere todas as tuplas na base de dados (CodPeça,NomePeça) que possuem a quantidade de peças embarcadas maior do que 100. Com base nessas informações, avalie os comandos a seguir. I. SELECT Embarque.CodPeça, Peça.NomePeça

```
FROM Peça WHERE CodPeça IN
      (SELECT Embarque.CodPeça
       FROM Embarque
       WHERE Embarque.QuantidadeEmbarque > 100);
```

II. SELECT Peça.CodPeça, Peça.NomePeça

```
FROM Peça Embarque
WHERE
             Peça.CodPeça
                                   =
                                           Embarque.CodPeça
                                                                     AND
Embarque.QuantidadeEmbarque > 100;
```

III. SELECT P.CodPeça, P.NomePeça

```
FROM Peça P JOIN Embarque E ON P.CodPeça = E.CodPeça AND
E.QuantidadeEmbarque > 100;
```

IV. SELECT CodPeça, NomePeça

```
FROM Peça JOIN Embarque ON Peça.CodPeça = Embarque.CodPeça AND
Embarque.QuantidadeEmbarque > 100;
```

São comandos SQL que promovem a recuperação da informação apenas os descritos em

## Alternativas

A. I e II.
B. I e IV.
C. II e III.
D. I, III e IV.
E. II, III e IV.
