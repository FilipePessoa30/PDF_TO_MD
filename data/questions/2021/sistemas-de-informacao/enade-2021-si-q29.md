---
id: enade-2021-si-q29
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-s
  pdf_sha256: 13d81a46488d93fb66836e7c704f9de1ba722c3b130ccb4f0aa9d3522c855ba7
  source_path: 2021/s1_prova.pdf
  pages:
  - 32
  - 33
  question_number: 29
  section: componente-especifico-objetiva
applicable_courses:
- sistemas-de-informacao
section: componente-especifico-objetiva
question_number: 29
question_type: multiple_choice
content_blocks: null
correct_answer: D
official_answer_source: 2021/s2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: diagram
  path: enade-2021-si-q29/figure-01.png
  source_page: 32
  extraction_method: raster_crop
  sha256: 0ebd55f91a13049816efc5af4f8ba52d1fb93d1992aa02d5097ba758038e2208
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

# Questão 29

Suponha que, como projetista de dados, você precisa desenvolver um sistema para uma clínica médica. Após consultar todos os envolvidos, foi proposto o seguinte modelo de entidades e relacionamentos.

![Figura da questão](enade-2021-si-q29/figure-01.png)

Considerando esse contexto e o modelo de entidades e relacionamentos proposto, avalie as afirmações a seguir. I. A restrição de participação da entidade MÉDICO é total, pois um médico precisa atuar em pelo menos uma área da medicina; com relação à ESPECIALIDADE, a restrição é parcial, pois pode haver especialidade sem nenhum médico associado. II. A restrição de participação de PACIENTE é parcial, pois não é obrigatório o PACIENTE ter dependentes; já para DEPENDENTE a restrição é total, uma vez que é preciso ter um responsável (PACIENTE) cadastrado no banco de dados. III. A restrição de participação de PACIENTE é parcial, já que se pode ter o cadastro do paciente no banco de dados sem ter consulta marcada; já para CONSULTA a restrição é total, uma vez que uma consulta somente pode ser agendada para um paciente cadastrado. IV. A razão da cardinalidade é 1:N, pois um paciente pode marcar várias consultas, em dias e horários diferentes, e a consulta (em data e horário específicos) pode ser agendada para vários pacientes. É correto apenas o que se afirma em

## Alternativas

A. I e III.
B. II e IV.
C. III e IV.
D. I, II e III.
E. I, II e IV.
