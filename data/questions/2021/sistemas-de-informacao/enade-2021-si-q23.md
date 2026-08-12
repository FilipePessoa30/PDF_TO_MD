---
id: enade-2021-si-q23
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-s
  pdf_sha256: 13d81a46488d93fb66836e7c704f9de1ba722c3b130ccb4f0aa9d3522c855ba7
  source_path: 2021/s1_prova.pdf
  pages:
  - 26
  - 27
  question_number: 23
  section: componente-especifico-objetiva
applicable_courses:
- sistemas-de-informacao
section: componente-especifico-objetiva
question_number: 23
question_type: multiple_choice
content_blocks: null
correct_answer: B
official_answer_source: 2021/s2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: diagram
  path: enade-2021-si-q23/figure-01.png
  source_page: 26
  extraction_method: raster_crop
  sha256: d3ef8e60a4bc39dfc4c9bcde47bc12c02a7c934b876756146bed70d4798a371e
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
extraction_status: extracted
automatic_validation: passed
visual_validation: not_performed
taxonomy_review_status: pending
---

# Questão 23

É possível recuperar conjuntos de dados de forma organizada e que façam sentido para gerar informações. Nesse contexto, a recuperação de informações gravadas nos bancos de dados ocorre por meio de consultas SQL - Structured Query Language (linguagem de consulta de dados estruturados). Considere o seguinte conjunto de tabelas de banco de dados:

![Figura da questão](enade-2021-si-q23/figure-01.png)

Com base nas informações apresentadas, qual das seguintes consultas traria o nome dos motoristas que reservaram os carros vermelhos?

## Alternativas

A. SELECT M.NOME FROM MOTORISTA M WHERE M.IDMOTO IN (SELECT R.IDMOTO FROM RESERVAS R WHERE R.IDCARRO NOT IN (SELECT C.IDCARRO FROM CARRO C WHERE C.COR = ‘Vermelho’))
B. SELECT M.NOME FROM MOTORISTA M WHERE M.IDMOTO IN (SELECT R.IDMOTO FROM RESERVAS R WHERE R.IDCARRO IN (SELECT C.IDCARRO FROM CARRO C WHERE C.COR = ‘Vermelho’))
C. SELECT M.NOME FROM MOTORISTA M WHERE M.IDMOTO IN (SELECT R.IDMOTO FROM RESERVAS R WHERE R.IDCARRO NOT IN (SELECT C.IDCARRO FROM CARRO C WHERE C.COR = ‘Vermelho’))
D. SELECT M.NOME FROM MOTORISTA M WHERE M.IDMOTO NOT IN (SELECT R.IDMOTO FROM RESERVAS R WHERE R.IDCARRO NOT IN (SELECT C.IDCARRO FROM CARRO C WHERE C.COR = ‘Vermelho’))
E. SELECT M.NOME FROM MARINHEIROS M WHERE M.IDMARI NOT IN (SELECT R.IDMARI FROM RESERVAS R WHERE R.IDBARCO ANY (SELECT B.IDBARCO FROM BARCO B WHERE B.COR = ‘Vermelho’))
