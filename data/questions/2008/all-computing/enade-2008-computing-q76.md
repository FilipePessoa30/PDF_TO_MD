---
id: enade-2008-computing-q76
exam_year: 2008
source_occurrences:
- exam_id: enade-2008-b-computacao
  pdf_sha256: 5c8a08f7fdaccaa3b5661f40705e214bffdab634b845bce6288f8eeaa25db264
  source_path: 2008/b1_prova.pdf
  pages:
  - 32
  question_number: 76
  section: sistemas-informacao-objetiva
applicable_courses:
- sistemas-de-informacao
section: sistemas-informacao-objetiva
question_number: 76
question_type: multiple_choice
content_blocks: null
correct_answer: D
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

# Questão 76

Considere o esquema de relação Cliente(CPF, nome, RGemissor, RGnro, endereco, loginemail, dominioemail) e as seguintes dependências funcionais (DF) válidas sobre o esquema: DF1: CPF ÷ nome, RGemissor, RGnro, endereco, loginemail, dominioemail DF2: RGemissor, RGnro ÷ CPF, nome, endereco, loginemail, dominioemail DF3: loginemail, dominioemail ÷ CPF Qual é o conjunto completo de chaves candidatas de Cliente e em que forma normal mais alta essa relação está?

## Alternativas

A. {(RGemissor, RGnro), (CPF)}, na Forma Normal de Boyce- Codd (FNBC).
B. {(RGemissor, RGnro), (CPF)}, na Segunda Forma Normal (2FN).
C. {(loginemail, dominioemail)}, na Forma Normal de Boyce- Codd (FNBC).
D. {(RGemissor, RGnro), (loginemail, dominioemail), (CPF)}, na Forma Normal de Boyce-Codd (FNBC).
E. {(RGemissor, RGnro), (loginemail, dominioemail), (CPF)}, na Segunda Forma Normal (2FN).
