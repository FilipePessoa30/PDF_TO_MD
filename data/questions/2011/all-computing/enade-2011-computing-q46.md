---
id: enade-2011-computing-q46
exam_year: 2011
source_occurrences:
- exam_id: enade-2011-unificado
  pdf_sha256: eb3b497f0d0967b1b6d063784c3012e719d1758ba182e4f6d6e6e47151934548
  source_path: 2011/1_prova.pdf
  pages:
  - 30
  question_number: 46
  section: componente-especifico-objetiva
applicable_courses:
- sistemas-de-informacao
section: componente-especifico-objetiva
question_number: 46
question_type: multiple_choice
content_blocks: null
correct_answer: A
official_answer_source: 2011/2_gabarito.pdf
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

# Questão 46

Em um modelo de dados que descreve a publicação acadêmica de pesquisadores de diferentes instituições em eventos acadêmicos, considere as tabelas abaixo. DEPARTAMENTO (#CodDepartamento, NomeDepartamento) EMPREGADO (#CodEmpregado, NomeEmpregado, CodDepartamento, Salario) Na linguagem SQL, o comando mais simples para recuperar os códigos dos departamentos cuja média salarial seja maior que 2000 é

## Alternativas

A. SELECT CodDepartamento FROM EMPREGADO GROUP BY CodDepartamento HAVING AVG (Salario) > 2000
B. SELECT CodDepartamento FROM EMPREGADO WHERE AVG (Salario) > 2000 GROUP BY CodDepartamento
C. SELECT CodDepartamento FROM EMPREGADO WHERE AVG (Salario) > 2000
D. SELECT CodDepartamento, AVG (Salario) > 2000 FROM EMPREGADO GROUP BY CodDepartamento
E. SELECT CodDepartamento FROM EMPREGADO GROUP BY CodDepartamento ORDER BY AVG (Salario) > 2000
