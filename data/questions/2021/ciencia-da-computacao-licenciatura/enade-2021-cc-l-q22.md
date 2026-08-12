---
id: enade-2021-cc-l-q22
exam_year: 2021
source_occurrences:
- exam_id: enade-2021-l
  pdf_sha256: 9537deb2d2d7f7e00eacd526a06b887e932fedf4b5e7abf9be6501138d561b72
  source_path: 2021/l1_prova.pdf
  pages:
  - 29
  question_number: 22
  section: componente-especifico-objetiva
applicable_courses:
- ciencia-da-computacao-licenciatura
section: componente-especifico-objetiva
question_number: 22
question_type: multiple_choice
content_blocks: null
correct_answer: A
official_answer_source: 2021/l2_gabarito.pdf
answer_validation_status: validated
answer_standard: null
assets:
- id: figure-01
  type: diagram
  path: enade-2021-cc-l-q22/figure-01.png
  source_page: 29
  extraction_method: raster_crop
  sha256: 6a36dcb4e410c1fd7fad80581d13eab7ed9501d85b92dfd4f1a77f00fe94ea75
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

# Questão 22

Uma Organização Não Governamental (ONG), relacionada à causa animal, registra os pets (animais de estimação) amparados por ela, de acordo com o seguinte Diagrama Entidade Relacionamento (DER).

![Figura da questão](enade-2021-cc-l-q22/figure-01.png)

A partir das regras de mapeamento do Modelo Conceitual para o Modelo Lógico Relacional, assinale o

## Alternativas

A. PESSOA(cpf: texto, nome: texto) TIPO_PET(codigo: inteiro, descricao: texto) PET(codigo: inteiro, nome: texto, data_nascimento: data, codigo_tipo_pet: inteiro, adotante: texto) codigo_tipo_pet referencia TIPO_PET(codigo) adotante referencia PESSOA(cpf)
B. PET(codigo: inteiro, nome: texto, data_nascimento: data) PESSOA(cpf: texto, nome: texto, codigo_pet: inteiro) codigo_pet referencia PET(codigo) TIPO_PET(codigo: inteiro, descricao: texto, codigo_pet: inteiro) codigo_pet referencia PET(codigo)
C. TIPO_PET(codigo: inteiro, descricao: texto) PET(codigo: inteiro, nome: texto, data_nascimento: data, codigo_tipo_pet: inteiro) codigo_tipo_pet referencia TIPO_PET(codigo) PESSOA(cpf: texto, nome: texto, codigo_pet: inteiro) codigo_pet referencia PET(codigo)
D. PET_PESSOA(codigo_pet: inteiro, nome_pet: texto, data_nascimento: data, cpf: texto, nome_pessoa: texto, codigo_tipo_pet: inteiro, descricao_tipo_pet: texto)
E. PESSOA(cpf: texto, nome: texto) PET(codigo: inteiro, nome: texto, data_nascimento: data, codigo_tipo_pet: inteiro, descricao_tipo_pet, adotante: texto) adotante referencia PESSOA(cpf)
