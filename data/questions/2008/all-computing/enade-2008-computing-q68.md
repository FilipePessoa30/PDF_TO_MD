---
id: enade-2008-computing-q68
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 29
  question_number: 68
  section: sistemas-informacao-objetiva
applicable_courses:
- sistemas-de-informacao
section: sistemas-informacao-objetiva
question_number: 68
question_type: multiple_choice
content_blocks:
- type: paragraph
  text: 'Considere as seguintes tabelas: CREATE TABLE Departamento ( IdDep int NOT
    NULL, NomeDep varchar(15), CONSTRAINT Departamentopkey PRIMARY KEY (IdDep) );
    CREATE TABLE Empregado ( IdEmpregado int NOT NULL, IdDep int, salario float, CONSTRAINT
    Empregadopkey PRIMARY KEY (IdEmpregado), CONSTRAINT EmpregadoIdDepfkey FOREIGN
    KEY (IdDep) REFERENCES Departamento(IdDep) ON UPDATE RESTRICT ON DELETE RESTRICT
    ) Considere as seguintes consultas SQL.'
- type: code
  text: I
  language: null
- type: paragraph
  text: SELECT NomeDep, count(*) FROM Departamento D, Empregado E WHERE D.IdDep=E.IdDep
    and E.salario > 10000 GROUP BY NomeDep HAVING count(*) > 5; II SELECT NomeDep,
    count(*) FROM Departamento D, Empregado E WHERE D.IdDep=E.IdDep and E.salario
    >10000 and E.IdDep IN (SELECT IdDep
- type: paragraph
  text: GROUP BY NomeDep; Quando as consultas acima são realizadas, o que é recuperado
    em cada uma delas? FROM Empregado GROUP BY IdDep HAVING count(*) > 5)
correct_answer: A
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

# Questão 68

Considere as seguintes tabelas: CREATE TABLE Departamento ( IdDep int NOT NULL, NomeDep varchar(15), CONSTRAINT Departamentopkey PRIMARY KEY (IdDep) ); CREATE TABLE Empregado ( IdEmpregado int NOT NULL, IdDep int, salario float, CONSTRAINT Empregadopkey PRIMARY KEY (IdEmpregado), CONSTRAINT EmpregadoIdDepfkey FOREIGN KEY (IdDep) REFERENCES Departamento(IdDep) ON UPDATE RESTRICT ON DELETE RESTRICT ) Considere as seguintes consultas SQL.

```
I
```

SELECT NomeDep, count(*) FROM Departamento D, Empregado E WHERE D.IdDep=E.IdDep and E.salario > 10000 GROUP BY NomeDep HAVING count(*) > 5; II SELECT NomeDep, count(*) FROM Departamento D, Empregado E WHERE D.IdDep=E.IdDep and E.salario >10000 and E.IdDep IN (SELECT IdDep

GROUP BY NomeDep; Quando as consultas acima são realizadas, o que é recuperado em cada uma delas? FROM Empregado GROUP BY IdDep HAVING count(*) > 5)

## Alternativas

A. I: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número de empregados nessa condição. II: os nomes dos departamentos que possuem mais de 5 empregados e o número de empregados que ganham mais de 10.000 reais.
B. I: os nomes dos departamentos que possuem mais de 5 empregados e o número de empregados que ganham mais de 10.000 reais. II: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número de empregados nessa condição.
C. I: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número total de funcionários do departamento. II: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número de empregados nessa condição.
D. I: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número de empregados nessa condição. II: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número total de funcionários do departamento.
E. I: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número de empregados nessa condição. II: os nomes dos departamentos que possuem mais de 5 empregados que ganham mais de 10.000 reais e o número de empregados nessa condição. FROM Empregado GROUP BY IdDep HAVING count(*) > 5)
